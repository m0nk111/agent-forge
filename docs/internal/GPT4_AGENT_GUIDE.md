# Agent Launcher Guide

Complete guide for using the universal agent launcher in Agent-Forge.

## Overview

The agent launcher (`scripts/launch_agent.py`) is a universal tool that automatically discovers and launches any agent profile from the `config/agents/` directory. It supports multiple LLM providers (OpenAI GPT-4, Anthropic Claude, Google Gemini, local Ollama) and provides interactive and direct issue handling modes.

## Quick Start

```bash
# List all available agents
python3 scripts/launch_agent.py --list

# Launch specific agent
python3 scripts/launch_agent.py --agent gpt4-coding-agent

# Handle issue with specific agent
python3 scripts/launch_agent.py --agent gpt4 --issue 92

# Interactive mode with agent selection
python3 scripts/launch_agent.py --interactive
```