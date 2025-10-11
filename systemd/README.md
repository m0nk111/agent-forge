# Systemd Service Files

## Installation

Copy service files to systemd:

```bash
sudo cp systemd/agent-forge-polling.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable agent-forge-polling
sudo systemctl start agent-forge-polling
```

## Configuration

### Environment File

Create `/etc/agent-forge/tokens.env` with:

```bash
# Bot account for general operations (issues, PRs, comments)
BOT_GITHUB_TOKEN=ghp_your_bot_token_here
BOT_GITHUB_USERNAME=m0nk111-post
BOT_GITHUB_EMAIL=m0nk111.post@example.com

# Code agent for git operations (commits, pushes)
CODEAGENT_GITHUB_TOKEN=ghp_your_codeagent_token_here
CODEAGENT_GITHUB_USERNAME=m0nk111-qwen-agent
CODEAGENT_GITHUB_EMAIL=m0nk111.qwen.agent@example.com

# Default token (fallback)
GITHUB_TOKEN=${BOT_GITHUB_TOKEN}
GITHUB_USERNAME=${BOT_GITHUB_USERNAME}
```

Set correct permissions:

```bash
sudo chmod 600 /etc/agent-forge/tokens.env
sudo chown root:root /etc/agent-forge/tokens.env
```

## Token Updates

To update tokens:

1. Edit `/etc/agent-forge/tokens.env`
2. Restart service: `sudo systemctl restart agent-forge-polling`

**Note**: No need to edit systemd service files - tokens are loaded from environment file.

## Monitoring

```bash
# Check status
sudo systemctl status agent-forge-polling

# View logs
sudo journalctl -u agent-forge-polling -f

# Check for errors
sudo journalctl -u agent-forge-polling --since "10 minutes ago" | grep -i error
```
