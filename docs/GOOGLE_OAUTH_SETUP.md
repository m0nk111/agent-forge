# Google OAuth Setup voor Agent-Forge Dashboard

## Overzicht

Deze guide legt uit hoe je Google OAuth authentication toevoegt aan het Agent-Forge dashboard. Dit is **100% GRATIS** voor persoonlijk gebruik (tot 10,000 requests/dag).

## Waarom Google OAuth?

✅ **Gratis**: Geen kosten voor OAuth functionaliteit  
✅ **Veilig**: Industry-standard security  
✅ **Makkelijk**: Users hoeven geen nieuwe account aan te maken  
✅ **Betrouwbaar**: Gebouwd op Google's infrastructure  

## Stap 1: Google Cloud Project Aanmaken

1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Klik op project dropdown (top) → "NEW PROJECT"
3. Project naam: `agent-forge-auth`
4. Klik "CREATE"

## Stap 2: OAuth Consent Screen Configureren

1. In sidebar: "APIs & Services" → "OAuth consent screen"
2. Kies "External" (voor persoonlijk gebruik)
3. Vul in:
   - **App name**: `Agent-Forge Dashboard`
   - **User support email**: Jouw email
   - **Developer contact**: Jouw email
4. Scopes: Voeg toe:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
5. Test users: Voeg jouw Google email toe (alleen deze users kunnen inloggen)
6. Klik "SAVE AND CONTINUE"

## Stap 3: OAuth Client Credentials

1. Sidebar: "APIs & Services" → "Credentials"
2. Klik "CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: **Web application**
4. Name: `Agent-Forge Dashboard Client`
5. Authorized JavaScript origins:
   ```
   http://localhost:8897
   http://192.168.1.26:8897
   http://ai-kvm1:8897
   ```
6. Authorized redirect URIs:
   ```
   http://localhost:8897/auth/callback
   http://192.168.1.26:8897/auth/callback
   http://ai-kvm1:8897/auth/callback
   ```
7. Klik "CREATE"
8. **KOPIEER** de Client ID en Client Secret

## Stap 4: Credentials Opslaan

Sla de credentials op in een config file:

```bash
# In /home/flip/agent-forge/config/auth.yaml
google_oauth:
  client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
  client_secret: "YOUR_CLIENT_SECRET"
  allowed_emails:
    - "jouw-email@gmail.com"
    - "andere-toegestane@gmail.com"
  session_secret: "RANDOM_STRING_MIN_32_CHARS"  # Genereer met: openssl rand -hex 32
```

**BELANGRIJK**: Voeg `config/auth.yaml` toe aan `.gitignore`!

## Stap 5: Agent-Forge Configureren

De Agent-Forge backend moet:
1. OAuth flow afhandelen (login redirect → callback)
2. Session cookies instellen
3. Protected endpoints checken voor valid session

Dit wordt geïmplementeerd in:
- `api/auth_routes.py` - OAuth endpoints
- `frontend/dashboard.html` - Login UI
- `agents/service_manager.py` - Auth middleware

## Stap 6: Testen

1. Open dashboard: `http://192.168.1.26:8897/dashboard.html`
2. Redirect naar Google login
3. Login met toegestane email
4. Redirect terug naar dashboard
5. Session cookie actief ✅

## Kosten Overzicht

| Service | Gratis Tier | Jouw Usage | Kosten |
|---------|-------------|------------|--------|
| OAuth 2.0 | Unlimited | ~100 logins/maand | €0 |
| User Info API | 10,000/dag | ~50/dag | €0 |
| **TOTAAL** | | | **€0/maand** |

## Security Best Practices

✅ Session cookies met `HttpOnly`, `Secure`, `SameSite=Lax`  
✅ CSRF protection met state parameter  
✅ Whitelist van toegestane emails in config  
✅ Session timeout (24 uur)  
✅ Credentials in gitignored config file  

## Alternatieve Opties

Als je Google OAuth niet wilt:

1. **Basic Auth**: Username/password (simpel, minder veilig)
2. **API Key**: Token-based auth (goed voor API, niet voor UI)
3. **GitHub OAuth**: Vergelijkbaar met Google (ook gratis)
4. **Microsoft OAuth**: Voor werk/enterprise (ook gratis)

## Volgende Stappen

Na setup van Google OAuth:
1. Implementeer backend OAuth flow (`api/auth_routes.py`)
2. Update frontend met login UI (`frontend/dashboard.html`)
3. Voeg session middleware toe aan alle endpoints
4. Test login flow en session persistence

## Support

- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
- [Google Cloud Console](https://console.cloud.google.com/)
