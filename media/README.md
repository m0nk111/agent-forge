# Agent-Forge Media Assets

This directory contains visual documentation, screenshots, and video assets for the Agent-Forge project.

---

## Contents

### Videos

- **agent-forge-gource-latest.mp4** - Gource visualization of repository history
- **agent-forge-gource-preview.gif** - Preview GIF of repository activity

### Screenshots

#### E2E Testing (October 12, 2025)

**Note**: These screenshots were captured using Playwright MCP browser automation and are currently stored in the Playwright temporary output directory. See test report for details.

- **e2e-test-dashboard-agents.png** - Dashboard showing sorted agents (7 active, 9 inactive)
  - Shows successful implementation of agent sorting and active/inactive grouping
  - Demonstrates WebSocket connectivity (Connected ✓)
  - All 4 infrastructure services visible (Monitoring API, Web Dashboard, Agent Runtime, GitHub Polling)
  - Clean separation with ⚡ Active Agents and 💤 Inactive Agents headers
  
- **e2e-test-github-issue3-claim.png** - GitHub Issue #3 with claim comment
  - Shows autonomous agent claiming issue within 2 minutes of creation
  - Claim comment: "🤖 Agent m0nk111-post started working on this issue at 2025-10-12T10:41:14.234350Z"
  - Issue labels: agent-ready, auto-assign, documentation, test
  - Demonstrates complete E2E workflow: issue creation → detection → claim

**Related Documentation**: See `docs/E2E_TEST_REPORT_2025-10-12.md` for comprehensive test analysis.

---

## Screenshot Locations

Playwright MCP stores screenshots in temporary directories:

- **Windows**: `C:\Users\onyou\AppData\Local\Temp\playwright-mcp-output\{session-id}\media\`
- **Linux**: `/tmp/playwright-mcp-output/{session-id}/media/`

Screenshots are preserved during the browser session and can be copied to this directory for permanent storage.

---

## Usage Guidelines

### Adding New Media

1. Place files in this directory
2. Update this README with description
3. Reference media files in documentation using relative paths: `../media/filename.ext`

### Naming Convention

- Use descriptive names with date: `{feature}-{description}-{YYYY-MM-DD}.{ext}`
- Use lowercase with hyphens: `e2e-test-dashboard-2025-10-12.png`
- Group related files with common prefix: `e2e-test-*`

### File Types

- **Screenshots**: PNG (preferred for UI), JPG (for photos)
- **Videos**: MP4 (compressed), GIF (short previews)
- **Diagrams**: SVG (preferred for scalability), PNG (export)

---

## Related Documentation

- `docs/E2E_TEST_REPORT_2025-10-12.md` - Complete E2E test report with analysis
- `ARCHITECTURE.md` - System architecture diagrams
- `docs/diagrams/` - Technical diagrams and flowcharts

---

**Last Updated**: October 12, 2025
