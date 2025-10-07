# OAuth Activatie Instructies - Agent-Forge Dashboard

**⏱️ Tijd nodig: 10-15 minuten**  
**💰 Kosten: €0 (volledig gratis)**

---

## Stap 1: Google Cloud Project Aanmaken (5 minuten)

### 1.1 - Open Google Cloud Console
```
URL: https://console.cloud.google.com/
```
- Login met je Google account (gebruik liefst persoonlijk account, niet werk)

### 1.2 - Nieuw Project Aanmaken
1. Klik op project dropdown (bovenaan, naast "Google Cloud")
2. Klik op **"NEW PROJECT"** (rechts bovenaan)
3. Vul in:
   - **Project name**: `agent-forge-auth`
   - **Organization**: Laat leeg (of kies je org)
   - **Location**: Laat leeg (of "No organization")
4. Klik **"CREATE"**
5. Wacht 10 seconden tot project is aangemaakt

### 1.3 - Selecteer het Nieuwe Project
1. Klik opnieuw op project dropdown
2. Selecteer `agent-forge-auth`
3. Verify dat je in het juiste project zit (zie naam bovenaan)

---

## Stap 2: OAuth Consent Screen Configureren (5 minuten)

### 2.1 - Open OAuth Consent Screen
1. In left sidebar: Klik op **"APIs & Services"**
2. Klik op **"OAuth consent screen"**

### 2.2 - Kies User Type
1. Selecteer **"External"** (voor persoonlijk gebruik)
2. Klik **"CREATE"**

### 2.3 - App Information (Tab 1)
Vul in:
```
App name: Agent-Forge Dashboard
User support email: [jouw-email@gmail.com]
App logo: (optioneel, skip)
```

Scroll naar beneden:
```
Application home page: http://192.168.1.26:8897
Application privacy policy: (laat leeg)
Application terms of service: (laat leeg)
```

Scroll naar beneden:
```
Authorized domains: (laat leeg voor localhost)
Developer contact: [jouw-email@gmail.com]
```

Klik **"SAVE AND CONTINUE"**

### 2.4 - Scopes (Tab 2)
1. Klik **"ADD OR REMOVE SCOPES"**
2. Filter op: `userinfo`
3. Selecteer (vink aan):
   - ✅ `.../auth/userinfo.email`
   - ✅ `.../auth/userinfo.profile`
   - ✅ `openid`
4. Klik **"UPDATE"** (onderaan modal)
5. Klik **"SAVE AND CONTINUE"**

### 2.5 - Test Users (Tab 3)
1. Klik **"ADD USERS"**
2. Voeg toe: `jouw-email@gmail.com` (je persoonlijke Gmail)
3. Klik **"ADD"**
4. Klik **"SAVE AND CONTINUE"**

### 2.6 - Summary (Tab 4)
1. Review de instellingen
2. Klik **"BACK TO DASHBOARD"**

✅ OAuth Consent Screen is klaar!

---

## Stap 3: OAuth Client ID Aanmaken (3 minuten)

### 3.1 - Open Credentials
1. In left sidebar: **"APIs & Services"** → **"Credentials"**
2. Klik bovenaan op **"CREATE CREDENTIALS"**
3. Selecteer **"OAuth client ID"**

### 3.2 - Configure Client
Application type: Selecteer **"Web application"**

Name:
```
Agent-Forge Dashboard Client
```

### 3.3 - Authorized JavaScript Origins
Klik **"ADD URI"** (3x) en voeg toe:
```
http://localhost:8897
http://192.168.1.26:8897
http://ai-kvm1:8897
```

### 3.4 - Authorized Redirect URIs
Klik **"ADD URI"** (3x) en voeg toe:
```
http://localhost:8897/auth/callback
http://192.168.1.26:8897/auth/callback
http://ai-kvm1:8897/auth/callback
```

### 3.5 - Aanmaken
1. Klik **"CREATE"**
2. **STOP!** Er verschijnt een popup met credentials:
   ```
   Your Client ID:
   1234567890-abc123xyz.apps.googleusercontent.com
   
   Your Client Secret:
   GOCSPX-abc123xyz456
   ```
