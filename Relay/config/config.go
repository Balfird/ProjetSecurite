package config

import (
	"os"
	"strconv"
)

// Config holds the application configuration
type Config struct {
	ListenAddr      string
	UpstreamHost    string
	UpstreamPort    int
	UpstreamUser    string
	UpstreamPass    string
	MaxMessageSize  int64 // bytes
	Debug           bool
	RedirectTo      string
}

// LoadConfig loads configuration from environment variables
func LoadConfig() *Config {
	return &Config{
		ListenAddr:     getEnv("LISTEN_ADDR", ":25"),
		UpstreamHost:   getEnv("UPSTREAM_HOST", ""),
		UpstreamPort:   getEnvAsInt("UPSTREAM_PORT", 0),
		UpstreamUser:   getEnv("UPSTREAM_USER", ""),
		UpstreamPass:   getEnv("UPSTREAM_PASS", ""),
		MaxMessageSize: int64(getEnvAsInt("MAX_MESSAGE_SIZE", 10*1024*1024)), // 10 MB default
		Debug:          getEnv("DEBUG", "false") == "true",
		RedirectTo:     getEnv("REDIRECT_TO", ""),
	}
}

func getEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}

func getEnvAsInt(key string, defaultVal int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return defaultVal
}
