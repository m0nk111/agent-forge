"""
PR Review Logic Module

Extracted review logic methods from PRReviewAgent for better modularity.
Handles static code analysis, test execution, and LLM-powered code review.
"""

import subprocess
import logging
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class ReviewLogic:
    """
    Review logic for pull requests.
    
    Performs static code analysis, test execution, and LLM-powered reviews.
    """
    
    def __init__(
        self,
        use_llm: bool = False,
        llm_model: str = "qwen2.5-coder:7b",
        ollama_url: str = "http://localhost:11434/api/generate"
    ):
        """
        Initialize review logic.
        
        Args:
            use_llm: Whether to use LLM for code review
            llm_model: LLM model to use for reviews
            ollama_url: Ollama API endpoint
        """
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.ollama_url = ollama_url
        
    def review_python_file(
        self,
        filename: str,
        patch: str,
        file_content: str,
        is_new_file: bool = False
    ) -> List[str]:
        """
        Perform static code review of a Python file.
        
        Checks for:
        - Large files (>500 lines)
        - Print statements
        - TODO/FIXME comments
        - Silent exception handlers
        - Missing docstrings on new functions
        
        Args:
            filename: Name of the file being reviewed
            patch: Git diff patch
            file_content: Full file content
            is_new_file: Whether this is a new file
        
        Returns:
            List of identified issues
        """
        issues = []
        
        try:
            # Check file size
            lines = file_content.split('\n')
            if len(lines) > 500:
                issues.append(f"⚠️ Large file ({len(lines)} lines). Consider breaking into smaller modules.")
            
            # Check for print statements
            if 'print(' in file_content:
                issues.append("⚠️ Contains print() statements. Use logging instead.")
            
            # Check for TODO/FIXME comments
            todos = [line for line in lines if 'TODO' in line or 'FIXME' in line]
            if todos:
                issues.append(f"ℹ️ Contains {len(todos)} TODO/FIXME comment(s). Consider addressing before merge.")
            
            # Check for exception handling issues
            silent_excepts = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped == 'pass' and i > 1:
                    prev_line = lines[i-2].strip()
                    if prev_line.startswith('except'):
                        silent_excepts.append(i)
            
            if silent_excepts:
                issues.append(f"⚠️ Silent exception handlers at line(s): {', '.join(map(str, silent_excepts))}")
            
            # For new files, check if functions have docstrings
            if is_new_file:
                func_lines = [i for i, line in enumerate(lines, 1) if line.strip().startswith('def ')]
                missing_docs = []
                for func_line in func_lines:
                    # Check if next non-empty line is a docstring
                    next_idx = func_line
                    while next_idx < len(lines) and not lines[next_idx].strip():
                        next_idx += 1
                    if next_idx < len(lines):
                        next_line = lines[next_idx].strip()
                        if not (next_line.startswith('"""') or next_line.startswith("'''")):
                            missing_docs.append(func_line)
                
                if missing_docs:
                    issues.append(f"ℹ️ Functions without docstrings at line(s): {', '.join(map(str, missing_docs))}")
            
            # If LLM review is enabled, get LLM feedback
            if self.use_llm:
                llm_issues = self.llm_review_file(filename, patch, file_content)
                issues.extend(llm_issues)
        
        except Exception as e:
            logger.error(f"❌ Error reviewing {filename}: {e}")
        
        return issues
    
    def run_tests(self, changed_files: List[str]) -> Dict[str, any]:
        """
        Run pytest on changed test files.
        
        Args:
            changed_files: List of changed file paths
        
        Returns:
            Dict with keys: passed (bool), failed (int), output (str)
        """
        # Find test files
        test_files = [f for f in changed_files if f.startswith('tests/') and f.endswith('.py')]
        
        if not test_files:
            return {"passed": True, "failed": 0, "output": "No test files changed."}
        
        try:
            logger.info(f"🧪 Running tests for {len(test_files)} file(s)...")
            
            # Run pytest
            result = subprocess.run(
                ['pytest', '-v'] + test_files,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            output = result.stdout + result.stderr
            
            # Parse output for failure count
            failed = 0
            if 'failed' in output.lower():
                # Try to extract failure count
                import re
                match = re.search(r'(\d+) failed', output)
                if match:
                    failed = int(match.group(1))
                else:
                    failed = 1  # At least one failure
            
            return {
                "passed": result.returncode == 0,
                "failed": failed,
                "output": output
            }
        
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Test execution timed out")
            return {"passed": False, "failed": 1, "output": "Tests timed out after 60 seconds"}
        except Exception as e:
            logger.error(f"❌ Test execution error: {e}")
            return {"passed": False, "failed": 1, "output": str(e)}
    
    def llm_review_file(
        self,
        filename: str,
        patch: str,
        file_content: Optional[str] = None
    ) -> List[str]:
        """
        Perform LLM-powered code review of a file.
        
        Args:
            filename: Name of the file being reviewed
            patch: Git diff patch
            file_content: Full file content (optional, for context)
        
        Returns:
            List of LLM-identified issues
        """
        if not self.use_llm:
            return []
        
        issues = []
        
        try:
            logger.info(f"🤖 LLM reviewing: {filename} (model: {self.llm_model})")
            
            # Prepare prompt
            prompt = f"""You are an expert code reviewer. Review this code change and provide specific, actionable feedback.

File: {filename}

Changes (git diff):
```
{patch[:2000]}  # Limit to prevent huge prompts
```

Analyze for:
1. Logic errors or bugs
2. Performance issues
3. Security vulnerabilities
4. Design pattern violations
5. Code maintainability concerns

Provide feedback in this format:
- [CRITICAL/WARNING/INFO] Issue description

Be concise. Only report real issues, not nitpicks."""

            # Query Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more focused reviews
                        "num_predict": 500   # Limit response length
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                llm_response = response.json().get('response', '').strip()
                
                if llm_response and len(llm_response) > 10:
                    # Parse LLM response into issues
                    lines = llm_response.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('-') and any(x in line.upper() for x in ['CRITICAL', 'WARNING', 'INFO']):
                            issues.append(f"🤖 LLM: {line.lstrip('-').strip()}")
                    
                    if not issues and llm_response:
                        # LLM found issues but not in expected format
                        issues.append(f"🤖 LLM feedback for {filename}: {llm_response[:200]}")
                    
                    logger.info(f"   Found {len(issues)} LLM-identified issue(s)")
            else:
                logger.warning(f"   LLM API error: status {response.status_code}")
        
        except requests.exceptions.Timeout:
            logger.warning(f"   LLM review timeout for {filename}")
        except Exception as e:
            logger.error(f"   LLM review error: {e}")
        
        return issues
