# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated CI/CD processes.

## Available Workflows

### 🤖 Automated PR Review (`pr-review.yml`)

Automatically reviews pull requests using AI-powered code analysis with the following features:

**Triggers:**
- Automatically on PRs from bot accounts: `m0nk111-post`, `m0nk111-coder1`, `m0nk111-coder2`, `m0nk111-qwen-agent`
- Manual trigger via workflow_dispatch for any PR

**Features:**
- 🤖 **LLM-powered review**: Uses Ollama (qwen2.5-coder:7b) for deep code analysis
- 📊 **Hybrid analysis**: Combines static checks with AI insights
- 🏷️ **Auto-labeling**: Adds labels based on review results (approved, changes-requested, etc.)
- 👥 **Reviewer assignment**: Assigns admin as reviewer
- 🔀 **Intelligent merge**: Auto-merges based on review results
- 📝 **GitHub PR Reviews**: Posts reviews using official GitHub PR Review API

**Merge Strategies:**
- `auto-merge-if-approved`: Merges PRs with 0 issues (default for auto-trigger)
- `merge-with-suggestions`: Merges PRs with suggestions/warnings (manual trigger option)

**Usage:**

1. **Automatic (for bot PRs):**
   - Simply create a PR from a bot account
   - Workflow runs automatically
   - PR reviewed and merged if approved

2. **Manual trigger:**
   ```bash
   # Via GitHub UI: Actions > Automated PR Review > Run workflow
   # Select PR number and merge strategy
   ```

3. **CLI trigger:**
   ```bash
   gh workflow run pr-review.yml \
     -f pr_number=95 \
     -f merge_with_suggestions=true
   ```

**Requirements:**
- Python 3.11+
- Ollama (installed during workflow)
- GitHub token with PR write permissions
- `requirements.txt` in repository root

**Review Decision Logic:**
- **AUTO_MERGE**: 0 issues → safe to auto-merge
- **MERGE_WITH_CONSIDERATION**: Only suggestions/warnings → merge with flag
- **MANUAL_REVIEW**: Critical issues or 3+ warnings → requires human review
- **DO_NOT_MERGE**: Changes requested → blocked

**Safety Checks:**
- Draft PR detection (blocks merge)
- Merge conflict detection (blocks merge)
- Failing/pending checks (blocks merge)
- Branch protection rules (blocks merge)

**Integration:**
Works alongside the polling service (`engine/runners/polling_service.py`) which provides:
- Continuous PR monitoring (every 10 minutes)
- Same review and merge logic
- Multi-repository support

**Configuration:**
Workflow uses hardcoded settings optimized for this repository. For custom configuration, use polling service with `config/services/polling.yaml`.

## Adding New Workflows

When adding new workflows:
1. Create `.yml` file in this directory
2. Follow naming convention: `<workflow-name>.yml`
3. Add documentation section to this README
4. Test with manual trigger before enabling auto-trigger
5. Update `CHANGELOG.md` with workflow addition

## Troubleshooting

**Workflow not running:**
- Check PR author is in allowed list
- Verify repository permissions
- Check workflow logs in Actions tab

**Ollama installation fails:**
- Workflow installs Ollama automatically
- Check runner has internet access
- Verify model pull succeeds in workflow logs

**Merge fails:**
- Check for merge conflicts
- Verify branch protection rules allow bot merges
- Review safety check logs

**Review not posting:**
- Verify `GITHUB_TOKEN` has correct permissions
- Check API rate limits
- Review error logs in workflow output

## Related Documentation

- Main README: `/README.md`
- Polling Service: `/engine/runners/polling_service.py`
- PR Review Agent: `/engine/operations/pr_review_agent.py`
- Configuration: `/config/services/polling.yaml`
- Architecture: `/ARCHITECTURE.md`