3. **KOPIEER BEIDE** → Plak in een tekst editor (tijdelijk)
4. Klik **"OK"**

✅ OAuth Client is klaar!

---

## Stap 4: Agent-Forge Configureren (2 minuten)

### 4.1 - Login op Server
```bash
ssh flip@ai-kvm1
cd /home/flip/agent-forge
```

### 4.2 - Maak .env Bestand
```bash
nano .env
```

### 4.3 - Plak Configuratie
Plak dit (vervang YOUR_... met je echte credentials):
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET

# Redirect URI (pas aan als je andere hostname gebruikt)
GOOGLE_REDIRECT_URI=http://192.168.1.26:8897/auth/callback

# Session secret (auto-generated)
SESSION_SECRET=$(openssl rand -hex 32)

# Toegestane emails (komma-gescheiden)
ALLOWED_EMAILS=jouw-email@gmail.com
```

**Belangrijke wijzigingen:**
1. Vervang `YOUR_CLIENT_ID` met je Client ID uit stap 3.5
2. Vervang `YOUR_CLIENT_SECRET` met je Client Secret uit stap 3.5
3. Vervang `jouw-email@gmail.com` met je Gmail adres

### 4.4 - Opslaan
```
Ctrl+O  (save)
Enter   (confirm)
Ctrl+X  (exit)
```

### 4.5 - Valideer Configuratie
```bash
cat .env | grep -v "^#"
```

Verwachte output:
```
GOOGLE_CLIENT_ID=1234567890-abc123xyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz456
GOOGLE_REDIRECT_URI=http://192.168.1.26:8897/auth/callback
SESSION_SECRET=abc123xyz...
ALLOWED_EMAILS=jouw-email@gmail.com
```

✅ Configuratie klaar!

---

## Stap 5: Auth Service Starten (1 minuut)

### 5.1 - Start Auth Service
```bash
cd /home/flip/agent-forge
./scripts/start-auth-service.sh
```

Verwachte output:
```
🔐 Agent-Forge Google OAuth Setup
==================================

✅ Configuratie validatie OK

📋 Configuratie:
   Client ID: 1234567890-abc123x...
   Redirect URI: http://192.168.1.26:8897/auth/callback
   Allowed emails: jouw-email@gmail.com

🚀 Start Auth API op poort 7999...
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:7999
```

### 5.2 - Test Auth Service (nieuw terminal)
Open **nieuw terminal venster**:
```bash
curl http://localhost:7999/health | jq
```

Verwachte output:
```json
{
  "status": "healthy",
  "oauth_configured": true,
  "allowed_emails_count": 1
}
```

✅ Auth service draait!

---

## Stap 6: Dashboard Testen (2 minuten)

### 6.1 - Open Dashboard
In je browser:
```
http://192.168.1.26:8897/dashboard.html
```

### 6.2 - Verwachte Flow
1. **Redirect naar Google**: Je wordt automatisch doorgestuurd naar Google login
2. **Login**: Login met je Gmail account (die je toegevoegd hebt als test user)
3. **Toestemming**: Google vraagt om toestemming:
   - ✅ "See your email address"
   - ✅ "See your personal info"
4. **Klik "Allow"**
5. **Redirect terug**: Je komt terug op dashboard
6. **Dashboard laadt**: Je ziet het dashboard met je email rechtsboven

### 6.3 - Verify in Browser Console
```
F12 → Console tab
```

Verwachte logs:
```
✅ Authenticated as: jouw-email@gmail.com
```

### 6.4 - Check User Info
- Rechtsboven in header zie je:
  - Je profielfoto (avatar)
  - Je email adres
  - **Logout** button (rood)

✅ OAuth werkt!

---

## Troubleshooting

### Probleem: "redirect_uri_mismatch"
**Oorzaak**: Redirect URI in Google Console komt niet overeen met .env

**Oplossing**:
1. Check .env: `cat .env | grep REDIRECT_URI`
2. Check Google Console: Credentials → je OAuth Client → Authorized redirect URIs
3. Zorg dat ze **EXACT** hetzelfde zijn (hoofdletters, http vs https, trailing slash)

### Probleem: "Access blocked: This app's request is invalid"
**Oorzaak**: Scopes niet goed geconfigureerd

**Oplossing**:
1. Google Console → OAuth consent screen → Edit app
2. Tab "Scopes" → Add or remove scopes
3. Zorg dat deze 3 scopes zijn geselecteerd:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`

