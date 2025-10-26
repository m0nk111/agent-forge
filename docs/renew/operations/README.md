# Operationele Componenten

De `engine/operations` map bevat de "denkende" en "doende" onderdelen van het systeem. Dit zijn de specialisten die het daadwerkelijke werk uitvoeren.

## Overzicht

*   **`code_agent.py`**: De Programmeur. Dit is de meest complexe agent. Hij praat met LLM's om code te begrijpen, te schrijven en aan te passen. Hij kan bestanden lezen, wijzigingen voorstellen en deze toepassen.
*   **`bot_agent.py`**: De Git-specialist. Deze agent handelt alle interacties met GitHub af die *niet* direct met code-generatie te maken hebben. Denk aan:
    *   Een issue claimen.
    *   Een nieuwe branch aanmaken.
    *   Bestanden committen en pushen.
    *   Een pull request openen.
    Hij gebruikt een aparte bot-account om de hoofd-account niet te spammen.
*   **`issue_handler.py`**: De Werkvoorbereider. Dit is de eerste stop voor een nieuwe issue. Hij:
    *   Leest de issue.
    *   Gebruikt "Smart Task Recognition" om uit een vage beschrijving concrete taken te destilleren.
    *   Vertaalt de vraag naar een gestructureerd formaat dat de `CoordinatorAgent` begrijpt.
*   **`github_api_helper.py`**: De Telefooncentrale voor GitHub. Een utility-klasse die alle directe `requests` naar de GitHub API centraliseert. Dit maakt het makkelijker om authenticatie, error handling en rate limiting op één plek te beheren.
*   **`file_editor.py`**: De Schrijver. Een simpele utility die door agents wordt gebruikt om veilig bestanden op schijf te lezen en te schrijven.

## Relaties

*   De `IssueHandler` ontvangt een issue en geeft een gestructureerde taak aan de `CoordinatorAgent`.
*   De `CoordinatorAgent` geeft de taak aan de `CodeAgent`.
*   De `CodeAgent` gebruikt de `LLMProvider` om code te genereren en de `FileEditor` om het op te slaan.
*   Als de `CodeAgent` klaar is, geeft hij een seintje aan de `CoordinatorAgent`.
*   De `CoordinatorAgent` geeft de `BotAgent` de opdracht om de wijzigingen te committen en een PR te openen.
*   Zowel de `BotAgent` als de `IssueHandler` gebruiken de `GithubAPIHelper` om met GitHub te praten.
