# Fastmail TUI

Privacy-focused, AI-enhanced terminal email client for Fastmail.

## Features

- **Full Email Management** - Read, compose, reply, archive, delete
- **Masked Email Manager** - Create masked emails with generated passwords for new logins
- **Claude AI Integration** - Email summaries, smart replies, categorization
- **Vim-Style Navigation** - j/k, gg/G, / for search
- **IlluminatiNebula Theme** - Stunning cyan/purple terminal aesthetic

## Installation

```bash
pip install fastmail-tui
```

Or from source:
```bash
git clone https://github.com/pdubbbbbs/fastmail-tui
cd fastmail-tui
pip install .
```

## Setup

1. Get your Fastmail API token:
   - Go to Fastmail Settings → Privacy & Security → Integrations → API Tokens
   - Create a new token with Mail access

2. (Optional) Get Claude API key from console.anthropic.com

3. Run setup:
```bash
fm setup
```

## Usage

Launch the TUI:
```bash
fastmail-tui
# or
fm
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| j/k | Navigate down/up |
| gg/G | Go to top/bottom |
| / | Search |
| Enter | Open email |
| c | Compose |
| r | Reply |
| R | Reply all |
| f | Forward |
| a | Archive |
| d | Delete |
| s | Star |
| m | Masked emails |
| Ctrl+M | Quick new masked |
| Ctrl+S | AI summarize |
| q | Quit |

### Commands

```bash
# Setup credentials
fm setup

# Generate a password
fm generate-password
fm generate-password --memorable

# Configure options
fm configure --enable-ai
fm configure --refresh-interval 60

# Show config path
fm config-path

# Clear credentials
fm clear-credentials
```

## Configuration

Config file location: `~/.config/fastmail-tui/config.yaml`

```yaml
fastmail:
  host: api.fastmail.com

claude:
  enabled: true
  model: claude-sonnet-4-5

cache:
  enabled: true
  max_messages: 500

ui:
  vim_mode: true
  show_ai_panel: true
  refresh_interval: 30
  page_size: 50
```

## Masked Email Feature

Create disposable email addresses with secure passwords for new website signups:

1. Press `m` to open Masked Email Manager
2. Press `n` or click "Create Login Credentials"
3. Enter the website domain (e.g., `example.com`)
4. A new masked email and secure 24-character password are generated
5. Copy both to your password manager

## License

MIT
