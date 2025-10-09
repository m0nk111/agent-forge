import pytest
from pathlib import Path

from engine.operations.issue_handler import IssueHandler
from engine.operations.llm_file_editor import LLMFileEditor


class DummySearch:
    def grep_search(self, **kwargs):
        return []


class DummyErrorChecker:
    def check_syntax(self, file_path):
        return {"valid": True}


class DummyTestRunner:
    def run_tests(self, tests):
        return {"passed": len(tests)}


class DummyAgent:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.codebase_search = DummySearch()
        self.error_checker = DummyErrorChecker()
        self.test_runner = DummyTestRunner()
        self.monitor = None
        self.last_prompt = None

    def query_qwen(self, *args, **kwargs):
        self.last_prompt = kwargs.get("prompt") or (args[0] if args else None)
        prompt_lower = (self.last_prompt or "").lower()
        if "chair" in prompt_lower:
            return """# Cozy Chair Sketch

```text
   __
  /  \
 /____\
 |    |
 |____|
  ||||
```

## Description
- Friendly chair requested during unit test

## Notes
- Stubbed LLM response for chair scenario
- Ensures ASCII art lands inside fenced block
"""

        return """# Sunny Test Sketch

```text
    \\ | /
     ( o )
    /_|_\\
```

## Description
- Friendly sun requested during unit test

## Notes
- Sample output from stubbed LLM
- Ensures ASCII art lands inside fenced block
"""


@pytest.fixture
def tmp_agent(tmp_path):
    return DummyAgent(tmp_path)


def test_infer_special_file_handles_sun_variants(tmp_agent):
    handler = IssueHandler(tmp_agent)
    inferred = handler._infer_special_file("Please draw a zonnetje", "Tekenen van zonnetje")
    assert inferred == "docs/sun.md"


def test_parse_issue_requirements_synthesizes_sun_task(tmp_agent):
    handler = IssueHandler(tmp_agent)
    issue = {
        "title": "Draw a bright sun",
        "body": "We need a warm sun illustration for the docs.",
        "labels": []
    }

    requirements = handler._parse_issue_requirements(issue)

    assert requirements["tasks"], "Expected synthesized task for sun diagram"
    assert requirements["tasks"][0]["description"].startswith("Create docs/sun.md"), requirements["tasks"][0]


def test_task_to_action_infers_sun_file(tmp_agent):
    handler = IssueHandler(tmp_agent)
    task = {"description": "Add ASCII sun with smiling rays", "completed": False}
    action = handler._task_to_action(task, issue_title="Create cheerful sun")

    assert action is not None
    assert action["type"] == "edit_file"
    assert action["file"] == "docs/sun.md"


def test_llm_editor_requests_ascii_from_llm(tmp_agent):
    editor = LLMFileEditor(tmp_agent)
    result = editor.edit_file(
        file_path="docs/sun.md",
        instruction="Draw a cheerful sun diagram",
        context=""
    )

    assert result["success"], result

    sun_path = tmp_agent.project_root / "docs" / "sun.md"
    content = sun_path.read_text()

    assert content.startswith("# Sunny Test Sketch"), content
    assert "```text" in content
    assert "( o )" in content
    assert "```" in content
    assert "## Description" in content
    assert "## Notes" in content

    assert tmp_agent.last_prompt is not None


def test_infer_special_file_handles_chair(tmp_agent):
    handler = IssueHandler(tmp_agent)
    inferred = handler._infer_special_file(
        "Maak een ASCII tekening van een stoel",
        "Stoel diagram gewenst"
    )
    assert inferred == "docs/chair.md"


def test_infer_special_file_handles_unknown_ascii_subject(tmp_agent):
    handler = IssueHandler(tmp_agent)
    inferred = handler._infer_special_file(
        "Please draw a playful ASCII rocket for the docs",
        "Draw rocket art"
    )
    assert inferred == "docs/rocket.md"


def test_llm_editor_handles_non_sun_subject(tmp_agent):
    editor = LLMFileEditor(tmp_agent)
    result = editor.edit_file(
        file_path="docs/chair.md",
        instruction="Draw a comfy chair diagram",
        context=""
    )

    assert result["success"], result

    chair_path = tmp_agent.project_root / "docs" / "chair.md"
    content = chair_path.read_text()

    assert content.startswith("# Cozy Chair Sketch"), content
    assert "```text" in content
    assert "____" in content
    assert "## Description" in content
