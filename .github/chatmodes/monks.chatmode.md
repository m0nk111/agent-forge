# Update Rule
...exis# Behavior
- Never commit or push inside external projects (such as SadTalker, Wav2Lip, Avatarify, AnimateDiff, etc.); only within first-party projects.
- External project directories are always read-only for git actions.
- All commit/push actions are limited to first-party project directories and repositories.
- External code may be used, imported, and invoked according to the existing instructions.
- The agent may use any available tool, including file editing, running terminal commands, installing packages, and updating configuration.
- If a command fails due to missing packages/tools, immediately install them using appropriate package manager (apt, pip, npm, etc.)
- The agent will not ask for permission before executing any action.
- The agent will proceed with all tasks until the user's request is fully resolved.
- The agent will only ask for clarification if the user's request is ambiguous or incomplete.
- The agent will always prioritize direct action and automation...
Any user wishes or changes must be immediately updated in both this chatmode file and the instructions file.

# Best Option Rule
The agent always chooses and executes the best option without waiting for permission or confirmation.

# Communication Rule
All project artifacts (documentation, code comments, commits) are in English. The agent communicates with users in Dutch when appropriate.

# Acceptance Rule
I accept the use of any free, open-source tools, libraries, and services that are available without hidden conditions of limitations. The agent may use these directly to perform tasks in my project.

---
description: 'Full Automation: The agent is authorized to use every available tool and execute actions immediately without asking for permission.'
tools: [all]
---

# Purpose
This chat mode enables full autonomous operation. The agent will use any available tool in the workspace and execute actions immediately, without asking for approval or confirmation.

# Behavior
- Never commit or push inside external projects (such as SadTalker, Wav2Lip, Avatarify, AnimateDiff, etc.); only within first-party projects.
- External project directories are always read-only for git actions.
- All commit/push actions are limited to first-party project directories and repositories.
- External code may be used, imported, and invoked according to the existing instructions.
- The agent may use any available tool, including file editing, running terminal commands, installing packages, and updating configuration.
- The agent will not ask for permission before executing any action.
- The agent will proceed with all tasks until the user’s request is fully resolved.
- The agent will only ask for clarification if the user’s request is ambiguous or incomplete.
- The agent will always prioritize direct action and automation.
- Autonomous Testing Rule: Never ask the user to perform tests or run commands that can be executed autonomously with available tools. Only request user execution when physical intervention or inaccessible credentials are strictly required, and explicitly state the reason.

# Changelog Discipline Reminder
- After each autonomous change, add an entry to `CHANGELOG.md` (newest-first). See `AGENT_CHANGELOG_POLICY.md` when available.
- For documentation-only edits, also append a short line to `DOCS_CHANGELOG.md` when present.

# Terminal Auto-Approve Policy
- Terminal commands are auto-approved via regex: `"/.*/": true`.
- Deny rules can be added with either simple prefixes (e.g., `"rm": false`) or full command-line regex with `{ approve: false, matchCommandLine: true }`.

## Lessons Learned & Best Practices

### Implementation Lessons from Recent Projects

#### Wav2Lip Voice Cloning Service Implementation
**What Could Have Been Avoided:**
- Multiple Dockerfile iterations: Started with Python 3.10 but had to upgrade to 3.12 due to dependency conflicts. Should have validated the best Python version for all dependencies upfront.
- Missing system dependencies: dlib build initially failed due to missing cmake. Should have identified all build dependencies in advance by analyzing requirements.txt thoroughly.
- Inconsistent endpoint naming: Services list referenced the wrong endpoint (/api/wav2lip instead of /api/voice-cloning). Should have followed a consistent naming convention from the start.

**Lessons Learned:**
- Dependency analysis first: Always analyze all dependencies before container builds. Use tools like `pip-tools` or `poetry` for better dependency management.
- Test builds locally: Run small test builds before large containers. Use multi-stage builds to shorten build time.
- Consistent API design: Follow RESTful conventions from the start. Document all endpoints in an OpenAPI spec before implementing.
- Version pinning: Pin all dependency versions from the beginning to guarantee reproducible builds.

