#!/usr/bin/env python3
"""
Qwen2.5-Coder Agent for Caramba Issue #7 (Personality AI Service)

This agent autonomously implements the Personality AI service using
Qwen2.5-Coder via Ollama, following a structured 7-phase approach.

Author: Agent Forge
Target: Caramba AI Platform - Issue #7
Model: qwen2.5-coder:7b
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional
import time

try:
    import requests
except ImportError:
    print("ERROR: requests module not found. Install with: pip install -r requirements.txt")
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


class QwenCarambaAgent:
    """Agent for implementing Caramba Issue #7 using Qwen2.5-Coder"""
    
    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        ollama_url: str = "http://localhost:11434",
        project_root: str = "/home/flip/caramba"
    ):
        self.model = model
        self.ollama_url = ollama_url
        self.project_root = Path(project_root)
        self.service_root = self.project_root / "app" / "services" / "personality-ai"
        
        # Issue #7 implementation phases
        self.phases = {
            1: {
                "name": "Service Structure",
                "hours": 4,
                "tasks": [
                    "Create app/services/personality-ai/ directory structure",
                    "Create src/ subdirectory with modules",
                    "Set up __init__.py, config.py, service.py",
                    "Create requirements.txt with dependencies (langchain, sentence-transformers, faiss, etc.)"
                ]
            },
            2: {
                "name": "LLM Integration",
                "hours": 6,
                "tasks": [
                    "Integrate with Tars-AI backend (192.168.1.26:8001) as primary LLM",
                    "Implement fallback to Ollama (localhost:11434) if Tars-AI unavailable",
                    "Create LLM client with retry logic and timeout handling",
                    "Add connection testing and health checks"
                ]
            },
            3: {
                "name": "RAG Pipeline",
                "hours": 8,
                "tasks": [
                    "Build transcript ingestion from AudioTransfer voice training sessions",
                    "Implement vector embeddings using sentence-transformers",
                    "Set up vector database (FAISS or ChromaDB) for semantic search",
                    "Create semantic search for relevant context retrieval",
                    "Add document chunking and metadata management"
                ]
            },
            4: {
                "name": "Conversation Analysis",
                "hours": 4,
                "tasks": [
                    "Implement tone analyzer (sentiment, formality, emotion detection)",
                    "Build style extractor (vocabulary patterns, sentence structure)",
                    "Create conversation pattern recognition",
                    "Build personality profile data structure with scoring"
                ]
            },
            5: {
                "name": "Response Generator",
                "hours": 4,
                "tasks": [
                    "Implement prompt engineering for personality matching",
                    "Build response generator with RAG context injection",
                    "Add personality consistency scoring mechanism",
                    "Implement conversation turn management (>10 turns support)"
                ]
            },
            6: {
                "name": "REST API",
                "hours": 3,
                "tasks": [
                    "Create app/backend/api/personality_ai.py FastAPI router",
                    "Implement /api/personality/analyze endpoint (conversation analysis)",
                    "Implement /api/personality/generate endpoint (response generation)",
                    "Implement /api/personality/profile endpoint (personality profile CRUD)",
                    "Add streaming response support (Server-Sent Events or WebSocket)"
                ]
            },
            7: {
                "name": "Testing & Documentation",
                "hours": 3,
                "tasks": [
                    "Write unit tests for RAG pipeline components",
                    "Write integration tests for API endpoints",
                    "Document API in OpenAPI/Swagger spec",
                    "Create docs/services/personality-ai/README.md",
                    "Update CHANGELOG.md with [PERS] prefix entries"
                ]
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
        
        # System prompt with Caramba project context
        system_prompt = f"""You are an expert Python developer working on Issue #7 (Personality AI Service) 
of the Caramba AI platform. The project is located at {self.project_root}.

Project structure:
- app/services/ - Service modules (face_swap, voice-training, etc.)
- app/backend/api/ - FastAPI REST endpoints
- app/frontend/ - React/TypeScript frontend
- docs/ - Documentation

Tech stack:
- Backend: FastAPI, Python 3.12, async/await
- LLM: Tars-AI (192.168.1.26:8001) with Ollama fallback (localhost:11434)
- RAG: LangChain or LlamaIndex, sentence-transformers, FAISS or ChromaDB
- Database: PostgreSQL with Alembic migrations
- Testing: pytest with async support

Existing services for reference:
- app/services/face_swap/ - SadTalker and Wav2Lip integration
- app/services/voice-training/ - AudioTransfer with Opus compression

You must generate COMPLETE, WORKING, PRODUCTION-READY code.
Include:
- All imports and dependencies
- Error handling and logging
- Type hints and docstrings
- Async/await patterns where appropriate
- Configuration management
Follow Python best practices and the existing codebase patterns.
"""
        
        success_count = 0
        for i, task in enumerate(phase['tasks'], 1):
            print(f"\n{Colors.BOLD}Task {i}/{len(phase['tasks'])}: {task}{Colors.ENDC}")
            
            # Generate code for this task
            prompt = f"""Task: {task}

Phase: {phase['name']}
Context: Implementing Personality AI service with LLM integration, RAG pipeline, and conversation analysis.

Generate the complete Python code for this task. Include:
1. File path (relative to {self.project_root})
2. Complete code with all imports and dependencies
3. Error handling and logging
4. Type hints and docstrings
5. Any configuration or setup needed

Format your response as:
```python
# File: <file_path>

<complete_code>
```

If multiple files are needed, provide each one separately with the same format.
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
        
        for line in lines:
            # Look for file path markers
            if line.strip().startswith('# File:'):
                # Save previous file if any
                if current_file and current_code:
                    self.create_file(current_file, '\n'.join(current_code))
                    files_created.append(current_file)
                
                # Start new file
                current_file = line.split('# File:')[1].strip()
                current_code = []
            
            # Look for code blocks
            elif line.strip().startswith('```python'):
                continue
            elif line.strip() == '```':
                continue
            elif current_file:
                current_code.append(line)
        
        # Save last file
        if current_file and current_code:
            self.create_file(current_file, '\n'.join(current_code))
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
        self.print_header("QWEN AGENT - CARAMBA ISSUE #7 (PERSONALITY AI)")
        self.print_info(f"Model: {self.model}")
        self.print_info(f"Ollama URL: {self.ollama_url}")
        self.print_info(f"Project root: {self.project_root}")
        self.print_info(f"Total phases: {len(self.phases)}")
        self.print_info(f"Total estimated time: {sum(p['hours'] for p in self.phases.values())} hours")
        
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
        
        system_prompt = f"""You are an expert Python developer working on the Caramba AI platform.
Project located at: {self.project_root}
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
        description="Qwen2.5-Coder Agent for Caramba Issue #7 (Personality AI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run phase 1
  python3 agents/qwen_caramba_issue7.py --phase 1 --dry-run
  
  # Execute phase 1
  python3 agents/qwen_caramba_issue7.py --phase 1
  
  # Execute all phases
  python3 agents/qwen_caramba_issue7.py --phase all
  
  # Custom task
  python3 agents/qwen_caramba_issue7.py --task "Add caching to LLM client"
        """
    )
    
    parser.add_argument(
        '--phase',
        type=str,
        help='Phase number to execute (1-7) or "all" for all phases'
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
        default='qwen2.5-coder:7b',
        help='Ollama model to use (default: qwen2.5-coder:7b)'
    )
    
    parser.add_argument(
        '--project-root',
        type=str,
        default='/home/flip/caramba',
        help='Project root directory (default: /home/flip/caramba)'
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = QwenCarambaAgent(
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
