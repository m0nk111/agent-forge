# Token Security Strategy - Agent-Forge

**Datum:** 2025-10-07  
**Prioriteit:** 🔴 KRITIEK  
**Status:** In implementatie

---

## Quick Start (Emergency Response)

**If you need to secure tokens RIGHT NOW, follow these steps first:**

### Step 1: Revoke Leaked Token (if applicable)

```bash
# 1. Open: https://github.com/settings/tokens
# 2. Find: leaked token (e.g., ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN)
# 3. Click: Delete/Revoke
```

### Step 2: Run Security Script

```bash
cd /home/flip/agent-forge
./scripts/secure-tokens.sh
```

This script will:
- ✅ Create `secrets/` directory (with 0700 permissions)
- ✅ Update `.gitignore` (block secrets/)
- ✅ Prompt for new token
- ✅ Remove token from `config/agents/*.yaml`
- ✅ Verify security setup

### Step 3: Commit Changes

```bash
git add .gitignore config/agents/*.yaml
git commit -m "security(tokens): move tokens to secrets directory"
git push
```

### Step 4: Verify Security

```bash
# Check: No tokens in git
grep -r "ghp_" config/
# Should return nothing

# Check: secrets/ is ignored
git status
# Should NOT show secrets/

# Check: File permissions correct
ls -la secrets/agents/
# Should show: -rw------- (600)

# Check: Token works
curl -H "Authorization: token $(cat secrets/agents/AGENT_ID.token)" \
  https://api.github.com/user
# Should return user details
```

✅ **Done!** Your tokens are now secure. Continue reading for complete security strategy.

---

## 📁 Secure File Structure

**Before (INSECURE):**
```
config/agents/*.yaml         # ❌ Plaintext token!
```

**After (SECURE):**
```
secrets/                   # ✅ Secured directory (0700)
├── agents/
│   └── agent-id.token    # ✅ Token files (0600)
└── keys/
    └── providers.json    # ✅ LLM API keys

.gitignore                # ✅ Blocks secrets/
config/agents/*.yaml        # ✅ Token references only
```

---

## 🔐 Security Principles

1. **Git Protection**
   - ✅ `secrets/` in `.gitignore`
   - ✅ Never commit tokens to git
   - ✅ Separate secrets from configuration

2. **Filesystem Protection**
   - ✅ File permissions: `0600` (owner read/write only)
   - ✅ Directory permissions: `0700` (owner access only)
   - ✅ Secrets in dedicated directory

3. **Access Control**
   - ✅ Tokens loaded only via ConfigManager
   - ✅ API responses show masked tokens
   - ✅ Dashboard never displays plaintext tokens

---

## 🚨 Current Security Issues (Detailed Analysis)

### ❌ Issue 1: Plaintext Tokens in Git
**Locatie:** `config/agents/*.yaml` line 49
```yaml
github_token: ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN  # ❌ LEAKED!
```

**Risico:** HIGH
- Token zichtbaar in git history
- Token zichtbaar op GitHub
- Token kan niet worden geroteerd zonder force push

### ❌ Issue 2: No Token Encryption
**Locatie:** `keys.json` (als die bestaat)
```json
{
  "OPENAI_API_KEY": "sk-proj-abc123..."  // ❌ Plaintext!
}
```

**Risico:** MEDIUM
- `.gitignore` voorkomt git leak
- Maar: filesystem toegang = token toegang
- Geen encryptie at rest

### ❌ Issue 3: No Token Rotation Policy
**Probleem:** Geen mechanisme voor:
- Automatische token expiry
- Token rotation schedule
- Revoke & replace workflow

---

## 🎯 Security Strategie

### Principe: Defense in Depth (3 Lagen)

```
┌─────────────────────────────────────────────┐
│  Layer 1: Git Protection                    │
│  ✅ .gitignore secrets files                │
│  ✅ Pre-commit hooks                        │
│  ✅ Separate secrets from config            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: Filesystem Protection             │
│  ✅ File permissions (0600)                 │
│  ✅ Encryption at rest                      │
│  ✅ Separate secrets directory              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: Runtime Protection                │
│  ✅ Memory-only decryption                  │
│  ✅ Masked API responses                    │
│  ✅ Audit logging                           │
└─────────────────────────────────────────────┘
```

---

## 📁 Nieuwe Structuur

```
agent-forge/
├── secrets/                      # ✨ NIEUW: Encrypted secrets
│   ├── .gitkeep
│   ├── agents/                   # Per-agent secrets
│   │   ├── qwen-main-agent.enc  # Encrypted token file
│   │   └── m0nk111-qwen.enc
│   ├── keys/                     # LLM API keys
│   │   └── providers.enc        # Encrypted keys.json
│   └── master.key                # Master encryption key (NEVER in git)
│
├── config/
│   └── agents.yaml              # ✅ NO TOKENS (alleen references)
│
├── .gitignore                    # ✅ Ignore secrets/ and master.key
└── .git-crypt/                   # 🔐 Optional: git-crypt setup
```

