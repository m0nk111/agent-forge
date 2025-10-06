"""
Instruction Parser for Copilot Instructions.

Parses .github/copilot-instructions.md and extracts rules by category.
Supports workspace-specific and global instructions with rule merging.

Author: Agent Forge
Date: 2025-01-06
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Rule:
    """Represents a single rule from copilot instructions."""
    category: str
    name: str
    rule_text: str
    rationale: Optional[str] = None
    enforcement: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"Rule(category={self.category}, name={self.name})"


@dataclass
class InstructionSet:
    """Collection of parsed rules organized by category."""
    rules: Dict[str, List[Rule]] = field(default_factory=dict)
    source_file: Optional[str] = None
    
    def add_rule(self, rule: Rule):
        """Add a rule to the instruction set."""
        if rule.category not in self.rules:
            self.rules[rule.category] = []
        self.rules[rule.category].append(rule)
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Get all rules in a category."""
        return self.rules.get(category, [])
    
    def get_all_categories(self) -> Set[str]:
        """Get all rule categories."""
        return set(self.rules.keys())


class InstructionParser:
    """
    Parse Copilot instructions from markdown files.
    
    Extracts rules from .github/copilot-instructions.md and organizes them
    by category for validation purposes.
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize instruction parser.
        
        Args:
            project_root: Root directory of project (optional)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def parse_file(self, file_path: str) -> InstructionSet:
        """
        Parse a copilot-instructions.md file.
        
        Args:
            file_path: Path to instructions file (absolute or relative to project_root)
            
        Returns:
            InstructionSet with parsed rules
        """
        # Resolve file path
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        if not path.exists():
            raise FileNotFoundError(f"Instructions file not found: {path}")
        
        # Read file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse content
        instruction_set = InstructionSet(source_file=str(path))
        self._parse_content(content, instruction_set)
        
        return instruction_set
    
    def _parse_content(self, content: str, instruction_set: InstructionSet):
        """
        Parse markdown content and extract rules.
        
        Args:
            content: Markdown content
            instruction_set: InstructionSet to populate
        """
        lines = content.split('\n')
        current_category = None
        current_rule = None
        current_section = None
        
        for line in lines:
            # Detect category headers (## heading)
            category_match = re.match(r'^##\s+(.+)$', line)
            if category_match:
                # Save previous rule if exists
                if current_rule:
                    instruction_set.add_rule(current_rule)
                    current_rule = None
                
                current_category = category_match.group(1).strip()
                current_section = None
                continue
            
            # Detect rule headers (### heading)
            rule_match = re.match(r'^###\s+(.+)$', line)
            if rule_match and current_category:
                # Save previous rule if exists
                if current_rule:
                    instruction_set.add_rule(current_rule)
                
                # Start new rule
                rule_name = rule_match.group(1).strip()
                current_rule = Rule(
                    category=current_category,
                    name=rule_name,
                    rule_text=""
                )
                current_section = None
                continue
            
            # Detect subsections (- **Key**: Value)
            subsection_match = re.match(r'^\s*-\s+\*\*(.+?)\*\*:\s*(.+)$', line)
            if subsection_match and current_rule:
                key = subsection_match.group(1).strip().lower()
                value = subsection_match.group(2).strip()
                
                if key == 'rule':
                    current_rule.rule_text = value
                    current_section = 'rule'
                elif key == 'rationale':
                    current_rule.rationale = value
                    current_section = 'rationale'
                elif key == 'enforcement':
                    current_rule.enforcement = value
                    current_section = 'enforcement'
                elif key == 'example' or key == 'examples':
                    current_rule.examples.append(value)
                    current_section = 'examples'
                elif key == 'exception' or key == 'exceptions':
                    current_rule.exceptions.append(value)
                    current_section = 'exceptions'
                elif key == 'format':
                    # Format is part of rule text
                    current_rule.rule_text += f" Format: {value}"
                elif key == 'types' or key == 'range' or key == 'pattern':
                    # Add to rule text
                    current_rule.rule_text += f" {key.capitalize()}: {value}"
                
                continue
            
            # Continue previous section
            if line.strip() and current_rule and current_section:
                stripped = line.strip()
                if stripped.startswith('-'):
                    # List item
                    item = stripped[1:].strip()
                    if current_section == 'examples':
                        current_rule.examples.append(item)
                    elif current_section == 'exceptions':
                        current_rule.exceptions.append(item)
        
        # Save last rule
        if current_rule:
            instruction_set.add_rule(current_rule)
    
    def merge_instructions(
        self,
        global_path: Optional[str] = None,
        project_path: Optional[str] = None
    ) -> InstructionSet:
        """
        Merge global and project-specific instructions.
        
        Project-specific rules override global rules with same name.
        
        Args:
            global_path: Path to global instructions file
            project_path: Path to project-specific instructions file
            
        Returns:
            Merged InstructionSet
        """
        merged = InstructionSet()
        
        # Parse global instructions first
        if global_path:
            try:
                global_set = self.parse_file(global_path)
                for category, rules in global_set.rules.items():
                    for rule in rules:
                        merged.add_rule(rule)
            except FileNotFoundError:
                pass  # Global file optional
        
        # Parse project instructions (override global)
        if project_path:
            try:
                project_set = self.parse_file(project_path)
                for category, rules in project_set.rules.items():
                    # Replace global rules with same name
                    for rule in rules:
                        # Remove any global rule with same category+name
                        if category in merged.rules:
                            merged.rules[category] = [
                                r for r in merged.rules[category]
                                if r.name != rule.name
                            ]
                        merged.add_rule(rule)
            except FileNotFoundError:
                pass  # Project file optional
        
        return merged
    
    def get_default_instruction_paths(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get default paths for global and project instructions.
        
        Returns:
            Tuple of (global_path, project_path)
        """
        # Global instructions (in home directory or system location)
        global_path = None
        home_instructions = Path.home() / ".github" / "copilot-instructions.md"
        if home_instructions.exists():
            global_path = str(home_instructions)
        
        # Project instructions
        project_path = None
        project_instructions = self.project_root / ".github" / "copilot-instructions.md"
        if project_instructions.exists():
            project_path = str(project_instructions)
        
        return global_path, project_path


# Example usage
if __name__ == "__main__":
    parser = InstructionParser()
    
    # Parse project instructions
    global_path, project_path = parser.get_default_instruction_paths()
    
    if project_path:
        print(f"📖 Parsing instructions from: {project_path}")
        instructions = parser.parse_file(project_path)
        
        print(f"\n✅ Found {len(instructions.rules)} rule categories:\n")
        
        for category in instructions.get_all_categories():
            rules = instructions.get_rules_by_category(category)
            print(f"  📋 {category}: {len(rules)} rules")
            for rule in rules:
                print(f"     - {rule.name}")
                if rule.rule_text:
                    print(f"       Rule: {rule.rule_text[:80]}...")
    else:
        print("❌ No copilot-instructions.md found in .github/")
