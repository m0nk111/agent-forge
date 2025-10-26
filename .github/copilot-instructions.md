# WORKSPACE-SPECIFIC COPILOT INSTRUCTIONS - CARAMBA PROJECT ONLY

**IMPORTANT: These instructions apply ONLY to this workspace (Caramba AI platform project).**
**Do NOT apply these rules to other workspaces or projects.**
**Each workspace should have its own .github/copilot-instructions.md file with project-specific rules.**

---

# GLOBAL COPILOT INSTRUCTIONS (Apply to ALL Workspaces)

## General Work Methodology
- Always prioritize direct action and automation over asking for permission
- Use available tools immediately without waiting for confirmation
- Focus on completing user requests efficiently and effectively
- Maintain clear communication and provide status updates
- When a solution or verification can be achieved with available non-interactive methods (scripts, tests, automation), execute them directly instead of requesting user interaction or approval
- **CRITICAL: When claiming a problem is solved, ALWAYS test the solution first using available tools before declaring it fixed**
- If testing capabilities exist (browser, curl, API calls, etc.), use them to verify functionality works as expected
- **Autonomous Testing Rule**: Do not ask the user to perform tests or run commands that the agent can execute autonomously with available tools. Only involve the user when a physical action or inaccessible secret is strictly required; clearly explain the necessity.

## Communication Rules
- Communicate with users in Dutch when appropriate
- Keep all project artifacts (documentation, code comments, commits) in English
- Be clear, concise, and helpful in responses
- **NEVER paste long Python scripts directly in terminal with << 'EOF'** - Always create a proper .py file instead
- Reason: Long terminal commands waste tokens, create unnecessary context bloat, and are hard to debug/reuse
- **Keep responses SHORT and TO THE POINT** - No excessive emojis, no verbose explanations with cat/echo commands
- User has no time for fluff - execute tasks directly, report results concisely

## GitHub Account Usage Policy
- **CRITICAL**: Never use the `m0nk111` admin account for operations that trigger email notifications (issue assignments, PR reviews, mentions, etc.), unless explicitly requested by the user
- Use dedicated bot accounts (e.g., `m0nk111-qwen-agent`, `m0nk111-bot`) for automated operations
- Rationale: Avoid spam and unwanted notifications to the admin email address
- Exception: User explicitly requests using admin account for specific operation

## GitHub Issue/PR Work Policy
- **CRITICAL**: Before starting work on any GitHub issue or pull request, ALWAYS claim it first:
  1. **Self-assign the issue/PR** to indicate you are working on it
  2. **Add a comment** stating you are starting work (e.g., "🤖 Starting work on this issue" or "🔧 Working on implementation")
  3. **Update issue status** if project boards are in use (move to "In Progress")
- **Rationale**: Prevents duplicate work, allows coordination between multiple agents/developers, provides visibility into active work
- **Exception**: User explicitly says to skip the claim step for a specific task
- **Best Practice**: When completing work, add a comment summarizing what was done before closing the issue

## Tool Usage Guidelines
- Use terminal tools when needed for system operations
- Apply best practices for code generation and editing
- Validate changes and test functionality when possible
- If a command fails due to missing packages/tools, immediately install them using appropriate package manager (apt, pip, npm, etc.)
- **Git Workflow**: Always create file-specific commit messages when modifying individual files, describing exactly what was changed and why
- **Always check available tools first** before resorting to shell commands - use file/edit tools for file operations
- **CRITICAL: When claiming a problem is solved, ALWAYS test the solution first using available tools before declaring it fixed**
- If testing capabilities exist (browser, curl, API calls, etc.), use them to verify functionality works as expected

## Quality Standards
- Write clean, maintainable code
- Follow established conventions and patterns
- Document important decisions and changes

## Project Structure Convention
- **Root Directory Rule**: Project root may ONLY contain README.md and CHANGELOG.md
- **All other files must be organized in subdirectories** with a narrow and deep tree structure
- **Rationale**: Keep root clean, promote organization, easier navigation, clear project structure
- **Examples**:
  - ✅ GOOD: `/docs/ARCHITECTURE.md`, `/app/backend/main.py`, `/scripts/deploy.sh`
  - ❌ BAD: `/ARCHITECTURE.md`, `/main.py`, `/deploy.sh` (all should be in subdirectories)
