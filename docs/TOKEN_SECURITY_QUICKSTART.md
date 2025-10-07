# Token Security - Snelle Referentie

**Status:** 🔴 URGENT - Leaked token gevonden  
**Actie:** Volg deze stappen NU

---

## 🚨 Urgente Acties (NU!)

### Stap 1: Revoke Leaked Token
```
1. Open: https://github.com/settings/tokens
2. Zoek: ghp_EXAMPLE_TOKEN_REPLACE_WITH_YOUR_OWN
3. Klik: Delete/Revoke
```

### Stap 2: Run Security Script
```bash
cd /home/flip/agent-forge
./scripts/secure-tokens.sh
```

Dit script doet:
- ✅ Create `secrets/` directory (met 0700 permissions)
- ✅ Update `.gitignore` (block secrets/)
- ✅ Vraagt om nieuwe token
- ✅ Verwijdert token uit `config/agents.yaml`
- ✅ Verifieert security

### Stap 3: Commit Changes
```bash
git add .gitignore config/agents.yaml
git commit -m "security(tokens): move tokens to secrets directory"
git push
```

---

## 📁 Nieuwe Structuur

**Voor:**
```
config/agents.yaml         # ❌ Plaintext token!
```

**Na:**
```
secrets/                   # ✅ Beveiligde directory
├── agents/
│   └── m0nk111-qwen-agent.token  # ✅ 0600 permissions
└── keys/
    └── providers.json     # ✅ LLM API keys

.gitignore                 # ✅ Blocks secrets/
```

---

## 🔐 Security Principes

1. **Git Protection**
   - ✅ `secrets/` in `.gitignore`
   - ✅ Nooit tokens in git commits

2. **Filesystem Protection**
   - ✅ File permissions: `0600` (owner only)
   - ✅ Directory permissions: `0700` (owner only)

3. **Access Control**
   - ✅ Tokens alleen via ConfigManager
   - ✅ API responses tonen gemaskeerde tokens
   - ✅ Dashboard nooit plaintext tokens

---

## 🧪 Verificatie

```bash
# Check: Geen tokens in git
grep -r "ghp_" config/

# Check: secrets/ is ignored
git status  # Should NOT show secrets/

# Check: File permissions correct
ls -la secrets/agents/
# Should show: -rw------- (600)

# Check: Token werkt
curl -H "Authorization: token $(cat secrets/agents/m0nk111-qwen-agent.token)" \
  https://api.github.com/user
```

---

## 📚 Volledige Documentatie

Zie: `docs/TOKEN_SECURITY.md`

---

## 🆘 Problemen?

**Probleem:** Script faalt  
**Oplossing:** Handmatige stappen in `docs/TOKEN_SECURITY.md`

**Probleem:** Token werkt niet  
**Oplossing:** Check scopes in GitHub (repo, workflow)

**Probleem:** Permission denied  
**Oplossing:** `chmod 600 secrets/agents/*.token`
