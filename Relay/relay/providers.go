package relay

import (
)

type Provider struct {
	Host string
	Port int
}

// CommonProviders maps domains to their SMTP settings
// GetUpstreamHost determines the SMTP server based on the email address
// Returns host, port, and true if found.
// Returns "", 0, false if not found (should fallback to default)
func GetUpstreamHost(email string) (string, int, bool) {
	// We want to force direct delivery or fallback to main config,
	// so we disable the hardcoded provider lookup.
	return "", 0, false
}
