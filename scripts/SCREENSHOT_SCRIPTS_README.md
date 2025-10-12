# Screenshot Management Scripts

## Windows → Linux Upload

**For Windows users running Playwright MCP client:**

Run `upload-screenshots.ps1` to automatically upload E2E test screenshots to the server:

```powershell
# Run in PowerShell (as Administrator if needed)
.\scripts\upload-screenshots.ps1
```

This script will:

- Search for E2E test screenshots in Playwright temp directories
- Find all `e2e-test-*.png` files
- Upload them to the server via SCP
- Show progress and results

**Requirements:**

- OpenSSH Client installed (Windows 10/11: Settings → Apps → Optional Features → OpenSSH Client)
- SSH access to the server (flip@192.168.1.30)

**Alternative (if SCP not available):**

- Use WinSCP GUI application
- Use FileZilla SFTP
- Mount network drive and copy manually

---

## Linux Copy Script

**For Linux users or server-side operations:**

Run `copy-e2e-screenshots.sh` to search and copy screenshots from Linux temp directories:

```bash
./scripts/copy-e2e-screenshots.sh
```

This script will:

- Search `/tmp/playwright-mcp-output/` for screenshots
- Copy found files to `media/` directory
- Provide manual copy instructions if not found

---

## Manual Copy Commands

### From Windows to Linux (SCP)

```powershell
scp "C:\Users\onyou\AppData\Local\Temp\playwright-mcp-output\*\media\e2e-test-*.png" flip@192.168.1.30:/home/flip/agent-forge/media/
```

### From Linux temp to media

```bash
cp /tmp/playwright-mcp-output/*/media/e2e-test-*.png /home/flip/agent-forge/media/
```

---

## Screenshot Locations

| Platform | Location |
|----------|----------|
| **Windows** | `%LOCALAPPDATA%\Temp\playwright-mcp-output\{session-id}\media\` |
| **Linux** | `/tmp/playwright-mcp-output/{session-id}/media/` |
| **Target** | `/home/flip/agent-forge/media/` |

---

## Related Files

- `media/SCREENSHOTS_INFO.txt` - Details about captured screenshots
- `media/README.md` - Media directory documentation
- `media/*.url` - Shortcuts to live URLs where screenshots were taken
