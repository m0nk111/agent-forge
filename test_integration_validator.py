"""
Integration test for instruction validation system.

Demonstrates the validation system working with IssueHandler, FileEditor, and GitOperations.
"""

import tempfile
import shutil
from pathlib import Path


def test_file_editor_integration():
    """Test FileEditor with instruction validation."""
    print("\n🧪 Testing FileEditor Integration")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        project_root = Path(tmpdir)
        
        # Create .github directory and instructions
        github_dir = project_root / ".github"
        github_dir.mkdir()
        (github_dir / "copilot-instructions.md").write_text("""
# Copilot Instructions

## Project Structure Conventions

### Root Directory Rule
- **Rule**: Only README.md, CHANGELOG.md, LICENSE allowed in root
- **Rationale**: Keep root clean
""")
        
        # Test FileEditor
        from agents.file_editor import FileEditor
        editor = FileEditor(str(project_root))
        
        # Create a file in subdirectory (should pass)
        test_file = project_root / "agents" / "test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("# Test file")
        
        print("\n1. Testing valid file location (agents/test.py):")
        success = editor.replace_in_file(
            "agents/test.py",
            "# Test file",
            "# Updated test file"
        )
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        # Try to create file in root (should warn but continue)
        root_file = project_root / "invalid.py"
        root_file.write_text("# Invalid location")
        
        print("\n2. Testing invalid file location (invalid.py in root):")
        success = editor.replace_in_file(
            "invalid.py",
            "# Invalid location",
            "# Updated"
        )
        print(f"   Result: {'⚠️  WARNED (blocked)' if not success else '✅ CONTINUED'}")


def test_git_operations_integration():
    """Test GitOperations with commit message validation."""
    print("\n🧪 Testing GitOperations Integration")
    print("=" * 60)
    
    import os
    os.environ['QWEN_GITHUB_TOKEN'] = 'dummy_token_for_testing'
    
    from agents.git_operations import GitOperations
    
    git = GitOperations()
    
    # Test commit message validation
    print("\n1. Testing valid commit message:")
    print("   Message: 'feat(validator): add instruction validation'")
    if git.validator:
        result = git.validator.validate_commit_message(
            "feat(validator): add instruction validation"
        )
        print(f"   Result: {'✅ VALID' if result.valid else '❌ INVALID'}")
    else:
        print("   ⚠️  Validator not available")
    
    print("\n2. Testing invalid commit message:")
    print("   Message: 'update files'")
    if git.validator:
        result = git.validator.validate_commit_message("update files")
        print(f"   Result: {'❌ INVALID' if not result.valid else '✅ VALID'}")
        if not result.valid and result.suggestions:
            print(f"   Suggestions: {result.suggestions[0]}")
        
        # Test auto-fix
        fixed = git.validator.auto_fix_commit_message("update files")
        if fixed:
            print(f"   Auto-fixed: {fixed}")
    else:
        print("   ⚠️  Validator not available")


def test_compliance_reporting():
    """Test compliance report generation."""
    print("\n🧪 Testing Compliance Reporting")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        project_root = Path(tmpdir)
        github_dir = project_root / ".github"
        github_dir.mkdir()
        (github_dir / "copilot-instructions.md").write_text("""
# Copilot Instructions

## Git Standards

### Commit Message Format
- **Rule**: Use conventional commits format
- **Format**: type(scope): description

## Documentation Standards

### CHANGELOG.md Requirements
- **Rule**: Every code change must have CHANGELOG.md entry
""")
        
        from agents.instruction_validator import InstructionValidator
        
        validator = InstructionValidator(
            str(github_dir / "copilot-instructions.md"),
            str(project_root)
        )
        
        # Generate report for changes
        print("\n1. Testing compliance report with violations:")
        report = validator.generate_compliance_report(
            changed_files=["agents/test.py", "agents/utils.py"],
            commit_message="update files"
        )
        
        print(f"   {report.get_summary()}")
        print(f"   - Passed: {report.passed}")
        print(f"   - Failed: {report.failed}")
        print(f"   - Warnings: {report.warnings}")
        
        if report.results:
            print("\n   Validation Results:")
            for result in report.results[:3]:  # Show first 3
                status = "✅" if result.valid else "❌"
                print(f"   {status} {result.rule_name}: {result.message}")
        
        # Test with proper commit message and changelog
        print("\n2. Testing compliance report without violations:")
        report = validator.generate_compliance_report(
            changed_files=["agents/validator.py", "CHANGELOG.md"],
            commit_message="feat(validator): add instruction validation system"
        )
        
        print(f"   {report.get_summary()}")


def test_auto_fix_capabilities():
    """Test auto-fix capabilities."""
    print("\n🧪 Testing Auto-Fix Capabilities")
    print("=" * 60)
    
    from agents.instruction_validator import InstructionValidator
    
    validator = InstructionValidator()
    
    # Test commit message auto-fix
    print("\n1. Commit message auto-fix:")
    original = "update validation logic"
    fixed = validator.auto_fix_commit_message(original)
    print(f"   Original: {original}")
    print(f"   Fixed:    {fixed}")
    
    # Test changelog generation
    print("\n2. Changelog entry generation:")
    entry = validator.generate_changelog_entry(
        "feat(validator): add port validation",
        ["agents/validator.py"]
    )
    print(f"   Generated entry:")
    for line in entry.split('\n')[:3]:
        print(f"   {line}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("INSTRUCTION VALIDATION INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_file_editor_integration()
    except Exception as e:
        print(f"\n❌ FileEditor test failed: {e}")
    
    try:
        test_git_operations_integration()
    except Exception as e:
        print(f"\n❌ GitOperations test failed: {e}")
    
    try:
        test_compliance_reporting()
    except Exception as e:
        print(f"\n❌ Compliance reporting test failed: {e}")
    
    try:
        test_auto_fix_capabilities()
    except Exception as e:
        print(f"\n❌ Auto-fix test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION TESTS COMPLETE")
    print("=" * 60 + "\n")