- **Exception**: Standard project files like `.gitignore`, `.github/`, `.vscode/` are allowed in root
- **When creating new files**: Always place them in appropriate subdirectory, create new subdirs if needed

## Debug Code Requirements

When implementing any feature or component:

1. **Always Include Debug Logging**: Add comprehensive debug output throughout all code
2. **Global Debug Control**: Implement a DEBUG flag (config variable or GUI checkbox) that controls debug output
3. **Persistence**: Debug flag state must be saved and restored (persist across sessions)
4. **Granular Output**: Include debug information for:
   - Function entry/exit points
   - Key variable values and state changes
   - Error conditions and exceptions
   - Performance metrics (timing, bandwidth, resource usage)
   - State transitions
   - Network operations (send/receive, compression stats)
5. **Clear Formatting**: Use emoji prefixes for easy scanning:
   - 🐛 General debug information
   - 🔍 Detailed inspection/analysis
   - ⚠️ Warnings or edge cases
   - ❌ Errors
   - ✅ Success confirmations
   - 📊 Statistics/metrics
   - 🔧 Configuration changes
6. **Performance Impact**: Ensure debug code has minimal overhead when disabled (use conditional checks, not just output suppression)
7. **GUI Integration**: When building GUI applications, include a debug checkbox that:
   - Persists state in configuration
   - Enables debug output in real-time
   - Shows/hides debug panels or log areas
   - Affects all components (network, audio, codec, etc.)

**Example Implementation:**
```python
# Configuration
class AppConfig:
    def __init__(self):
        self.debug_enabled = self.load_setting('debug_enabled', default=False)
    
    def set_debug(self, enabled: bool):
        self.debug_enabled = enabled
        self.save_setting('debug_enabled', enabled)

# Usage in code
def process_audio(data):
    if config.debug_enabled:
        logger.debug(f"🐛 Processing audio: {len(data)} bytes")
    
    result = perform_processing(data)
    
    if config.debug_enabled:
        logger.debug(f"✅ Audio processed: {len(result)} bytes (compression: {calculate_ratio(data, result):.1f}%)")
    
    return result
```

## Git Commit Standards
- **Per-File Commit Comments**: When making changes to individual files, always create specific git commit messages that describe the exact changes made to that file
- **Granular Commits**: Prefer smaller, focused commits with clear descriptions over large commits with generic messages
- **Descriptive Messages**: Each commit message should explain what was changed, why it was changed, and the impact of the change
- **File-Specific Context**: Include the filename or component being modified in the commit message for clarity

---

## Port Management (global rule)
- Do not create overlapping or conflicting port mappings. Caramba-owned services must use ports in the 7000–7999 range by convention (e.g., backend 7999, frontend 7998). External tools may keep defaults.
- The authoritative Port Inventory and conventions live in the project documentation: see `caramba/docs/PORTS.md`.

## Terminal Auto-Approve Policy (summary)
- Chat › Tools › Terminal: Auto Approve is configured via regular expressions to allow all commands by default: `"/.*/": true`.
- Additional regex patterns for common commands are included for enhanced compatibility: `/^curl\\b/`, `/^docker\\b/`, `/^docker-compose\\b/`, etc.
- Explicit deny rules can still be layered using either prefix matches (e.g., `"rm": false`) or full command line regex with `{ approve: false, matchCommandLine: true }`.
- This policy must be synchronized in project-level settings (e.g., `.vscode/settings.json`).

## Post-Todo Auto-Approve Cleanup
- After completing each todo item, review any new entries added to `chat.tools.terminal.autoApprove` that approve a full, literal command line.
- Convert those literal approvals into wildcard or regex-based patterns that generalize the intent (e.g., prefer `/^curl\\b/` or `/^docker\\b/` over specific command strings).
- Keep both the global wildcard `"/.*/": true` and useful regex patterns for optimal compatibility and maintainability.

# Update Rule
Any user wishes or changes must be immediately updated in both the chatmode file and the instructions file. All automation, GUI, logging, and desktop actions may be executed immediately and autonomously, without asking for permission or confirmation, unless a specific project rule forbids it.

