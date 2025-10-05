"""
Instruction Parser Module

Parses .github/copilot-instructions.md files and extracts rules by category.
Supports both workspace-specific and global instruction files.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """Represents a single validation rule."""
    category: str
    name: str
    description: str
    pattern: Optional[str] = None
    severity: str = "error"  # error, warning, info
    auto_fixable: bool = False


@dataclass
class RuleCategory:
    """Group of related rules."""
    name: str
    description: str
    rules: List[Rule]


class InstructionParser:
    """
    Parses copilot-instructions.md files and extracts validation rules.
    
    Supports:
    - Project structure rules (file placement, directory organization)
    - Git standards (commit format, changelog requirements)
    - Documentation standards (language, formatting)
    - Code quality rules (debug logging, error handling)
    - Infrastructure standards (port/IP conventions)
    """
    
    # Rule categories to extract
    CATEGORIES = {
        'project_structure': [
            'root directory', 'file placement', 'directory organization',
            'narrow and deep', 'tree structure'
        ],
        'git_standards': [
            'commit message', 'commit format', 'changelog', 'git commit',
            'conventional commit'
        ],
        'documentation': [
            'language convention', 'documentation', 'english', 'markdown',
            'code comment'
        ],
        'code_quality': [
            'debug', 'logging', 'error handling', 'test coverage',
            'debug flag'
        ],
        'infrastructure': [
            'port', 'ip address', 'docker', 'network', 'port range'
        ]
    }
    
    def __init__(self, global_instructions: Optional[Path] = None):
        """
        Initialize parser.
        
        Args:
            global_instructions: Path to global copilot-instructions.md
        """
        self.global_instructions = global_instructions
        self.rules: Dict[str, List[Rule]] = {cat: [] for cat in self.CATEGORIES.keys()}
        
    def parse_file(self, file_path: Path) -> Dict[str, List[Rule]]:
        """
        Parse a copilot-instructions.md file.
        
        Args:
            file_path: Path to instructions file
            
        Returns:
            Dictionary mapping category names to lists of rules
        """
        if not file_path.exists():
            logger.warning(f"📄 Instructions file not found: {file_path}")
            return self.rules
            
        try:
            content = file_path.read_text(encoding='utf-8')
            logger.info(f"📖 Parsing instructions from {file_path}")
            
            # Parse different rule categories
            self._parse_project_structure_rules(content)
            self._parse_git_standards(content)
            self._parse_documentation_rules(content)
            self._parse_code_quality_rules(content)
            self._parse_infrastructure_rules(content)
            
            # Log summary
            total_rules = sum(len(rules) for rules in self.rules.values())
            logger.info(f"✅ Parsed {total_rules} rules from {file_path.name}")
            
            return self.rules
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")
            return self.rules
    
    def parse_workspace(self, workspace_path: Path) -> Dict[str, List[Rule]]:
        """
        Parse both global and workspace-specific instructions.
        
        Workspace-specific rules override global rules.
        
        Args:
            workspace_path: Path to workspace root
            
        Returns:
            Merged rules dictionary
        """
        # Parse global instructions first
        if self.global_instructions and self.global_instructions.exists():
            self.parse_file(self.global_instructions)
            
        # Parse workspace-specific instructions (override)
        workspace_instructions = workspace_path / ".github" / "copilot-instructions.md"
        if workspace_instructions.exists():
            workspace_rules = InstructionParser().parse_file(workspace_instructions)
            # Merge with priority to workspace rules
            for category, rules in workspace_rules.items():
                if rules:  # Only override if workspace has rules for this category
                    self.rules[category] = rules
                    
        return self.rules
    
    def _parse_project_structure_rules(self, content: str):
        """Extract project structure rules."""
        rules = []
        
        # Root Directory Rule
        if "root directory" in content.lower() or "narrow and deep" in content.lower():
            rules.append(Rule(
                category="project_structure",
                name="root_directory_rule",
                description="Files should be in subdirectories, not root (except README/CHANGELOG)",
                pattern=r"^[^/]+\.(py|js|ts|yaml|yml|json)$",
                severity="error",
                auto_fixable=False
            ))
            
        # External Code Protection
        if "external-code" in content.lower() or "external project" in content.lower():
            rules.append(Rule(
                category="project_structure",
                name="external_code_protection",
                description="Never commit or push inside external-code directories",
                pattern=r"(external-code|external_code)/",
                severity="error",
                auto_fixable=False
            ))
            
        self.rules['project_structure'].extend(rules)
        
    def _parse_git_standards(self, content: str):
        """Extract Git standards rules."""
        rules = []
        
        # Conventional Commits
        if "conventional commit" in content.lower() or "commit format" in content.lower():
            rules.append(Rule(
                category="git_standards",
                name="conventional_commits",
                description="Commit messages must follow conventional format: type(scope): description",
                pattern=r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{10,}",
                severity="error",
                auto_fixable=True
            ))
            
        # Changelog Requirement
        if "changelog" in content.lower() and "update" in content.lower():
            rules.append(Rule(
                category="git_standards",
                name="changelog_required",
                description="CHANGELOG.md must be updated for every change",
                severity="error",
                auto_fixable=True
            ))
            
        # File-Specific Commits
        if "file-specific" in content.lower() or "per-file commit" in content.lower():
            rules.append(Rule(
                category="git_standards",
                name="file_specific_commits",
                description="Commit messages should describe exact changes to specific files",
                severity="warning",
                auto_fixable=False
            ))
            
        self.rules['git_standards'].extend(rules)
        
    def _parse_documentation_rules(self, content: str):
        """Extract documentation rules."""
        rules = []
        
        # Language Convention
        if "english" in content.lower() and "documentation" in content.lower():
            rules.append(Rule(
                category="documentation",
                name="english_only",
                description="All documentation, code comments, and commits must be in English",
                severity="error",
                auto_fixable=False
            ))
            
        # Documentation Changelog
        if "docs_changelog" in content.lower() or "documentation changelog" in content.lower():
            rules.append(Rule(
                category="documentation",
                name="docs_changelog_required",
                description="DOCS_CHANGELOG.md must be updated for documentation changes",
                severity="warning",
                auto_fixable=True
            ))
            
        self.rules['documentation'].extend(rules)
        
    def _parse_code_quality_rules(self, content: str):
        """Extract code quality rules."""
        rules = []
        
        # Debug Logging
        if "debug" in content.lower() and ("emoji" in content.lower() or "logging" in content.lower()):
            rules.append(Rule(
                category="code_quality",
                name="debug_logging_required",
                description="Debug logging with emoji prefixes required",
                pattern=r'logger\.(debug|info|warning|error)\(["\'][\U0001F300-\U0001F9FF]',
                severity="warning",
                auto_fixable=True
            ))
            
        # Global DEBUG Flag
        if "global debug flag" in content.lower() or "debug flag" in content.lower():
            rules.append(Rule(
                category="code_quality",
                name="global_debug_flag",
                description="Services must implement global DEBUG flag",
                severity="warning",
                auto_fixable=False
            ))
            
        self.rules['code_quality'].extend(rules)
        
    def _parse_infrastructure_rules(self, content: str):
        """Extract infrastructure rules."""
        rules = []
        
        # Port Range Convention
        port_match = re.search(r'port[s]?\s+(\d+)-(\d+)', content.lower())
        if port_match:
            start, end = port_match.groups()
            rules.append(Rule(
                category="infrastructure",
                name="port_range",
                description=f"Services must use ports {start}-{end}",
                pattern=f"port.*({start}|{end}|[{start[0]}-{end[0]}]\\d{{3}})",
                severity="error",
                auto_fixable=False
            ))
            
        # IP Convention
        if "ip address" in content.lower() and "convention" in content.lower():
            rules.append(Rule(
                category="infrastructure",
                name="ip_conventions",
                description="IP addresses must follow documented conventions",
                severity="warning",
                auto_fixable=False
            ))
            
        self.rules['infrastructure'].extend(rules)
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Get all rules for a specific category."""
        return self.rules.get(category, [])
    
    def get_all_rules(self) -> List[Rule]:
        """Get all parsed rules."""
        all_rules = []
        for rules in self.rules.values():
            all_rules.extend(rules)
        return all_rules
    
    def find_applicable_rules(self, file_path: str, operation: str = "edit") -> List[Rule]:
        """
        Find rules applicable to a specific file and operation.
        
        Args:
            file_path: Path to file being operated on
            operation: Type of operation (create, edit, delete, commit)
            
        Returns:
            List of applicable rules
        """
        applicable = []
        
        # Check project structure rules
        if operation in ['create', 'edit']:
            for rule in self.rules['project_structure']:
                if rule.pattern and re.search(rule.pattern, file_path):
                    applicable.append(rule)
                    
        # Git standards apply to commits
        if operation == 'commit':
            applicable.extend(self.rules['git_standards'])
            
        # Documentation rules for doc files
        if any(ext in file_path for ext in ['.md', '.rst', '.txt']):
            applicable.extend(self.rules['documentation'])
            
        # Code quality for code files
        if any(ext in file_path for ext in ['.py', '.js', '.ts', '.java', '.go']):
            applicable.extend(self.rules['code_quality'])
            
        # Infrastructure for config files
        if any(name in file_path for name in ['docker', 'compose', 'nginx', 'systemd']):
            applicable.extend(self.rules['infrastructure'])
            
        return applicable
    
    def export_rules_yaml(self, output_path: Path):
        """
        Export parsed rules to YAML format.
        
        Args:
            output_path: Path to output YAML file
        """
        import yaml
        
        rules_dict = {}
        for category, rules in self.rules.items():
            rules_dict[category] = [
                {
                    'name': rule.name,
                    'description': rule.description,
                    'pattern': rule.pattern,
                    'severity': rule.severity,
                    'auto_fixable': rule.auto_fixable
                }
                for rule in rules
            ]
            
        with open(output_path, 'w') as f:
            yaml.dump(rules_dict, f, default_flow_style=False, sort_keys=False)
            
        logger.info(f"📝 Exported rules to {output_path}")


def main():
    """CLI for testing parser."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse Copilot instructions")
    parser.add_argument('file', type=Path, help="Path to copilot-instructions.md")
    parser.add_argument('--export', type=Path, help="Export rules to YAML")
    parser.add_argument('--verbose', action='store_true', help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Parse instructions
    instruction_parser = InstructionParser()
    rules = instruction_parser.parse_file(args.file)
    
    # Print summary
    print(f"\n📊 Parsed {args.file}")
    print("=" * 60)
    for category, category_rules in rules.items():
        if category_rules:
            print(f"\n{category.replace('_', ' ').title()}: {len(category_rules)} rules")
            for rule in category_rules:
                emoji = "🔴" if rule.severity == "error" else "🟡" if rule.severity == "warning" else "🔵"
                fix_emoji = "🔧" if rule.auto_fixable else ""
                print(f"  {emoji} {rule.name} {fix_emoji}")
                print(f"     {rule.description}")
    
    # Export if requested
    if args.export:
        instruction_parser.export_rules_yaml(args.export)
        print(f"\n✅ Rules exported to {args.export}")


if __name__ == "__main__":
    main()
