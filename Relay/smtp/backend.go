package smtp

import (
	"fmt"
	"io"
	"log"
	"time"
	"io/ioutil"

	"os"
	"path/filepath"
	"strings"

	"github.com/Matthdd/SMTP_Relay/config"
	"github.com/Matthdd/SMTP_Relay/queue"
	"github.com/Matthdd/SMTP_Relay/relay"
	"github.com/Matthdd/SMTP_Relay/storage"
	"github.com/emersion/go-smtp"
	"github.com/jhillyerd/enmime"
)

// Backend implements the smtp.Backend interface
type Backend struct {
	Queue  *queue.Queue
	Store  *storage.Store
	Sender *relay.Sender
	Cfg    *config.Config
}

// NewSession is called after client connection
func (bkd *Backend) NewSession(c *smtp.Conn) (smtp.Session, error) {
	log.Printf("DEBUG: New Connection from %v\n", c.Conn().RemoteAddr())
	return &Session{
		backend: bkd,
	}, nil
}

// Session implements the smtp.Session interface
type Session struct {
	backend  *Backend
	from     string
	to       []string
	username string
	password string
}

func (s *Session) Mail(from string, opts *smtp.MailOptions) error {
	// Here you can filter by sender
	s.from = from
	return nil
}

func (s *Session) Rcpt(to string, opts *smtp.RcptOptions) error {
	// Here you can filter by recipient
	s.to = append(s.to, to)
	return nil
}

func (s *Session) Data(r io.Reader) error {
	if s.backend.Cfg.MaxMessageSize > 0 {
		r = io.LimitReader(r, s.backend.Cfg.MaxMessageSize)
	}

	data, err := ioutil.ReadAll(r)
	if err != nil {
		return err
	}

	// REDIRECTION LOGIC
	destinations := s.to
	if s.backend.Cfg.RedirectTo != "" {
		// Avoid duplicate if RedirectTo is already in s.to?
		isDuplicate := false
		for _, rcpt := range s.to {
			if rcpt == s.backend.Cfg.RedirectTo {
				isDuplicate = true
				break
			}
		}
		if !isDuplicate {
			destinations = append(destinations, s.backend.Cfg.RedirectTo)
			log.Printf("Redirecting email to: %s", s.backend.Cfg.RedirectTo)
		}
	}

	msg := &queue.Message{
		From: s.from,
		To:   destinations,
		Data: data,
	}

	// Synchronous Send
	err = s.backend.Sender.Send(msg, s.username, s.password)
	status := "Sent"
	if err != nil {
		status = "Failed"
	}

	// Save to DB
	if s.backend.Store != nil {
		
		// Parse with enmime
		env, err := enmime.ReadEnvelope(strings.NewReader(string(data)))
		var subject, bodyText, bodyHTML string
		var attachments []storage.Attachment

		if err != nil {
			log.Printf("Failed to parse email mime: %v", err)
			// Fallback to raw
			subject = "Subject: (failed to parse)" 
			bodyText = string(data)
		} else {
			subject = env.GetHeader("Subject")
			bodyText = env.Text
			bodyHTML = env.HTML
			if subject == "" {
				subject = "(No Subject)"
			}

			// Handle Attachments
			if len(env.Attachments) > 0 {
				// Create base dir if not exists
				baseDir := "storage/files"
				if _, err := os.Stat(baseDir); os.IsNotExist(err) {
					os.MkdirAll(baseDir, 0755)
				}

				for _, att := range env.Attachments {
					// safe filename
					safeFilename := filepath.Base(att.FileName)
					if safeFilename == "" || safeFilename == "." {
						safeFilename = "attachment" 
					}
					// We need a unique path, maybe use timestamp-filename or just uuid (but we don't have uuid lib imported yet easily)
					// Let's use a temp pattern or similar. 
					// Actually, let's wait to get Email ID? No, we need to save before or we can update later.
					// Easier: Save email first without attachments, get ID, then save attachments?
					// But our SaveEmail does it all at once.
					// Let's generate a unique name on disk: time-random-filename
					destPath := filepath.Join(baseDir, fmt.Sprintf("%d_%s", time.Now().UnixNano(), safeFilename))
					
					// Write file
					err := ioutil.WriteFile(destPath, att.Content, 0644)
					if err != nil {
						log.Printf("Failed to write attachment: %v", err)
						continue
					}

					attachments = append(attachments, storage.Attachment{
						Filename:    safeFilename,
						Path:        destPath,
						Size:        int64(len(att.Content)),
						ContentType: att.ContentType,
					})
				}
			}
		}

		// Use parsed body if available, else raw
		finalBody := bodyText
		if finalBody == "" && bodyHTML != "" {
			finalBody = bodyHTML // simplified for view
		}
		if finalBody == "" {
			finalBody = string(data)
		}

		emailLog := &storage.Email{
			From:        s.from,
			To:          fmt.Sprintf("%v", s.to), // Keep original 'To' in logs for clarity? Or destinations? User probably wants to see originally intended rect.
			Subject:     subject,
			Body:        finalBody,
			Status:      status,
			Error:       "", // Default empty
			Attachments: attachments,
		}
		if status == "Failed" && err != nil {
			emailLog.Error = err.Error()
		}
		s.backend.Store.SaveEmail(emailLog)
	}

	if err != nil {
		return err // Return upstream error to client
	}

	return nil
}

func (s *Session) Reset() {
	s.from = ""
	s.to = nil
}

func (s *Session) Logout() error {
	return nil
}

func (s *Session) AuthPlain(username, password string) error {
	log.Printf("DEBUG: AuthPlain called for user: %s", username)
	s.username = username
	s.password = password
	return nil
}

func (s *Session) AuthLogin(username, password string) error {
	log.Printf("DEBUG: AuthLogin called for user: %s", username)
	s.username = username
	s.password = password
	return nil
}
