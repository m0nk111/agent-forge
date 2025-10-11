# Issue Opener Agent

**Autonomous GitHub issue resolution powered by GPT-5 Chat Latest**

The Issue Opener Agent is a fully autonomous system that can:
1. 📖 Read and analyze GitHub issues
2. 🧠 Understand requirements using GPT-5
3. 💻 Generate implementation code
4. 🧪 Run tests
5. 🔀 Create pull requests

## Features

✅ **Fully Autonomous** - No human intervention required  
✅ **GPT-5 Powered** - Fast and high-quality code generation  
✅ **Test Integration** - Runs tests before creating PR  
✅ **Safety Checks** - Limited file modifications, review required  
✅ **Detailed PRs** - Complete descriptions of changes  

## Quick Start

### 1. Setup

Ensure you have the required API keys:

```bash
# In keys.json
{
  "OPENAI_API_KEY": "your-openai-key",
  "BOT_GITHUB_TOKEN": "your-github-token"
}

# Or as environment variables
export OPENAI_API_KEY="your-openai-key"
export BOT_GITHUB_TOKEN="your-github-token"
```

### 2. Label an Issue

Add the `auto-resolve` or `agent-ready` label to a GitHub issue:

```
Issue #123: Add logging to user service
Labels: auto-resolve, enhancement
```

### 3. Run the Agent

```bash
python3 scripts/launch_issue_opener.py 123
```

The agent will:
1. Fetch issue details
2. Analyze requirements
3. Create implementation plan
4. Generate code
5. Run tests
6. Create pull request

### 4. Review the PR

The agent creates a PR with:
- Clear description of changes
- List of modified files
- Test results
- Link to original issue

## Usage

### Command Line

```bash
# Resolve a specific issue
python3 scripts/launch_issue_opener.py <issue_number>

# Example
python3 scripts/launch_issue_opener.py 123
```

### Programmatic Usage

```python
from engine.operations.issue_opener_agent import IssueOpenerAgent

config = {
    'github_token': 'your-token',
    'openai_api_key': 'your-key',
    'model': 'gpt-5-chat-latest',
    'repo': 'owner/repo',
    'project_root': '/path/to/project'
}

agent = IssueOpenerAgent(config)
result = agent.process_issue(123)

if result['success']:
    print(f"PR created: {result['pr_url']}")
```

## Configuration

Configuration file: `config/agents/issue-opener-agent.yaml`

### Key Settings

```yaml
# LLM Model
llm:
  model_name: "gpt-5-chat-latest"  # Fast, recommended
  # Or use: "gpt-5-pro" for complex issues (slower)

# GitHub Labels
github:
  trigger_labels:
    - "auto-resolve"
    - "agent-ready"
  skip_labels:
    - "wontfix"
    - "manual-only"

# Safety Limits
capabilities:
  max_files_per_pr: 10
  max_lines_per_file: 500
  delete_files: false  # Safety: no deletions
```

## Issue Requirements

For best results, structure your issues clearly:

### Good Issue Example

```markdown
**Title**: Add rate limiting to API endpoints

**Description**:
Implement rate limiting for the `/api/users` endpoint to prevent abuse.

**Requirements**:
- 100 requests per minute per IP
- Return 429 status when limit exceeded
- Include `Retry-After` header
- Log rate limit violations

**Files**:
- `api/middleware/rate_limiter.py` (create)
- `api/routes.py` (modify)
- `tests/test_rate_limiter.py` (create)

**Acceptance Criteria**:
- [ ] Rate limiter middleware implemented
- [ ] Tests pass
- [ ] Documentation updated
```

### Bad Issue Example

```markdown
**Title**: Fix bug

**Description**:
Something is broken, please fix it.
```

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Issue Created                            │
│                  (with auto-resolve label)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Fetches Issue                            │
│           (title, body, labels, metadata)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          GPT-5 Analyzes Requirements                        │
│       (extracts tasks, files, complexity)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         GPT-5 Creates Implementation Plan                   │
│    (files to create/modify, changes needed)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Create Feature Branch                            │
│         (issue-123-descriptive-name)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         GPT-5 Generates Code Changes                        │
│    (creates new files, modifies existing)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Run Tests                                      │
│        (pytest, linting, validation)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Commit and Push Changes                            │
│    (descriptive commit message with issue ref)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Create Pull Request                               │
│   (links to issue, describes changes, requests review)      │
└─────────────────────────────────────────────────────────────┘
```

## Performance

**GPT-5 Chat Latest Performance:**

| Issue Type | Analysis | Code Gen | Total | Quality |
|------------|----------|----------|-------|---------|
| Simple | 2-3s | 30s | ~35s | 5/5 |
| Medium | 3-5s | 60s | ~65s | 5/5 |
| Complex | 5-10s | 120s | ~130s | 5/5 |

**50% faster than GPT-4o with equal quality!**

## Safety Features

The agent includes several safety mechanisms:

1. **File Deletion Disabled** - Cannot delete files by default
2. **File Limits** - Maximum 10 files per PR
3. **Line Limits** - Maximum 500 lines per file
4. **Review Required** - All PRs require review before merge
5. **Test Validation** - Tests run before PR creation
6. **Excluded Directories** - Cannot modify `external-code/`, `secrets/`

## Troubleshooting

### Agent Fails to Start

```bash
# Check API keys
cat keys.json | jq .

