# Agent-Forge Bugs Tracking

**Last Updated**: 2025-10-05 19:05 UTC

## 🐛 Active Bugs

### Bug #1: GitHub CLI Incompatible with Systemd Services [CRITICAL] ✅ FIXED
- **Status**: ✅ **FIXED** (October 5, 2025 19:43 UTC)
- **Severity**: CRITICAL (Was a show stopper)
- **Impact**: Entire autonomous development system was non-functional
- **Error**: `failed to read configuration: open /home/agent-forge/.config/gh/config.yml: permission denied`
- **Location**: All `gh` CLI subprocess calls in `agents/polling_service.py`
- **Root Cause**: gh CLI has design flaw - ALWAYS requires config files even with GH_TOKEN
- **Time Spent**: 2+ hours debugging + 45 minutes implementing fix
- **Resolution Date**: 2025-10-05 19:43 UTC

#### Fix Implementation
**Solution**: Complete migration from gh CLI to GitHub REST API

**Changes Made**:
1. **Replaced subprocess with requests library**
   - Removed all `subprocess.run(["gh", ...])` calls
   - Direct HTTP requests to `api.github.com`

2. **Added GitHubAPI Helper Class** (`agents/polling_service.py` lines 67-143)
   - Session management with persistent headers
   - Bearer token authentication: `Authorization: Bearer {token}`
   - Timeout handling (30s per request)
   - Comprehensive error handling (Timeout, HTTPError, generic Exception)

3. **Implemented Retry Logic**
   - 3 attempts per operation (configurable)
   - 2-second delays between retries
   - Specific handling for timeout, HTTP, and authentication errors
   - Early exit on authentication failures (no retry)

4. **Updated Three Core Methods**:
   - `check_assigned_issues()`: GET `/repos/{owner}/{repo}/issues` with query params
   - `is_issue_claimed()`: GET `/repos/{owner}/{repo}/issues/{num}/comments`
   - `claim_issue()`: POST `/repos/{owner}/{repo}/issues/{num}/comments`

5. **Service Manager Update** (`agents/service_manager.py` line 125)
   - Removed `enable_monitoring` parameter from PollingService initialization
   - Simplified configuration

6. **Systemd Configuration Fix** (`/etc/systemd/system/agent-forge.service`)
   - Added: `EnvironmentFile=/opt/agent-forge/config/github.env`
   - Ensures `GITHUB_TOKEN` and `GH_TOKEN` are available to service

#### Verification Results (October 5, 2025 19:43 UTC)
```bash
Oct 05 19:43:37: agents.polling_service: INFO - Found 8 assigned issues in m0nk111/agent-forge
Oct 05 19:43:37: agents.polling_service: INFO - Found 0 assigned issues in m0nk111/stepperheightcontrol
Oct 05 19:43:40: __main__: INFO - === All services started successfully ===
Oct 05 19:43:40: __main__: INFO - Services: ['polling', 'monitoring', 'web_ui', 'qwen_agent']
Oct 05 19:44:10: Health check: {'polling': True, 'monitoring': True, 'web_ui': True, 'qwen_agent': True}
```

**Success Metrics**:
- ✅ **Zero** permission denied errors
- ✅ Polling service successfully queries GitHub REST API
- ✅ All 4 services healthy and operational
- ✅ 8 assigned issues detected in first polling cycle
- ✅ System fully operational and autonomous

**Git Commit**: `7d638d7` - "Fix Bug #1: Replace gh CLI with GitHub REST API in polling service"  
**Related GitHub Issue**: [#39 - URGENT: Replace gh CLI with GitHub REST API](https://github.com/m0nk111/agent-forge/issues/39)

---

### Bug #2: Agent Metrics Show 0 Values
- **Status**: ⏳ IN PROGRESS
- **Severity**: MEDIUM
- **Impact**: Dashboard and CLI show 0 for CPU, memory, API calls
- **Root Cause**: Metrics only update after polling cycle completes
- **Location**: `agents/polling_service.py:update_metrics()`
- **Fix Applied**:
  - Added psutil integration
  - Added `update_metrics()` method
  - Added API call counter
  - Installed psutil 7.1.0
- **Verification Pending**: Wait for polling cycle completion
- **Date Started**: 2025-10-05 18:48 UTC

### Bug #3: HTML Parser in MCP Client is Crude
- **Status**: 📝 DOCUMENTED
- **Severity**: LOW
- **Impact**: Web documentation fetching may have formatting issues
- **Location**: `agents/mcp_client.py:175`
- **Note**: Contains TODO comment for proper HTML parser
- **Current**: Uses regex `re.sub(r'<[^>]+>', '', content)`
- **Recommended Fix**: Use BeautifulSoup or html.parser
- **Priority**: Low (functional but not optimal)

## ✅ Fixed Bugs

### Bug #1: GitHub CLI Not Installed
- **Fixed**: 2025-10-05 19:00 UTC
- **Solution**: Installed and authenticated gh CLI

## 🔍 Potential Issues to Investigate

### Issue #1: No Error Handling for Subprocess Failures
- **Location**: `agents/polling_service.py:check_assigned_issues()`
- **Risk**: subprocess.run() failures logged but not re-raised
- **Impact**: Silent failures possible
- **Severity**: MEDIUM
- **Suggested Fix**: Add proper exception handling and retry logic

### Issue #2: Missing File Validation in Issue Handler
- **Location**: `agents/issue_handler.py:_validate_changes()`
- **Risk**: Only checks syntax, not file existence
- **Impact**: Could validate non-existent files
- **Severity**: LOW
- **Suggested Fix**: Add file existence check before syntax validation

### Issue #3: No Rate Limiting on Monitor WebSocket
- **Location**: `agents/websocket_handler.py`
- **Risk**: Clients could spam WebSocket connections
- **Impact**: Potential DoS
- **Severity**: LOW
- **Suggested Fix**: Add connection rate limiting

### Issue #4: Hardcoded Paths in Tests
- **Location**: Various test files
- **Risk**: Tests may fail on different systems
- **Impact**: CI/CD brittleness
- **Severity**: LOW
- **Suggested Fix**: Use pathlib and temporary directories

## 📊 Bug Statistics

- **Total Bugs Tracked**: 3
- **Fixed**: 1
- **In Progress**: 1
- **Documented**: 1
- **Potential Issues**: 4

## 🔄 Testing Status

### Automated Tests
- **Unit Tests**: Not yet implemented
- **Integration Tests**: Not yet implemented
- **E2E Tests**: Manual testing only

### Manual Testing Required
1. ✅ Dashboard accessibility (PASSED)
2. ✅ CLI monitoring tool (PASSED)
3. ⏳ Polling service with gh CLI (PENDING)
4. ⏳ Agent metrics collection (PENDING)
5. ❌ Grid/list toggle (NOT TESTED)

## 📝 Notes

- Service runs stable with 4 components (polling, monitoring, web_ui, qwen_agent)
- All dependencies installed and configured
- Next polling cycle at ~19:03 UTC (300s interval)
- Need to verify gh CLI integration works correctly

## 🎯 Next Actions

1. **Immediate** (next 5 minutes):
   - Monitor service logs for gh CLI success/failure
   - Verify metrics update after polling cycle

2. **Short-term** (today):
   - Test grid/list toggle in browser
   - Add error handling to subprocess calls
   - Write unit tests for critical paths

3. **Medium-term** (this week):
   - Implement proper HTML parser for MCP client
   - Add WebSocket rate limiting
   - Create comprehensive test suite

4. **Long-term** (next sprint):
   - CI/CD pipeline with automated tests
   - Performance profiling and optimization
   - Security audit
