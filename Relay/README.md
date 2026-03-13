# Simple SMTP Relay in Go

This is a lightweight SMTP relay server written in Go. It accepts incoming emails via SMTP and relays them to a configured upstream SMTP server.

## Prerequisites

- Go 1.18 or higher

## Installation

1.  **Dependencies**:
    Since `go mod init` might not have run successfully if `go` wasn't in the path, ensure you initialize the module and tidy dependencies:
    ```bash
    go mod tidy
    ```

2.  **Build**:
    ```bash
    go build -o smtp_relay .
    ```

## Configuration

The application is configured via environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `LISTEN_ADDR` | Address to listen on | `:2525` |
| `UPSTREAM_HOST` | Upstream SMTP Host | `smtp.gmail.com` |
| `UPSTREAM_PORT` | Upstream SMTP Port | `587` |
| `MAX_MESSAGE_SIZE` | Max size in bytes | `10485760` (10MB) |
| `DEBUG` | Enable debug logging | `false` |

## Web Dashboard

The application now includes a web dashboard to view email logs.
- **URL**: `http://localhost:8080`
- **Features**: List of emails, view details (Body, Headers), Status tracking.

## Persistence

Emails are stored in a local SQLite database (`emails.db`) created in the working directory.

## Usage

**Note:** This relay operates in **Real-time Proxy Mode**. It does not use static upstream credentials. Instead, it captures the credentials provided by the client (e.g., your script or mail client) and uses them to authenticate with the upstream server immediately.

1.  **Set Environment Variables**:
    Create a `.env` file or export variables in your shell.
    ```bash
    export UPSTREAM_HOST="smtp.gmail.com"
    export UPSTREAM_PORT=587
    export LISTEN_ADDR=":2525"
    ```

2.  **Run**:
    ```bash
    ./smtp_relay
    ```

3.  **View Dashboard**:
    Open [http://localhost:8080](http://localhost:8080) in your browser.

4.  **Test / Send Mail**:
    You **must** provide authentication matching the upstream server.
    ```bash
    swaks --to destinataire@example.com --from your-email@gmail.com \
      --auth-user your-email@gmail.com --auth-password "your-app-password" \
      --server localhost --port 2525
    ```

### From Windows (PowerShell)

**Option 1: Interactive (Pop-up)**
1.  Run: `$cred = Get-Credential`
2.  Enter your Gmail address and **App Password** (not your Google password).
3.  Run:
    ```powershell
    Send-MailMessage -From "your-email@gmail.com" -To "destinataire@example.com" `
        -Subject "Test" -Body "Hello" `
        -SmtpServer "localhost" -Port 2525 -Credential $cred
    ```

**Option 2: Script (No Pop-up)**
Replace with your real App Password:
```powershell
$User = "your-email@gmail.com"
$Pass = "xxxx xxxx xxxx xxxx" # Your 16-char App Password
$SecurePass = $Pass | ConvertTo-SecureString -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($User, $SecurePass)

Send-MailMessage -From $User -To "destinataire@example.com" `
    -Subject "Test App Password" -Body "It works!" `
    -SmtpServer "localhost" -Port 2525 -Credential $cred
```
