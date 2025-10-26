# Core Engine Componenten

Dit is de machinekamer. De `engine/core` map bevat de meest cruciale, hoog-niveau componenten die het hele systeem aansturen.

## Overzicht

* **`coordinator_agent.py`**: De Grote Baas. De coördinator is geen "denkende" agent, maar een dirigent. Hij ontvangt een taak (meestal van de `IssueHandler`), selecteert de juiste agent voor de klus (zoals de `CodeAgent`), geeft de taak door, en houdt de voortgang in de gaten.
* **`service_manager.py`**: De Facilitair Manager. Deze klasse is verantwoordelijk voor het starten, stoppen en beheren van de levenscyclus van achtergrondservices, zoals de `PollingService`.
* **`agent_manager.py`**: De HR-afdeling. Beheert de pool van beschikbare agents. Weet welke agents er zijn, wat hun status is, en hoe ze geïnitialiseerd moeten worden.

## Workflow

1. Een externe trigger (zoals de `PollingService` die een nieuwe issue vindt) roept de `CoordinatorAgent` aan met een nieuwe taak.
2. De `CoordinatorAgent` gebruikt de `AgentManager` om een geschikte, beschikbare agent te vinden.
3. De `CoordinatorAgent` start de gekozen agent en geeft de taakdetails door.
4. De agent voert zijn taak uit (bv. code schrijven).
5. De agent rapporteert de status terug aan de `CoordinatorAgent`.
6. De `CoordinatorAgent` sluit de taak af.

Deze scheiding van verantwoordelijkheden is cruciaal. De coördinator hoeft niet te weten *hoe* code wordt geschreven, alleen *wie* het moet doen. De agent hoeft zich geen zorgen te maken over waar de taak vandaan kwam, alleen over de uitvoering ervan.
