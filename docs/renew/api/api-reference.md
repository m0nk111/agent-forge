# API Reference

This document provides a detailed reference for the Agent-Forge RESTful API. The API is built using FastAPI and provides endpoints for managing and monitoring the system.

## Base URL

The API is served from the root of the application.

## Authentication

Authentication is handled via JWT (JSON Web Tokens). A valid token must be provided in the `Authorization` header as a Bearer token.

`Authorization: Bearer <your_jwt_token>`

Tokens can be obtained via the `/login` endpoint provided by `api/auth_routes.py`.

---

## 1. Authentication API (`api/auth_routes.py`)

### POST /login

Authenticates a user against the system's PAM (SSH) credentials and returns a JWT session token.

- **Request Body**:
    ```json
    {
      "username": "your_system_username",
      "password": "your_password"
    }
    ```
- **Success Response (200 OK)**:
    ```json
    {
      "success": true,
      "token": "ey...",
      "username": "your_system_username",
      "expires": "2025-10-15T12:00:00Z"
    }
    ```
- **Error Response (401 Unauthorized)**:
    ```json
    {
      "success": false,
      "error": "Invalid credentials"
    }
    ```

---

## 2. Configuration API (`api/config_routes.py`)

These endpoints require a valid JWT for access.

### Agents

#### GET /agents

Retrieves a list of all configured agents.

- **Success Response (200 OK)**:
    ```json
    [
      {
        "agent_id": "qwen-coder",
        "name": "Qwen Coder",
        "model": "qwen2.5-coder:7b",
        "role": "developer",
        "enabled": true,
        ...
      }
    ]
    ```

#### POST /agents

Creates a new agent configuration.

- **Request Body**: `AgentConfigModel`
- **Success Response (201 Created)**: The newly created agent configuration object.

#### GET /agents/{agent_id}

Retrieves the configuration for a specific agent.

- **Success Response (200 OK)**: The agent configuration object.
- **Error Response (404 Not Found)**: If the agent ID does not exist.

#### PUT /agents/{agent_id}

Updates the configuration for a specific agent.

- **Request Body**: `AgentUpdateModel` (all fields are optional)
- **Success Response (200 OK)**: The updated agent configuration object.

#### DELETE /agents/{agent_id}

Deletes the configuration for a specific agent.

- **Success Response (204 No Content)**.

### Repositories

#### GET /repositories

Retrieves a list of all configured repositories.

#### POST /repositories

Creates a new repository configuration.

#### GET /repositories/{repo_id}

Retrieves the configuration for a specific repository.

#### PUT /repositories/{repo_id}

Updates the configuration for a specific repository.

#### DELETE /repositories/{repo_id}

Deletes the configuration for a specific repository.

### System

#### GET /system/config

Retrieves the main system configuration.

#### PUT /system/config

Updates the main system configuration.

### Keys & Providers

#### GET /keys/providers

Lists all available LLM provider keys that can be managed.

#### GET /keys

Retrieves the names of all currently set API keys.

#### POST /keys/{key_name}

Adds or updates an API key.

-   **Request Body**:
    ```json
    {
      "value": "your_api_key_value"
    }
    ```

#### DELETE /keys/{key_name}

Deletes an API key.

### Permissions

#### GET /permissions/presets

Lists all available permission presets (e.g., `read_only`, `developer`, `admin`).

#### GET /permissions/metadata

Provides metadata for all available individual permissions.
