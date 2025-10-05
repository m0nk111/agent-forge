"""
Tests for Instruction Parser

Tests parsing of copilot-instructions.md files and rule extraction.
"""

import pytest
from pathlib import Path
from agents.instruction_parser import InstructionParser, Rule


@pytest.fixture
def sample_instructions(tmp_path):
    """Create a sample copilot-instructions.md file."""
    content = """
# Copilot Instructions

## Root Directory Rule
Files should be in subdirectories, not root. Keep a narrow and deep tree structure.

## Git Commit Standards
- Use conventional commit format: type(scope): description
- Update CHANGELOG.md for every change
- File-specific commit messages describing exact changes

## Language Convention
All documentation, code comments, and commits must be in English.

## Debug Code Requirements
Debug logging with emoji prefixes required.
Services must implement global DEBUG flag.

## Port Management
Services must use ports 7000-7999 for this project.

## External Projects Policy
Never commit or push inside external-code directories.
"""
    
    instructions_file = tmp_path / "copilot-instructions.md"
    instructions_file.write_text(content)
    return instructions_file


@pytest.fixture
def parser():
    """Create InstructionParser instance."""
    return InstructionParser()


class TestInstructionParser:
    """Test InstructionParser class."""
    
    def test_parser_initialization(self, parser):
        """Test parser initializes with empty rules."""
        assert isinstance(parser.rules, dict)
        assert 'project_structure' in parser.rules
        assert 'git_standards' in parser.rules
        assert 'documentation' in parser.rules
        assert 'code_quality' in parser.rules
        assert 'infrastructure' in parser.rules
    
    def test_parse_file_success(self, parser, sample_instructions):
        """Test successful parsing of instructions file."""
        rules = parser.parse_file(sample_instructions)
        
        assert isinstance(rules, dict)
        # Should have extracted some rules
        total_rules = sum(len(r) for r in rules.values())
        assert total_rules > 0
    
    def test_parse_file_not_found(self, parser, tmp_path):
        """Test parsing non-existent file."""
        fake_file = tmp_path / "nonexistent.md"
        rules = parser.parse_file(fake_file)
        
        # Should return empty rules, not crash
        assert isinstance(rules, dict)
        total_rules = sum(len(r) for r in rules.values())
        assert total_rules == 0
    
    def test_parse_project_structure_rules(self, parser, sample_instructions):
        """Test extraction of project structure rules."""
        parser.parse_file(sample_instructions)
        rules = parser.get_rules_by_category('project_structure')
        
        # Should find root directory rule
        rule_names = [r.name for r in rules]
        assert 'root_directory_rule' in rule_names
        
        # Should find external code protection
        assert 'external_code_protection' in rule_names
    
    def test_parse_git_standards(self, parser, sample_instructions):
        """Test extraction of git standards."""
        parser.parse_file(sample_instructions)
        rules = parser.get_rules_by_category('git_standards')
        
        rule_names = [r.name for r in rules]
        assert 'conventional_commits' in rule_names
        assert 'changelog_required' in rule_names
        assert 'file_specific_commits' in rule_names
    
    def test_parse_documentation_rules(self, parser, sample_instructions):
        """Test extraction of documentation rules."""
        parser.parse_file(sample_instructions)
        rules = parser.get_rules_by_category('documentation')
        
        rule_names = [r.name for r in rules]
        assert 'english_only' in rule_names
    
    def test_parse_code_quality_rules(self, parser, sample_instructions):
        """Test extraction of code quality rules."""
        parser.parse_file(sample_instructions)
        rules = parser.get_rules_by_category('code_quality')
        
        rule_names = [r.name for r in rules]
        assert 'debug_logging_required' in rule_names
        assert 'global_debug_flag' in rule_names
    
    def test_parse_infrastructure_rules(self, parser, sample_instructions):
        """Test extraction of infrastructure rules."""
        parser.parse_file(sample_instructions)
        rules = parser.get_rules_by_category('infrastructure')
        
        rule_names = [r.name for r in rules]
        assert 'port_range' in rule_names
    
    def test_get_all_rules(self, parser, sample_instructions):
        """Test getting all parsed rules."""
        parser.parse_file(sample_instructions)
        all_rules = parser.get_all_rules()
        
        assert isinstance(all_rules, list)
        assert len(all_rules) > 0
        assert all(isinstance(r, Rule) for r in all_rules)
    
    def test_find_applicable_rules_create(self, parser, sample_instructions):
        """Test finding rules applicable to file creation."""
        parser.parse_file(sample_instructions)
        
        # Root Python file should trigger rules
        rules = parser.find_applicable_rules("test.py", "create")
        assert len(rules) > 0
        
        # Should include project structure rules
        categories = [r.category for r in rules]
        assert 'project_structure' in categories
    
    def test_find_applicable_rules_commit(self, parser, sample_instructions):
        """Test finding rules applicable to commits."""
        parser.parse_file(sample_instructions)
        
        rules = parser.find_applicable_rules("any_file.py", "commit")
        
        # Should include git standards
        categories = [r.category for r in rules]
        assert 'git_standards' in categories
    
    def test_find_applicable_rules_documentation(self, parser, sample_instructions):
        """Test finding rules for documentation files."""
        parser.parse_file(sample_instructions)
        
        rules = parser.find_applicable_rules("README.md", "edit")
        
        # Should include documentation rules
        categories = [r.category for r in rules]
        assert 'documentation' in categories
    
    def test_find_applicable_rules_infrastructure(self, parser, sample_instructions):
        """Test finding rules for infrastructure files."""
        parser.parse_file(sample_instructions)
        
        rules = parser.find_applicable_rules("docker-compose.yml", "edit")
        
        # Should include infrastructure rules
        categories = [r.category for r in rules]
        assert 'infrastructure' in categories
    
    def test_rule_severity_levels(self, parser, sample_instructions):
        """Test that rules have proper severity levels."""
        parser.parse_file(sample_instructions)
        all_rules = parser.get_all_rules()
        
        severities = {r.severity for r in all_rules}
        # Should have multiple severity levels
        assert severities.issubset({'error', 'warning', 'info'})
    
    def test_auto_fixable_flag(self, parser, sample_instructions):
        """Test that some rules are marked as auto-fixable."""
        parser.parse_file(sample_instructions)
        all_rules = parser.get_all_rules()
        
        auto_fixable = [r for r in all_rules if r.auto_fixable]
        # Should have at least one auto-fixable rule
        assert len(auto_fixable) > 0
    
    def test_rule_patterns(self, parser, sample_instructions):
        """Test that rules have regex patterns where appropriate."""
        parser.parse_file(sample_instructions)
        
        # Root directory rule should have pattern
        ps_rules = parser.get_rules_by_category('project_structure')
        root_rule = next(r for r in ps_rules if r.name == 'root_directory_rule')
        assert root_rule.pattern is not None
        
        # Conventional commits should have pattern
        git_rules = parser.get_rules_by_category('git_standards')
        commit_rule = next(r for r in git_rules if r.name == 'conventional_commits')
        assert commit_rule.pattern is not None
    
    def test_parse_workspace_merge(self, parser, tmp_path):
        """Test workspace-specific rules override global rules."""
        # Create global instructions
        global_instructions = tmp_path / "global.md"
        global_instructions.write_text("""
## Root Directory Rule
Files should be in subdirectories.
""")
        
        # Create workspace with different rules
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        workspace_github = workspace / ".github"
        workspace_github.mkdir()
        workspace_instructions = workspace_github / "copilot-instructions.md"
        workspace_instructions.write_text("""
## Root Directory Rule
Root files are allowed in this workspace.

## Custom Rule
This is workspace-specific.
""")
        
        # Parse with global instructions
        parser_with_global = InstructionParser(global_instructions)
        rules = parser_with_global.parse_workspace(workspace)
        
        # Workspace rules should override
        assert isinstance(rules, dict)
        total_rules = sum(len(r) for r in rules.values())
        assert total_rules > 0
    
    def test_export_rules_yaml(self, parser, sample_instructions, tmp_path):
        """Test exporting rules to YAML."""
        parser.parse_file(sample_instructions)
        
        output_file = tmp_path / "rules.yaml"
        parser.export_rules_yaml(output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert 'project_structure' in content
        assert 'git_standards' in content


class TestRule:
    """Test Rule dataclass."""
    
    def test_rule_creation(self):
        """Test creating Rule instance."""
        rule = Rule(
            category="test",
            name="test_rule",
            description="Test rule",
            pattern=r"test.*",
            severity="error",
            auto_fixable=True
        )
        
        assert rule.category == "test"
        assert rule.name == "test_rule"
        assert rule.description == "Test rule"
        assert rule.pattern == r"test.*"
        assert rule.severity == "error"
        assert rule.auto_fixable is True
    
    def test_rule_defaults(self):
        """Test Rule default values."""
        rule = Rule(
            category="test",
            name="test_rule",
            description="Test rule"
        )
        
        assert rule.pattern is None
        assert rule.severity == "error"
        assert rule.auto_fixable is False
