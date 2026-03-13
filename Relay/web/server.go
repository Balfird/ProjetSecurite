package web

import (
	"database/sql"
	"encoding/json"

	"html/template"
	"log"
	"math"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/Matthdd/SMTP_Relay/storage"
)

type PageData struct {
	Emails     []storage.Email
	Pagination Pagination
	Status     string
}

type Pagination struct {
	CurrentPage int
	TotalPages  int
	Limit       int
	TotalCount  int
	HasPrev     bool
	HasNext     bool
	PrevPage    int
	NextPage    int
}

const (
	AuthUser   = "user"
	AuthPass   = "mdppxk3y8t7Y8y"
	CookieName = "session_token"
)

type Server struct {
	store *storage.Store
}

func NewServer(store *storage.Store) *Server {
	return &Server{store: store}
}

func (s *Server) Start(addr string) {
	mux := http.NewServeMux()

	// Public routes
	mux.HandleFunc("/login", s.handleLogin)

	// Protected routes
	mux.HandleFunc("/", s.authMiddleware(s.handleIndex))
	mux.HandleFunc("/attachment/", s.authMiddleware(s.handleAttachment))
	mux.HandleFunc("/email/delete/", s.authMiddleware(s.handleDelete))
	// NEW: Detail route for AJAX
	mux.HandleFunc("/email/details/", s.authMiddleware(s.handleEmailDetails))

	log.Printf("Web Dashboard listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Printf("Web Server failed: %v", err)
	}
}

func (s *Server) authMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		c, err := r.Cookie(CookieName)
		if err != nil {
			http.Redirect(w, r, "/login", http.StatusSeeOther)
			return
		}

		if c.Value != "authenticated" {
			http.Redirect(w, r, "/login", http.StatusSeeOther)
			return
		}

		next(w, r)
	}
}

func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		tmplPath := "web/templates/login.html"
		tmpl, err := template.ParseFiles(tmplPath)
		if err != nil {
			http.Error(w, "Template not found: "+err.Error(), http.StatusInternalServerError)
			return
		}
		tmpl.Execute(w, nil)
		return
	}

	if r.Method == "POST" {
		u := r.FormValue("username")
		p := r.FormValue("password")

		if u == AuthUser && p == AuthPass {
			http.SetCookie(w, &http.Cookie{
				Name:    CookieName,
				Value:   "authenticated",
				Expires: time.Now().Add(24 * time.Hour),
				Path:    "/",
			})
			http.Redirect(w, r, "/", http.StatusSeeOther)
			return
		}

		tmplPath := "web/templates/login.html"
		tmpl, err := template.ParseFiles(tmplPath)
		if err != nil {
			http.Error(w, "Template error", http.StatusInternalServerError)
			return
		}
		tmpl.Execute(w, map[string]string{"Error": "Invalid credentials"})
	}
}

func (s *Server) handleAttachment(w http.ResponseWriter, r *http.Request) {
	relPath := strings.TrimPrefix(r.URL.Path, "/attachment/")
	relPath = strings.ReplaceAll(relPath, "..", "")

	if !strings.HasPrefix(relPath, "storage/files/") {
		http.NotFound(w, r)
		return
	}

	http.ServeFile(w, r, relPath)
}

func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	pageStr := r.URL.Query().Get("page")
	limitStr := r.URL.Query().Get("limit")
	statusFilter := r.URL.Query().Get("status")

	page, _ := strconv.Atoi(pageStr)
	if page < 1 {
		page = 1
	}

	limit, _ := strconv.Atoi(limitStr)
	if limit == 0 {
		limit = 50
	}

	offset := 0
	if limit > 0 {
		offset = (page - 1) * limit
	} else {
		page = 1
	}

	totalCount, err := s.store.CountEmails(statusFilter)
	if err != nil {
		http.Error(w, "Failed to count emails", http.StatusInternalServerError)
		return
	}

	emails, err := s.store.GetEmails(limit, offset, statusFilter)
	if err != nil {
		http.Error(w, "Failed to fetch emails", http.StatusInternalServerError)
		return
	}

	totalPages := 1
	if limit > 0 {
		totalPages = int(math.Ceil(float64(totalCount) / float64(limit)))
		if totalPages < 1 {
			totalPages = 1
		}
	}

	pagination := Pagination{
		CurrentPage: page,
		TotalPages:  totalPages,
		Limit:       limit,
		TotalCount:  totalCount,
		HasPrev:     page > 1,
		HasNext:     page < totalPages,
		PrevPage:    page - 1,
		NextPage:    page + 1,
	}

	// Pass status filter to template (we can misuse PageData or create a new struct, 
	// but I'll add it to the struct definition if needed. 
	// Actually PageData needs updating to hold the current filter so UI can reflect it.
	// But first let's just update the PageData struct definition.
	type PageData struct {
		Emails     []storage.Email
		Pagination Pagination
		Status     string
	}

	tmplPath := "web/templates/index.html"
	tmpl, err := template.ParseFiles(tmplPath)
	if err != nil {
		http.Error(w, "Template not found: "+err.Error(), http.StatusInternalServerError)
		return
	}

	err = tmpl.Execute(w, PageData{Emails: emails, Pagination: pagination, Status: statusFilter})
	if err != nil {
		http.Error(w, "Failed to render template", http.StatusInternalServerError)
	}
}

func (s *Server) handleDelete(w http.ResponseWriter, r *http.Request) {
	if r.Method != "DELETE" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}
	idStr := parts[3]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	err = s.store.DeleteEmail(id)
	if err != nil {
		http.Error(w, "Failed to delete email: "+err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (s *Server) handleEmailDetails(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}
	idStr := parts[3]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	email, err := s.store.GetEmail(id)
	if err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "Email not found", http.StatusNotFound)
		} else {
			http.Error(w, "Failed to fetch email: "+err.Error(), http.StatusInternalServerError)
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(email); err != nil {
		log.Printf("Failed to encode email JSON: %v", err)
	}
}
