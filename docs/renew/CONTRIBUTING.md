# Contributing - Hoe je kunt helpen

Oké, dus je wilt bijdragen. Fantastisch. Maar we doen de dingen hier wel op een bepaalde manier. Lees dit voordat je begint, anders wordt je PR waarschijnlijk genegeerd.

## Filosofie

*   **Automatisering eerst**: Alles wat geautomatiseerd kan worden, moet geautomatiseerd worden.
*   **Actie > Vragen**: Probeer iets. Als het breekt, fix het. Wacht niet op toestemming.
*   **Engels is de voertaal**: Alle code, comments, en commit-berichten zijn in het Engels. Geen uitzonderingen.

## Workflow

1.  **Claim een Issue**: Zoek een issue dat je wilt oppakken. Als er geen is, maak er een aan. Wijs het aan jezelf toe en zet een commentaar dat je eraan begint ("🤖 Starting work..."). Dit voorkomt dubbel werk.

2.  **Maak een Branch**: Maak een nieuwe branch vanuit `main`. Gebruik een logische naam.

    ```bash
    git checkout -b feature/add-cool-new-thing
    # of
    git checkout -b fix/solve-annoying-bug
    ```

3.  **Schrijf Code**:
    *   Volg de bestaande stijl. We gebruiken `black` voor Python code formatting. Draai het voordat je commit.
    *   Voeg debug logging toe. Veel. Gebruik de emoji-prefixes (🐛, 🔍, ⚠️, ❌, ✅).
    *   Zorg voor goede error handling. Een `try...except` blok is je vriend.

4.  **Schrijf Tests**:
    *   Nieuwe feature? Nieuwe test. Bug gefixt? Schrijf een test die de bug reproduceert en nu slaagt.
    *   Plaats je tests in de `tests/` map, met een structuur die de `engine/` map spiegelt.
    *   Draai alle tests voordat je een PR maakt:

        ```bash
        pytest
        ```

5.  **Update de Changelog**:
    *   Voeg een regel toe aan `CHANGELOG.md` onder de `[Unreleased]` sectie. Beschrijf wat je hebt veranderd.

6.  **Maak een Pull Request**:
    *   Push je branch naar GitHub.
    *   Maak een Pull Request naar de `main` branch.
    *   De titel van je PR moet duidelijk zijn.
    *   In de beschrijving, link naar het issue dat je oplost (bv. "Closes #123").
    *   Wees voorbereid op een code review.

## Commit Berichten

We gebruiken Conventional Commits. Dit is niet optioneel.

**Formaat**: `type(scope): description`

*   **`type`**: `feat` (nieuwe feature), `fix` (bugfix), `docs` (documentatie), `style` (formatting), `refactor`, `test`, `chore` (build scripts, etc.).
*   **`scope`**: Het deel van de codebase dat je hebt aangepast (bv. `polling`, `code_agent`, `config`).
*   **`description`**: Een korte, duidelijke beschrijving in de tegenwoordige tijd.

**Voorbeelden**:

*   `feat(parser): add support for YAML-based instructions`
*   `fix(github): correct handling of rate limit errors`
*   `docs(contributing): add guidelines for commit messages`

Houd je hieraan. Het helpt ons om de geschiedenis schoon en leesbaar te houden.
