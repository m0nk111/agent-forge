"""
LLM-powered File Editor

Uses LLM to generate actual code changes based on task descriptions.
Inspired by Continue's edit/apply pattern.

Author: Agent Forge
Date: 2025-10-08
"""

import re
from typing import Dict, Optional, List
from pathlib import Path


class LLMFileEditor:
    """
    LLM-powered file editor that generates real code modifications.
    
    Uses a two-phase approach:
    1. LLM generates the modified code
    2. Apply the changes to the file
    """
    
    def __init__(self, agent):
        """
        Initialize LLM file editor.
        
        Args:
            agent: CodeAgent instance with LLM access
        """
        self.agent = agent
        self.project_root = agent.project_root
    
    def edit_file(self, file_path: str, instruction: str, context: Optional[str] = None) -> Dict:
        """
        Edit a file using LLM guidance.
        
        Args:
            file_path: Relative path to file from project root
            instruction: What to change (e.g., "Add version badge to README.md")
            context: Optional context about the change
            
        Returns:
            Dict with: success, file_path, changes_made, old_content, new_content
        """
        full_path = self.project_root / file_path
        
        # Read current file content (or empty for new files)
        if full_path.exists():
            old_content = full_path.read_text()
            is_new_file = False
        else:
            old_content = ""
            is_new_file = True
        
        print(f"      🤖 LLM generating {'new file' if is_new_file else 'changes'}: {file_path}")
        
        # Generate new content with LLM
        new_content = self._generate_file_content(
            file_path=file_path,
            old_content=old_content,
            instruction=instruction,
            context=context,
            is_new_file=is_new_file
        )
        
        if not new_content:
            return {
                'success': False,
                'error': 'LLM failed to generate content'
            }
        
        # Write the new content
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(new_content)
            
            print(f"      ✅ {'Created' if is_new_file else 'Modified'} {file_path}")
            print(f"         Old lines: {len(old_content.splitlines())}")
            print(f"         New lines: {len(new_content.splitlines())}")
            print(f"         Diff: {len(new_content.splitlines()) - len(old_content.splitlines()):+d} lines")
            
            return {
                'success': True,
                'file_path': file_path,
                'is_new_file': is_new_file,
                'old_content': old_content,
                'new_content': new_content,
                'changes_made': f"{'Created' if is_new_file else 'Modified'} {file_path}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to write file: {e}"
            }
    
    def _generate_file_content(
        self,
        file_path: str,
        old_content: str,
        instruction: str,
        context: Optional[str],
        is_new_file: bool
    ) -> Optional[str]:
        """
        Use LLM to generate new file content.
        
        Returns:
            New file content or None if failed
        """
        # Determine file language/extension
        ext = Path(file_path).suffix.lstrip('.')
        language = ext if ext else 'text'
        
        # Construct prompt based on whether it's a new file or edit
        if is_new_file:
            prompt = self._build_new_file_prompt(file_path, instruction, context, language)
        else:
            prompt = self._build_edit_prompt(file_path, old_content, instruction, context, language)
        
        # Call LLM using agent's query_qwen method
        try:
            response = self.agent.query_qwen(
                prompt=prompt,
                stream=False,
                system_prompt="You are an expert code editor. Generate precise, well-formatted code."
            )
            
            if not response:
                return None
            
            # Extract code from response (remove markdown code blocks if present)
            new_content = self._extract_code_from_response(response, language)
            
            return new_content
        except Exception as e:
            print(f"      ❌ LLM error: {e}")
            return None
    
    def _build_new_file_prompt(
        self,
        file_path: str,
        instruction: str,
        context: Optional[str],
        language: str
    ) -> str:
        """Build prompt for creating a new file."""
        prompt = f"""You are creating a new file: {file_path}

Task: {instruction}
"""
        if context:
            prompt += f"\nContext: {context}"
        
        prompt += f"""

Generate the complete content for this file. Output ONLY the file content, no explanations.
Do not wrap in code blocks. Just output the raw file content."""
        
        return prompt
    
    def _build_edit_prompt(
        self,
        file_path: str,
        old_content: str,
        instruction: str,
        context: Optional[str],
        language: str
    ) -> str:
        """Build prompt for editing an existing file."""
        # Truncate old content if too long
        max_lines = 200
        old_lines = old_content.split('\n')
        if len(old_lines) > max_lines:
            # Show beginning and end
            truncated_content = '\n'.join(old_lines[:max_lines//2]) + \
                              f'\n... ({len(old_lines) - max_lines} lines omitted) ...\n' + \
                              '\n'.join(old_lines[-max_lines//2:])
        else:
            truncated_content = old_content
        
        prompt = f"""You are editing the file: {file_path}

CURRENT FILE CONTENT:
```{language}
{truncated_content}
```

TASK: {instruction}
"""
        if context:
            prompt += f"\nCONTEXT: {context}"
        
        prompt += f"""

Generate the COMPLETE modified file content. Apply the requested changes to the original file.

IMPORTANT RULES:
1. Output the ENTIRE file with modifications applied
2. Do NOT use "... existing code ..." or placeholders
3. Do NOT wrap in markdown code blocks
4. Just output the complete raw file content
5. Maintain proper formatting and indentation
6. If the change is simple (like adding one line), just add it - don't rewrite everything

OUTPUT:"""
        
        return prompt
    
    def _extract_code_from_response(self, response: str, language: str) -> str:
        """
        Extract code from LLM response, removing markdown code blocks if present.
        
        Args:
            response: Raw LLM response
            language: Expected language (for code block detection)
            
        Returns:
            Clean code content
        """
        # Pattern 1: ```language\ncode\n```
        pattern1 = rf'```{language}\s*\n(.*?)\n```'
        match = re.search(pattern1, response, re.DOTALL)
        if match:
            return match.group(1)
        
        # Pattern 2: ```\ncode\n```
        pattern2 = r'```\s*\n(.*?)\n```'
        match = re.search(pattern2, response, re.DOTALL)
        if match:
            return match.group(1)
        
        # Pattern 3: No code blocks, return as-is but trim
        return response.strip()
    
    def add_line_to_file(self, file_path: str, line_content: str, position: str = "end") -> Dict:
        """
        Simple helper to add a line to a file.
        
        Args:
            file_path: Path to file
            line_content: Line to add
            position: "start", "end", or "after:PATTERN"
            
        Returns:
            Result dict
        """
        instruction = f"Add this line to the file: {line_content}"
        
        if position == "start":
            instruction += " at the beginning"
        elif position == "end":
            instruction += " at the end"
        elif position.startswith("after:"):
            pattern = position[6:]
            instruction += f" after the line containing '{pattern}'"
        
        return self.edit_file(file_path, instruction)
    
    def replace_in_file(self, file_path: str, old_text: str, new_text: str) -> Dict:
        """
        Simple helper to replace text in a file.
        
        Args:
            file_path: Path to file
            old_text: Text to find
            new_text: Replacement text
            
        Returns:
            Result dict
        """
        instruction = f"Replace '{old_text}' with '{new_text}'"
        return self.edit_file(file_path, instruction)
