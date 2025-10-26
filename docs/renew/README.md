# Agent-Forge

Dit is Agent-Forge. Een systeem van AI-agenten dat zelfstandig softwareontwikkelingstaken uitvoert. Geef 'm een GitHub issue en hij fixt het.

## Wat doet het?

1.  **Monitort GitHub**: Een `polling_service` scant continu naar nieuwe issues met de juiste labels.
2.  **Claimt & Analyseert**: Ziet 'ie een issue, dan wordt die geclaimd. De `issue_handler` pluist de vraag uit.
3.  **Genereert Code**: De `code_agent` (die met een LLM praat) schrijft de code die nodig is.
4.  **Maakt een PR**: De `bot_agent` commit de changes, maakt een branch en opent een pull request.

Klaar. Zonder dat een mens eraan te pas komt.

## Kerntechnologie

- **Python**: De hele backend draait op Python.
- **LLM's**: Gekoppeld aan verschillende LLM-providers (OpenAI, Anthropic, Google, etc.) om de "denk"-kracht te leveren.
- **GitHub API**: Intensief gebruik van de GitHub API voor alles wat met repo's, issues en PR's te maken heeft.
- **Docker**: Voor het draaien van afhankelijke services zoals Milvus (vector database).
- **YAML**: Alle configuratie is in YAML-bestanden. Geen hardcoded onzin.

## Hoe start je het?

Zie `GETTING_STARTED.md` voor de details, maar in het kort:
1.  Zorg dat je `requirements.txt` geïnstalleerd is.
2.  Start de Milvus docker container (`docker-compose-milvus.yml`).
3.  Configureer je `config/secrets/keys.json` met de nodige API-sleutels.
4.  Draai een van de `launch_*.sh` of `start-*.sh` scripts.

Dit is geen speelgoed. Het is een machinekamer. Wees voorzichtig.

