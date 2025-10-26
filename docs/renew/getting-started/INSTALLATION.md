# Installation Guide

This guide will walk you through the steps to install and set up Agent-Forge on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

*   Python 3.10 or higher
*   pip (Python package installer)
*   Git
*   Docker (for Milvus vector database)

## 1. Clone the Repository

Start by cloning the Agent-Forge repository from GitHub:

```bash
git clone https://github.com/your-username/agent-forge.git
cd agent-forge
```

## 2. Install Dependencies

Install the required Python packages using `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 3. Set up Milvus Vector Database

Agent-Forge uses Milvus for vector storage and similarity search. The easiest way to run Milvus is with Docker.

1.  **Download the Docker Compose file:**
    ```bash
    wget https://raw.githubusercontent.com/milvus-io/milvus/master/deployments/docker/compose/docker-compose.yml
    ```

2.  **Start Milvus:**
    ```bash
    docker-compose up -d
    ```

    This will start the Milvus service in the background.

## 4. Configure API Keys and Secrets

Agent-Forge requires API keys for various services like GitHub and LLM providers.

1.  **Copy the example keys file:**
    ```bash
    cp config/keys.example.json config/secrets/keys.json
    ```

2.  **Edit `config/secrets/keys.json`** and add your API keys:
    ```json
    {
      "github_token": "your_github_personal_access_token",
      "bot_github_token": "your_bot_account_github_token",
      "openai_api_key": "your_openai_api_key",
      "google_api_key": "your_google_api_key",
      "openrouter_api_key": "your_openrouter_api_key"
    }
    ```

## 5. Run the Application

You can run the main application using the provided scripts. For example, to start the polling service:

```bash
./scripts/install-polling-service.sh
```

This will set up and run the polling service as a systemd service.

Refer to the scripts in the `scripts/` directory for running other components like agents and dashboards.

## Next Steps

Now that you have Agent-Forge installed, you can proceed to the **[Architecture Overview](../architecture/OVERVIEW.md)** to understand how the system works.
