# API Reference

This document provides a reference for the RESTful APIs exposed by Agent-Forge.

## Base URL

All API endpoints are relative to the base URL where the service is hosted.

---

## Authentication API (`api/auth_routes.py`)

Handles user authentication and authorization.

### `POST /login`

Authenticates a user and returns a session token.

*   **Request Body**:
    ```json
    {
      "username": "your_username",
      "password": "your_password"
    }
    ```

*   **Response (Success)**:
    ```json
    {
      "token": "jwt_session_token",
      "message": "Login successful"
    }
    ```

*   **Response (Error)**:
    ```json
    {
      "message": "Invalid credentials"
    }
    ```

---

## Configuration API (`api/config_routes.py`)

Allows for viewing and updating system configuration.

### `GET /config/{service_name}`

Retrieves the configuration for a specific service.

*   **URL Parameters**:
    *   `service_name` (string, required): The name of the service (e.g., `polling`, `code_agent`).

*   **Response (Success)**:
    ```yaml
    # Contents of the requested YAML configuration file
    github_username: "m0nk111-qwen-agent"
    poll_interval: 30
    claim_timeout: 10
    ...
    ```

### `PUT /config/{service_name}`

Updates the configuration for a specific service.

*   **URL Parameters**:
    *   `service_name` (string, required): The name of the service.

*   **Request Body**:
    *   The full YAML configuration to be applied.

*   **Response (Success)**:
    ```json
    {
      "message": "Configuration for 'polling' updated successfully."
    }
    ```

---

## Agent Control API (Conceptual)

These endpoints are conceptual and represent the future direction for agent management.

### `POST /agent/start`

Starts a new agent instance.

*   **Request Body**:
    ```json
    {
      "agent_type": "code_agent",
      "task_id": "issue-123"
    }
    ```

### `GET /agent/status/{agent_id}`

Gets the status of a running agent.

*   **URL Parameters**:
    *   `agent_id` (string, required): The unique ID of the agent.

*   **Response**:
    ```json
    {
      "agent_id": "agent-xyz",
      "status": "in-progress",
      "current_step": "Analyzing codebase"
    }
    ```