# Terminal Auto-Approve Policy
- Chat › Tools › Terminal: Auto Approve is configured via regular expressions to allow all commands by default: `"/.*/": true`.
- **Balanced Security Approach**: User-level settings maintain catchall as ultimate fallback while adding explicit denies for dangerous patterns (rm -rf, shutdown, privileged docker, disk tools).
- **Pattern Priority**: deny > literal > regex > wildcard > catchall
- Explicit deny rules can still be layered using either prefix matches (e.g., `"rm": false`) or full command line regex with `{ approve: false, matchCommandLine: true }`.
- This policy must be synchronized in project-level settings (e.g., `.vscode/settings.json`) to ensure consistent behavior across agents.

## VSCode Settings File Editing Methodology
- **User-level settings**: Use URI `vscode-userdata:/c%3A/Users/onyou/AppData/Roaming/Code/User/settings.json` with replace_string_in_file tool
- **Workspace-level settings**: Use standard file path `.vscode/settings.json` with replace_string_in_file tool
- **Auto-approve optimization strategy**: Remove overly-specific `matchCommandLine: true` entries, keep literal commands as fallbacks, retain catchall for compatibility, add security denies for dangerous patterns
- **Pattern improvement**: Group related commands in regex patterns (e.g., `/^[eg]rep\b/` for grep/egrep), use word boundaries `\b` for precision

## Post-Todo Auto-Approve Cleanup
- After completing each todo item, review any new entries added to `chat.tools.terminal.autoApprove` that approve a full, literal command line.
- Convert those literal approvals into wildcard or regex-based patterns that generalize the intent (e.g., prefer `/^curl\b/` or `"curl": true` over a specific `curl ...` string).
- Remove redundant literal approvals after adding the generalized rule to keep the setting compact and maintainable.

# Best Option Rule
The agent always chooses the best option and executes it directly, without waiting for permission, input, or confirmation. This applies to all desktop, GUI, logging, and automation actions in any app or environment.

# Sync Rule
All `copilot-instructions.md` files across different locations (e.g., `~/.github/copilot-instructions.md`, `project/.github/copilot-instructions.md`) **MUST** be kept in sync. Any changes to one file must be immediately replicated to all other locations to ensure consistency.

# CARAMBA PROJECT-SPECIFIC RULES

## Superproject Overview
- **Location**: `/home/flip/caramba/`
- **Type**: Unified AI platform with a central frontend, backend, and modular services.
- **Backend**: FastAPI-based, exposes REST endpoints that delegate to services under `app/services/`.
- **Frontend**: React/Vite application that integrates features exposed by the backend.
- **Services**: Each AI capability is an isolated module in `app/services/<name>` (e.g., `sadtalker`, `wav2lip`, `tts`).
- **External Code**: Read-only integrations under `app/external-code/`. **Never commit or push changes in this directory.**

## Port Usage Inventory
| Project/Scope | Service/Process          | Port     | Protocol | Notes                                                     |
|---------------|--------------------------|----------|----------|-----------------------------------------------------------|
| Trading       | Frontend Dashboard       | 7990     | TCP      | Flask dashboard at 192.168.1.31                           |
| Caramba       | FastAPI backend          | 7999     | TCP      | Default backend REST API                                  |
| Caramba       | React/Vite frontend      | 5173     | TCP      | Dev server (systemd service: caramba-frontend)            |
| Caramba       | Nginx (docker, deploy)   | 80/443   | TCP      | Webserver/proxy; HTTPS via 443                            |
| Caramba       | Conversation Processor   | 7995     | TCP      | Whisper transcription REST API (Digital Twin Phase 1)     |
| Caramba       | Voice Training Receiver  | 7100     | TCP      | Audio receiver for voice training (dual stream)           |
| Agent-Forge   | Monitor Server           | 7997     | TCP      | Service manager monitoring at 192.168.1.30                |
| Agent-Forge   | Dashboard & Platform     | 8897     | TCP      | External project at 192.168.1.30 (Grafana+Prometheus)    |
| Stepper       | Height Control API       | 7996     | TCP      | Lamp height control backend (FastAPI)                     |
| Stepper       | Web Interface            | 8080     | TCP      | HTTP server for dark mode control interface               |
| Frigate       | NVR Web UI               | 8971     | TCP      | Frigate web interface (HTTPS)                             |
| Frigate       | NVR API                  | 5000     | TCP      | Frigate REST API                                          |
| Frigate       | RTSP Server              | 8554     | TCP      | RTSP streams for cameras                                  |
| Tars-AI (ext) | Uvicorn backend          | 8001     | TCP      | Conversation AI backend (external service)                |
| ComfyUI (ext) | Workflow server          | 8188     | TCP      | Only active when ComfyUI runs                             |
| Ollama (ext)  | LLM server               | 11434    | TCP      | LLM API                                                   |
| TTS Docker    | TTS server               | 5002     | TCP      | Text-to-speech (docker container)                         |
| Monitoring    | Prometheus               | 9090     | TCP      | Internal monitoring                                       |
| Monitoring    | Grafana                  | 3000     | TCP      | Dashboard                                                 |
| Node (misc)   | Assorted dev servers     | 3694/4453| TCP      | Extra node servers used for experiments (dev/test)        |
| VSCode        | VSCode server            | 35455    | TCP      | Only during remote development                            |
| System        | SSH                      | 22       | TCP      | System access                                             |

