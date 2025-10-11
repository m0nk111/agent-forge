#!/usr/bin/env python3
"""Test PR reviewer with real GitHub data."""

import asyncio
import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.operations.pr_reviewer import PRReviewer, ReviewCriteria
from engine.operations.github_api_helper import GitHubAPIHelper


async def main():
    """Test PR reviewer with real PR data."""
    
    # Load GitHub token
    keys = json.load(open('keys.json'))
    github_token = keys['BOT_GITHUB_TOKEN']
    
    # Initialize GitHub API
    github_api = GitHubAPIHelper(token=github_token)
    
    # PR to review
    repo = "m0nk111/agent-forge"
    owner, repo_name = repo.split('/')
    pr_number = 95
    
    print(f"🔍 Fetching PR #{pr_number} from {repo}...")
    
    # Fetch PR data
    pr_data = github_api.get_pull_request(owner, repo_name, pr_number)
    print(f"✅ PR Title: {pr_data['title']}")
    print(f"✅ Author: {pr_data['user']['login']}")
    print(f"✅ State: {pr_data['state']}")
    
    # Fetch PR files
    files = github_api.get_pr_files(owner, repo_name, pr_number)
    print(f"✅ Files changed: {len(files)}")
    for f in files:
        print(f"   - {f['filename']} (+{f['additions']} -{f['deletions']})")
    
    # Initialize reviewer
    reviewer = PRReviewer(
        github_username='m0nk111-reviewer-bot',  # Different username to avoid "own PR" skip
        criteria=ReviewCriteria(),
        llm_model="gpt-5-pro",  # Specify LLM model
        agent_id="reviewer-agent-test"  # Specify agent ID
    )
    
    print(f"\n🤖 Starting PR review...")
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    # Review PR
    should_approve, summary, comments = await reviewer.review_pr(
        repo=repo,
        pr_number=pr_number,
        pr_data=pr_data,
        files=files
    )
    
    print("\n" + "="*80)
    print(f"DEBUG: Summary type: {type(summary)}, len: {len(summary)}")
    print(f"DEBUG: Summary repr: {repr(summary[:200])}")
    print(summary)
    print("="*80)
    print(f"\n{'✅ APPROVE' if should_approve else '❌ REQUEST_CHANGES'}")
    print(f"💬 {len(comments)} comments generated")
    
    # Ask if we should post the review
    print("\n" + "="*80)
    response = input("Post this review to GitHub? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("📤 Posting review to GitHub...")
        result = github_api.submit_pr_review(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number,
            event='APPROVE' if should_approve else 'REQUEST_CHANGES',
            body=summary,
            commit_id=pr_data['head']['sha']
        )
        print(f"✅ Review posted: {result['html_url']}")
    else:
        print("❌ Review not posted (dry run)")


if __name__ == "__main__":
    asyncio.run(main())
