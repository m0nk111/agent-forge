# Gids: Debuggen en Testen

Iets werkt niet. Gebeurt de hele tijd. Zo vind je uit wat er mis is.

## De Heilige Graal: Logging

Alles, maar dan ook **alles**, wordt gelogd. Als je een service via `systemd` draait (`install-polling-service.sh`), dan check je de logs zo:

```bash
# Volg de logs live
journalctl -u agent-forge-polling -f

# Bekijk de laatste 200 regels
journalctl -u agent-forge-polling -n 200
```

Als je een script handmatig start, zie je de output direct in je terminal.

### Log Levels & Emojis

We gebruiken verschillende log-levels, herkenbaar aan de emojis:

*   `🐛 DEBUG`: Algemene debug info. "Ik ben nu hier."
*   `🔍 INFO`: Gedetailleerde inspectie. "Ik heb dit object ontvangen."
*   `✅ SUCCESS`: Een belangrijke stap is gelukt. "PR succesvol aangemaakt."
*   `⚠️ WARNING`: Iets is raar, maar niet fataal. "API-sleutel niet gevonden, val terug op fallback."
*   `❌ ERROR`: Er is iets goed mis. Hier moet je kijken. "Kon bestand niet schrijven: permissie geweigerd."

Filteren op deze emojis in je log-output is de snelste manier om problemen te vinden.

## Handmatig Draaien

De `polling_service` is handig, maar voor debuggen wil je directe controle. Gebruik de `launch_*.py` scripts.

```bash
python scripts/launch_agent.py --issue-number 123 --repo-owner m0nk111 --repo-name agent-forge
```

Nu zie je precies wat de agent doet voor dat ene issue, zonder de ruis van de polling. Je kunt `print()` statements toevoegen in de code en ze direct zien.

## Testen

We gebruiken `pytest`. De tests staan in de `tests/` map.

### Alle Tests Draaien

Simpelweg:

```bash
pytest
```

Dit vindt en draait alle tests in de `tests/` map. Doe dit **altijd** voordat je een PR maakt.

### Eén Testbestand Draaien

Stel je werkt aan de `issue_handler`. Dan wil je alleen die tests draaien.

```bash
pytest tests/operations/test_issue_handler.py
```

### Eén Specifieke Test Draaien

Nog specifieker, je wilt één testfunctie in dat bestand draaien.

```bash
pytest tests/operations/test_issue_handler.py::test_claims_issue_successfully
```

### Testen met Coverage

Wil je weten hoe goed je tests de code dekken?

```bash
pytest --cov=engine
```

Dit geeft je een rapport dat laat zien welke regels code wel en niet zijn geraakt door je tests.

## Veelvoorkomende Problemen

1.  **Configuratie Fout**: 9 van de 10 keer is dit het. Een missende API-sleutel, een verkeerd pad in een `.yaml` bestand. Controleer `config/` en `config/secrets/keys.json` dubbel.
2.  **GitHub Permissies**: De `GITHUB_TOKEN` heeft niet genoeg rechten. Zorg dat het token `repo` en `workflow` scopes heeft.
3.  **Python Dependencies**: Een package is niet (correct) geïnstalleerd. Draai `pip install -r requirements.txt` opnieuw, eventueel in een schone virtual environment.
4.  **LLM Fouten**: De LLM API geeft een fout terug (rate limit, verkeerd model, etc.). De error van de LLM wordt meestal direct in de logs geprint.
