# Project Bootstrap Agent

**Status**: 🎯 Concept Design  
**Priority**: Medium  
**Complexity**: High  

## Overview

Automated agent that creates and configures complete GitHub repositories with all necessary setup, team invites, and project structure.

## Features

### 1. Repository Creation
- Create GitHub repository via API
- Initialize with README, LICENSE, .gitignore
- Setup branch protection rules
- Configure default branch settings
- Enable required features (Issues, Projects, Wiki, Discussions)

### 2. Team & Access Management
- Invite bot accounts as collaborators
- Auto-accept invitations via bot tokens
- Configure team permissions (read/write/admin)
- Setup CODEOWNERS file
- Configure protected branch reviewers

### 3. Project Structure Generation
```
project-name/
├── .github/
│   ├── workflows/          # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── copilot-instructions.md
├── docs/                   # Documentation
├── src/                    # Source code
├── tests/                  # Test files
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── .gitignore
├── README.md
├── LICENSE
├── CHANGELOG.md
└── CONTRIBUTING.md
```

### 4. Configuration Setup
- Generate appropriate .gitignore (based on language/framework)
- Setup CI/CD workflows (GitHub Actions)
- Configure linting/formatting
- Setup pre-commit hooks
- Add security scanning (Dependabot, CodeQL)

### 5. Documentation Generation
- Create comprehensive README.md
- Generate CONTRIBUTING.md guidelines
- Setup CHANGELOG.md
- Add LICENSE file (MIT, Apache, GPL, etc.)
- Create docs/ structure with templates

## Architecture

### Components

#### 1. Repository Creator (`repository_creator.py`)
```python
class RepositoryCreator:
    def create_repository(
        self,
        name: str,
        description: str,
        visibility: str = "private",
        organization: Optional[str] = None,
        template: Optional[str] = None
    ) -> Dict:
        """Create GitHub repository with initial setup."""
        pass
```

#### 2. Team Manager (`team_manager.py`)
```python
class TeamManager:
    def invite_collaborators(
        self,
        repo: str,
        collaborators: List[Dict[str, str]]
    ) -> List[str]:
        """Invite bot accounts and team members."""
        pass
    
    def accept_invitations(
        self,
        tokens: Dict[str, str]
    ) -> List[str]:
        """Auto-accept invitations for bot accounts."""
        pass
```

#### 3. Structure Generator (`structure_generator.py`)
```python
class StructureGenerator:
    def generate_structure(
        self,
        repo: str,
        template: str,
        language: str,
        framework: Optional[str] = None
    ) -> None:
        """Generate project directory structure and files."""
        pass
```

#### 4. Config Manager (`config_manager.py`)
```python
class ConfigManager:
    def setup_branch_protection(
        self,
        repo: str,
        branch: str = "main",
        rules: Dict = None
    ) -> None:
        """Configure branch protection rules."""
        pass
    
    def setup_workflows(
        self,
        repo: str,
        workflows: List[str]
    ) -> None:
        """Setup GitHub Actions workflows."""
        pass
```

## Usage Examples

### Example 1: Create Python Project
```python
bootstrap = ProjectBootstrapAgent(
    owner="m0nk111",
    admin_token=admin_token
)

project = await bootstrap.create_project(
    name="my-new-project",
    description="A cool new Python project",
    language="python",
    framework="fastapi",
    visibility="private",
    collaborators=[
        {"username": "m0nk111-post", "token": bot_token_1, "role": "write"},
        {"username": "m0nk111-qwen-agent", "token": bot_token_2, "role": "write"},
        {"username": "m0nk111-reviewer", "token": bot_token_3, "role": "write"}
    ],
    features={
        "ci_cd": True,
        "pre_commit": True,
        "dependabot": True,
        "codeql": True,
        "issue_templates": True,
        "pr_template": True,
        "codeowners": True
    }
)
```

### Example 2: Bootstrap from Template
```python
project = await bootstrap.bootstrap_from_template(
    name="agent-project-2",
    template="agent-forge",  # Use existing repo as template
    collaborators=bot_accounts,
    customize={
        "description": "Second agent project",
        "topics": ["ai", "agents", "automation"]
    }
)
```

## Configuration Format

### Project Config (`project_bootstrap.yaml`)
```yaml
# Project Bootstrap Configuration

defaults:
  visibility: "private"
  auto_init: true
  default_branch: "main"
  
  # Branch protection
  branch_protection:
    require_pull_request: true
    require_approvals: 1
    dismiss_stale_reviews: true
    require_code_owner_reviews: false
    require_status_checks: true
    
  # Collaborators (bot accounts)
  collaborators:
    - username: "m0nk111-post"
      role: "write"
      token_key: "BOT_GITHUB_TOKEN"
    - username: "m0nk111-qwen-agent"
      role: "write"
      token_key: "CODEAGENT_GITHUB_TOKEN"
    - username: "m0nk111-reviewer"
      role: "write"
      token_key: "REVIEWER_GITHUB_TOKEN"
  
  # Features to enable
  features:
    issues: true
    projects: true
    wiki: false
    discussions: false
    
  # Security features
  security:
    dependabot: true
    secret_scanning: true
    code_scanning: true  # CodeQL

# Project templates
templates:
  python-fastapi:
    language: "python"
    framework: "fastapi"
    structure:
      - "src/"
      - "tests/"
      - "docs/"
      - "scripts/"
      - "config/"
    files:
      - ".gitignore:python"
      - "requirements.txt"
      - "setup.py"
      - "pyproject.toml"
      - "README.md:python-project"
      - "LICENSE:MIT"
      - ".github/workflows/ci.yml:python-ci"
      
  typescript-node:
    language: "typescript"
    framework: "node"
    structure:
      - "src/"
      - "tests/"
      - "dist/"
      - "docs/"
    files:
      - ".gitignore:node"
      - "package.json"
      - "tsconfig.json"
      - "README.md:typescript-project"
      - "LICENSE:MIT"
      - ".github/workflows/ci.yml:node-ci"

# File templates
file_templates:
  readme_sections:
    - "Project Title"
    - "Description"
    - "Installation"
    - "Usage"
    - "Configuration"
    - "Contributing"
    - "License"
    
  workflows:
    python_ci:
      name: "Python CI"
      triggers: ["push", "pull_request"]
      jobs:
        - lint
        - test
        - build
```

