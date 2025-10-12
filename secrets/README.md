# Secrets Directory Structure

This directory contains API keys and authentication tokens for Agent-Forge.

## 📁 Directory Structure

```
secrets/
├── agents/              # GitHub bot account tokens (one file per account)
│   ├── m0nk111.token              # Admin account (for repo management)
│   ├── m0nk111-post.token         # Bot for issue detection, PR creation, comments
│   ├── m0nk111-qwen-agent.token   # Bot for git commits/pushes (codeagent)
│   ├── m0nk111-coder1.token       # Primary GPT-5 coder bot
│   ├── m0nk111-coder2.token       # Primary GPT-4o coder bot
│   └── m0nk111-reviewer.token     # Code review bot
│
├── keys/                # LLM API keys (one file per service)
│   ├── openai.key               # OpenAI API key
│   ├── openrouter.key           # OpenRouter API key (multi-model gateway)
│   ├── anthropic.key (future)   # Anthropic/Claude API key
│   └── ollama.key (future)      # Ollama API key (if needed)
│
└── keys.json            # ⚠️  DEPRECATED - DO NOT USE
                         # Legacy file, use agents/ and keys/ instead
```

## 🔑 Token File Format

Each token/key file contains **only the token/key string**, no additional formatting:

```
# agents/m0nk111.token
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# keys/openai.key
sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🔐 Security Notes

- **Never commit these files to git** (covered by .gitignore)
- Each file should have `600` permissions (owner read/write only)
- GitHub tokens need appropriate scopes:
  - Admin token: `repo`, `admin:org`, `workflow`
  - Bot tokens: `repo`, `workflow`
- Store backups in a secure location (password manager, encrypted storage)

## 🔧 Usage in Code

### Loading Agent Tokens

```python
from pathlib import Path

def load_agent_token(agent_name: str) -> str:
    """Load GitHub token for a specific agent."""
    token_file = Path(f'secrets/agents/{agent_name}.token')
    if not token_file.exists():
        raise FileNotFoundError(f"Token file not found: {token_file}")
    return token_file.read_text().strip()

# Usage
admin_token = load_agent_token('m0nk111')
bot_token = load_agent_token('m0nk111-post')
```

### Loading API Keys

```python
from pathlib import Path

def load_api_key(service: str) -> str:
    """Load API key for a specific LLM service."""
    key_file = Path(f'secrets/keys/{service}.key')
    if not key_file.exists():
        raise FileNotFoundError(f"Key file not found: {key_file}")
    return key_file.read_text().strip()

# Usage
openai_key = load_api_key('openai')
openrouter_key = load_api_key('openrouter')
anthropic_key = load_api_key('anthropic')  # Future
```

## 📋 Migration from keys.json

If you have an old `keys.json` file, migrate it using:

```bash
python3 scripts/migrate_secrets.py
```

This will:
1. Extract tokens to `agents/` directory
2. Extract API keys to `keys/` directory
3. Rename `keys.json` to `keys.json.deprecated`
4. Show a summary of migrated secrets

## 🎯 Repository Management

The admin token (`m0nk111.token`) is used for:
- Inviting bot accounts to repositories
- Managing repository settings
- Creating/deleting branches
- Managing webhooks and integrations

Bot tokens are used for:
- Creating issues and pull requests
- Commenting on issues/PRs
- Pushing code changes
- Running workflows

## ❓ FAQ

**Q: Why separate files instead of one JSON?**
A: Separation of concerns - each bot/service has its own credential file, making it easier to rotate tokens and manage permissions.

**Q: Can I use environment variables instead?**
A: Yes, but file-based tokens are preferred for:
- Better organization
- Easier rotation
- Clear separation of credentials
- No risk of leaking via process environment

**Q: What if a token expires?**
A: 
1. Generate a new token on GitHub (Settings → Developer settings → Personal access tokens)
2. Replace the content of the corresponding `.token` file
3. Restart services that use that token

**Q: How do I create a new bot account?**
A:
1. Create GitHub account (e.g., `m0nk111-newbot`)
2. Generate personal access token with `repo` scope
3. Save to `secrets/agents/m0nk111-newbot.token`
4. Update `config/services/polling.yaml` if needed
5. Use repo management tools to invite bot to repositories
