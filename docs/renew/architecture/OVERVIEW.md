# Architectuur - De Grote Lijnen

## Kern
Alles draait om de `engine`. Dit is het hart van het systeem.
- **`core`**: De motor. Hier vind je `agent_manager`, `coordinator_agent`, `service_manager`. Dit zijn de dirigenten van het orkest.
- **`operations`**: De doeners. `code_agent` die de code schrijft, `issue_handler` die GitHub issues aanpakt, `github_api_helper` voor alle communicatie met GitHub.
- **`runners`**: De lange-afstandslopers. Diensten die continu draaien, zoals de `polling_service` die naar nieuwe issues zoekt.
- **`validation`**: De poortwachters. Zorgen dat alles wat binnenkomt en buitengaat klopt. `instruction_validator` bijvoorbeeld.

## Communicatie & Data
- **`api`**: De voordeur. Hier komen externe verzoeken binnen. Routes voor authenticatie, configuratie, etc.
- **`config`**: Het geheugen. Alle instellingen voor agents, services, en het systeem zelf.
- **`data`**: De opslagplaats. Tijdelijke data, state-bestanden zoals `polling_state.json`.

## Gebruikersinterface & Scripts
- **`frontend`**: Wat de gebruiker ziet. HTML-bestanden voor de dashboard, login, etc.
- **`scripts`**: De gereedschapskist. Allerlei losse scripts om dingen te testen, te deployen, of te beheren.

## Structuur & Regels
- **Root-level bestanden**: `README.md`, `CHANGELOG.md`, `requirements.txt`. De basisinfo.
- **`docs`**: De bibliotheek. Alle documentatie, inclusief deze.
- **`tests`**: De kwaliteitscontrole. Zorgt ervoor dat niks kapotgaat.

