#!/usr/bin/env python3
"""
Repository Management CLI - Manage bot account access to repositories.

Usage:
    python scripts/manage_repos.py setup          # Invite & accept all
    python scripts/manage_repos.py invite         # Only invite bots
    python scripts/manage_repos.py accept         # Only accept invites
    python scripts/manage_repos.py verify         # Only verify access
    python scripts/manage_repos.py list           # List config
    python scripts/manage_repos.py setup --dry-run  # Show what would be done
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.operations.repo_manager import RepoManager


def cmd_list(manager: RepoManager):
    """List configured repositories and bot accounts."""
    print("\n" + "="*70)
    print("REPOSITORY MANAGEMENT CONFIGURATION")
    print("="*70)
    
    repos = manager.get_repositories()
    bots = manager.get_bot_accounts()
    
    print(f"\n📦 Repositories ({len(repos)}):")
    for repo in repos:
        print(f"   - {repo}")
    
    print(f"\n🤖 Bot Accounts ({len(bots)}):")
    for bot in bots:
        print(f"   - {bot}")
    
    print(f"\n📊 Total Operations:")
    print(f"   - Invitations needed: {len(repos) * len(bots)}")
    print()


def cmd_invite(manager: RepoManager, dry_run: bool = False):
    """Invite all bot accounts to all repositories."""
    repos = manager.get_repositories()
    bots = manager.get_bot_accounts()
    
    print(f"\n📤 Inviting {len(bots)} bots to {len(repos)} repositories...\n")
    
    if dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    
    invited = 0
    already_member = 0
    failed = 0
    
    for repo in repos:
        print(f"📦 {repo}")
        for bot in bots:
            if dry_run:
                print(f"   Would invite: {bot}")
            else:
                # Check if already member
                if manager.invite_bot_to_repo(repo, bot):
                    invited += 1
                    print(f"   ✅ {bot}")
                else:
                    failed += 1
                    print(f"   ❌ {bot}")
        print()
    
    if not dry_run:
        print("="*70)
        print(f"Summary:")
        print(f"  ✅ Invited/Already member: {invited}")
        print(f"  ❌ Failed: {failed}")
        print()


def cmd_accept(manager: RepoManager, dry_run: bool = False):
    """Accept all pending repository invitations for bot accounts."""
    bots = manager.get_bot_accounts()
    
    print(f"\n📥 Accepting invitations for {len(bots)} bot accounts...\n")
    
    if dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    
    total_accepted = 0
    
    for bot in bots:
        print(f"🤖 {bot}")
        if dry_run:
            print(f"   Would accept pending invitations")
        else:
            accepted = manager.accept_invitations(bot)
            total_accepted += accepted
            if accepted > 0:
                print(f"   ✅ Accepted {accepted} invitation(s)")
            else:
                print(f"   ✉️  No pending invitations")
        print()
    
    if not dry_run:
        print("="*70)
        print(f"Summary:")
        print(f"  ✅ Total accepted: {total_accepted}")
        print()


def cmd_verify(manager: RepoManager):
    """Verify bot account access to all repositories."""
    repos = manager.get_repositories()
    bots = manager.get_bot_accounts()
    
    print(f"\n✅ Verifying access for {len(bots)} bots to {len(repos)} repositories...\n")
    
    has_access = 0
    no_access = 0
    
    for repo in repos:
        print(f"📦 {repo}")
        for bot in bots:
            if manager.verify_access(repo, bot):
                has_access += 1
                print(f"   ✅ {bot}")
            else:
                no_access += 1
                print(f"   ❌ {bot}")
        print()
    
    print("="*70)
    print(f"Summary:")
    print(f"  ✅ Has access: {has_access}")
    print(f"  ❌ No access: {no_access}")
    print()
    
    if no_access > 0:
        print("⚠️  Some bots don't have access. Run 'setup' to fix.")
        return 1
    
    return 0


def cmd_setup(manager: RepoManager, dry_run: bool = False):
    """Complete setup: invite bots, accept invitations, verify access."""
    print("\n" + "="*70)
    print("REPOSITORY SETUP - COMPLETE FLOW")
    print("="*70)
    
    if dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
    
    # Run complete setup
    summary = manager.setup_all_repositories(dry_run=dry_run)
    
    # Print summary
    print("\n" + "="*70)
    print("SETUP SUMMARY")
    print("="*70)
    print(f"  Repositories: {summary['repos']}")
    print(f"  Bot Accounts: {summary['bots']}")
    print(f"  Total Operations: {summary['repos'] * summary['bots']}")
    print()
    print(f"  ✅ Invited/Already member: {summary['invited']}")
    print(f"  ✅ Invitations accepted: {summary['accepted']}")
    print(f"  ✅ Access verified: {summary['verified']}")
    print(f"  ❌ Failed: {summary['failed']}")
    print()
    
    if summary['failed'] > 0:
        print("⚠️  Some operations failed. Check logs above.")
        return 1
    
    print("🎉 All bot accounts have access to all repositories!")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Manage bot account access to repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete setup (invite + accept + verify)
  python scripts/manage_repos.py setup
  
  # Dry run (show what would happen)
  python scripts/manage_repos.py setup --dry-run
  
  # Only invite bots
  python scripts/manage_repos.py invite
  
  # Only accept pending invitations
  python scripts/manage_repos.py accept
  
  # Only verify access
  python scripts/manage_repos.py verify
  
  # List configuration
  python scripts/manage_repos.py list
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'invite', 'accept', 'verify', 'list'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )
    
    try:
        # Initialize manager
        manager = RepoManager()
        
        # Execute command
        if args.command == 'list':
            cmd_list(manager)
            return 0
        elif args.command == 'invite':
            cmd_invite(manager, dry_run=args.dry_run)
            return 0
        elif args.command == 'accept':
            cmd_accept(manager, dry_run=args.dry_run)
            return 0
        elif args.command == 'verify':
            return cmd_verify(manager)
        elif args.command == 'setup':
            return cmd_setup(manager, dry_run=args.dry_run)
        else:
            parser.print_help()
            return 1
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. secrets/agents/m0nk111.token exists (admin token)")
        print("  2. secrets/agents/*.token exist for each bot")
        print("  3. config/services/polling.yaml exists")
        return 1
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
