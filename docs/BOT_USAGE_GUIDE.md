# Bot Operations Usage Guide

Guide for using the GitHub bot account across different Copilot agent sessions.

## Overview

The `m0nk111-bot` account provides administrative capabilities for GitHub operations:
- ✅ Create and manage issues
- ✅ Create and manage pull requests  
- ✅ Add comments and reviews
- ✅ Manage labels and milestones
- ❌ Cannot push code (security separation)

**Security Model:**
- Bot account: Administrative operations only (Triage role)
- Agent accounts: Code commits and pushes (Write role)

## Prerequisites

All agents must have access to the bot token via environment variables:

```bash
# Source the agent-forge environment (already in ~/.bashrc)
source ~/.agent-forge.env

# Verify token is loaded
echo $BOT_GITHUB_TOKEN  # Should show: ghp_...
```

**Credentials:**
- Token: Available in `~/.agent-forge.env` as `BOT_GITHUB_TOKEN`
- Username: `m0nk111-bot`
- Email: `aicodingtime+bot@gmail.com`
- Expires: ~90 days from October 5, 2025

**Security:** Never commit tokens to git. Use environment variables only.

## Method 1: Python API (Recommended)

Use the `BotOperations` class for type-safe operations:

### Setup

```python
import sys
sys.path.insert(0, '/home/flip/agent-forge/agents')
from bot_operations import BotOperations

bot = BotOperations()  # Automatically loads from environment
```

### Common Operations

#### Create Issue

```python
issue = bot.create_issue(
    repo='agent-forge',
    title='Bug: Something is broken',
    body='Description of the problem...',
    labels=['bug', 'priority-high'],
    assignees=['m0nk111-qwen-agent']
)
print(f"Created issue #{issue['number']}")
```

#### Add Comment

```python
bot.add_comment(
    repo='agent-forge',
    issue_number=5,
    comment='✅ Fixed in commit abc123'
)
```

#### Close Issue

```python
bot.update_issue(
    repo='agent-forge',
    issue_number=5,
    state='closed'
)
```

#### List Issues

```python
issues = bot.list_issues(
    repo='agent-forge',
    state='open',  # or 'closed', 'all'
    labels=['bug']
)

for issue in issues:
    print(f"#{issue['number']}: {issue['title']}")
```

#### Create Pull Request

```python
pr = bot.create_pull_request(
    repo='agent-forge',
    title='Fix: Resolve bug #5',
    head='feature-branch',
    base='main',
    body='This PR fixes issue #5 by...'
)
```

### Complete Example

```python
#!/usr/bin/env python3
"""Example: Create issue and track resolution"""

import sys
sys.path.insert(0, '/home/flip/agent-forge/agents')
from bot_operations import BotOperations

def main():
    bot = BotOperations()
    
    # Create issue
    issue = bot.create_issue(
        repo='agent-forge',
        title='Feature: Add new capability',
        body="""## Problem
        We need X functionality.
        
        ## Solution
        Implement Y approach.
        
        ## Acceptance Criteria
        - [ ] Feature works
        - [ ] Tests pass
        """,
        labels=['enhancement', 'priority-medium']
    )
    
    issue_number = issue['number']
    print(f"✅ Created issue #{issue_number}")
    
    # Work on the issue...
    # (make changes, commit, etc.)
    
    # Add progress comment
    bot.add_comment(
        repo='agent-forge',
        issue_number=issue_number,
        comment='🔄 Working on implementation...'
    )
    
    # Complete and close
    bot.add_comment(
        repo='agent-forge',
        issue_number=issue_number,
        comment='✅ Implementation complete! See commit xyz123'
    )
    
    bot.update_issue(
        repo='agent-forge',
        issue_number=issue_number,
        state='closed'
    )
    
    print(f"✅ Issue #{issue_number} resolved")

if __name__ == '__main__':
    main()
```

## Method 2: Direct API Calls

For non-Python agents or one-off operations:

### Create Issue

```bash
curl -X POST \
  -H "Authorization: Bearer ${BOT_GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/m0nk111/agent-forge/issues \
  -d '{
    "title": "Issue title",
    "body": "Issue description",
    "labels": ["bug"]
  }'
```

### Add Comment

```bash
curl -X POST \
  -H "Authorization: Bearer ${BOT_GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/m0nk111/agent-forge/issues/5/comments \
  -d '{"body": "Comment text"}'
```

### Close Issue

```bash
curl -X PATCH \
  -H "Authorization: Bearer ${BOT_GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/m0nk111/agent-forge/issues/5 \
  -d '{"state": "closed"}'
```

### List Issues

```bash
curl -H "Authorization: Bearer ${BOT_GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/m0nk111/agent-forge/issues?state=open"
```

## Method 3: Via Agent-Forge Framework

If you're building an autonomous agent using agent-forge:

