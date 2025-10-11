# GitHub Token Permissions - Agent Forge

## Required Token Scopes per Account

### 1. m0nk111-reviewer (REVIEWER_GITHUB_TOKEN)

**Primary Functions:**
- Read pull requests
- Submit PR reviews (APPROVE, REQUEST_CHANGES, COMMENT)
- Add comments to PRs
- Read repository content

**Required Scopes:**

#### ✅ **repo** (Full control of private repositories)
This is the MAIN scope needed for PR reviews.

Includes:
- ☑️ **repo:status** - Access commit status
- ☑️ **repo_deployment** - Access deployment status
- ☑️ **public_repo** - Access public repositories
- ☑️ **repo:invite** - Access repository invitations

**Why needed:**
- Submit PR reviews (APPROVE/REQUEST_CHANGES)
- Read PR content and files
- Add review comments
- Access private repositories (if needed)

#### ✅ **write:discussion** (Read and write team discussions)
**Why needed:**
- Post comments on PRs
- Participate in code discussions

#### Optional but Recommended:

#### ⚪ **read:org** (Read org and team membership)
**Why useful:**
- Verify team membership
- Check organization access
- Not strictly required for basic reviewing

#### ❌ **NOT NEEDED:**
- ❌ admin:org - No org management
- ❌ delete_repo - No repo deletion
- ❌ admin:repo_hook - No webhook management
- ❌ admin:public_key - No SSH key management
- ❌ admin:gpg_key - No GPG key management
- ❌ workflow - No GitHub Actions changes (unless reviewing workflow files)

### Minimum Token Configuration

**For m0nk111-reviewer:**
```
Required scopes:
☑️ repo (full control)
☑️ write:discussion

Optional:
⚪ read:org (if working with organizations)
```

### 2. m0nk111-qwen-agent (CODEAGENT_GITHUB_TOKEN)

**Primary Functions:**
- Create/push branches
- Commit code changes
- Create pull requests
- Push to repositories

**Required Scopes:**

#### ✅ **repo** (Full control)
All sub-scopes needed for code operations.

#### ✅ **workflow** (Update GitHub Actions)
**Why needed:**
- Create/modify .github/workflows files
- Required if code includes workflow changes

**For Code Agent:**
```
Required scopes:
☑️ repo (full control)
☑️ workflow
☑️ write:discussion

Optional:
⚪ read:org
```

### 3. m0nk111-post (BOT_GITHUB_TOKEN)

**Primary Functions:**
- Monitor issues
- Create issues/comments
- Create repositories (Bootstrap Agent)
- Invite collaborators
- Manage repository settings

**Required Scopes:**

#### ✅ **repo** (Full control)
Needed for repository management.

#### ✅ **admin:org** (if creating org repositories)
**Why needed:**
- Create repositories in organizations
- Manage team access
- Invite collaborators

#### ✅ **workflow** (if managing workflows)

**For Bot Agent:**
```
Required scopes:
☑️ repo (full control)
☑️ admin:org (if using organizations)
☑️ workflow
☑️ write:discussion

Optional:
⚪ read:org
```

## Token Creation Steps

### Creating m0nk111-reviewer Token

1. **Login to GitHub** as m0nk111-reviewer

2. **Navigate to Settings**
   ```
   https://github.com/settings/tokens
   ```

3. **Click "Generate new token (classic)"**

4. **Configure Token:**
   ```
   Note: Agent Forge PR Reviewer Bot
   Expiration: No expiration (or 1 year)
   
   Select scopes:
   ☑️ repo
      ☑️ repo:status
      ☑️ repo_deployment  
      ☑️ public_repo
      ☑️ repo:invite
   ☑️ write:discussion
      ☑️ read:discussion
   ⚪ read:org (optional)
      ⚪ read:org
   ```

