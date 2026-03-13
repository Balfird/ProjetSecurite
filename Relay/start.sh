#!/bin/bash
set -e

# Setup Go environment
export PATH=$PATH:/usr/local/go/bin:/tmp/go/bin
export GOCACHE=/tmp/.cache
export GOPATH=/tmp/go_path
export DEBUG=true

# Resource Limits
export GOMAXPROCS=3
# Optional: Set memory limit if managed by systemd or container, but here we just rely on OS.
# 18GB is plenty for Go GC.

# Load configuration
if [ -f .env ]; then
    echo "Loading .env..."
    source .env
fi

echo "Using Go from: $(which go)"
go version

echo "Tidying dependencies..."
go mod tidy

# Ensure modernc.org/sqlite dependency is fetched if missing
go get modernc.org/sqlite

echo "Building binary..."
go build -o smtp_relay .

echo "Starting SMTP Relay..."
echo "SMTP Server: :2525"
echo "Web Dashboard: http://localhost:8080"

# Run in foreground or back?
# Existing script ran in foreground maybe? Or user runs it manually.
# I'll exec it so it replaces the shell process.
exec ./smtp_relay