---

## 🔐 Implementatie Plan

### Option A: Eenvoudig (Filesystem Only)

**Best voor:** Single-user, lokaal deployment

```
secrets/
├── agents/
│   ├── qwen-main-agent.token    # Plaintext, maar 0600 permissions
│   └── m0nk111-qwen.token
├── keys/
│   └── providers.json           # Plaintext, maar 0600 permissions
└── .gitkeep
```

**Security:**
- ✅ `.gitignore` voorkomt git leak
- ✅ File permissions (0600) voorkomt andere users
- ❌ Geen encryption at rest
- ❌ Root kan alles lezen

**Implementatie:**
```python
# engine/core/config_manager.py
def load_agent_token(agent_id: str) -> Optional[str]:
    token_file = Path(f"secrets/agents/{agent_id}.token")
    if token_file.exists():
        return token_file.read_text().strip()
    return None

def save_agent_token(agent_id: str, token: str) -> None:
    token_file = Path(f"secrets/agents/{agent_id}.token")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token)
    os.chmod(token_file, 0o600)  # Owner read/write only
```

---

### Option B: Encrypted (Fernet)

**Best voor:** Multi-user, gedeelde systemen

```
secrets/
├── agents/
│   ├── qwen-main-agent.enc      # Fernet encrypted
│   └── m0nk111-qwen.enc
├── keys/
│   └── providers.enc            # Fernet encrypted
└── master.key                   # Encryption key (0600, not in git)
```

**Security:**
- ✅ `.gitignore` voorkomt git leak
- ✅ File permissions (0600)
- ✅ Encryption at rest (Fernet)
- ✅ Root kan niet direct lezen (needs key)
- ❌ Master key nog steeds op filesystem

**Implementatie:**
```python
from cryptography.fernet import Fernet
import os

class TokenVault:
    def __init__(self, master_key_file: str = "secrets/master.key"):
        self.master_key_file = Path(master_key_file)
        self.cipher = self._load_or_create_cipher()
    
    def _load_or_create_cipher(self) -> Fernet:
        """Load master key or create new one"""
        if self.master_key_file.exists():
            key = self.master_key_file.read_bytes()
        else:
            # Generate new master key
            key = Fernet.generate_key()
            self.master_key_file.parent.mkdir(parents=True, exist_ok=True)
            self.master_key_file.write_bytes(key)
            os.chmod(self.master_key_file, 0o600)
        
        return Fernet(key)
    
    def encrypt_token(self, token: str) -> bytes:
        """Encrypt token"""
        return self.cipher.encrypt(token.encode())
    
    def decrypt_token(self, encrypted: bytes) -> str:
        """Decrypt token"""
        return self.cipher.decrypt(encrypted).decode()
    
    def save_agent_token(self, agent_id: str, token: str) -> None:
        """Save encrypted agent token"""
        encrypted = self.encrypt_token(token)
        token_file = Path(f"secrets/agents/{agent_id}.enc")
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_bytes(encrypted)
        os.chmod(token_file, 0o600)
    
    def load_agent_token(self, agent_id: str) -> Optional[str]:
        """Load and decrypt agent token"""
        token_file = Path(f"secrets/agents/{agent_id}.enc")
        if not token_file.exists():
            return None
        
        encrypted = token_file.read_bytes()
        return self.decrypt_token(encrypted)
```

**Dependencies:**
```bash
pip install cryptography>=41.0.0
```

---

### Option C: Git-Crypt (Advanced)

**Best voor:** Team collaboration met git

```bash
# Setup git-crypt
sudo apt install git-crypt
cd /home/flip/agent-forge

# Initialize git-crypt
git-crypt init

# Add GPG keys voor team members
git-crypt add-gpg-user flip@example.com

# Configure .gitattributes
echo "secrets/** filter=git-crypt diff=git-crypt" >> .gitattributes
echo "*.token filter=git-crypt diff=git-crypt" >> .gitattributes
echo "*.key filter=git-crypt diff=git-crypt" >> .gitattributes
```

**Security:**
- ✅ Transparante encryptie in git
- ✅ Team kan samenwerken
- ✅ Secrets in git, maar encrypted
- ❌ Complexer setup
- ❌ Vereist GPG keys

---

## 🛠️ Migratie Plan

### Stap 1: Backup Huidige Tokens (1 min)
```bash
cd /home/flip/agent-forge

# Extract tokens from agents.yaml
grep -A1 "github_token:" config/agents/*.yaml > /tmp/tokens_backup.txt

# Show tokens (manual copy to safe place)
cat /tmp/tokens_backup.txt

# CRITICAL: Save deze tokens veilig VOORDAT we ze verwijderen!
```