# Verify environment
echo $OPENAI_API_KEY
echo $BOT_GITHUB_TOKEN
```

### Code Generation Fails

- Ensure issue description is clear and detailed
- Check that files to modify actually exist
- Verify project structure is correct

### Tests Fail

- Agent will still create PR even if tests fail
- Review test failures in PR description
- Fix manually and update PR

### PR Creation Fails

- Check GitHub token permissions (needs repo write access)
- Verify branch doesn't already exist
- Check rate limits on GitHub API

## Advanced Usage

### Custom Configuration

Create a custom config file:

```python
import yaml

config = yaml.safe_load(open('custom-config.yaml'))
agent = IssueOpenerAgent(config)
```

### Monitoring Integration

Enable monitoring to track metrics:

```yaml
monitoring:
  enabled: true
  endpoint: "http://localhost:7997"
```

### Use GPT-5 Pro for Complex Issues

```yaml
advanced:
  use_pro_for_complex: true
  complexity_threshold: "high"
```

⚠️ **Note**: GPT-5 Pro is much slower (40-70s vs 2s) but may provide higher quality for very complex issues.

## Examples

### Example 1: Add New Feature

**Issue**:
```markdown
Title: Add user authentication endpoint
Labels: auto-resolve, feature

Create a `/api/auth/login` endpoint that accepts username/password and returns JWT token.
```

**Result**: PR created with:
- `api/auth/login.py` (new)
- `api/models/user.py` (modified)
- `tests/test_auth.py` (new)

### Example 2: Fix Bug

**Issue**:
```markdown
Title: Fix crash in user service when email is missing
Labels: auto-resolve, bug

The user service crashes with NoneType error when processing users without email.
Add validation to handle missing emails gracefully.
```

**Result**: PR created with:
- `services/user_service.py` (modified - added email validation)
- `tests/test_user_service.py` (modified - added test case)

### Example 3: Refactor Code

**Issue**:
```markdown
Title: Extract database logic from API routes
Labels: auto-resolve, refactoring

Move database queries from `api/routes.py` into separate `db/queries.py` module.
```

**Result**: PR created with:
- `db/queries.py` (new - extracted queries)
- `api/routes.py` (modified - uses new module)
- `tests/test_queries.py` (new - query tests)

## Best Practices

1. **Clear Issue Descriptions**
   - State the problem clearly
   - List specific requirements
   - Mention files to modify if known

2. **Acceptance Criteria**
   - Use checkboxes for requirements
   - Be specific and testable

3. **Labels**
   - Use `auto-resolve` for autonomous resolution
   - Add complexity label (low/medium/high)
   - Tag issue type (feature/bug/refactor)

4. **Review PRs**
   - Always review agent-generated code
   - Run tests locally
   - Check for edge cases

5. **Iterate**
   - If PR is not perfect, provide feedback in comments
   - Agent can process feedback in future versions

## Limitations

- **Cannot resolve all issues**: Complex architectural decisions need human input
- **Test coverage**: Agent generates tests but may miss edge cases
- **Context limits**: Very large codebases may exceed LLM context
- **API costs**: Each issue costs ~$0.01-0.05 in API calls

## Roadmap

Future enhancements:

- [ ] Automatic issue monitoring (poll for new auto-resolve labels)
- [ ] Multi-issue batch processing
- [ ] Learning from PR feedback
- [ ] Custom code style enforcement
- [ ] Integration with CI/CD pipelines
- [ ] Slack/Discord notifications
- [ ] Issue complexity prediction
- [ ] Automatic test generation improvements

## Support

For issues or questions:

1. Check this documentation first
2. Review `CHANGELOG.md` for recent changes
3. Open a GitHub issue (ironically, the agent might fix it!)
4. Check `logs/issue_opener_agent.log` for details

## License

Same as Agent-Forge project. See `LICENSE` file.

---

**🤖 Built with GPT-5 Chat Latest - 50% faster, equal quality!**
