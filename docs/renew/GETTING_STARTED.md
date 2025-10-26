# Getting Started - Snel aan de slag

Oké, je wilt dit ding dus draaien. Volg deze stappen. Sla je er een over, dan werkt het niet.

## 1. Dependencies

Eerst de basis. Zorg dat je Python 3.10+ hebt.

Open een terminal en ram dit erin:

```bash
pip install -r requirements.txt
```

Dit installeert alle Python-packages die nodig zijn. Kan even duren.

## 2. Externe Services

Agent-Forge heeft een paar vrienden nodig om te kunnen werken.

### Milvus (Vector Database)

Voor het onthouden van code en context (embedding search) gebruiken we Milvus. De makkelijkste manier om dit te starten is met Docker.

```bash
docker-compose -f docker-compose-milvus.yml up -d
```

Dit start Milvus op de achtergrond. Controleer met `docker ps` of het draait.

## 3. Configuratie

Dit is het belangrijkste deel. Zonder de juiste sleutels en instellingen is de machine blind en doof.

### API Sleutels

1. Navigeer naar de `config/secrets/` map.
2. Hernoem `keys.example.json` naar `keys.json`.
3. Open `keys.json` en vul je API-sleutels in. Je hebt minimaal nodig:
    * `GITHUB_TOKEN`: Een GitHub Personal Access Token met `repo` en `workflow` permissies. Dit is voor de bot die PR's maakt.
    * Een LLM API-sleutel. Bijvoorbeeld `OPENAI_API_KEY` voor OpenAI.

**WAARSCHUWING**: Zet dit `keys.json` bestand **NOOIT** in een publieke repo. Het staat in de `.gitignore`, en dat is met een reden.

### Agent & Systeem Configuratie

De rest van de configuratie zit in `config/`.

*   `config/agents/`: Bepaalt welke agents er zijn en wat ze kunnen.
*   `config/services/`: Instellingen voor de `polling_service` en anderen.
*   `config/system/`: Algemene systeeminstellingen.

Voor een standaard-setup hoef je hier in eerste instantie niet aan te komen.

## 4. Starten

Alles is nu klaar. Tijd om de motor te starten.

Er zijn verschillende manieren, afhankelijk van wat je wilt doen.

### De Polling Service (Standaard Manier)

Dit is de normale modus. De service zoekt zelf naar issues en lost ze op.

```bash
./scripts/install-polling-service.sh
```

Dit installeert en start de `agent-forge-polling.service` via `systemd`. Hij draait nu permanent op de achtergrond.
Met `sudo systemctl status agent-forge-polling` kun je de status checken.

### Handmatig een Agent Lanceren

Wil je een specifieke agent testen op een issue? Gebruik een van de `launch_*.py` scripts.

Voorbeeld:

```bash
python scripts/launch_agent.py --issue-number 123 --repo-owner m0nk111 --repo-name agent-forge
```

Dit start een agent specifiek voor issue #123 in de `agent-forge` repo.

## 5. Wat nu?

Als alles goed is gegaan, zie je activiteit in de logs (voor de systemd service: `journalctl -u agent-forge-polling -f`) of direct in je terminal. De agent zal de issue claimen, een branch maken, code pushen en een PR openen.

Succes. Don't break stuff.