**Convention:**
- All Caramba-owned services must use ports within the `7000-7999` range (exception: frontend dev server on 5173).
- External tools (ComfyUI, Ollama, Docker services, etc.) may use their default ports, but they **MUST** be recorded in this table.
- Agent-Forge uses ports 7997 (monitor) and 8897 (dashboard) at 192.168.1.30 - avoid conflicts.

## Developer Workflows
- **Build Frontend**: Run `npm run build` inside `app/frontend/`.
- **Start Backend**: Run Uvicorn for the FastAPI app in `app/backend/` (use a virtual environment).
- **Test Backend**: Run project tests (pytest recommended) under `app/backend/` and `app/services/`.
- **Health Check**: Run `scripts/healthcheck.sh` for a quick smoke test.

## Project Conventions

### Language Convention
All project documentation, code comments, and commit messages **MUST** be in **English**. User-facing UI text may be localized when explicitly requested.
- **Communication with Users**: Agents may communicate with users in Dutch when appropriate, but all project artifacts (documentation, code, commits) remain in English.

### Service Rule
As soon as a demo, integration, or endpoint works, convert it into a reusable service (backend service, FastAPI endpoint module, or frontend service module) to guarantee reuse in the web app.

### External Projects Policy
- "External projects" are everything under `app/external-code/` (e.g., SadTalker, Wav2Lip, ComfyUI).
- **Never commit or push inside external projects.** They are strictly read-only from this repository’s perspective.
- External code can be integrated, imported, or invoked by Caramba services, as long as their Git repositories are left untouched.

### System Changes & Installations
System-level changes and installations (apt, pip, npm) are allowed, as long as they do not modify external GitHub projects under `app/external-code/`.

### Port Range Policy
All Caramba-owned components (frontend, backend, services) run on ports `7000-7999` by convention (exception: frontend dev on 5173).
- **Backend REST API**: `7999` (not currently running)
- **Frontend Dev Server**: `5173` (Vite default, systemd service)
- **Conversation Processor**: `7995` (Whisper transcription API)
- **Voice Training Receiver**: `7100` (TCP receiver for dual audio streams)
- **Nginx Proxy**: HTTP port `80` (HTTPS port `443` optional/disabled in development)
- **Reserved by Agent-Forge**: `7997` (monitor), `8897` (dashboard) at 192.168.1.30
- **Reserved by Stepper**: `7996` (height control API)
External tools may keep their defaults but must be registered in the port inventory table.

### Voice Training Service (Recent Implementation - October 2025)
**Location**: `/home/flip/caramba/app/services/voice-training/`

**Purpose**: Capture dual audio streams (microphone + system audio) for voice cloning and customer service AI training

**Protocol**: AudioTransfer v1.0 with 16-byte header format
- Magic bytes: 'AUD' (3B) + version (1B) + packet_type (1B) + stream_type (1B) + compression (1B) + reserved (1B)
- Sample rate (4B little-endian) + channels (2B) + data_length (2B)
- Packet types: 0x01=AUDIO_DATA, 0x02=STREAM_INFO
- Compression: 0=PCM, 1=OPUS (24 kbps, 96.7% bandwidth reduction)

**Key Components**:
- `audio_protocol.py`: AudioPacket/StreamInfo parsing, receive_packet() function
- `audio_codec.py`: OpusDecoder using pyogg/libopus for decompression
- `audio_receiver.py`: TCP server on port 7100, STREAM_INFO + AUDIO_DATA handling
- `storage_manager.py`: Session-based WAV storage with dynamic format configuration
- `service.py`: Coordinator with callback chain (receiver → service → storage)

