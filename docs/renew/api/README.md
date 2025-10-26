# API Referentie

De `api/` map bevat de RESTful API endpoints van Agent-Forge. Deze worden gebruikt door de frontend en kunnen ook door externe tools worden aangesproken.

De API is gebouwd met Flask.

## Endpoints

### Authenticatie (`api/auth_routes.py`)

*   **`/login`** `[POST]`
    *   **Doel**: Gebruiker inloggen.
    *   **Body**: `{ "username": "...", "password": "..." }`
    *   **Response**: JWT token voor verdere requests.

*   **`/logout`** `[POST]`
    *   **Doel**: Gebruiker uitloggen.
    *   **Vereist**: Geldig JWT token.

### Configuratie (`api/config_routes.py`)

*   **`/config/system`** `[GET]`
    *   **Doel**: Haalt de volledige systeemconfiguratie op (`system/main.yaml`).
    *   **Vereist**: Authenticatie.

*   **`/config/system`** `[POST]`
    *   **Doel**: Werkt de systeemconfiguratie bij.
    *   **Body**: Een YAML-string met de nieuwe configuratie.
    *   **Vereist**: Admin-rechten.

*   **`/config/agents/<agent_name>`** `[GET]`
    *   **Doel**: Haalt de configuratie voor een specifieke agent op.
    *   **Voorbeeld**: `/config/agents/code_agent`
    *   **Vereist**: Authenticatie.

## Hoe te gebruiken

Je kunt `curl` of een andere HTTP-client gebruiken om met de API te praten.

**Voorbeeld: Configuratie ophalen**
```bash
# Eerst inloggen om een token te krijgen
TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"<jouw_wachtwoord>"}' http://localhost:7997/login | jq -r .token)

# Token gebruiken om de config op te halen
curl -H "Authorization: Bearer $TOKEN" http://localhost:7997/config/system
```

**Let op**: De poort (`7997` in dit voorbeeld) kan verschillen afhankelijk van je configuratie.