### Probleem: "Access denied: Email not in allowed list"
**Oorzaak**: Je email niet in ALLOWED_EMAILS

**Oplossing**:
```bash
nano .env
# Voeg je email toe aan ALLOWED_EMAILS
# Restart auth service: pkill -f auth_routes && ./scripts/start-auth-service.sh
```

### Probleem: "Auth service not available"
**Oorzaak**: Auth service draait niet

**Oplossing**:
```bash
./scripts/start-auth-service.sh
```

### Probleem: "Dashboard laadt maar geen login prompt"
**Oorzaak**: Auth service draait maar OAuth niet configured

**Oplossing**:
```bash
curl http://localhost:7999/health
# Check "oauth_configured": moet true zijn
```

---

## Auth Service in Achtergrond Draaien

### Optie 1: Tmux (Recommended)
```bash
# Start tmux sessie
tmux new -s auth

# Start auth service
cd /home/flip/agent-forge
./scripts/start-auth-service.sh

# Detach van tmux (service blijft draaien)
Ctrl+B, D

# Later: Reattach
tmux attach -t auth
```

### Optie 2: systemd Service
```bash
# Maak service file
sudo nano /etc/systemd/system/agent-forge-auth.service
```

Inhoud:
```ini
[Unit]
Description=Agent-Forge OAuth Service
After=network.target

[Service]
Type=simple
User=flip
WorkingDirectory=/home/flip/agent-forge
EnvironmentFile=/home/flip/agent-forge/.env
ExecStart=/opt/agent-forge/venv/bin/python3 -m api.auth_routes
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agent-forge-auth
sudo systemctl start agent-forge-auth
sudo systemctl status agent-forge-auth
```

---

## OAuth Uitschakelen (Terug naar Open Mode)

### Tijdelijk Uitschakelen
```bash
pkill -f "api.auth_routes"
# Dashboard draait nu weer in open mode (geen login)
```

### Permanent Uitschakelen
```bash
# Rename .env
mv .env .env.disabled

# Stop auth service
pkill -f "api.auth_routes"

# Dashboard draait nu permanent in open mode
```

---

## Security Best Practices

✅ **Gebruik HTTPS in productie** (voor nu HTTP is OK op LAN)  
✅ **Roteer SESSION_SECRET regelmatig**  
✅ **Beperk ALLOWED_EMAILS tot vertrouwde users**  
✅ **Check Google Console audit logs regelmatig**  
✅ **Revoke OAuth tokens als niet meer nodig**  
✅ **Gebruik sterke passwords voor Google account**  

---

## Kosten Overzicht

| Component | Gratis Tier | Kosten |
|-----------|-------------|--------|
| Google OAuth 2.0 | Unlimited | **€0** |
| User Info API | 10,000/dag | **€0** |
| Agent-Forge Auth | Self-hosted | **€0** |
| **TOTAAL** | | **€0/maand** |

---

## Support & Documentatie

📚 **Volledige docs**: `docs/GOOGLE_OAUTH_SETUP.md`  
🔧 **Backend code**: `api/auth_routes.py`  
🎨 **Frontend code**: `frontend/dashboard.html`  
⚙️ **Start script**: `scripts/start-auth-service.sh`

**Google Docs**:
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [OAuth Playground](https://developers.google.com/oauthplayground/)
- [Cloud Console](https://console.cloud.google.com/)

---

## Samenvatting

✅ **Stap 1**: Google Cloud project aanmaken (5 min)  
✅ **Stap 2**: OAuth Consent Screen configureren (5 min)  
✅ **Stap 3**: OAuth Client ID aanmaken (3 min)  
✅ **Stap 4**: .env bestand configureren (2 min)  
✅ **Stap 5**: Auth service starten (1 min)  
✅ **Stap 6**: Dashboard testen (2 min)  

**Totale tijd**: ~15 minuten  
**Kosten**: €0  

🎉 **Succes!**
