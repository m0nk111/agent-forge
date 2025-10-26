# Agent-Forge System Architecture

This document provides a detailed description of the Agent-Forge system architecture, outlining its core components and their interactions.

## 1. High-Level Overview

Agent-Forge is a multi-agent platform designed for autonomous software development and task execution. It operates by monitoring GitHub repositories for new issues, assigning them to specialized agents, and orchestrating a pipeline to resolve them.

The architecture is modular, consisting of three main layers:
- **API Layer**: A FastAPI application that provides RESTful endpoints for configuration, monitoring, and control.
- **Engine Layer**: The core of the system, containing all business logic for agent management, task orchestration, and execution.
- **Data Layer**: Manages the state of the system, including configuration files, polling state, and logs.

## 2. Core Components

### 2.1. Engine

The `engine` is the heart of Agent-Forge. It is responsible for all autonomous operations.

#### 2.1.1. `engine/core`

This directory contains the foundational components that manage the system's state and lifecycle.

- **`service_manager.py`**: Manages the lifecycle of all Agent-Forge services (polling, monitoring, web UI) as a single systemd-compatible process. It handles graceful shutdowns and health checks.
- **`agent_registry.py`**: A unified system for managing the lifecycle of all agents. It supports "always-on" and "on-demand" loading strategies to optimize resource usage.
- **`config_manager.py`**: Handles loading, validation, and management of all YAML-based configurations for agents, repositories, and the system itself.
- **`pipeline_orchestrator.py`**: Orchestrates the end-to-end autonomous workflow, from issue detection to pull request merging. It manages service communication, error recovery, and progress tracking.
- **`key_manager.py`**: Securely manages API keys and other secrets.
- **`llm_providers.py`**: A factory for creating clients for different LLM providers (OpenAI, Anthropic, Google, local Ollama).

#### 2.1.2. `engine/runners`

This directory contains long-running services that operate in the background.

- **`polling_service.py`**: Periodically polls GitHub repositories for new or updated issues that match predefined criteria (e.g., specific labels). It initiates the issue resolution pipeline when an actionable issue is found.
- **`monitor_service.py`**: Provides a monitoring service that collects logs and status updates from all agents and services, making them available through a WebSocket connection for real-time dashboards.
- **`coordinator_agent.py`**: A central agent that orchestrates tasks among other specialized agents based on their roles and capabilities.

#### 2.1.3. `engine/operations`

This directory contains modules that implement the specific actions (capabilities) that agents can perform.

- **`github_api_helper.py`**: A wrapper around the GitHub REST API for all interactions with repositories, issues, and pull requests.
- **`issue_handler.py`**: Parses and analyzes incoming GitHub issues to determine the requirements and create a plan for implementation.
- **`code_generator.py`**: Uses an LLM to generate code based on the requirements extracted by the `issue_handler`.
- **`file_editor.py`**: Provides tools for agents to read, write, and modify files within the workspace.
- **`git_operations.py`**: Handles all Git-related actions, such as creating branches, committing changes, and pushing to remote repositories.
- **`pr_reviewer.py`**: An agent that can automatically review pull requests, check for common issues, and provide feedback.
- **`shell_runner.py` / `terminal_operations.py`**: Securely executes shell commands on behalf of agents, subject to permissions defined in the configuration.

#### 2.1.4. `engine/validation`

This directory contains modules responsible for validating inputs and instructions.

- **`instruction_parser.py`**: Parses natural language instructions from issues into structured commands that agents can execute.
- **`instruction_validator.py`**: Validates parsed instructions against a set of rules to ensure they are safe and well-formed.
- **`security_auditor.py`**: Performs security checks on generated code and shell commands.

### 2.2. API

The `api` directory contains the FastAPI application that exposes the system's functionality.

- **`auth_routes.py`**: Provides SSH-based authentication using PAM, issuing JWTs for secure access to the dashboard and API.
- **`config_routes.py`**: Exposes CRUD endpoints for managing the configuration of agents, repositories, and system settings. This allows for dynamic reconfiguration without restarting the service.

## 3. Data Flow: A Typical Issue Resolution Pipeline

1.  **Detection**: The `PollingService` runs on a schedule and queries GitHub for issues assigned to the bot user or labeled with `agent-ready`.
2.  **Claiming**: To prevent race conditions, the service "claims" an issue by adding a specific comment or label.
3.  **Orchestration**: The `PollingService` hands the issue over to the `PipelineOrchestrator`.
4.  **Parsing**: The orchestrator invokes the `IssueHandler` to parse the issue body and comments, extracting actionable requirements.
5.  **Task Assignment**: The `CoordinatorAgent` receives the requirements and breaks them down into tasks, assigning them to appropriate agents (e.g., `CodeGenerator`, `FileEditor`).
6.  **Implementation**:
    - The `CodeGenerator` agent generates the necessary code.
- The `FileEditor` agent applies the changes to the local file system.
- The `GitOperations` agent creates a new branch and commits the changes.
7.  **Pull Request**: The `BotAgent` (using `github_api_helper`) creates a pull request with the changes.
8.  **Review**: The `PRReviewer` agent is triggered, which reviews the code and can approve it or request changes.
9.  **Merge**: If approved (and auto-merge is enabled), the `BotAgent` merges the pull request.
10. **Cleanup**: The issue is closed, and the pipeline for that issue is terminated.

This modular and service-oriented architecture allows for scalability, maintainability, and the flexible addition of new agents and capabilities.