**Dependencies**: pyogg (0.6.14+), libopus0, libopus-dev

**Debug Implementation**: Comprehensive debug logging with emoji prefixes (🔄 📖 📥 📦 📡 🎤 🔊), print() + logger dual output for thread visibility

**Status**: Receiver tested and running on port 7100, waiting for Windows client testing

**AudioTransfer Windows Client**:
- Repository: `/home/flip/audiotransfer/` (v1.0.0-stable)
- Connection: Reverse mode (Windows server connects to Linux receiver)
- Compression: Opus 24 kbps, 20ms frames, 48kHz (1411 kbps → 52 kbps = 93.2% reduction)
- Streams: Stream 1 (mic), Stream 2 (system audio via WASAPI)
- **Action Required**: User must rebuild Windows .exe or run Python source directly

### Git Operations
**IMPORTANT**: For all Git operations (commits, status, diffs, etc.), prefer using the `github-mcp-server` tools when available instead of running raw git commands in terminal. This provides better integration and tracking.

### IP Address Convention
- **Caramba (primary)**: `192.168.1.27` for frontend/backend/webapp
  - Frontend: http://192.168.1.27:5173/
  - Conversation Processor: http://192.168.1.27:7995/health
  - Voice Training Receiver: tcp://192.168.1.27:7100
- **Agent-Forge (external)**: `192.168.1.30` for monitoring and dashboard
  - Monitor: http://192.168.1.30:7997
  - Dashboard: http://192.168.1.30:8897/dashboard.html
- **Tars-AI (external)**: `192.168.1.26` for its own backend/frontend
- All HTTPS, proxy, and network configurations should target these IP addresses accordingly.

### LAN Host Inventory (Authoritative Mapping)
Use these host endings only for their designated purposes. Do not repurpose without updating this table and related docs.

| Host IP           | Purpose / Role                              | Notes |
|-------------------|---------------------------------------------|-------|
| 192.168.1.200     | Aquaponics control (primary, eth0 wired)    | Controllers / sensors stack A |
| 192.168.1.201     | Aquaponics control (secondary, Wi-Fi)       | Redundant / experimental stack B |
| 192.168.1.160     | Home Assistant + OctoPrint services         | HA automations & 3D printer mgmt |
| 192.168.1.27      | Frigate NVR / Caramba primary host          | Camera ingestion & RTSP / UI + Caramba services |
| 192.168.1.26      | AI KVM guest / Tars-AI services             | Runs AI model services & Tars-AI backend/frontend |
| 192.168.1.245     | Game / dev Windows PC                       | High-GPU workstation (Windows) |
| 192.168.1.101     | Living room Windows PC                      | General user workstation |
| 192.168.1.98      | Managed LAN switch                          | Layer2/Layer3 switching; do not deploy services |
| 192.168.1.25      | AI physical host / KVM hypervisor           | Hosts KVM guests (192.168.1.26-30) |
| 192.168.1.26-30   | KVM guest range (AI & infra VMs)            | Distributed by 192.168.1.25 (hypervisor) |
| 192.168.1.203-209 | RTSP IP cameras                             | Static assignments for surveillance (Frigate ingest) |
| 192.168.1.1       | Main router / gateway                       | Primary LAN router |
| 192.168.1.253     | Wi-Fi access point (bridge/AP mode)         | Auxiliary AP - do not host services |
| 192.168.1.250     | Wi-Fi bridge router                         | Wireless bridge link |

### Frigate Integration
- **Status**: Active and working via redirect
- **Nginx Config**: `/frigate/` location redirects to `https://192.168.1.27:8971$request_uri`
- **Direct Access**: `https://192.168.1.27:8971` (HTTPS required)
- **Via Caramba**: `http://192.168.1.27/frigate/` (automatic redirect)
- **Port**: `8971` (web UI), `5000` (API), `8554` (RTSP streams)
- **Network**: Runs as standalone container, accessible via host networking

## Copilot Agent Registry

### Registered Agents
All Copilot-style agents working on this project must be registered here for traceability and collaboration.