## GitHub API Methods Needed

### Repository API
```python
# Create repository
POST /user/repos
POST /orgs/{org}/repos

# Update repository settings
PATCH /repos/{owner}/{repo}

# Branch protection
PUT /repos/{owner}/{repo}/branches/{branch}/protection

# Topics
PUT /repos/{owner}/{repo}/topics
```

### Collaborators API
```python
# Invite collaborator
PUT /repos/{owner}/{repo}/collaborators/{username}

# Accept invitation (as bot)
PATCH /user/repository_invitations/{invitation_id}

# List invitations
GET /user/repository_invitations
```

### Contents API
```python
# Create/update files
PUT /repos/{owner}/{repo}/contents/{path}

# Create multiple files (use Git Tree API)
POST /repos/{owner}/{repo}/git/trees
POST /repos/{owner}/{repo}/git/commits
```

## Workflow

### Phase 1: Repository Creation
1. Validate project name and settings
2. Create repository via GitHub API
3. Initialize with README (if auto_init=true)
4. Set repository description and topics
5. Enable features (issues, projects, etc.)

### Phase 2: Team Setup
1. Invite collaborators with appropriate roles
2. For each bot account:
   - Get their token from keys.json
   - Fetch pending invitations
   - Accept invitation for this repo
3. Wait for all acceptances
4. Verify all bots have access

### Phase 3: Structure Generation
1. Generate project structure based on template
2. Create initial files (README, LICENSE, etc.)
3. Generate .gitignore based on language
4. Create .github/ directory with templates
5. Commit all files via Git API (single commit)

### Phase 4: Configuration
1. Setup branch protection rules
2. Configure required status checks
3. Add CODEOWNERS file
4. Setup webhooks (if needed)
5. Enable security features (Dependabot, CodeQL)

### Phase 5: CI/CD Setup
1. Create workflow files in .github/workflows/
2. Configure secrets (if needed)
3. Test workflows by triggering manual run
4. Verify all checks pass

### Phase 6: Documentation
1. Generate comprehensive README
2. Create CONTRIBUTING.md
3. Add CHANGELOG.md
4. Setup docs/ structure
5. Add example files/templates

## Error Handling

### Common Issues
1. **Repository already exists**: Check first, offer to use existing
2. **Bot invitation fails**: Retry with exponential backoff
3. **Bot can't accept invite**: Manual intervention needed
4. **Permission denied**: Verify admin token has correct scopes
5. **API rate limit**: Implement proper rate limiting and retry

### Recovery Strategies
- **Rollback**: Delete repo if setup fails
- **Resume**: Save state, allow resume from last successful step
- **Manual mode**: Fall back to generating setup instructions for user

## Security Considerations

1. **Token Management**
   - Store tokens securely in keys.json
   - Never commit tokens to repo
   - Use minimal required scopes

2. **Repository Visibility**
   - Default to private
   - Confirm before making public
   - Audit who has access

3. **Branch Protection**
   - Require PR reviews by default
   - Prevent force pushes
   - Require status checks

4. **Security Scanning**
   - Enable Dependabot by default
   - Setup CodeQL for supported languages
   - Enable secret scanning

## Integration with Existing Systems

### Polling Service
- Monitor new repositories for initial setup
- Trigger bootstrap if needed
- Track setup status

### Issue Opener
- Create "Setup" issue with checklist
- Track setup progress
- Auto-close when complete

### Documentation
- Auto-update docs/ when new repo created
- Add to project inventory
- Update README with repo link

## Future Enhancements

1. **Template Marketplace**
   - Curated project templates
   - Community-contributed templates
   - Template versioning

2. **Interactive Setup**
   - CLI wizard for project creation
   - Web UI for configuration
   - Preview before creation

3. **Migration Support**
   - Import from other platforms (GitLab, Bitbucket)
   - Migrate existing repos to template
   - Bulk operations

4. **Analytics**
   - Track setup success rate
   - Measure time to first commit
   - Monitor feature usage

## Implementation Priority

### Phase 1 (MVP) - High Priority
- [ ] Repository creation API
- [ ] Basic team invitation
- [ ] Simple structure generation
- [ ] README/LICENSE creation

### Phase 2 - Medium Priority
- [ ] Branch protection setup
- [ ] Workflow generation
- [ ] Template system
- [ ] Auto-accept invitations

### Phase 3 - Low Priority
- [ ] Advanced templates
- [ ] Migration tools
- [ ] Analytics dashboard
- [ ] Web UI

## References

- [GitHub REST API - Repositories](https://docs.github.com/en/rest/repos)
- [GitHub REST API - Collaborators](https://docs.github.com/en/rest/collaborators)
- [GitHub Actions Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Branch Protection Rules](https://docs.github.com/en/rest/branches/branch-protection)
