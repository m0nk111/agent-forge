#!/usr/bin/env python3
"""
Refactor polling_service.py to use GitHub REST API instead of gh CLI.
This script replaces all subprocess calls with requests-based API calls.
"""

import re

# Read the original file
with open('agents/polling_service.py', 'r') as f:
    content = f.read()

# 1. Replace subprocess import with requests
content = content.replace('import subprocess', 'import requests')

# 2. Add GitHubAPI helper class after IssueState dataclass
github_api_class = '''

class GitHubAPI:
    """Helper class for GitHub REST API calls."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str):
        """Initialize with GitHub token.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
    
    def get_issues(self, owner: str, repo: str, assignee: str, state: str = 'open', per_page: int = 100) -> list:
        """Get issues from a repository."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        params = {
            'assignee': assignee,
            'state': state,
            'per_page': per_page
        }
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> list:
        """Get comments for an issue."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        """Create a comment on an issue."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {'body': body}
        response = self.session.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
'''

# Insert after IssueState class
content = content.replace(
    '    completed_at: Optional[str] = None\n\n\nclass PollingService:',
    '    completed_at: Optional[str] = None\n' + github_api_class + '\n\nclass PollingService:'
)

# 3. Update __init__ to initialize GitHub API client
old_init = '''    def __init__(self, config: PollingConfig, monitor=None):
        """Initialize polling service.
        
        Args:
            config: Polling configuration
            monitor: Optional monitor service for status updates
        """
        self.config = config
        self.monitor = monitor
        self.state_file = Path(config.state_file)
        self.state: Dict[str, IssueState] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Load existing state
        self.load_state()'''

new_init = '''    def __init__(self, config: PollingConfig, monitor=None):
        """Initialize polling service.
        
        Args:
            config: Polling configuration
            monitor: Optional monitor service for status updates
        """
        self.config = config
        self.monitor = monitor
        self.state_file = Path(config.state_file)
        self.state: Dict[str, IssueState] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Initialize GitHub API client
        if not config.github_token:
            raise ValueError("GitHub token is required. Set BOT_GITHUB_TOKEN or GITHUB_TOKEN environment variable.")
        self.github_api = GitHubAPI(config.github_token)
        
        # Metrics tracking
        self.api_calls = 0
        
        # Load existing state
        self.load_state()'''

content = content.replace(old_init, new_init)

# 4. Replace check_assigned_issues method
old_check_assigned = '''    async def check_assigned_issues(self) -> List[Dict]:
        """Check for issues assigned to the bot.
        
        Returns:
            List of assigned issue dictionaries
        """
        logger.info("Checking for assigned issues...")
        all_issues = []
        
        for repo in self.config.repositories:
            # Use gh CLI to query issues
            cmd = [
                "gh", "issue", "list",
                "--repo", repo,
                "--assignee", self.config.github_username,
                "--state", "open",
                "--json", "number,title,labels,assignees,url,createdAt,updatedAt",
                "--limit", "100"
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                issues = json.loads(result.stdout)
                for issue in issues:
                    issue['repository'] = repo
                all_issues.extend(issues)
                
                logger.info(f"Found {len(issues)} assigned issues in {repo}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to query issues for {repo}: {e.stderr}")
            except Exception as e:
                logger.error(f"Error checking {repo}: {e}")
        
        return all_issues'''

new_check_assigned = '''    async def check_assigned_issues(self) -> List[Dict]:
        """Check for issues assigned to the bot.
        
        Returns:
            List of assigned issue dictionaries
        """
        logger.info("Checking for assigned issues...")
        all_issues = []
        max_retries = 3
        retry_delay = 2
        
        for repo in self.config.repositories:
            owner, repo_name = repo.split('/')
            
            for attempt in range(max_retries):
                try:
                    # Use GitHub REST API to query issues
                    issues = self.github_api.get_issues(
                        owner=owner,
                        repo=repo_name,
                        assignee=self.config.github_username,
                        state='open',
                        per_page=100
                    )
                    
                    # Increment API call counter
                    self.api_calls += 1
                    
                    # Transform API response to match expected format
                    for issue in issues:
                        issue['repository'] = repo
                        issue['createdAt'] = issue.get('created_at')
                        issue['updatedAt'] = issue.get('updated_at')
                    
                    all_issues.extend(issues)
                    logger.info(f"Found {len(issues)} assigned issues in {repo}")
                    break  # Success
                    
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout querying {repo} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries exceeded for {repo} (timeout)")
                        
                except requests.exceptions.HTTPError as e:
                    logger.error(f"HTTP error querying {repo}: {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                    if 'authentication' in str(e).lower() or 'token' in str(e).lower():
                        logger.error("Authentication error - skipping retries")
                        break
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries exceeded for {repo}")
                        
                except Exception as e:
                    logger.error(f"Error checking {repo}: {type(e).__name__}: {e} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries exceeded for {repo}")
        
        return all_issues'''

content = content.replace(old_check_assigned, new_check_assigned)

