# Guide: Polling Service

This guide explains the functionality and configuration of the Polling Service in Agent-Forge.

## Overview

The Polling Service (`engine/runners/polling_service.py`) is a long-running process responsible for monitoring GitHub repositories for new issues that need to be handled by the agent system.

## How It Works

1.  **Initialization**: The service starts and loads its configuration from `config/services/polling.yaml`.

2.  **Polling Loop**: The service enters a loop where it periodically performs the following actions:
    *   It queries the GitHub API for issues in the configured repository.
    *   It filters issues based on criteria defined in `polling.yaml`, such as `github_username` (to find issues assigned to the bot) and `claim_timeout`.

3.  **Issue Detection**: When an un-claimed and relevant issue is found, the service retrieves its details.

4.  **State Management**: The service maintains a state file (`data/polling_state.json`) to keep track of issues that have already been processed, preventing the same issue from being handled multiple times.

5.  **Dispatching**: The detected issue is then passed to the **Issue Handler** (`engine/operations/issue_handler.py`) to begin the task resolution workflow.

## Configuration

The behavior of the Polling Service is controlled by `config/services/polling.yaml`.

```yaml
# config/services/polling.yaml

# The GitHub username to search for assigned issues.
# This should be the username of your bot/agent account.
github_username: "m0nk111-qwen-agent"

# The interval in seconds between each poll of the GitHub API.
poll_interval: 30

# The time in minutes before a claimed issue is considered expired and can be re-claimed.
claim_timeout: 10

# The repository to monitor.
# Format: owner/repo_name
target_repo: "m0nk111/agent-forge"
```

### Key Configuration Parameters

*   `github_username`: This is crucial. The polling service looks for issues assigned to this specific user. Make sure it matches the GitHub account used for your agents.
*   `poll_interval`: A shorter interval means faster issue pickup but more API calls. A longer interval is gentler on API rate limits.
*   `claim_timeout`: This is a safety mechanism. If an agent claims an issue but fails to process it, this timeout allows another agent to pick it up after the specified duration.

## Running the Service

The recommended way to run the Polling Service is using the provided systemd installation script:

```bash
./scripts/install-polling-service.sh
```

This script will:
1.  Create a systemd service file in `/etc/systemd/system/`.
2.  Enable and start the service.
3.  Ensure the service runs automatically on system startup.

You can check the status of the service using:

```bash
systemctl status polling-service
```

And view its logs with:

```bash
journalctl -u polling-service -f
```

## Troubleshooting

*   **No issues are being picked up**:
    *   Verify that the `github_username` in `polling.yaml` is correct.
    *   Ensure that issues in your repository are assigned to that user.
    *   Check the logs (`journalctl -u polling-service`) for any API errors.
*   **"Too many API requests" errors**:
    *   Increase the `poll_interval` in `polling.yaml` to reduce the frequency of API calls.
