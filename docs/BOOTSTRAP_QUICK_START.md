# Project Bootstrap Agent - Quick Start Guide

## Overview

The Project Bootstrap Agent automates the complete setup of new GitHub repositories, including:
- ✅ Repository creation with proper configuration
- ✅ Bot collaborator invitation and auto-acceptance
- ✅ Project structure generation from templates
- ✅ Initial file push (code, docs, tests, CI/CD)
- ✅ Branch protection configuration
- ✅ GitHub Actions workflows

## Quick Start

### 1. Basic Repository Creation

```python
from engine.operations.bootstrap_coordinator import BootstrapCoordinator

# Initialize with GitHub token
coordinator = BootstrapCoordinator(
    admin_token="ghp_your_token_here",
    bot_tokens={
        "m0nk111-post": "ghp_bot_token_1",
        "m0nk111-qwen-agent": "ghp_bot_token_2"
    }
)

# Create a Python project
result = coordinator.bootstrap_repository(
    name="my-awesome-project",
    description="An awesome Python project",
    template="python",  # or "typescript", "go"
    private=False,
    bot_collaborators=[
        {"username": "m0nk111-post", "permission": "push"},
        {"username": "m0nk111-qwen-agent", "permission": "push"}
    ]
)

print(f"✅ Repository created: {result['repository']['html_url']}")
```

### 2. Available Templates

List available project templates:

```python
templates = coordinator.list_available_templates()
for template in templates:
    print(f"{template['name']}: {template['description']}")
```

**Available Templates:**
- **python**: Python project with pytest, setup.py, GitHub Actions
- **typescript**: TypeScript/Node.js project with jest, tsconfig
- **go**: Go project with modules structure

### 3. Template Structure

#### Python Template
```
my-project/
├── src/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── docs/
│   ├── API.md
│   └── ARCHITECTURE.md
├── .github/
│   └── workflows/
│       └── test.yml
├── requirements.txt
├── setup.py
├── README.md
└── LICENSE
```

#### TypeScript Template
```
my-project/
├── src/
│   └── index.ts
├── tests/
│   └── index.test.ts
├── .github/
│   └── workflows/
│       └── test.yml
├── package.json
├── tsconfig.json
├── jest.config.js
├── README.md
└── LICENSE
```

## Configuration

Edit `config/services/project_bootstrap.yaml`:

```yaml
# Bot collaborators to invite
bot_collaborators:
  - username: m0nk111-post
    permission: push
  - username: m0nk111-qwen-agent
    permission: push

# Branch protection settings
repository:
  branch_protection:
    enabled: true
    required_reviews: 1
```

## Usage Examples

### Example 1: Create Private Repository

```python
result = coordinator.bootstrap_repository(
    name="secret-project",
    description="A private project",
    template="python",
    private=True,  # Private repository
    organization=None,  # User repo (or specify org name)
    enable_branch_protection=False  # Skip protection for quick setup
)
```

### Example 2: Organization Repository

```python
result = coordinator.bootstrap_repository(
    name="company-project",
    description="Company project",
    template="typescript",
    organization="my-company",  # Create in organization
    bot_collaborators=[
        {"username": "company-bot", "permission": "admin"}
    ]
)
```

### Example 3: Minimal Setup (No Bots, No Protection)

```python
result = coordinator.bootstrap_repository(
    name="simple-project",
    template="go",
    bot_collaborators=None,  # No bots
    enable_branch_protection=False  # No protection
)
```

## Testing

Run the comprehensive test suite:

```bash
cd /home/flip/agent-forge
PYTHONPATH=/home/flip/agent-forge python3 tests/test_bootstrap_agent.py
```

**Test Results:**
```
✅ PASS: List Templates
✅ PASS: Generate Structure
✅ PASS: Full Bootstrap (DRY RUN)

Total: 3/3 tests passed
```

## API Reference

### BootstrapCoordinator

#### `bootstrap_repository()`

Create and configure a complete repository.

**Parameters:**
- `name` (str): Repository name
- `description` (str): Repository description
- `template` (str): Project template ('python', 'typescript', 'go')
- `private` (bool): Private repository flag (default: False)
- `organization` (str): Organization name (None = user repo)
- `bot_collaborators` (list): List of bot configs with username and permission
- `enable_branch_protection` (bool): Enable branch protection (default: True)
- `required_reviews` (int): Number of required reviews (default: 1)

