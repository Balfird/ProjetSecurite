package storage

import (
	"database/sql"
	"fmt"
	"time"

	_ "modernc.org/sqlite"
)

type Email struct {
	ID          int
	From        string
	To          string // Stored as comma separated
	Subject     string
	Body        string // Stored as text (simplified)
	Status      string // Queued, Sent, Failed
	Error       string // Detailed error message
	CreatedAt   time.Time
	Attachments []Attachment
}

type Attachment struct {
	ID          int
	EmailID     int
	Filename    string
	Path        string
	Size        int64
	ContentType string
}

type Store struct {
	db *sql.DB
}

func NewStore(dbPath string) (*Store, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}

	query := `
	CREATE TABLE IF NOT EXISTS emails (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		sender TEXT,
		recipients TEXT,
		subject TEXT,
		body TEXT,
		status TEXT,
        created_at DATETIME
	);

	CREATE TABLE IF NOT EXISTS attachments (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		email_id INTEGER,
		filename TEXT,
		path TEXT,
		size INTEGER,
		content_type TEXT,
		FOREIGN KEY(email_id) REFERENCES emails(id)
	);
	`
	_, err = db.Exec(query)
	if err != nil {
		return nil, fmt.Errorf("failed to init db: %w", err)
	}

	// Migration: Add error column if not exists
	_, err = db.Exec("ALTER TABLE emails ADD COLUMN error TEXT")
	if err != nil {
		// Ignore error if column exists
	}

	// INDICES FOR OPTIMIZATION
	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_emails_created_at ON emails(created_at)")
	if err != nil {
		return nil, fmt.Errorf("failed to create index idx_emails_created_at: %w", err)
	}
	_, err = db.Exec("CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON attachments(email_id)")
	if err != nil {
		return nil, fmt.Errorf("failed to create index idx_attachments_email_id: %w", err)
	}

	return &Store{db: db}, nil
}

func (s *Store) SaveEmail(e *Email) error {
	query := `INSERT INTO emails (sender, recipients, subject, body, status, error, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`
	res, err := s.db.Exec(query, e.From, e.To, e.Subject, e.Body, e.Status, e.Error, time.Now())
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	e.ID = int(id)

	for _, a := range e.Attachments {
		queryAtt := `INSERT INTO attachments (email_id, filename, path, size, content_type) VALUES (?, ?, ?, ?, ?)`
		_, err := s.db.Exec(queryAtt, e.ID, a.Filename, a.Path, a.Size, a.ContentType)
		if err != nil {
			return fmt.Errorf("failed to save attachment %s: %w", a.Filename, err)
		}
	}

	return nil
}

func (s *Store) GetEmails(limit, offset int, statusFilter string) ([]Email, error) {
	// OPTIMIZATION: Body removed from selection
	query := "SELECT id, sender, recipients, subject, status, error, created_at FROM emails"
	var args []interface{}

	if statusFilter != "" {
		query += " WHERE status = ?"
		args = append(args, statusFilter)
	}

	query += " ORDER BY created_at DESC"

	if limit > 0 {
		query += " LIMIT ? OFFSET ?"
		args = append(args, limit, offset)
	}

	rows, err := s.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var emails []Email
	for rows.Next() {
		var e Email
		var errStr sql.NullString
		// Removed &e.Body from Scan
		if err := rows.Scan(&e.ID, &e.From, &e.To, &e.Subject, &e.Status, &errStr, &e.CreatedAt); err != nil {
			return nil, err
		}
		e.Error = errStr.String

		attRows, err := s.db.Query("SELECT id, email_id, filename, path, size, content_type FROM attachments WHERE email_id = ?", e.ID)
		if err != nil {
			// continue
		} else {
			for attRows.Next() {
				var a Attachment
				if err := attRows.Scan(&a.ID, &a.EmailID, &a.Filename, &a.Path, &a.Size, &a.ContentType); err == nil {
					e.Attachments = append(e.Attachments, a)
				}
			}
			attRows.Close()
		}

		emails = append(emails, e)
	}
	return emails, nil
}

// NEW FUNCTION: Retrieve single email with body
func (s *Store) GetEmail(id int) (*Email, error) {
	query := "SELECT id, sender, recipients, subject, body, status, error, created_at FROM emails WHERE id = ?"
	var e Email
	var errStr sql.NullString

	err := s.db.QueryRow(query, id).Scan(&e.ID, &e.From, &e.To, &e.Subject, &e.Body, &e.Status, &errStr, &e.CreatedAt)
	if err != nil {
		return nil, err
	}
	e.Error = errStr.String

	attQuery := "SELECT id, email_id, filename, path, size, content_type FROM attachments WHERE email_id = ?"
	rows, err := s.db.Query(attQuery, e.ID)
	if err != nil {
		return &e, nil
	}
	defer rows.Close()

	for rows.Next() {
		var a Attachment
		if err := rows.Scan(&a.ID, &a.EmailID, &a.Filename, &a.Path, &a.Size, &a.ContentType); err == nil {
			e.Attachments = append(e.Attachments, a)
		}
	}
	return &e, nil
}

func (s *Store) CountEmails(statusFilter string) (int, error) {
	query := "SELECT COUNT(*) FROM emails"
	var args []interface{}
	if statusFilter != "" {
		query += " WHERE status = ?"
		args = append(args, statusFilter)
	}

	var count int
	err := s.db.QueryRow(query, args...).Scan(&count)
	if err != nil {
		return 0, err
	}
	return count, nil
}

func (s *Store) DeleteEmail(id int) error {
	_, err := s.db.Exec("DELETE FROM attachments WHERE email_id = ?", id)
	if err != nil {
		return err
	}
	_, err = s.db.Exec("DELETE FROM emails WHERE id = ?", id)
	return err
}