| Agent Name           | Agent Tag | Model Tag   | Specialization                                  | Contact/Owner    | Last Active   |
|----------------------|-----------|-------------|-------------------------------------------------|------------------|---------------|
| GitHub Copilot       | GCOP      | GPT-4       | General AI assistance, code generation, docs    | GitHub/Microsoft | October 2025  |
| Claude Sonnet 4.5    | CLAU      | SONNET4.5   | Advanced reasoning, complex problem solving     | Anthropic        | Active        |
| Custom Qwen2.5-Coder | QWEN      | QWEN25      | Code generation, refactoring, debugging         | Local/Custom     | Active        |

### Agent Collaboration Rules
- All agents must respect the changelog discipline and todo list management.
- Agents may work simultaneously on different tasks but must coordinate via todo lists.
- For conflicting changes, the agent with the earliest todo start time takes precedence.
- All agents must communicate in English for project artifacts, but may use Dutch for user communication.

## Lessons Learned & Best Practices (Recent Updates)

### Voice Training Service Implementation (October 2025)

**What Could Have Been Avoided:**
- **Protocol version mismatch**: Initially implemented receiver for 8-byte header format, but audiotransfer was updated to 16-byte format. Should have checked GitHub repository for latest protocol before implementing.
- **Missing callback wiring**: STREAM_INFO packets were parsed but storage manager wasn't notified, causing connection failures. Should have implemented complete data flow (receiver → service → storage) from the start.
- **Thread debugging challenges**: Logger output not visible in threads, required adding print() statements with flush=True. Should have used dual logging (print + logger) from the beginning for thread visibility.
- **Connection testing assumptions**: Assumed connection established = data flowing, but Windows client connected without sending data. Should have added comprehensive debug logging at socket level immediately.

**Lessons Learned:**
- **Protocol synchronization**: Always pull latest version of external dependencies (audiotransfer) before implementing integration code.
- **Complete data flow design**: Map out entire callback chain (A → B → C) with all intermediate steps before writing any code.
- **Thread-safe debugging**: Use print(msg, flush=True) alongside logger for thread visibility, add emoji prefixes for easy scanning.
- **Socket-level debugging**: Add debug logging at lowest level (read_exact, receive_packet) to see exactly what's happening on the wire.
- **Incremental testing**: Test each component independently (protocol parsing, codec, receiver, storage) before integrating.
- **Callback systems**: When implementing event-driven architecture, wire all callbacks during initialization, not as afterthought.

**Debug Logging Best Practices Applied:**
- Emoji prefixes for easy scanning: 🔄 (thread), 📖 (read), 📥 (receive), 📦 (packet), 📡 (info), 🎤 (mic), 🔊 (system)
- Dual output: print() with flush=True for immediate visibility + logger for structured logging
- Granular checkpoints: Log every significant step (thread start, socket read, packet parse, callback invoke)
- Clear error messages: Specific descriptions of what failed and why (e.g., "Connection closed (received 0 bytes)")

## Task Management with Todo Lists
| Custom Qwen2.5-Coder | QWEN      | QWEN25    | Code generation, refactoring, debugging         | Local/Custom     | Active      |

### Agent Collaboration Rules
- All agents must respect the changelog discipline and todo list management.
- Agents may work simultaneously on different tasks but must coordinate via todo lists.
- For conflicting changes, the agent with the earliest todo start time takes precedence.
- All agents must communicate in English for project artifacts, but may use Dutch for user communication.

## Task Management with Todo Lists

All Copilot-style agents **MUST** use structured todo lists for planning, tracking, and executing complex multi-step tasks.

### Workflow
1.  **Check `CHANGELOG.md`**: Understand what has already been implemented.
2.  **Plan Tasks**: Write a complete todo list with specific, actionable items before starting.
3.  **Mark In-Progress**: Set **ONE** todo to `in-progress` before working on it.
4.  **Execute**: Complete the work for that specific todo.
5.  **Mark Completed**: **IMMEDIATELY** mark the todo as `completed`.
6.  **Repeat**: Move to the next todo and repeat the process.

### Tool Usage
- **`manage_todo_list` Tool**: This tool is **MANDATORY** for managing tasks. It must be updated immediately upon any status change.
- **Dual Tracking**: Create todo lists in both the Copilot interface and a `TODO_LIST.md` file in the project root for persistence and collaboration.

---
*Questions or improvements? Propose additions and update this file accordingly.*