**Returns:**
```python
{
    'repository': {
        'full_name': 'owner/repo',
        'html_url': 'https://github.com/owner/repo',
        'clone_url': 'https://github.com/owner/repo.git',
        'default_branch': 'main',
        'owner': 'owner'
    },
    'team': True,  # Team setup success
    'files': 10,   # Number of files created
    'protection': True  # Branch protection enabled
}
```

### RepositoryCreator

#### `create_repository()`

Create a basic repository with configuration.

**Parameters:**
- `name` (str): Repository name
- `description` (str): Description
- `private` (bool): Private flag
- `organization` (str): Organization name
- `template` (str): Project template
- `enable_auto_init` (bool): Initialize with README

### TeamManager

#### `invite_collaborators()`

Invite multiple collaborators to a repository.

**Parameters:**
- `owner` (str): Repository owner
- `repo` (str): Repository name
- `collaborators` (list): List of dicts with 'username' and 'permission'

#### `auto_accept_invitations()`

Auto-accept pending invitations for bot accounts.

**Parameters:**
- `bot_usernames` (list): List of bot usernames (None = all bots)
- `max_retries` (int): Maximum retry attempts
- `retry_delay` (int): Delay between retries in seconds

### StructureGenerator

#### `generate_structure()`

Generate project structure from template.

**Parameters:**
- `template` (str): Template name
- `project_name` (str): Project name
- `description` (str): Description
- `owner` (str): Owner name

**Returns:**
```python
{
    'format': 'files',
    'data': {
        'src/main.py': '#!/usr/bin/env python3\n...',
        'tests/test_main.py': '"""Tests"""...',
        # ... more files
    },
    'file_count': 10,
    'template': 'python'
}
```

## Troubleshooting

### Issue: "Rate limit reached"

**Solution:** Wait a few minutes and retry. The system has built-in rate limiting.

### Issue: "Failed to accept invitation"

**Solution:** Check that bot tokens are correctly configured in `keys.json`:

```json
{
  "BOT_GITHUB_TOKEN": "ghp_bot_token_here"
}
```

### Issue: "Branch protection failed"

**Solution:** Branch protection requires:
- Repository must have at least one commit
- User must have admin rights
- Wait 10-15 seconds after repository creation before applying protection

### Issue: "No module named 'engine'"

**Solution:** Set PYTHONPATH:

```bash
export PYTHONPATH=/home/flip/agent-forge
python3 tests/test_bootstrap_agent.py
```

## Best Practices

1. **Use Dry Run First**: Test with `dry_run=True` before creating real repositories
2. **Check Bot Tokens**: Ensure all bot tokens are valid and have required permissions
3. **Wait for Invitations**: Allow 10-15 seconds for invitations to propagate before auto-accept
4. **Review Templates**: Check generated structure before pushing to repository
5. **Enable Protection Later**: For quick testing, disable branch protection initially
6. **Use Organizations**: For team projects, create in organization instead of user account
7. **Monitor Rate Limits**: GitHub API has rate limits (5000 requests/hour for authenticated users)

## Integration with Polling Service

The bootstrap agent can be integrated with the polling service for automated repository creation triggered by GitHub issues:

```python
# In polling service
if issue_has_label(issue, "bootstrap-repo"):
    coordinator.bootstrap_repository(
        name=extract_repo_name_from_issue(issue),
        template=extract_template_from_issue(issue),
        # ... other config from issue body
    )
```

## Next Steps

1. **Create m0nk111-reviewer account** and add to bot_collaborators
2. **Add REVIEWER_GITHUB_TOKEN** to keys.json
3. **Test with real repository** creation
4. **Integrate with polling service** for issue-triggered creation
5. **Extend templates** with more project types (React, Vue, Django, Flask, etc.)
6. **Add template marketplace** for community-contributed templates

## Support

For issues and questions:
- Check `docs/PROJECT_BOOTSTRAP_AGENT.md` for detailed design
- Review `tests/test_bootstrap_agent.py` for usage examples
- Check GitHub issues: https://github.com/m0nk111/agent-forge/issues
- Consult `CHANGELOG.md` for recent changes

## License

MIT License - See LICENSE file for details
