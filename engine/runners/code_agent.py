#!/usr/bin/env python3
"""
Qwen Agent - Generic autonomous coding agent using Qwen2.5-Coder via Ollama

This agent can work on any project by loading configuration from a YAML file.
It follows a structured phase-based approach for implementing features.

Author: Agent Forge
Model: Configurable (default: qwen2.5-coder:7b)
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Any
import time

try:
    import requests
except ImportError:
    print("ERROR: requests module not found. Install with: pip install -r requirements.txt")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML module not found. Install with: pip install pyyaml")
    sys.exit(1)

# Import from engine modules
from engine.operations.workspace_tools import WorkspaceTools
from engine.core.context_manager import ContextManager
from engine.operations.file_editor import FileEditor
from engine.operations.terminal_operations import TerminalOperations
from engine.operations.test_runner import TestRunner
from engine.operations.codebase_search import CodebaseSearch
from engine.operations.error_checker import ErrorChecker
from engine.operations.mcp_client import MCPClient
from engine.operations.issue_handler import IssueHandler

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CodeAgent:
    """Generic code agent that can use any LLM to implement projects from config"""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        model: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        project_root: Optional[str] = None,
        enable_monitoring: bool = False,
        agent_id: Optional[str] = None,
        llm_provider: Optional[str] = None,  # NEW: openai, anthropic, google, local
        api_key: Optional[str] = None  # NEW: API key override
    ):
        # Load configuration
        if config_path:
            self.config = self.load_config(config_path)
        else:
            self.config = self.get_default_config()
        
        # Override with command-line arguments
        self.model = model or self.config.get('model', {}).get('name', 'qwen2.5-coder:7b')
        self.ollama_url = self.config.get('model', {}).get('ollama_url', ollama_url)
        self.project_root = Path(project_root) if project_root else Path(self.config.get('project', {}).get('root', '.'))
        
        # LLM Provider initialization (NEW)
        self.llm_provider = None
        self.llm_provider_name = llm_provider or "local"
        self._initialize_llm_provider(api_key)
        
        # Initialize workspace tools for file exploration
        self.workspace = WorkspaceTools(str(self.project_root.resolve()))
        
        # Initialize context manager for sliding window
        self.context = ContextManager(max_tokens=6000)
        
        # Initialize file editing capabilities (Issue #5)
        self.file_editor = FileEditor(str(self.project_root.resolve()))
        
        # Initialize terminal operations (Issue #6)
        self.terminal = TerminalOperations(str(self.project_root.resolve()))
        
        # Initialize test runner (Issue #10)
        self.test_runner = TestRunner(self.terminal)
        
        # Initialize codebase search (Issue #7)
        self.codebase_search = CodebaseSearch(str(self.project_root.resolve()))
        
        # Initialize error checker (Issue #9)
        self.error_checker = ErrorChecker(self.terminal)
        
        # Initialize MCP client (Issue #12)
        self.mcp_client = MCPClient(self.terminal)
        
        # Initialize issue handler (autonomous GitHub issue resolution)
        self.issue_handler = IssueHandler(self)
        
        # Project metadata
        self.project_name = self.config.get('project', {}).get('name', 'Unnamed Project')
        self.project_issue = self.config.get('project', {}).get('issue', '')
        
        # Phases from config
        self.phases = self.config.get('phases', {})
        
        # Initialize monitoring (optional)
        self.monitor = None
        self.agent_id = agent_id or f"qwen-agent-{id(self)}"
        if enable_monitoring:
            try:
                from .monitor_service import get_monitor
                self.monitor = get_monitor()
                # Register this agent
                self.monitor.register_agent(self.agent_id, f"Qwen Agent - {self.project_name}")
                self.print_success(f"Monitoring enabled for agent {self.agent_id}")
            except Exception as e:
                self.print_warning(f"Could not enable monitoring: {e}")
                self.monitor = None
    
    def _initialize_llm_provider(self, api_key_override: Optional[str] = None):
        """
        Initialize LLM provider (OpenAI, Anthropic, Google, or local Ollama).
        
        Priority:
        1. api_key_override parameter
        2. KeyManager (keys.json)
        3. Environment variables
        4. Fall back to local Ollama
        
        Args:
            api_key_override: Optional API key to use instead of KeyManager
        """
        if self.llm_provider_name == "local":
            # Use Ollama (no API key needed)
            self.print_info(f"🏠 Using local Ollama: {self.model} @ {self.ollama_url}")
            return
        
        # Try to get API key for commercial providers
        try:
            from engine.core.key_manager import KeyManager
            from engine.core.llm_providers import get_provider
            
            api_key = api_key_override
            
            if not api_key:
                # Load from KeyManager
                key_manager = KeyManager()
                
                # Map provider name to key name
                key_names = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "google": "GEMINI_API_KEY",
                    "groq": "GROQ_API_KEY"
                }
                
                key_name = key_names.get(self.llm_provider_name)
                if key_name:
                    api_key = key_manager.get_key(key_name)
            
            if api_key:
                # Initialize provider
                self.llm_provider = get_provider(self.llm_provider_name, api_key)
                
                if self.llm_provider:
                    # Test connection
                    if self.llm_provider.test_connection():
                        models = self.llm_provider.get_available_models()
                        self.print_success(f"✅ {self.llm_provider_name.upper()} provider initialized")
                        self.print_info(f"   📋 Available models: {', '.join(models[:3])}...")
                        
                        # Update model if not set
                        if not self.model or self.model == "qwen2.5-coder:7b":
                            # Use first available model as default
                            self.model = models[0] if models else "gpt-4"
                            self.print_info(f"   🎯 Using model: {self.model}")
                    else:
                        self.print_warning(f"⚠️  {self.llm_provider_name.upper()} connection test failed, falling back to Ollama")
                        self.llm_provider = None
                        self.llm_provider_name = "local"
                else:
                    self.print_warning(f"⚠️  Failed to initialize {self.llm_provider_name}, falling back to Ollama")
                    self.llm_provider_name = "local"
            else:
                self.print_warning(f"⚠️  No API key found for {self.llm_provider_name}, falling back to Ollama")
                self.llm_provider_name = "local"
                
        except Exception as e:
            self.print_error(f"❌ LLM provider initialization failed: {e}")
            self.print_info("   Falling back to local Ollama")
            self.llm_provider = None
            self.llm_provider_name = "local"
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.print_error(f"Failed to load config from {config_path}: {e}")
            sys.exit(1)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when no config file provided"""
        return {
            'project': {
                'name': 'Generic Project',
                'root': '.',
                'issue': ''
            },
            'model': {
                'name': 'qwen2.5-coder:7b',
                'ollama_url': 'http://localhost:11434'
            },
            'context': {
                'description': 'Generic software project',
                'structure': '- Standard project structure',
                'tech_stack': ['Python 3.12+'],
                'reference_services': []
            },
            'phases': {
                1: {
                    'name': 'Setup',
                    'hours': 2,
                    'tasks': ['Create project structure']
                }
            }
        }
    
    def load_project_docs(self) -> Dict[str, str]:
        """Load key project documentation files automatically
        
        Addresses Issue #1: Agent lacks access to project documentation
        Automatically reads critical docs from project root and docs/ folder.
        
        Returns:
            dict: Mapping of doc filename to content
        """
        docs = {}
        doc_candidates = [
            'ARCHITECTURE.md',
            'PORTS.md',
            'FEATURES.md',
            'SECURITY.md',
            'README.md',
            '.github/copilot-instructions.md',
            'docs/ARCHITECTURE.md',
            'docs/PORTS.md',
            'docs/FEATURES.md',
            'docs/CONVENTIONS.md',
            'docs/API.md'
        ]
        
        for doc_file in doc_candidates:
            doc_path = self.project_root / doc_file
            if doc_path.exists() and doc_path.is_file():
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    # Store with relative path as key
                    docs[doc_file] = content
                    self.print_info(f"Loaded documentation: {doc_file} ({len(content)} chars)")
                except Exception as e:
                    self.print_warning(f"Failed to read {doc_file}: {e}")
        
        if docs:
            self.print_success(f"Loaded {len(docs)} documentation file(s)")
        else:
            self.print_info("No documentation files found in project")
        
        return docs
    
    def prepare_task_context(self, task_description: str, phase_name: str) -> str:
        """
        Gather relevant workspace context before executing a task.
        
        This helps the agent understand existing code patterns and structure.
        
        Args:
            task_description: Description of the task to be executed
            phase_name: Name of the current phase
        
        Returns:
            Context string to inject into task prompt
        """
        context_parts = []
        
        # Keywords to detect task type
        task_lower = task_description.lower()
        
        # Service-related tasks
        if 'service' in task_lower or 'app/services' in task_lower:
            try:
                services = self.workspace.list_dir('app/services')
                if services:
                    context_parts.append(f"📁 Existing services: {', '.join(services)}")
                    
                    # Read structure from one example service
                    if services:
                        example_svc = services[0]
                        svc_files = self.workspace.find_files('*.py', f'app/services/{example_svc}')
                        if svc_files:
                            context_parts.append(f"   Example service structure ({example_svc}): {', '.join([Path(f).name for f in svc_files])}")
            except Exception as e:
                self.print_warning(f"Could not list services: {e}")
        
        # API/Backend tasks
        if 'api' in task_lower or 'endpoint' in task_lower or 'backend' in task_lower:
            try:
                # Look for controller patterns
                controllers = self.workspace.find_files('*controller*.py', 'app/backend')
                if controllers:
                    context_parts.append(f"🔌 Existing controllers: {', '.join([Path(f).name for f in controllers])}")
                
                # Check routes file
                if self.workspace.file_exists('app/backend/routes.py'):
                    context_parts.append("   Routes defined in: app/backend/routes.py")
            except Exception as e:
                self.print_warning(f"Could not analyze backend: {e}")
        
        # Database/Model tasks
        if 'model' in task_lower or 'database' in task_lower or 'schema' in task_lower:
            try:
                models = self.workspace.find_files('*model*.py', 'app/backend')
                if models:
                    context_parts.append(f"💾 Existing models: {', '.join([Path(f).name for f in models])}")
                
                if self.workspace.file_exists('app/backend/database.py'):
                    context_parts.append("   Database config: app/backend/database.py")
            except Exception as e:
                self.print_warning(f"Could not analyze models: {e}")
        
        # Docker/Container tasks
        if 'docker' in task_lower or 'container' in task_lower:
            try:
                dockerfiles = self.workspace.find_files('Dockerfile*', '.')
                if dockerfiles:
                    context_parts.append(f"🐳 Dockerfiles: {', '.join([Path(f).name for f in dockerfiles])}")
                
                if self.workspace.file_exists('docker-compose.yml'):
                    context_parts.append("   Compose file: docker-compose.yml")
            except Exception as e:
                self.print_warning(f"Could not analyze Docker files: {e}")
        
        if context_parts:
            return "\n🔍 WORKSPACE CONTEXT:\n" + "\n".join(context_parts) + "\n"
        else:
            return ""
    
    def print_header(self, text: str):
        """Print colored header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    # Monitoring helper methods
    def _log(self, level: str, message: str):
        """Add log entry to monitor if enabled"""
        if self.monitor:
            self.monitor.add_log(self.agent_id, level, message)
    
    def _update_status(self, status=None, task=None, issue=None, pr=None, progress=None, phase=None, error=None):
        """Update agent status in monitor if enabled"""
        if self.monitor:
            from .monitor_service import AgentStatus
            
            # Convert string status to enum if needed
            if isinstance(status, str):
                status_map = {
                    'idle': AgentStatus.IDLE,
                    'working': AgentStatus.WORKING,
                    'error': AgentStatus.ERROR,
                    'offline': AgentStatus.OFFLINE
                }
                status = status_map.get(status.lower(), AgentStatus.IDLE)
            
            self.monitor.update_agent_status(
                agent_id=self.agent_id,
                status=status,
                current_task=task,
                current_issue=issue,
                current_pr=pr,
                progress=progress,
                phase=phase,
                error_message=error
            )
    
    def _update_metrics(self, cpu=None, memory=None, api_calls=None, api_rate_limit=None):
        """Update agent metrics in monitor if enabled"""
        if self.monitor:
            self.monitor.update_agent_metrics(
                agent_id=self.agent_id,
                cpu_usage=cpu,
                memory_usage=memory,
                api_calls=api_calls,
                api_rate_limit_remaining=api_rate_limit
            )
    
    def query_qwen(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """
        Query Qwen2.5-Coder via Ollama API (using /api/chat endpoint).
        
        DEPRECATED: Use query_llm() instead for multi-provider support.
        This method is kept for backward compatibility.
        """
        return self.query_llm(prompt, system_prompt, stream)
    
    def query_llm(self, prompt: str, system_prompt: Optional[str] = None, 
                  stream: bool = False, model: Optional[str] = None) -> str:
        """
        Query LLM (OpenAI, Anthropic, Google, or local Ollama).
        
        Automatically uses configured provider:
        - OpenAI GPT-4/3.5 (if API key configured)
        - Anthropic Claude (if API key configured)
        - Google Gemini (if API key configured)
        - Ollama local models (fallback)
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt for context
            stream: Whether to stream response (only for Ollama)
            model: Optional model override
            
        Returns:
            str: Generated text response
        """
        model_to_use = model or self.model
        
        # Try commercial provider first
        if self.llm_provider_name != "local" and self.llm_provider:
            try:
                from engine.core.llm_providers import LLMMessage
                
                self.print_info(f"🌐 Querying {self.llm_provider_name.upper()}: {model_to_use}...")
                
                # Build messages
                messages = []
                if system_prompt:
                    messages.append(LLMMessage(role="system", content=system_prompt))
                messages.append(LLMMessage(role="user", content=prompt))
                
                # Call provider
                response = self.llm_provider.chat_completion(
                    messages=messages,
                    model=model_to_use,
                    temperature=0.7,
                    max_tokens=4096
                )
                
                self.print_success(f"✅ {self.llm_provider_name.upper()} response received ({response.usage.get('total_tokens', 0)} tokens)")
                
                # Log API usage if monitoring enabled
                if self.monitor:
                    self._update_metrics(api_calls=1)
                
                return response.content
                
            except Exception as e:
                self.print_error(f"❌ {self.llm_provider_name.upper()} error: {e}")
                self.print_info("   Falling back to Ollama...")
                # Fall through to Ollama
        
        # Use Ollama (local)
        self.print_info(f"🏠 Querying Ollama: {model_to_use}...")
        
        # Build messages array for chat API
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            self.print_info(f"Ollama chat URL: {self.ollama_url}/api/chat")
            self.print_info(f"Ollama payload roles: {[m['role'] for m in messages]}")
            response = requests.post(
                f"{self.ollama_url}/api/chat",  # Use /api/chat instead of /api/generate
                json={
                    "model": model_to_use,
                    "messages": messages,
                    "stream": stream
                },
                timeout=300  # 5 minute timeout for complex generations
            )
            self.print_info(f"Ollama response status: {response.status_code}")
            if response.status_code != 200:
                truncated_body = response.text[:500] if response.text else ""
                self.print_error(f"Ollama response body: {truncated_body}")
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                result = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            result += content
                            print(content, end='', flush=True)
                print()  # New line after streaming
                return result
            else:
                result = response.json()
                return result.get('message', {}).get('content', '')
        
        except requests.exceptions.RequestException as e:
            error_text = ""
            if hasattr(e, "response") and e.response is not None:
                error_text = e.response.text[:500]
                self.print_error(f"Ollama error body: {error_text}")
            self.print_error(f"Failed to query Qwen: {e}")
            return ""
    
    def execute_phase(self, phase_num: int, dry_run: bool = False) -> bool:
        """Execute a specific phase of Issue #7"""
        if phase_num not in self.phases:
            self.print_error(f"Invalid phase number: {phase_num}")
            return False
        
        phase = self.phases[phase_num]
        self.print_header(f"PHASE {phase_num}: {phase['name']} ({phase['hours']}h)")
        
        # Load project documentation (Issue #1 solution)
        project_docs = self.load_project_docs()
        
        # System prompt with project context
        context_config = self.config.get('context', {})
        conventions = context_config.get('conventions', {})
        
        # Build conventions section
        conventions_text = ""
        if conventions:
            conventions_text = "\n=== PROJECT CONVENTIONS (MUST FOLLOW) ===\n"
            for category, rules in conventions.items():
                conventions_text += f"\n{category.replace('_', ' ').title()}:\n"
                for rule in rules:
                    conventions_text += f"  • {rule}\n"
        
        # Build documentation section (Issue #1 solution)
        docs_text = ""
        if project_docs:
            docs_text = "\n=== PROJECT DOCUMENTATION ===\n"
            # Prioritize certain docs for system prompt
            priority_docs = ['ARCHITECTURE.md', 'docs/ARCHITECTURE.md', '.github/copilot-instructions.md']
            for doc_name in priority_docs:
                if doc_name in project_docs:
                    content = project_docs[doc_name]
                    # Truncate if too long (keep first 2000 chars)
                    if len(content) > 2000:
                        content = content[:2000] + "\n... (truncated)"
                    docs_text += f"\n--- {doc_name} ---\n{content}\n"
            
            # Add reference to other available docs
            other_docs = [d for d in project_docs.keys() if d not in priority_docs]
            if other_docs:
                docs_text += f"\nOther available documentation: {', '.join(other_docs)}\n"
        
        system_prompt = f"""You are an expert Python developer working on: {self.project_name}
{f"({self.project_issue})" if self.project_issue else ""}

Project located at: {self.project_root}

{context_config.get('description', '')}

Project structure:
{context_config.get('structure', '')}

Tech stack:
{chr(10).join('- ' + tech for tech in context_config.get('tech_stack', []))}

{f"Reference services/modules:" if context_config.get('reference_services') else ""}
{chr(10).join('- ' + ref for ref in context_config.get('reference_services', []))}
{conventions_text}
{docs_text}

You must generate COMPLETE, WORKING, PRODUCTION-READY code.
Include:
- All imports and dependencies
- Error handling and logging
- Type hints and docstrings
- Async/await patterns where appropriate
- Configuration management
Follow best practices and existing codebase patterns.
"""
        
        success_count = 0
        for i, task in enumerate(phase['tasks'], 1):
            print(f"\n{Colors.BOLD}Task {i}/{len(phase['tasks'])}: {task}{Colors.ENDC}")
            
            # Gather workspace context for this specific task
            workspace_context = self.prepare_task_context(task, phase['name'])
            if workspace_context:
                self.print_info("Workspace context gathered for task")
            
            # Get relevant historical context
            historical_context = self.context.get_relevant_context(task, max_tokens=1500)
            
            # Generate code for this task
            prompt = f"""Task: {task}

Phase: {phase['name']}
Context: {context_config.get('description', '')}
{workspace_context}
{historical_context}

Generate the complete code for this task. 

CRITICAL FORMAT REQUIREMENTS:
1. Start EVERY file with exactly: # File: <relative_path>
2. Use relative paths from project root: {self.project_root}
3. Include complete code with all imports
4. Add error handling and logging
5. Include type hints and docstrings

REQUIRED FORMAT (follow exactly):
```python
# File: path/to/file.py

<complete_code_here>
```

For requirements.txt or other non-Python files:
```
# File: path/to/requirements.txt

<content_here>
```

If multiple files needed, separate each with the # File: marker.

Example:
```python
# File: app/services/my-service/__init__.py

from .service import MyService
```

```python
# File: app/services/my-service/config.py

class Config:
    pass
```
"""
            
            if dry_run:
                self.print_info(f"[DRY RUN] Would execute: {task}")
                success_count += 1
                # Track in context manager (no code in dry-run)
                self.context.add_task_result(
                    task_description=task,
                    code_generated="[dry-run mode]",
                    success=True,
                    phase_name=phase['name']
                )
            else:
                # Query Qwen for implementation
                code = self.query_qwen(prompt, system_prompt=system_prompt)
                
                if code:
                    # Parse and save generated code
                    if self.save_generated_code(code):
                        self.print_success(f"Completed: {task}")
                        success_count += 1
                        # Track successful task
                        self.context.add_task_result(
                            task_description=task,
                            code_generated=code[:1000],  # First 1000 chars
                            success=True,
                            phase_name=phase['name']
                        )
                    else:
                        self.print_warning(f"Code generated but needs manual review: {task}")
                        # Track partial success
                        self.context.add_task_result(
                            task_description=task,
                            code_generated=code[:1000],
                            success=False,
                            phase_name=phase['name']
                        )
                else:
                    self.print_error(f"Failed to generate code for: {task}")
                    # Track failure
                    self.context.add_task_result(
                        task_description=task,
                        code_generated="",
                        success=False,
                        phase_name=phase['name']
                    )
            
            time.sleep(1)  # Brief pause between tasks
        
        # Phase summary
        print(f"\n{Colors.BOLD}Phase {phase_num} Summary:{Colors.ENDC}")
        print(f"  Completed: {success_count}/{len(phase['tasks'])} tasks")
        print(f"  Success rate: {(success_count/len(phase['tasks'])*100):.1f}%")
        
        # Log context metrics
        metrics = self.context.get_metrics()
        self.print_info(f"Context: {metrics['task_count']} tasks, {metrics['total_tokens']} tokens ({metrics['usage_percent']:.1f}%)")
        if metrics['truncation_events'] > 0:
            self.print_warning(f"Context truncation: {metrics['truncation_events']} events")
        
        return success_count == len(phase['tasks'])
    
    def save_generated_code(self, code: str) -> bool:
        """Parse and save generated code to appropriate files"""
        # Extract file paths and code blocks from response
        lines = code.split('\n')
        current_file = None
        current_code = []
        files_created = []
        in_code_block = False
        
        for line in lines:
            # Look for file path markers (various formats)
            if '# File:' in line or '#File:' in line or '# file:' in line:
                # Save previous file if any
                if current_file and current_code:
                    content = '\n'.join(current_code).strip()
                    if content:  # Only save if there's actual content
                        self.create_file(current_file, content)
                        files_created.append(current_file)
                
                # Start new file - extract path after "File:"
                file_marker = line.split('File:', 1)[-1].strip()
                current_file = file_marker
                current_code = []
                in_code_block = False
                continue
            
            # Handle code block markers
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Collect code lines if we're in a file
            if current_file:
                current_code.append(line)
        
        # Save last file
        if current_file and current_code:
            content = '\n'.join(current_code).strip()
            if content:
                self.create_file(current_file, content)
                files_created.append(current_file)
        
        if files_created:
            self.print_success(f"Created {len(files_created)} file(s):")
            for f in files_created:
                print(f"  - {f}")
            return True
        else:
            self.print_warning("No files extracted from generated code")
            # Save raw output for manual review
            review_file = Path.home() / "agent-forge" / "output_review.txt"
            try:
                review_file.parent.mkdir(parents=True, exist_ok=True)
                review_file.write_text(code)
                self.print_info(f"Raw output saved to: {review_file}")
                self.print_info("Check the output - LLM may not have used the correct # File: format")
            except Exception as e:
                self.print_error(f"Could not save raw output: {e}")
            return False
    
    def create_file(self, file_path: str, content: str) -> bool:
        """Create a file with given content"""
        # Resolve absolute path
        if not file_path.startswith('/'):
            full_path = self.project_root / file_path.lstrip('./')
        else:
            full_path = Path(file_path)
        
        try:
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content)
            self.print_success(f"Created: {full_path}")
            return True
        
        except Exception as e:
            self.print_error(f"Failed to create {full_path}: {e}")
            return False
    
    def run_tests_after_generation(self, test_paths: Optional[List[str]] = None) -> bool:
        """
        Run tests after code generation to validate implementation.
        
        Part of Issue #10 integration - automatic testing after code changes.
        
        Args:
            test_paths: Specific test files to run (None = all tests)
            
        Returns:
            True if tests pass, False if tests fail or testing disabled
        """
        # Check if testing is enabled in config
        testing_config = self.config.get('testing', {})
        if not testing_config.get('enabled', False):
            self.print_info("Testing disabled in config, skipping validation")
            return True
        
        self.print_info("Running tests to validate generated code...")
        
        try:
            results = self.test_runner.run_tests(test_paths=test_paths)
            
            if results['success']:
                self.print_success(f"✅ All tests passed ({results['passed']}/{results['tests_run']})")
                return True
            else:
                self.print_warning(f"⚠️  Some tests failed ({results['failed']}/{results['tests_run']})")
                
                # Add test failures to context for self-correction
                if results['failures']:
                    failure_context = "Test failures detected:\n"
                    for failure in results['failures']:
                        failure_context += self.test_runner.get_failure_context(failure)
                    
                    self.context.add_task_result(
                        task_description="Test execution after code generation",
                        code_generated=failure_context,
                        success=False,
                        phase_name="testing"
                    )
                
                return False
        
        except Exception as e:
            self.print_error(f"Error running tests: {e}")
            return False
    
    def execute_all_phases(self, dry_run: bool = False) -> Dict[int, bool]:
        """Execute all phases sequentially"""
        self.print_header(f"QWEN AGENT - {self.project_name.upper()}")
        self.print_info(f"Model: {self.model}")
        self.print_info(f"Ollama URL: {self.ollama_url}")
        self.print_info(f"Project root: {self.project_root}")
        self.print_info(f"Total phases: {len(self.phases)}")
        
        total_hours = sum(p.get('hours', 0) for p in self.phases.values())
        if total_hours > 0:
            self.print_info(f"Total estimated time: {total_hours} hours")
        
        if dry_run:
            self.print_warning("DRY RUN MODE - No files will be created")
        
        results = {}
        for phase_num in sorted(self.phases.keys()):
            success = self.execute_phase(phase_num, dry_run=dry_run)
            results[phase_num] = success
            
            if not success and not dry_run:
                self.print_warning(f"Phase {phase_num} had issues. Continue anyway? (y/n)")
                response = input().strip().lower()
                if response != 'y':
                    self.print_info("Stopping at user request")
                    break
        
        # Final summary
        self.print_header("FINAL SUMMARY")
        completed = sum(1 for success in results.values() if success)
        print(f"Phases completed: {completed}/{len(results)}")
        print(f"Success rate: {(completed/len(results)*100):.1f}%")
        
        return results
    
    def execute_custom_task(self, task_description: str, dry_run: bool = False) -> bool:
        """Execute a custom task not in the predefined phases"""
        self.print_header(f"CUSTOM TASK: {task_description}")
        
        context_config = self.config.get('context', {})
        system_prompt = f"""You are an expert developer working on: {self.project_name}
Project located at: {self.project_root}
{context_config.get('description', '')}
Generate complete, production-ready code following best practices."""
        
        prompt = f"""Task: {task_description}

Generate complete Python code for this task.
Format your response with file paths and complete code as shown in examples.
"""
        
        if dry_run:
            self.print_info("[DRY RUN] Would execute custom task")
            return True
        
        code = self.query_qwen(prompt, system_prompt=system_prompt, stream=True)
        return self.save_generated_code(code)
    
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if self.model in model_names:
                self.print_success(f"Ollama is running, {self.model} is available")
                return True
            else:
                self.print_error(f"Model {self.model} not found. Available: {model_names}")
                self.print_info(f"Pull model with: ollama pull {self.model}")
                return False
        
        except Exception as e:
            self.print_error(f"Ollama not accessible: {e}")
            self.print_info("Start Ollama with: sudo systemctl start ollama")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Qwen Agent - Generic autonomous coding agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use config file
  python3 agents/code_agent.py --config configs/caramba_personality_ai.yaml --phase 1 --dry-run
  
  # Override project root
  python3 agents/code_agent.py --config configs/my_project.yaml --project-root /path/to/project --phase 1
  
  # Execute all phases
  python3 agents/code_agent.py --config configs/my_project.yaml --phase all
  
  # Custom task
  python3 agents/code_agent.py --task "Add authentication middleware"
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--phase',
        type=str,
        help='Phase number to execute (1-N) or "all" for all phases'
    )
    
    parser.add_argument(
        '--task',
        type=str,
        help='Custom task description to execute'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Ollama model to use (overrides config)'
    )
    
    parser.add_argument(
        '--project-root',
        type=str,
        help='Project root directory (overrides config)'
    )
    
    parser.add_argument(
        '--enable-monitoring',
        action='store_true',
        help='Enable real-time monitoring dashboard integration'
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        help='Agent ID for monitoring (auto-generated if not specified)'
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = CodeAgent(
        config_path=args.config,
        model=args.model,
        project_root=args.project_root,
        enable_monitoring=args.enable_monitoring,
        agent_id=args.agent_id
    )
    
    # Check Ollama status
    if not agent.check_ollama_status():
        sys.exit(1)
    
    # Execute requested action
    if args.task:
        success = agent.execute_custom_task(args.task, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
    
    elif args.phase:
        if args.phase.lower() == 'all':
            results = agent.execute_all_phases(dry_run=args.dry_run)
            all_success = all(results.values())
            sys.exit(0 if all_success else 1)
        else:
            try:
                phase_num = int(args.phase)
                success = agent.execute_phase(phase_num, dry_run=args.dry_run)
                sys.exit(0 if success else 1)
            except ValueError:
                agent.print_error(f"Invalid phase: {args.phase}")
                sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
