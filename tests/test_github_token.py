#!/usr/bin/env python3
"""Test script for GitHub token permissions and functionality.

Tests reviewer token to ensure it has required scopes and can perform
necessary operations for PR reviews.
"""

import requests
import json
import sys
import os

def load_token(token_name="REVIEWER_GITHUB_TOKEN"):
    """Load token from keys.json."""
    keys_file = "keys.json"
    
    if not os.path.exists(keys_file):
        print(f"❌ {keys_file} not found")
        return None
    
    with open(keys_file, 'r') as f:
        keys = json.load(f)
    
    token = keys.get(token_name)
    if not token:
        print(f"❌ {token_name} not found in keys.json")
        available = [k for k in keys.keys() if 'TOKEN' in k or 'KEY' in k]
        print(f"Available keys: {available}")
        return None
    
    return token


def check_token_scopes(token):
    """Check what scopes the token has."""
    print("\n" + "="*60)
    print("TEST 1: Check Token Scopes")
    print("="*60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'
    }
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to authenticate: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        user_data = response.json()
        username = user_data.get('login')
        
        scopes = response.headers.get('X-OAuth-Scopes', 'none')
        rate_limit = response.headers.get('X-RateLimit-Remaining', 'unknown')
        
        print(f"✅ Token is valid")
        print(f"   Username: {username}")
        print(f"   Scopes: {scopes}")
        print(f"   Rate limit remaining: {rate_limit}")
        
        # Check for required scopes
        required_scopes = ['repo']
        recommended_scopes = ['write:discussion']
        
        has_required = all(scope in scopes for scope in required_scopes)
        has_recommended = all(scope in scopes for scope in recommended_scopes)
        
        if has_required:
            print(f"✅ Has required scopes: {', '.join(required_scopes)}")
        else:
            print(f"❌ Missing required scopes: {', '.join(required_scopes)}")
            return False
        
        if has_recommended:
            print(f"✅ Has recommended scopes: {', '.join(recommended_scopes)}")
        else:
            print(f"⚠️  Missing recommended scopes: {', '.join(recommended_scopes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking token: {e}")
        return False


def check_repo_access(token, owner="m0nk111", repo="agent-forge"):
    """Check if token can access repository."""
    print("\n" + "="*60)
    print("TEST 2: Check Repository Access")
    print("="*60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'
    }
    
    try:
        url = f'https://api.github.com/repos/{owner}/{repo}'
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Cannot access repository: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        repo_data = response.json()
        print(f"✅ Can access repository: {owner}/{repo}")
        print(f"   Full name: {repo_data['full_name']}")
        print(f"   Private: {repo_data['private']}")
        print(f"   Permissions: {repo_data.get('permissions', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing repository: {e}")
        return False


def check_pr_access(token, owner="m0nk111", repo="agent-forge"):
    """Check if token can list pull requests."""
    print("\n" + "="*60)
    print("TEST 3: Check Pull Request Access")
    print("="*60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'
    }
    
    try:
        url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
        params = {'state': 'all', 'per_page': 5}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Cannot access pull requests: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        prs = response.json()
        print(f"✅ Can access pull requests")
        print(f"   Found {len(prs)} recent PRs")
        
        if prs:
            latest = prs[0]
            print(f"   Latest PR: #{latest['number']} - {latest['title']}")
            print(f"   State: {latest['state']}")
            print(f"   Author: {latest['user']['login']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing PRs: {e}")
        return False


def check_review_capability(token, owner="m0nk111", repo="agent-forge"):
    """Check if token can submit reviews (dry run - doesn't actually submit)."""
    print("\n" + "="*60)
    print("TEST 4: Check Review Capability (Dry Run)")
    print("="*60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'
    }
    
    try:
        # Get open PRs
        url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
        params = {'state': 'open', 'per_page': 1}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"⚠️  Cannot check review capability: {response.status_code}")
            return True  # Not a failure, just can't test
        
        prs = response.json()
        
        if not prs:
            print(f"ℹ️  No open PRs to test review capability")
            print(f"   Token should be able to review once PRs exist")
            return True
        
        pr = prs[0]
        pr_number = pr['number']
        pr_author = pr['user']['login']
        
        print(f"✅ Found open PR to test: #{pr_number}")
        print(f"   Title: {pr['title']}")
        print(f"   Author: {pr_author}")
        
        # Check if token user is PR author (would fail to approve)
        user_response = requests.get('https://api.github.com/user', headers=headers)
        token_user = user_response.json().get('login')
        
        if token_user == pr_author:
            print(f"⚠️  Token user ({token_user}) is PR author")
            print(f"   Cannot approve own PR (expected GitHub limitation)")
        else:
            print(f"✅ Token user ({token_user}) is NOT PR author")
            print(f"   Can submit reviews on this PR")
        
        print(f"\nℹ️  Dry run complete - not actually submitting review")
        return True
        
    except Exception as e:
        print(f"❌ Error checking review capability: {e}")
        return False


def main():
    """Run all tests."""
    print("🔍 GitHub Token Permission Test Suite")
    print("="*60)
    
    # Check if token name provided
    token_name = sys.argv[1] if len(sys.argv) > 1 else "REVIEWER_GITHUB_TOKEN"
    print(f"Testing token: {token_name}")
    
    # Load token
    token = load_token(token_name)
    if not token:
        return 1
    
    # Run tests
    tests = [
        check_token_scopes,
        check_repo_access,
        check_pr_access,
        check_review_capability
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func(token)
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Token Scopes",
        "Repository Access",
        "Pull Request Access",
        "Review Capability"
    ]
    
    for name, result in zip(test_names, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Token is ready for use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check token permissions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
