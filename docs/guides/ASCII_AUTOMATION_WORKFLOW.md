# ASCII Automation Workflow

## Overview

This document explains how the Agent Forge pipeline interprets GitHub issues that request ASCII drawings and produces playful Markdown output via the LLM-powered file editor. It supplements the multi-agent GitHub strategy guide and focuses on the implementation introduced on 2025-10-09.

## End-to-End Flow

1. **Issue ingestion**
   - `issue_handler.py` evaluates the title and body for creative drawing cues such as *sun*, *chair*, *car*, or any request that implies an ASCII illustration.
   - When the handler infers the need for a Markdown asset (for example `docs/sun.md`), it schedules a file generation task for the code agent.
2. **Task hand-off**
   - The coordinator assigns the task to the code agent with the inferred target path and high-level prompt extracted from the issue.
   - All debug logs for this stage use the Agent Forge emoji conventions (🐛, 🔍, ⚠️, ❌, ✅, 📊, 🔧) and are gated behind the global `DEBUG` flag.
3. **LLM-driven file creation**
   - `engine/operations/llm_file_editor.py` routes Markdown requests through `_handle_special_cases()`.
   - If the path or requirements hint at ASCII art, `_extract_ascii_subject()` derives the object (defaulting to *sun* when ambiguous).
   - `_generate_ascii_markdown_via_llm()` builds a structured prompt:
     - Heading `# ASCII {Subject}`
     - Friendly note that references the trigger issue
     - ` ```text ` fenced block containing the drawing
   - The module sends the prompt to the configured LLM provider and writes the response to disk.
      - The issue handler now normalises subjects like *stoel*, *auto*, or *raket* to English slugs (chair, car, rocket) and stores the art in `docs/<subject>.md`.
4. **Pull request automation**
   - The coordinator commits the generated file, updates the changelog, and opens a pull request describing the new illustration.
   - The bot agent ensures rate limits and claim policies are respected while publishing the PR.

## Debugging the Workflow

| Stage | Helpful log prefix | File | Notes |
| --- | --- | --- | --- |
| Issue parsing | `🔍 IssueHandler` | `engine/operations/issue_handler.py` | Confirms detection of ASCII keywords and destination path |
| Task execution | `🐛 Coordinator` | `engine/runners/coordinator_agent.py` | Shows delegation to the code agent |
| File editing | `🔍 LLMFileEditor` | `engine/operations/file_editor.py` & `engine/operations/llm_file_editor.py` | Displays prompt payload and selected subject |
| PR publication | `✅ BotAgent` | `engine/runners/bot_agent.py` | Confirms branch creation and PR URL |

Enable `DEBUG=1` in the environment before running services to surface these logs.

## Testing Strategy

- Run `pytest tests/test_issue_handler_sun.py` to validate the ASCII automation without making external LLM calls.
- The suite stubs the LLM response, asserting that the Markdown structure and fenced `text` block are preserved.
- Extend coverage by creating companion tests (e.g., `test_issue_handler_chair.py`) that reuse the same stub infrastructure when adding new keywords or heuristics.

## Issue & PR Validation Plan

1. **Dry-run issue**: Open a draft GitHub issue that requests a specific drawing (e.g., "Maak een ASCII raket"), tag it for automation, and confirm that the polling service picks it up without immediately assigning real production labels.
2. **Monitor agent logs**: With `DEBUG=1`, verify that `IssueHandler` infers `docs/<subject>.md`, the coordinator delegates to the code agent, and the LLM prompt includes the requested subject.
3. **Branch verification**: Inspect the generated branch to confirm the Markdown file, changelog entry, and any documentation updates before merging.
4. **PR review checklist**: Ensure the PR description explains the drawing produced, references the triggering issue, and links to the rendered Markdown preview for manual inspection.
5. **Regression sweep**: After merging, rerun the `pytest` suite and spot-check the repository to guarantee that repeated issue triggers (sun, chair, car, rocket) each produce discrete Markdown files.

## Extending the Subject Detection

1. Update `_ASCII_KEYWORDS` in `llm_file_editor.py` with the new term(s).
2. Add subject-specific guidance to `_extract_ascii_subject()` if the default heuristics need refinement.
3. Create a new integration test under `tests/` that stubs the expected Markdown response.
4. Document the addition in `CHANGELOG.md` and ensure `README.md` highlights the new capability.

## Known Constraints

- The LLM response is responsible for crafting valid ASCII; ensure prompts are explicit about style ("like a kid's drawing") when creating new tests.
- The changelog and README require manual updates during each enhancement to stay aligned with automation behaviour.
- Duplicate Markdown headings in `CHANGELOG.md` are tolerated by tooling but should be consolidated during the next documentation cleanup.

## Next Steps

- Add regression tests for non-sun subjects as they become common requests.
- Consider capturing the raw LLM prompt/response pair in artifacts for troubleshooting when DEBUG mode is active.
- Expand documentation with an OpenAPI excerpt illustrating the issue → PR workflow once the endpoint stabilises.
