package main

import (
	"log"
	"time"

	"github.com/Matthdd/SMTP_Relay/config"
	"github.com/Matthdd/SMTP_Relay/queue"
	"github.com/Matthdd/SMTP_Relay/relay"
	proxysmtp "github.com/Matthdd/SMTP_Relay/smtp"
	"github.com/Matthdd/SMTP_Relay/storage"
	"github.com/Matthdd/SMTP_Relay/web"
	"github.com/emersion/go-smtp"
	"github.com/emersion/go-sasl"
	"errors"
)


func main() {
	// 1. Load Config
	cfg := config.LoadConfig()
	log.Printf("Starting SMTP Relay on %s (Debug: %v)", cfg.ListenAddr, cfg.Debug)

	// 2. Initialize Storage
	store, err := storage.NewStore("emails.db")
	if err != nil {
		log.Fatalf("Failed to init storage: %v", err)
	}

	// 3. Initialize Web Server
	webServer := web.NewServer(store)
	go webServer.Start(":8080")

	// 4. Initialize Queue (Optional, can be kept for future or removed)
	q := queue.NewQueue()

	// 5. Initialize Sender
	sender := relay.NewSender(cfg)

	// 6. Start SMTP Server
	be := &proxysmtp.Backend{
		Queue:  q,
		Store:  store,
		Sender: sender,
		Cfg:    cfg,
	}

	s := smtp.NewServer(be)
	s.Addr = cfg.ListenAddr
	s.Domain = "localhost"
	s.ReadTimeout = 10 * time.Second
	s.WriteTimeout = 10 * time.Second
	s.MaxMessageBytes = cfg.MaxMessageSize
	s.MaxRecipients = 50
	s.AllowInsecureAuth = true // For relaying, often needed if no TLS certs locally

	s.EnableAuth(sasl.Login, func(conn *smtp.Conn) sasl.Server {
		return sasl.NewLoginServer(func(username, password string) error {
			if session, ok := conn.Session().(interface {
				AuthLogin(username, password string) error
			}); ok {
				return session.AuthLogin(username, password)
			}
			return errors.New("AuthLogin not supported by backend")
		})
	})

	log.Printf("Listening on %s...", s.Addr)
	if err := s.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}
