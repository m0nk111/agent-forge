# Anti-Spam Protection & Rate Limiting

## Overview

Agent-Forge implements comprehensive anti-spam protection to prevent abuse of GitHub's API and protect against account suspension.

## Features

### 1. Rate Limiting

**Per-Operation Limits:**
- Comments: 3/min, 30/hour, 200/day
- Issue creation: 10/hour
- PR creation: 5/hour
- Updates: 5/min, 50/hour

**GitHub API Limits:**
- Tracks API calls remaining (5000/hour limit)
- Stops operations when < 100 calls remaining
- Respects reset times

### 2. Cooldown Periods

**Enforced Delays:**
- Comments: 20 seconds between operations
- Issue creation: 60 seconds between operations
- PR creation: 120 seconds between operations

### 3. Duplicate Detection

**Prevents Repeated Actions:**
- Tracks content hashes for 1 hour
- Blocks duplicate operations (max 2 identical within window)
- Prevents accidental comment spam

### 4. Burst Protection

**Prevents Rapid-Fire Operations:**
- Max 10 operations per minute across all types
- Detects and blocks suspicious activity patterns
- Automatic cooldown on burst detection

## Implementation

### Rate Limiter

Located: `engine/core/rate_limiter.py`

```python
from engine.core.rate_limiter import get_rate_limiter, OperationType

# Get global rate limiter
limiter = get_rate_limiter()

# Check if operation is allowed
allowed, reason = limiter.check_rate_limit(
    OperationType.ISSUE_COMMENT,
    target="owner/repo#123",
    content="Comment text"
)

if not allowed:
    logger.warning(f"Rate limit blocked: {reason}")
    return

# Record operation after completion
limiter.record_operation(
    OperationType.ISSUE_COMMENT,
    target="owner/repo#123",
    content="Comment text",
    success=True
)
```

### GitHub API Helper

Located: `engine/operations/github_api_helper.py`

Rate limiting is automatically integrated:

```python
helper = GitHubAPIHelper(token=token)

# Automatically rate limited
helper.create_issue_comment(
    owner="your-org",
    repo="agent-forge",
    issue_number=80,
    body="Test comment"
)
```

## Configuration

Default configuration in `RateLimitConfig`:

```python
@dataclass
class RateLimitConfig:
    # GitHub API limits
    github_api_hourly_limit: int = 5000
    github_api_safety_threshold: int = 4500
    
    # Comment limits
    comments_per_minute: int = 3
    comments_per_hour: int = 30
    comments_per_day: int = 200
    
    # Issue/PR creation limits
    issues_per_hour: int = 10
    prs_per_hour: int = 5
    
    # Cooldown periods (seconds)
    comment_cooldown: int = 20
    issue_cooldown: int = 60
    pr_cooldown: int = 120
    
    # Duplicate detection
    duplicate_detection_window: int = 3600  # 1 hour
    max_duplicate_operations: int = 2
    
    # Burst detection
    burst_window: int = 60  # 1 minute
    max_burst_operations: int = 10
```

## Monitoring

### Get Statistics

```python
limiter = get_rate_limiter()
stats = limiter.get_stats()

print(stats)
# {
#   "operations_last_minute": 5,
#   "operations_last_hour": 42,
#   "operations_last_day": 156,
#   "by_type": {
#     "issue_comment": 20,
#     "api_read": 22,
#     ...
#   },
#   "github_api_remaining": 4850,
#   "api_reset_time": "2025-10-08T14:30:00"
# }
```

### Log Output

Rate limiter logs all blocks:

```
⚠️ Rate limit blocked: Comment rate limit: 3/min exceeded
⚠️ Rate limit blocked: Cooldown active. Wait 15s before next issue_comment
⚠️ Rate limit blocked: Duplicate operation detected (same content within 1 hour)
⚠️ Rate limit blocked: Burst detected. Too many operations in short time
```

## Token Security

### Best Practices

1. **Never hardcode tokens**
   - Use `secrets/agents/{agent-id}.token` files
   - Load via environment variables
   - Tokens in 600 permissions files only

2. **Gitignore patterns**
   ```
   secrets/
   *.token
   *github.env*
   .config/gh/
   ghp_*
   ```

3. **Token Loading**
   ```python
   # Load from secrets file
   with open(f'/opt/agent-forge/secrets/agents/{agent_id}.token') as f:
       token = f.read().strip()
   
   # Or from environment
   token = os.getenv('GITHUB_TOKEN')
   ```

### Removed Files

Following files were removed in security cleanup:
- `/opt/agent-forge/config/github.env` (contained hardcoded tokens)
- `/opt/agent-forge/config/.config/gh/` (gh CLI config with tokens)
- `/home/agent-forge/.config/gh/` (gh CLI config with tokens)

## Error Handling

### Rate Limit Exceeded

When rate limit is hit:

```python
try:
    helper.create_issue_comment(...)
except RuntimeError as e:
    if "Rate limit" in str(e):
        logger.warning(f"Rate limited: {e}")
        # Wait for cooldown or skip operation
```

### Graceful Degradation

Operations fail safely:
- Read operations return empty lists
- Write operations raise exceptions
- System continues functioning

## Testing

### Manual Testing

```python
from engine.core.rate_limiter import RateLimiter, RateLimitConfig, OperationType

# Create limiter with strict limits
config = RateLimitConfig(
    comments_per_minute=1,
    comment_cooldown=10
)
limiter = RateLimiter(config)

# Test rate limiting
for i in range(5):
    allowed, reason = limiter.check_rate_limit(
        OperationType.ISSUE_COMMENT,
        target="test",
        content=f"Comment {i}"
    )
    print(f"Attempt {i}: {'✅' if allowed else f'❌ {reason}'}")
    
    if allowed:
        limiter.record_operation(
            OperationType.ISSUE_COMMENT,
            target="test",
            content=f"Comment {i}"
        )
```

## Future Enhancements

- [ ] Per-repository rate limits
- [ ] Configurable limits via YAML
- [ ] Rate limit dashboard widget
- [ ] Automatic backoff strategies
- [ ] Whitelist for trusted operations
- [ ] Alert on suspicious patterns

## References

- [GitHub API Rate Limits](https://docs.github.com/en/rest/overview/rate-limits-for-the-rest-api)
- [GitHub Abuse Prevention](https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-rate-limits)