### Stap 2: Create Secrets Infrastructure (5 min)
```bash
# Option A: Simple filesystem
mkdir -p secrets/agents secrets/keys
chmod 700 secrets

# Option B: Encrypted
mkdir -p secrets/agents secrets/keys
chmod 700 secrets
# Run Python script to generate master.key

# Update .gitignore
echo "" >> .gitignore
echo "# Secrets (Issue #XX)" >> .gitignore
echo "secrets/" >> .gitignore
echo "!secrets/.gitkeep" >> .gitignore
echo "master.key" >> .gitignore
echo "*.token" >> .gitignore
echo "*.enc" >> .gitignore
```

### Stap 3: Migrate Tokens (10 min)
```bash
# Manual: Save tokens to separate files
echo "ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN" > secrets/agents/m0nk111-qwen-agent.token
chmod 600 secrets/agents/m0nk111-qwen-agent.token

# Or: Use Python script
python3 << EOF
from pathlib import Path
import os

tokens = {
    "m0nk111-qwen-agent": "ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN"
}

Path("secrets/agents").mkdir(parents=True, exist_ok=True)

for agent_id, token in tokens.items():
    token_file = Path(f"secrets/agents/{agent_id}.token")
    token_file.write_text(token)
    os.chmod(token_file, 0o600)
    print(f"✅ Saved: {token_file}")
EOF
```

### Stap 4: Remove Tokens from Git (15 min)
```bash
# Update agents.yaml (remove plaintext tokens)
sed -i 's/github_token: ghp_.*/github_token: null  # Moved to secrets\//' config/agents/*.yaml

# Verify
grep "github_token" config/agents/*.yaml

# Commit change
git add config/agents/*.yaml .gitignore
git commit -m "security(tokens): remove plaintext tokens from config"

# CRITICAL: Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch config/agents/*.yaml" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (⚠️ DESTRUCTIVE!)
git push origin --force --all
```

**⚠️ WARNING:** `git filter-branch` herschrijft git history! Backup eerst!

**Alternatief (veiliger):** Gewoon token revooken in GitHub en nieuwe maken.

### Stap 5: Update ConfigManager (30 min)
```python
# engine/core/config_manager.py (na refactor)
# Of: engine/core/config_manager.py (nu)

from pathlib import Path
from typing import Optional
import os

class ConfigManager:
    def __init__(self):
        self.secrets_dir = Path("secrets")
        # ... existing code ...
    
    def get_agent_token(self, agent_id: str, token_type: str = "github") -> Optional[str]:
        """
        Get agent token from secrets directory.
        
        Priority:
        1. secrets/agents/{agent_id}.token
        2. Environment variable {AGENT_ID}_GITHUB_TOKEN
        3. None
        """
        # Try secrets file
        token_file = self.secrets_dir / "agents" / f"{agent_id}.token"
        if token_file.exists():
            return token_file.read_text().strip()
        
        # Try environment variable
        env_var = f"{agent_id.upper().replace('-', '_')}_GITHUB_TOKEN"
        env_token = os.getenv(env_var)
        if env_token:
            return env_token
        
        return None
    
    def set_agent_token(self, agent_id: str, token: str) -> None:
        """Save agent token to secrets directory"""
        token_file = self.secrets_dir / "agents" / f"{agent_id}.token"
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token)
        os.chmod(token_file, 0o600)
```

### Stap 6: Update API Endpoints (20 min)
```python
# api/config_routes.py

@router.patch("/api/config/agents/{agent_id}")
async def update_agent_config(agent_id: str, updates: dict):
    """Update agent config (tokens go to secrets/)"""
    
    # Extract token if present
    github_token = updates.pop("github_token", None)
    
    # Save token separately
    if github_token and github_token != "null":
        config_manager.set_agent_token(agent_id, github_token)
    
    # Update config (without token)
    config_manager.update_agent(agent_id, updates)
    
    return {"success": True}

@router.get("/api/config/agents/{agent_id}")
async def get_agent_config(agent_id: str):
    """Get agent config (token masked)"""
    config = config_manager.get_agent(agent_id)
    
    # Check if token exists (but don't return it)
    token = config_manager.get_agent_token(agent_id)
    config["github_token_configured"] = token is not None
    config["github_token"] = "***MASKED***" if token else null
    
    return config
```