5. **Generate token**
   - Copy token immediately (shown only once!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

6. **Save to keys.json:**
   ```json
   {
     "OPENAI_API_KEY": "sk-...",
     "BOT_GITHUB_TOKEN": "ghp_...",
     "REVIEWER_GITHUB_TOKEN": "ghp_NEW_TOKEN_HERE"
   }
   ```

## Security Best Practices

### Token Storage
- ✅ Store in `keys.json` (in .gitignore)
- ✅ Never commit tokens to git
- ✅ Use environment variables in production
- ✅ Rotate tokens periodically (every 6-12 months)

### Token Permissions
- ✅ Use minimum required scopes
- ✅ Create separate tokens per function
- ✅ Don't reuse tokens across services
- ❌ Don't use personal tokens for bots

### Token Security
- ✅ Set expiration dates (1 year recommended)
- ✅ Monitor token usage in GitHub settings
- ✅ Revoke compromised tokens immediately
- ✅ Use fine-grained tokens for new projects (beta)

## Verifying Token Scopes

### Using GitHub API

```bash
# Check token scopes
TOKEN="ghp_your_token_here"
curl -H "Authorization: Bearer $TOKEN" \
     -I https://api.github.com/user \
     2>&1 | grep -i "x-oauth-scopes"
```

Output will show:
```
x-oauth-scopes: repo, write:discussion
```

### Using Python

```python
import requests

token = "ghp_your_token_here"
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json'
}

response = requests.get('https://api.github.com/user', headers=headers)
scopes = response.headers.get('X-OAuth-Scopes', '')
print(f"Token scopes: {scopes}")
```

## Testing Reviewer Token

After creating the token, test it:

```python
import requests

token = "ghp_your_reviewer_token"
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json'
}

# Test 1: Check user identity
response = requests.get('https://api.github.com/user', headers=headers)
print(f"Username: {response.json()['login']}")  # Should be m0nk111-reviewer

# Test 2: Check repo access
response = requests.get('https://api.github.com/repos/m0nk111/agent-forge', 
                       headers=headers)
print(f"Repo access: {response.status_code == 200}")  # Should be True

# Test 3: Check PR access
response = requests.get('https://api.github.com/repos/m0nk111/agent-forge/pulls',
                       headers=headers)
print(f"PR access: {response.status_code == 200}")  # Should be True
```

## Common Issues

### "Resource not accessible by integration"
**Cause:** Token lacks required scope
**Solution:** Regenerate token with `repo` scope

### "Bad credentials"
**Cause:** Token expired or invalid
**Solution:** Check token in keys.json, regenerate if needed

### "Not Found" on private repos
**Cause:** Token lacks repo scope or account not invited
**Solution:** 
1. Check token has `repo` scope
2. Invite reviewer account to repository

### "Cannot approve your own pull request"
**Cause:** Token belongs to PR author
**Solution:** Use different account token (this is why we need separate reviewer)

## Token Lifecycle

### Creation
1. Create GitHub account
2. Generate token with required scopes
3. Save to keys.json
4. Update configuration files
5. Test token functionality

### Usage
1. Token loaded from keys.json
2. Used in GitHub API calls
3. Rate limits tracked (5000 req/hour)
4. Operations logged

### Rotation
1. Generate new token
2. Update keys.json
3. Restart services
4. Revoke old token
5. Verify new token works

### Revocation
1. Go to https://github.com/settings/tokens
2. Find token by name
3. Click "Delete"
4. Token immediately invalid

## Summary

**For m0nk111-reviewer (CRITICAL):**
```
Minimum scopes:
✅ repo (full control) - REQUIRED for PR reviews
✅ write:discussion - REQUIRED for comments

Optional:
⚪ read:org - Useful but not required
```

**That's it!** Just these 2 scopes are enough for PR reviewing. 🎯

The `repo` scope is the key one - it gives access to:
- Read pull requests
- Submit reviews (APPROVE/REQUEST_CHANGES)
- Add comments
- Access repository content

**Time to create:** 5 minutes
**Complexity:** Simple
**Risk:** Low (limited permissions)

Ready to create the token? I can provide a test script to verify it works! 🚀
