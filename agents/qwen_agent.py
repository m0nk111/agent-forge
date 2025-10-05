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


class QwenAgent:
    """Generic agent that uses Qwen2.5-Coder to implement projects from config"""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        model: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        project_root: Optional[str] = None
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
        
        # Project metadata
        self.project_name = self.config.get('project', {}).get('name', 'Unnamed Project')
        self.project_issue = self.config.get('project', {}).get('issue', '')
        
        # Phases from config
        self.phases = self.config.get('phases', {})
    
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
    
    def query_qwen(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """Query Qwen2.5-Coder via Ollama API"""
        self.print_info(f"Querying {self.model}...")
        
        # Build full prompt with system context
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": stream
                },
                timeout=300  # 5 minute timeout for complex generations
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                result = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            result += chunk['response']
                            print(chunk['response'], end='', flush=True)
                print()  # New line after streaming
                return result
            else:
                result = response.json()
                return result.get('response', '')
        
        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to query Qwen: {e}")
            return ""
    
    def execute_phase(self, phase_num: int, dry_run: bool = False) -> bool:
        """Execute a specific phase of Issue #7"""
        if phase_num not in self.phases:
            self.print_error(f"Invalid phase number: {phase_num}")
            return False
        
        phase = self.phases[phase_num]
        self.print_header(f"PHASE {phase_num}: {phase['name']} ({phase['hours']}h)")
        
        # System prompt with project context
        context_config = self.config.get('context', {})
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
            
            # Generate code for this task
            prompt = f"""Task: {task}

Phase: {phase['name']}
Context: {context_config.get('description', '')}

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
            else:
                # Query Qwen for implementation
                code = self.query_qwen(prompt, system_prompt=system_prompt)
                
                if code:
                    # Parse and save generated code
                    if self.save_generated_code(code):
                        self.print_success(f"Completed: {task}")
                        success_count += 1
                    else:
                        self.print_warning(f"Code generated but needs manual review: {task}")
                else:
                    self.print_error(f"Failed to generate code for: {task}")
            
            time.sleep(1)  # Brief pause between tasks
        
        # Phase summary
        print(f"\n{Colors.BOLD}Phase {phase_num} Summary:{Colors.ENDC}")
        print(f"  Completed: {success_count}/{len(phase['tasks'])} tasks")
        print(f"  Success rate: {(success_count/len(phase['tasks'])*100):.1f}%")
        
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
  python3 agents/qwen_agent.py --config configs/caramba_personality_ai.yaml --phase 1 --dry-run
  
  # Override project root
  python3 agents/qwen_agent.py --config configs/my_project.yaml --project-root /path/to/project --phase 1
  
  # Execute all phases
  python3 agents/qwen_agent.py --config configs/my_project.yaml --phase all
  
  # Custom task
  python3 agents/qwen_agent.py --task "Add authentication middleware"
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
    
    args = parser.parse_args()
    
    # Create agent
    agent = QwenAgent(
        config_path=args.config,
        model=args.model,
        project_root=args.project_root
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
