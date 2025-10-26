# Gids: Het Configuratie Systeem Begrijpen

Alles in Agent-Forge is configureerbaar. Hardcoded waarden zijn de vijand. Als je het systeem wilt aanpassen, is de `config/` map waar je moet zijn.

## De Structuur

De `config/` map is het centrale zenuwstelsel. Het is als volgt opgebouwd:

```yaml
config/
├── agents/
│   ├── code_agent.yaml
│   └── ...
├── rules/
│   └── default_rules.yaml
├── secrets/
│   └── keys.example.json
├── services/
│   └── polling.yaml
└── system/
    └── main.yaml
```

### `config/system/main.yaml`

Hier staan de globale instellingen. Denk aan de naam van de applicatie, de standaard log-level, en andere overkoepelende parameters.

### `config/secrets/keys.json`

**Dit is de belangrijkste en gevaarlijkste map.** Hier bewaar je je API-sleutels. Het bestand `keys.json` wordt geladen door het systeem en de waarden worden beschikbaar gemaakt. Dit bestand staat (en moet in) je `.gitignore` staan. Pleeg dit nooit naar een publieke repository.

### `config/services/`

Hier configureer je de langlopende services. Het meest prominente voorbeeld is `polling.yaml`.

**`polling.yaml`**:

*   `github_query`: De exacte zoekopdracht die wordt gebruikt om naar issues te zoeken (bv. `is:open is:issue label:agent-forge-task assignee:m0nk111-coder`).
*   `interval_seconds`: Hoeveel seconden de service wacht tussen elke zoekopdracht.
*   `claim_username`: Welke GitHub gebruiker wordt toegewezen aan de issue wanneer deze wordt geclaimd.

### `config/agents/`

Hier krijgt elke agent zijn eigen configuratiebestand. In `code_agent.yaml` kun je bijvoorbeeld instellen:

*   `llm_provider`: Welke LLM-provider de agent moet gebruiken (bv. `openai`, `anthropic`).
*   `model`: Het specifieke model (bv. `gpt-4o`, `claude-3-opus-20240229`).
*   `max_retries`: Hoe vaak de agent een taak opnieuw mag proberen als deze faalt.

### `config/rules/`

Hier definieer je regels en prompts die door het hele systeem worden gebruikt. `default_rules.yaml` kan bijvoorbeeld de standaard prompts bevatten voor het genereren van commit-berichten of het analyseren van een issue.

## Hoe wordt het geladen?

Bij de start van de applicatie (of een service) wordt een `ConfigManager` (of een vergelijkbare utility) geïnitialiseerd. Deze leest de relevante YAML-bestanden, combineert ze tot één groot configuratie-object en maakt dit beschikbaar voor de rest van de applicatie.

Het systeem gebruikt vaak een "cascading" model: je kunt een standaardwaarde in `system/main.yaml` hebben, die overschreven kan worden door een specifiekere instelling in bijvoorbeeld `agents/code_agent.yaml`.

## Best Practices

1.  **Geen Geheimen in Git**: API-sleutels en andere geheimen horen **alleen** in `config/secrets/` en dit pad moet in `.gitignore` staan.
2.  **Wees Specifiek**: Maak liever een nieuw, klein configuratiebestand voor een nieuwe feature dan een bestaand bestand vol te proppen.
3.  **Gebruik Variabelen**: Sommige configuraties ondersteunen omgevingsvariabelen (bv. `os.getenv('MY_SETTING')`). Dit is handig voor productie-deployments.
4.  **Valideer bij het Opstarten**: Goede code controleert bij het opstarten of alle benodigde configuratiewaarden aanwezig zijn en crasht als dat niet zo is. Dit voorkomt onverwacht gedrag later.

Als je het gedrag van een agent of service wilt veranderen, is de kans 99% dat je in de `config/` map moet beginnen met zoeken.
