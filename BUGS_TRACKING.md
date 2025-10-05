# Agent-Forge Bugs Tracking

**Last Updated**: 2025-10-05 19:05 UTC

## 🐛 Active Bugs

### Bug #1: GitHub CLI Not Installed [FIXED]
- **Status**: ✅ FIXED
- **Severity**: HIGH
- **Impact**: Polling service could not query GitHub API
- **Error**: `[Errno 2] No such file or directory: 'gh'`
- **Location**: `agents/polling_service.py:240, 323, 373`
- **Fix Applied**: 
  - Installed `gh` CLI: `sudo apt install -y gh`
  - Authenticated with bot token: `gh auth login --with-token`
  - Service restarted
- **Verification Pending**: Wait for next polling cycle (300s interval)
- **Date Fixed**: 2025-10-05 19:00 UTC

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