# 5. Replace is_issue_claimed method
old_is_claimed = '''    def is_issue_claimed(self, repo: str, issue_number: int) -> bool:
        """Check if an issue is already claimed by another agent.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if issue is claimed by another agent, False otherwise
        """
        try:
            # Query issue comments
            cmd = [
                "gh", "issue", "view", str(issue_number),
                "--repo", repo,
                "--json", "comments",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            comments = data.get('comments', [])
            
            # Check for agent claim comments
            now = datetime.utcnow()
            timeout = timedelta(minutes=self.config.claim_timeout_minutes)
            
            for comment in comments:
                body = comment.get('body', '')
                if '🤖 Agent' in body and 'started working on this issue' in body:
                    # Check timestamp
                    try:
                        created_at = datetime.fromisoformat(
                            comment['createdAt'].replace('Z', '+00:00')
                        )
                        if now - created_at.replace(tzinfo=None) < timeout:
                            logger.info(f"Issue {repo}#{issue_number} claimed by another agent")
                            return True
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Could not parse comment timestamp: {e}")
                        continue
            
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check claim status for {repo}#{issue_number}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error checking claim status for {repo}#{issue_number}: {e}")
            return False'''

new_is_claimed = '''    def is_issue_claimed(self, repo: str, issue_number: int) -> bool:
        """Check if an issue is already claimed by another agent.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if issue is claimed by another agent, False otherwise
        """
        try:
            owner, repo_name = repo.split('/')
            
            # Query issue comments using GitHub REST API
            comments = self.github_api.get_issue_comments(
                owner=owner,
                repo=repo_name,
                issue_number=issue_number
            )
            
            if not comments:
                return False
            
            # Check for agent claim comments
            now = datetime.utcnow()
            timeout = timedelta(minutes=self.config.claim_timeout_minutes)
            
            for comment in comments:
                body = comment.get('body', '')
                if '🤖 Agent' in body and 'started working on this issue' in body:
                    # Check timestamp
                    try:
                        created_at_str = comment.get('created_at', '')
                        created_at = datetime.fromisoformat(
                            created_at_str.replace('Z', '+00:00')
                        )
                        if now - created_at.replace(tzinfo=None) < timeout:
                            logger.info(f"Issue {repo}#{issue_number} claimed by another agent")
                            return True
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Could not parse comment timestamp: {type(e).__name__}: {e}")
                        continue
            
            return False
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout checking claim status for {repo}#{issue_number}")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error checking claim status for {repo}#{issue_number}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error checking claim status for {repo}#{issue_number}: {type(e).__name__}: {e}")
            return False'''

content = content.replace(old_is_claimed, new_is_claimed)

# 6. Replace claim_issue method
old_claim = '''    async def claim_issue(self, repo: str, issue_number: int) -> bool:
        """Claim an issue by adding a comment.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if issue was claimed successfully
        """
        try:
            comment = f"🤖 Agent **{self.config.github_username}** started working on this issue at {datetime.utcnow().isoformat()}Z"
            
            cmd = [
                "gh", "issue", "comment", str(issue_number),
                "--repo", repo,
                "--body", comment
            ]
            
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Claimed issue {repo}#{issue_number}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to claim {repo}#{issue_number}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error claiming {repo}#{issue_number}: {e}")
            return False'''

new_claim = '''    async def claim_issue(self, repo: str, issue_number: int) -> bool:
        """Claim an issue by adding a comment.
        
        Args:
            repo: Repository name (owner/repo)
            issue_number: Issue number
            
        Returns:
            True if issue was claimed successfully
        """
        max_retries = 3
        retry_delay = 2
        owner, repo_name = repo.split('/')
        
        for attempt in range(max_retries):
            try:
                comment = f"🤖 Agent **{self.config.github_username}** started working on this issue at {datetime.utcnow().isoformat()}Z"
                
                # Use GitHub REST API to create comment
                self.github_api.create_issue_comment(
                    owner=owner,
                    repo=repo_name,
                    issue_number=issue_number,
                    body=comment
                )
                
                logger.info(f"Claimed issue {repo}#{issue_number}")
                return True
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout claiming {repo}#{issue_number} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries exceeded claiming {repo}#{issue_number} (timeout)")
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error claiming {repo}#{issue_number}: {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries exceeded claiming {repo}#{issue_number}")
                    
            except Exception as e:
                logger.error(f"Unexpected error claiming {repo}#{issue_number}: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Max retries exceeded claiming {repo}#{issue_number} (unexpected error)")
        
        return False'''

content = content.replace(old_claim, new_claim)

# Write the refactored content
with open('agents/polling_service.py', 'w') as f:
    f.write(content)

print("✅ Successfully refactored polling_service.py")
print("   - Replaced subprocess with requests")
print("   - Added GitHubAPI helper class")
print("   - Refactored check_assigned_issues()")
print("   - Refactored is_issue_claimed()")
print("   - Refactored claim_issue()")
print("   - Added comprehensive error handling and retries")
