# Gids: Een Nieuwe Agent Aanmaken

Je wilt dus een nieuwe, gespecialiseerde agent bouwen. Goed. Het systeem is modulair, dus dit is prima te doen. Volg deze stappen.

## 1. Het Concept

Bedenk eerst: **wat moet deze agent doen?** Is het een `DocWriterAgent`, een `DatabaseAdminAgent`, een `SecurityScanAgent`? Een agent moet één duidelijke taak hebben. Als het te veel doet, wordt het een rommel.

Voor dit voorbeeld maken we een `DocWriterAgent` die documentatie kan schrijven of bijwerken.

## 2. Maak het Bestand

Alle agents wonen in `engine/operations/`.
Maak een nieuw bestand aan: `engine/operations/doc_writer_agent.py`.

## 3. De Basisstructuur

Elke agent erft van een basisklasse of heeft op zijn minst een vergelijkbare structuur. Een agent is in essentie een Python-klasse met een `run` methode.

```python
# engine/operations/doc_writer_agent.py

from engine.operations.base_agent import BaseAgent # (Stel dat we een BaseAgent hebben)

class DocWriterAgent(BaseAgent):
    def __init__(self, issue_context, file_handler, llm_provider):
        """
        Initialiseer de DocWriterAgent.

        :param issue_context: De context van de issue (titel, body, etc.).
        :param file_handler: Een utility om bestanden te lezen/schrijven.
        :param llm_provider: De LLM-provider om mee te praten.
        """
        self.issue_context = issue_context
        self.file_handler = file_handler
        self.llm_provider = llm_provider
        # Voeg hier eventuele andere benodigde dependencies toe

    def run(self):
        """
        De hoofd-entrypoint voor de agent. Hier gebeurt de magie.
        """
        print("🐛 DocWriterAgent gestart...")

        # 1. Analyseer de vraag
        task = self._analyze_request()

        # 2. Genereer de documentatie
        generated_doc = self._generate_documentation(task)

        # 3. Schrijf het bestand
        self._write_documentation(task, generated_doc)

        print("✅ DocWriterAgent klaar.")

    def _analyze_request(self):
        # Gebruik de LLM om de issue body te interpreteren
        # en er een concrete taak van te maken.
        # Bv: "Maak een README voor de 'parser' module."
        prompt = f"Analyseer deze vraag en bepaal welk document geschreven moet worden en waar: {self.issue_context['body']}"
        task_description = self.llm_provider.query(prompt)
        # ... parse de output van de LLM naar een gestructureerd object ...
        return parsed_task

    def _generate_documentation(self, task):
        # Gebruik de LLM om de daadwerkelijke documentatie te genereren.
        # Geef 'm context mee, zoals de code van de module.
        prompt = f"Schrijf documentatie voor de volgende taak: {task}. Hier is de relevante code: {self.file_handler.read(task['target_file'])}"
        documentation = self.llm_provider.query(prompt)
        return documentation

    def _write_documentation(self, task, content):
        # Gebruik de file_handler om het resultaat weg te schrijven.
        self.file_handler.write(task['output_path'], content)
        print(f"🔍 Documentatie geschreven naar {task['output_path']}")

```

**Belangrijk**: Dit is een versimpeld voorbeeld. In de echte `code_agent.py` zie je een veel complexere `run` loop met state management, retries, en validatie.

## 4. Registreer de Agent

Het systeem moet weten dat je nieuwe agent bestaat. Dit gebeurt meestal in de `CoordinatorAgent` of een `AgentManager`.

Open `engine/core/coordinator_agent.py` (of waar de agent-selectie logica zit).

Voeg een `case` toe voor je nieuwe agent. De coordinator moet op basis van de issue (bv. een label `documentation`) bepalen welke agent hij moet starten.

```python
# In de CoordinatorAgent of vergelijkbaar

def _select_agent(self, issue_context):
    labels = issue_context.get('labels', [])

    if 'bug' in labels:
        print("🔧 CodeAgent geselecteerd voor bugfix.")
        return CodeAgent(...)
    elif 'documentation' in labels:
        print("✍️ DocWriterAgent geselecteerd voor documentatie.")
        return DocWriterAgent(...) # Zorg dat je de juiste dependencies meegeeft
    else:
        print("🔧 Standaard CodeAgent geselecteerd.")
        return CodeAgent(...)
```

## 5. Configureer de Agent (Optioneel)

Als je agent specifieke instellingen heeft (bv. welke LLM te gebruiken, standaard output map), voeg dan een `config/agents/doc_writer.yaml` bestand toe en laad dit in je agent.

## 6. Testen

Schrijf een test in `tests/operations/test_doc_writer_agent.py`. Maak een mock `issue_context`, een mock `llm_provider` en een mock `file_handler`. Roep de `run` methode aan en controleer of de `file_handler.write` methode wordt aangeroepen met de verwachte content.

Dat is het. Je hebt nu een nieuwe, gespecialiseerde agent in het systeem.
