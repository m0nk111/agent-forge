# Getting Started Guide

This guide will walk you through setting up a local development environment for Agent-Forge.

## Prerequisites

- Python 3.10+
- Git
- Docker and Docker Compose (for Milvus and other services)
- An Ollama instance with the required models (e.g., `qwen2.5-coder:7b`)

## 1. Clone the Repository

```bash
git clone https://github.com/m0nk111/agent-forge.git
cd agent-forge
```

## 2. Set up the Python Environment

It is recommended to use a virtual environment.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure Secrets and Keys

-   Copy the example keys file:
    ```bash
    cp config/keys.example.json config/keys.json
    ```
-   Edit `config/keys.json` and add your API keys, especially `BOT_GITHUB_TOKEN`.

## 4. Start Dependent Services

Agent-Forge relies on a Milvus vector database for certain features like Claude Context. A `docker-compose` file is provided for convenience.

```bash
docker-compose -f docker-compose-milvus.yml up -d
```

## 5. Run the Main Service

You can run the entire suite of services using the `service_manager`.

```bash
python -m engine.core.service_manager
```

This will start:
-   The Polling Service
-   The Monitoring Service
-   The Web UI Dashboard

## 6. Access the Dashboard

Once the services are running, you can access the main dashboard at:

-   **URL**: `http://localhost:8897`

You will need to log in with your system (SSH) username and password.

## 7. Next Steps

-   **Create a new Agent**: See the `guides/creating-an-agent.md` guide.
-   **Explore the API**: Refer to the `api/api-reference.md` documentation.
-   **Configure a Repository**: Use the dashboard or the API to add a repository for the agents to monitor.