### Stap 7: Update Dashboard (10 min)
```javascript
// frontend/dashboard.html

// When loading agent config
function loadAgentConfig(agentId) {
    fetch(`/api/config/agents/${agentId}`)
        .then(r => r.json())
        .then(config => {
            // Show masked token status
            if (config.github_token_configured) {
                tokenInput.placeholder = "Token configured (hidden)";
                tokenInput.value = "";
            } else {
                tokenInput.placeholder = "Enter GitHub token";
            }
        });
}

// When saving
function saveAgentConfig(agentId, config) {
    // Only send token if user entered new one
    if (tokenInput.value && tokenInput.value !== "") {
        config.github_token = tokenInput.value;
    }
    // Otherwise don't include token field (keep existing)
}
```

---

## 🧪 Testing Checklist

- [ ] Tokens niet zichtbaar in git: `git log -p | grep "ghp_"`
- [ ] Tokens niet zichtbaar op GitHub
- [ ] `.gitignore` blocks secrets/: `git status`
- [ ] File permissions correct: `ls -la secrets/agents/`
- [ ] API returns masked tokens
- [ ] Dashboard kan tokens updaten
- [ ] Agents kunnen tokens gebruiken
- [ ] Token rotation werkt
- [ ] Backup & restore werkt

---

## 🔄 Token Rotation Workflow

### Manual Rotation
```bash
# 1. Generate new token on GitHub
# 2. Update via dashboard or CLI
echo "ghp_NEW_TOKEN" > secrets/agents/m0nk111-qwen-agent.token
chmod 600 secrets/agents/m0nk111-qwen-agent.token

# 3. Test new token
curl -H "Authorization: token $(cat secrets/agents/m0nk111-qwen-agent.token)" \
  https://api.github.com/user

# 4. Revoke old token on GitHub
```

### Automated Rotation (Toekomst)
```python
# engine/core/token_manager.py
class TokenManager:
    def rotate_token(self, agent_id: str) -> str:
        """
        Rotate agent token:
        1. Generate new token via GitHub API
        2. Test new token
        3. Save new token
        4. Revoke old token
        5. Return new token
        """
        pass  # TODO: Implement
```

---

## 📊 Security Comparison

| Feature | Option A (Simple) | Option B (Encrypted) | Option C (Git-Crypt) |
|---------|-------------------|----------------------|----------------------|
| Git protection | ✅ .gitignore | ✅ .gitignore | ✅ Encrypted in git |
| Filesystem | ✅ 0600 perms | ✅ 0600 + Fernet | ✅ 0600 perms |
| Root access | ❌ Root can read | ✅ Needs master key | ❌ Root can read |
| Team collab | ❌ Manual sharing | ❌ Manual sharing | ✅ GPG-based |
| Complexity | 🟢 Low | 🟡 Medium | 🔴 High |
| Setup time | 5 min | 15 min | 30 min |
| Dependencies | None | cryptography | git-crypt, GPG |

---

## 🎯 Aanbeveling

**Voor Agent-Forge (nu):**
→ **Option A (Simple Filesystem)** ✅

**Redenen:**
1. Single-user deployment (flip@ai-kvm1)
2. Lokaal netwerk (geen internet exposure)
3. `.gitignore` + permissions is voldoende
4. Snelle implementatie (5-10 min)
5. Geen extra dependencies

**Later upgraden naar Option B als:**
- Multi-user access nodig
- Production deployment
- Compliance requirements
- Team collaboration

---

## 🚨 Directe Acties (NU!)

### CRITICAL: Stop Token Leak
```bash
# 1. Revoke exposed token on GitHub
# Ga naar: https://github.com/settings/tokens
# Find: ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN
# Click: Revoke

# 2. Generate new token
# https://github.com/settings/tokens/new
# Scopes: repo, workflow, admin:org
# Save securely!

# 3. Update agents.yaml (temporary)
nano config/agents/*.yaml
# Replace token with new one (we'll move to secrets/ later)

# 4. Commit fix
git add config/agents/*.yaml
git commit -m "security(urgent): rotate leaked GitHub token"
git push
```

---

## 📝 Next Steps

1. **Immediate** (nu):
   - [ ] Revoke exposed token
   - [ ] Generate new token
   - [ ] Update `.gitignore`
   
2. **Short-term** (deze week):
   - [ ] Implement Option A (filesystem secrets)
   - [ ] Migrate tokens to secrets/
   - [ ] Update ConfigManager
   - [ ] Update API endpoints
   
3. **Medium-term** (volgende sprint):
   - [ ] Implement token masking in UI
   - [ ] Add audit logging
   - [ ] Document rotation workflow
   
4. **Long-term** (toekomst):
   - [ ] Consider Option B (encryption)
   - [ ] Automated rotation
   - [ ] Token expiry policies

---

## 📚 References

- [GitHub Token Security](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Python Cryptography](https://cryptography.io/en/latest/fernet/)
- [Git-Crypt](https://github.com/AGWA/git-crypt)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