```python
# In your agent config YAML
project:
  name: "My Project"
  repo: "my-repo"
  owner: "m0nk111"
  
# In your agent code
from agents.bot_operations import BotOperations

class MyAgent:
    def __init__(self, config):
        self.bot = BotOperations()
        self.repo = config['project']['repo']
    
    def report_progress(self, phase_number, status):
        """Report progress to GitHub issue"""
        self.bot.add_comment(
            repo=self.repo,
            issue_number=self.project_issue_number,
            comment=f"📊 Phase {phase_number}: {status}"
        )
```

## Cross-Agent Coordination

Multiple agents can coordinate via issues:

### Pattern 1: Issue Assignment

```python
# Agent A creates issue
issue = bot.create_issue(
    repo='agent-forge',
    title='Task: Implement feature X',
    body='Details...',
    assignees=['m0nk111-qwen-agent']  # Assign to specific agent
)

# Agent B (Qwen) receives notification and works on it
# Agent B updates progress
bot.add_comment(
    repo='agent-forge',
    issue_number=issue['number'],
    comment='🔄 Agent B: Started implementation'
)
```

### Pattern 2: Labels for State

```python
# Create with 'in-progress' label
issue = bot.create_issue(
    repo='agent-forge',
    title='Task',
    body='Details',
    labels=['in-progress', 'agent-qwen']
)

# Other agents can query
open_tasks = bot.list_issues(
    repo='agent-forge',
    state='open',
    labels=['in-progress']
)
```

### Pattern 3: Comment Protocol

```python
# Agent A requests help
bot.add_comment(
    repo='agent-forge',
    issue_number=5,
    comment='@m0nk111-bot Please review implementation'
)

# Agent B responds
bot.add_comment(
    repo='agent-forge',
    issue_number=5,
    comment='✅ Review complete. Approved.'
)
```

## Best Practices

### 1. Use Structured Comments

```python
comment = """
## Implementation Summary

**Changes:**
- Added feature X
- Fixed bug Y

**Test Results:**
✅ All tests passing
✅ No regressions

**Commit:** abc123
"""
bot.add_comment(repo='agent-forge', issue_number=5, comment=comment)
```

### 2. Emoji Conventions

Use consistent emoji for status:
- 🔄 In progress
- ✅ Complete/Success
- ❌ Failed/Error
- ⚠️ Warning
- 📊 Status update
- 🐛 Bug report
- 💡 Suggestion

### 3. Link Commits

Always reference commits in issue comments:

```python
comment = f"""
✅ Implemented in commit: https://github.com/m0nk111/agent-forge/commit/{commit_sha}

Changes:
- Feature X added
- Tests updated
"""
```

### 4. Close Issues Properly

Always add completion comment before closing:

```python
# Add completion summary
bot.add_comment(
    repo='agent-forge',
    issue_number=5,
    comment='✅ Issue resolved. All acceptance criteria met.'
)

# Then close
bot.update_issue(repo='agent-forge', issue_number=5, state='closed')
```

## Security Notes

- **Token Expiration:** Classic tokens expire in ~90 days (set reminder!)
- **Permissions:** Bot has Triage role (cannot push code)
- **Token Storage:** Keep tokens in `~/.agent-forge.env` with `chmod 600`
- **Never commit tokens:** Tokens are in `.gitignore`

## Troubleshooting

### "BOT_GITHUB_TOKEN not set"

```bash
# Check environment
echo $BOT_GITHUB_TOKEN

# If empty, source the env file
source ~/.agent-forge.env

# Verify it's in .bashrc
grep agent-forge.env ~/.bashrc
```

### "401 Unauthorized"

- Token expired (regenerate in GitHub settings)
- Token not in environment (run `source ~/.agent-forge.env`)

### "403 Forbidden"

- Bot lacks permissions for the operation
- Repository not accessible to bot account
- Check bot is added as collaborator

### "404 Not Found"

- Repository name incorrect
- Issue/PR number doesn't exist
- Bot doesn't have access to private repo

## API Reference

Full API documentation: `/home/flip/agent-forge/engine/operations/bot_operations.py`

Key methods:
- `create_issue(repo, title, body, labels=None, assignees=None)`
- `update_issue(repo, issue_number, title=None, body=None, state=None)`
- `add_comment(repo, issue_number, comment)`
- `list_issues(repo, state='open', labels=None, assignee=None)`
- `get_issue(repo, issue_number)`
- `create_pull_request(repo, title, head, base, body)`
- `update_pull_request(repo, pr_number, title=None, body=None, state=None)`
- `add_label(repo, issue_number, labels)`
- `remove_label(repo, issue_number, label)`

## Examples Repository

See practical examples in:
- `/home/flip/agent-forge/engine/operations/bot_operations.py` (implementation)
- Recent conversation history (Issues #1-3 workflow)

## Questions?

Check the code or ask the main agent (m0nk111) for clarification.
