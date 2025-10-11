#!/usr/bin/env python3
"""Test script for Project Bootstrap Agent.

Tests repository creation, team setup, and project structure generation.
"""

import os
import sys
import json
import logging
import pytest
from engine.operations.bootstrap_coordinator import BootstrapCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def coordinator():
    """Create a BootstrapCoordinator instance for testing."""
    admin_token, bot_token = load_tokens()
    if not admin_token:
        pytest.skip("GitHub tokens not available")
    return BootstrapCoordinator(admin_token, bot_token)


def load_tokens():
    """Load GitHub tokens from keys.json."""
    keys_file = 'keys.json'
    
    if not os.path.exists(keys_file):
        logger.error(f"❌ {keys_file} not found")
        return None, None
    
    with open(keys_file, 'r') as f:
        keys = json.load(f)
    
    # Use BOT_GITHUB_TOKEN as admin token (m0nk111-post has admin rights)
    admin_token = keys.get('BOT_GITHUB_TOKEN')
    
    if not admin_token:
        logger.error("❌ BOT_GITHUB_TOKEN not found in keys.json")
        return None, None
    
    return admin_token, admin_token  # Same token for both


def test_list_templates(coordinator):
    """Test listing available templates."""
    logger.info("\n" + "="*60)
    logger.info("TEST: List Available Templates")
    logger.info("="*60)
    
    templates = coordinator.list_available_templates()
    
    logger.info(f"\n📋 Available Templates ({len(templates)}):")
    for template in templates:
        logger.info(f"  • {template['name']}: {template['description']}")
    
    return True


def test_structure_generation(coordinator):
    """Test project structure generation."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Generate Project Structure")
    logger.info("="*60)
    
    result = coordinator.structure_generator.generate_structure(
        template='python',
        project_name='test-bootstrap-project',
        description='A test project for bootstrap agent',
        owner='test-owner'
    )
    
    logger.info(f"\n✅ Generated {result['file_count']} files:")
    for file_path in sorted(result['data'].keys())[:10]:  # Show first 10
        logger.info(f"  • {file_path}")
    
    if result['file_count'] > 10:
        logger.info(f"  ... and {result['file_count'] - 10} more files")
    
    return True


def test_full_bootstrap(coordinator, dry_run=True):
    """Test complete repository bootstrap workflow."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Full Repository Bootstrap")
    logger.info("="*60)
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual repository will be created")
        logger.info("\nWould create repository with:")
        logger.info("  • Name: agent-forge-test-bootstrap")
        logger.info("  • Template: python")
        logger.info("  • Private: False")
        logger.info("  • Bot collaborators: m0nk111-post, m0nk111-qwen-agent")
        logger.info("  • Branch protection: Enabled (1 required review)")
        logger.info("\nSkipping actual creation in dry run mode.")
        return True
    
    # Confirm with user
    print("\n⚠️  This will create a REAL repository on GitHub!")
    print("Repository: agent-forge-test-bootstrap")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Aborted by user")
        return False
    
    try:
        # Define bot collaborators
        bot_collaborators = [
            {'username': 'm0nk111-post', 'permission': 'push'},
            {'username': 'm0nk111-qwen-agent', 'permission': 'push'}
        ]
        
        # Bootstrap repository
        result = coordinator.bootstrap_repository(
            name='agent-forge-test-bootstrap',
            description='Test repository created by Bootstrap Agent',
            template='python',
            private=False,
            organization=None,  # Create in user account
            bot_collaborators=bot_collaborators,
            enable_branch_protection=False,  # Disable for test
            required_reviews=1
        )
        
        logger.info("\n" + "="*60)
        logger.info("BOOTSTRAP RESULTS")
        logger.info("="*60)
        
        if result['repository']:
            logger.info(f"\n✅ Repository: {result['repository']['html_url']}")
            logger.info(f"   Owner: {result['repository']['owner']}")
            logger.info(f"   Branch: {result['repository']['default_branch']}")
        
        if result['team']:
            logger.info(f"\n✅ Team setup: {'Success' if result['team'] else 'Failed'}")
        
        logger.info(f"\n✅ Files created: {result['files']}")
        
        if result['protection']:
            logger.info(f"\n✅ Branch protection: Enabled")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Bootstrap failed: {e}")
        return False


def main():
    """Main test function."""
    logger.info("🚀 Project Bootstrap Agent Test Suite")
    logger.info("="*60)
    
    # Load tokens
    logger.info("\n📋 Loading GitHub tokens...")
    admin_token, bot_token = load_tokens()
    
    if not admin_token:
        logger.error("❌ Failed to load tokens")
        return 1
    
    logger.info("✅ Tokens loaded")
    
    # Initialize coordinator
    bot_tokens = {}
    if bot_token:
        bot_tokens['m0nk111-post'] = bot_token
    
    coordinator = BootstrapCoordinator(
        admin_token=admin_token,
        bot_tokens=bot_tokens
    )
    
    # Run tests
    tests = [
        ("List Templates", lambda: test_list_templates(coordinator)),
        ("Generate Structure", lambda: test_structure_generation(coordinator)),
        ("Full Bootstrap (DRY RUN)", lambda: test_full_bootstrap(coordinator, dry_run=True))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    # Ask about real creation
    if passed == total:
        logger.info("\n" + "="*60)
        print("\n🎉 All tests passed!")
        print("\nWould you like to test REAL repository creation?")
        response = input("This will create 'agent-forge-test-bootstrap' on GitHub (yes/no): ").strip().lower()
        
        if response == 'yes':
            test_full_bootstrap(coordinator, dry_run=False)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