#### TTS Service Container Implementation
**What Could Have Been Avoided:**
- Subprocess dependency: The service tried to call the Docker binary which doesn't work inside containers. Should have chosen a pure Python implementation from the beginning.
- Missing error handling: `/generate` endpoint crashed on errors without proper logging. Should have implemented comprehensive error handling early.
- Port conflicts: Service used port 5002 while the backend proxy was already configured for another service. Should have checked the port usage inventory.

**Lessons Learned:**
- Container-native design: Services must be container-native, without external dependencies like Docker binaries.
- Proper logging: Implement structured logging from the start with correlation IDs for debugging.
- Resource management: Check existing resources (ports, volumes, networks) before adding new services.
- Health checks: Implement meaningful health checks that verify actual functionality.

#### SadTalker GPU Service Implementation
**What Could Have Been Avoided:**
- Venv vs system packages: Initially tried system packages but had to switch to a venv. Should have chosen a consistent package management strategy from the start.
- Mount path issues: External code mount paths were incorrect. Should have tested mount paths before building the container.
- CUDA version mismatch: PyTorch CUDA version did not match system CUDA. Should have checked the CUDA compatibility matrix.

**Lessons Learned:**
- Environment consistency: Always use virtual environments in containers for isolation.
- Mount testing: Test all volume mounts during development, not only at deployment time.
- GPU compatibility: Check CUDA/driver compatibility before installing GPU libraries.
- Base images: Use NVIDIA's official CUDA base images for consistent GPU support.

#### General Infrastructure Lessons
**What Could Have Been Avoided:**
- Docker Compose v1.29.2 GPU bug: Compose ignored `runtime: nvidia`. Should have upgraded the version or implemented a workaround earlier.
- Port conflicts: Multiple services attempted to use the same ports. Should have maintained a port inventory from the start.
- Environment file paths: docker-compose had incorrect `env_file` paths. Should have used absolute paths.

**Lessons Learned:**
- Version management: Track versions of all tools (Docker, Compose, CUDA, Python) and test compatibility.
- Configuration management: Use environment variables and config files for all configuration.
- Documentation discipline: Update documentation immediately upon changes, not afterward.
- Testing strategy: Implement testing (unit, integration, e2e) from the beginning of each component.

### Best Practices Going Forward

#### Development Workflow
1. Planning phase: Analyze dependencies, check compatibility, plan architecture before coding.
2. Incremental development: Build and test small components before large systems.
3. Documentation first: Document API contracts, configurations, and deployment before implementation.
4. Testing integration: Write tests alongside code, not afterward.

#### Container Development
1. Multi-stage builds: Use them for more efficient images and faster builds.
2. Base image selection: Choose appropriate base images based on requirements (CUDA, Python version).
3. Dependency management: Pin versions, use virtual environments, minimize image size.
4. Security: Run as non-root, update base images regularly, scan for vulnerabilities.

#### Service Architecture
1. API design: RESTful conventions, OpenAPI documentation, consistent error handling.
2. Health checks: Implement meaningful health endpoints that validate functionality.
3. Logging: Structured logging with correlation IDs and appropriate log levels.
4. Configuration: Environment-based config, secrets management, validation.

#### Infrastructure Management
1. Version control: Everything in Git, including infrastructure as code.
2. Automation: Automate builds, tests, and deployments wherever possible.
3. Monitoring: Implement metrics, logging, and health checks from the start.
4. Disaster recovery: Backups, rollback procedures, documentation.

# Todo Tool Requirement
All Copilot-style agents MUST use the `manage_todo_list` tool for task management on complex, multi-step work. Update statuses immediately upon any change. Use the tool for planning, tracking, and execution.