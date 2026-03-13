package relay

import (
	"crypto/tls"
	"fmt"
	"log"
	"net"
	"net/smtp"
	"strings"

	"github.com/Matthdd/SMTP_Relay/config"
	"github.com/Matthdd/SMTP_Relay/queue"
)

// Sender handles sending messages to the upstream server
type Sender struct {
	cfg *config.Config
}

// NewSender creates a new Sender
func NewSender(cfg *config.Config) *Sender {
	return &Sender{cfg: cfg}
}

// Send processes a message and sends it upstream
// Send processes a message and sends it upstream or directly to MX
func (s *Sender) Send(msg *queue.Message, username, password string) error {
	log.Println("CRITICAL DEBUG: Send function called - new code version")
	
	// 1. Try to get specific upstream for user (disabled now, but kept for logic structure)
	host, port, found := GetUpstreamHost(username)
	
	// 2. If not found, check if we have a global upstream configured
	// The user wants to avoid relaying to Gmail/Outlook for specific domains, so we should prioritize direct delivery
	// unless a global relay is strictly enforced.
	// However, the current config might have a default upstream.
	// Let's assume if UpstreamHost is empty or we want to force direct, we do MX lookup.
	
	var targets []string // List of "host:port" to try

	if !found && s.cfg.UpstreamHost != "" {
		// Use configured relay
		targets = append(targets, fmt.Sprintf("%s:%d", s.cfg.UpstreamHost, s.cfg.UpstreamPort))
	} else if found {
		targets = append(targets, fmt.Sprintf("%s:%d", host, port))
	} else {
		// 3. Direct Delivery via MX Lookup
		// We need to look up MX records for the recipient's domain.
		// Taking the first recipient's domain for simplicity (mass mailing might need splitting)
		if len(msg.To) == 0 {
			return fmt.Errorf("no recipients")
		}
		parts := strings.Split(msg.To[0], "@")
		if len(parts) != 2 {
			return fmt.Errorf("invalid recipient address: %s", msg.To[0])
		}
		domain := parts[1]

		mxRecords, err := net.LookupMX(domain)
		if err != nil {
			return fmt.Errorf("failed to lookup MX for %s: %w", domain, err)
		}
		if len(mxRecords) == 0 {
			return fmt.Errorf("no MX records found for %s", domain)
		}

		// Sort by preference is automatic usually, but good to be sure.
		// net.LookupMX returns sorted by preference.
		for _, mx := range mxRecords {
			// Trim trailing dot if present
			host := strings.TrimSuffix(mx.Host, ".")
			targets = append(targets, fmt.Sprintf("%s:25", host))
		}
	}

	// Try to deliver to targets
	var lastErr error
	for _, addr := range targets {
		log.Printf("DEBUG: Attempting delivery to %s", addr)
		
		// Extract host for TLS usage
		host, _, _ := net.SplitHostPort(addr)

		// Custom dialer to force IPv4
		log.Printf("DEBUG: Connecting to %s using IPv4...", addr)
		conn, err := net.Dial("tcp4", addr)
		if err != nil {
			log.Printf("DEBUG: Connection failed to %s: %v", addr, err)
			lastErr = err
			continue
		}

		// Create SMTP client
		c, err := smtp.NewClient(conn, host)
		if err != nil {
			conn.Close()
			log.Printf("DEBUG: SMTP client creation failed for %s: %v", addr, err)
			lastErr = err
			continue
		}
		
		// Allow defer c.Quit() to run when we leave this iteration scope? No, defer is function-scoped.
		// We must handle checking out manually or wrap in func.
		err = func() error {
			defer c.Quit()

			// Say HELO
			// Use our own hostname if possible, or localhost
			if err := c.Hello("localhost"); err != nil {
				return fmt.Errorf("failed to say HELO: %w", err)
			}

			// Use STARTTLS if supported and not skipped
			if ok, _ := c.Extension("STARTTLS"); ok {
				tlsConfig := &tls.Config{ServerName: host}
				if s.cfg.Debug {
					tlsConfig.InsecureSkipVerify = true
				}
				if err = c.StartTLS(tlsConfig); err != nil {
					log.Printf("DEBUG: STARTTLS failed for %s (continuing in plain text if allowed? No, usually fatal if offered): %v", addr, err)
					return fmt.Errorf("failed to STARTTLS: %w", err)
				}
			}

			// Authentication (Only if we are using a specific relay that requires it)
			// For MX direct delivery, we NEVER auth.
			// How do we know? If username is set and we're not doing direct MX.
			// But here username comes from the client connecting to US.
			// We only Auth to upstream if we have upstream creds.
			// The current code used `username` / `password` passed to Send, which were the credentials used by the client to auth to US.
			// This is wrong for relaying unless it's a proxy.
			// The user said "je veux conserver aucune authentification".
			// So we skip Auth completely.
			
			// Set sender and recipient
			if err := c.Mail(msg.From); err != nil {
				return fmt.Errorf("failed to set sender: %w", err)
			}
			for _, rcpt := range msg.To {
				if err := c.Rcpt(rcpt); err != nil {
					return fmt.Errorf("failed to set recipient %s: %w", rcpt, err)
				}
			}

			// Send Body
			w, err := c.Data()
			if err != nil {
				return fmt.Errorf("failed to open data writer: %w", err)
			}
			_, err = w.Write(msg.Data)
			if err != nil {
				return fmt.Errorf("failed to write data: %w", err)
			}
			err = w.Close()
			if err != nil {
				return fmt.Errorf("failed to close data writer: %w", err)
			}
			return nil
		}()

		if err == nil {
			return nil // Success!
		}
		
		log.Printf("DEBUG: Delivery failed to %s: %v", addr, err)
		lastErr = err
	}
	
	return fmt.Errorf("all delivery attempts failed. Last error: %w", lastErr)
}
