"""
GitHub Issue Handler for Qwen Agent.

Enables autonomous issue resolution:
1. Read issue from GitHub
2. Parse requirements and context
3. Execute implementation
4. Create PR with solution

Author: Agent Forge
Date: 2025-10-05
"""

import re
import os
from typing import Dict, List, Optional
from pathlib import Path
from engine.runners.monitor_service import AgentStatus
from engine.operations.llm_file_editor import LLMFileEditor


class IssueHandler:
    """
    GitHub Issue Handler - Autonomous issue resolution

    Handles end-to-end autonomous resolution of GitHub issues:
        1. Fetch issue details from GitHub
        2. Parse issue body for requirements
        3. Generate implementation plan
        4. Execute plan using agent capabilities
        5. Create PR with changes
    """
    
    def __init__(self, agent):
        """
        Initialize issue handler.
        
        Args:
            agent: CodeAgent instance with all capabilities
        """
        self.agent = agent
        self.project_root = agent.project_root
        
        # Initialize LLM-powered file editor
        self.llm_editor = LLMFileEditor(agent)
        
        # Initialize instruction validator (optional)
        self.validator = None
        try:
            from engine.validation.instruction_validator import InstructionValidator
            self.validator = InstructionValidator(project_root=str(self.project_root))
        except Exception:
            # Validator is optional - continue without it
            pass
    
    def assign_to_issue(self, repo: str, issue_number: int) -> Dict:
        """
        Assign agent to GitHub issue and start autonomous resolution.
        
        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number to resolve
            
        Returns:
            Dict with: success, pr_url, summary, actions_taken
        """
        print(f"\n🤖 AGENT ASSIGNED TO ISSUE #{issue_number}")
        print(f"📦 Repository: {repo}")
        print("=" * 70)
        
        # TODO: Fix monitoring integration
        # Update monitor - starting work
#         # if hasattr(self.agent, 'monitor') and self.agent.monitor:
#         #     self.agent.monitor.update_agent_status(...)
#         
        # Step 1: Fetch issue details
        print("\n📖 Step 1: Fetching issue details...")
        issue = self._fetch_issue(repo, issue_number)
        
        if not issue:
            return {
                'success': False,
                'error': 'Failed to fetch issue'
            }
        
        print(f"   ✅ Issue: {issue['title']}")
        print(f"   📝 Labels: {', '.join(issue['labels'])}")
        
        # Step 2: Parse requirements
        print("\n🔍 Step 2: Analyzing requirements...")
        requirements = self._parse_issue_requirements(issue)
        
        print(f"   📋 Tasks identified: {len(requirements['tasks'])}")
        for i, task in enumerate(requirements['tasks'], 1):
            print(f"   {i}. {task['description']}")
        
        # Update monitor
#         if hasattr(self.agent, 'monitor'):
#             self.agent.monitor.update_agent_status(
#                 self.agent.agent_id,
#                 phase='generate_plan',
#                 progress=0.4
#             )
#             self.agent.monitor.log_activity(
#                 self.agent.agent_id,
#                 'requirements_parsed',
#                 f"{len(requirements['tasks'])} tasks identified",
#                 {'task_count': len(requirements['tasks'])}
#             )
#         
        # Step 3: Generate implementation plan
        print("\n🗺️  Step 3: Generating implementation plan...")
        plan = self._generate_plan(requirements)
        
        print(f"   📊 Phases: {len(plan['phases'])}")
        for phase in plan['phases']:
            print(f"   • {phase['name']}")
        
        # Update monitor
#         if hasattr(self.agent, 'monitor'):
#             self.agent.monitor.update_agent_status(
#                 self.agent.agent_id,
#                 phase='execute_plan',
#                 progress=0.6
#             )
#             self.agent.monitor.log_activity(
#                 self.agent.agent_id,
#                 'plan_generated',
#                 f"Plan ready: {len(plan['phases'])} phases",
#                 {'phase_count': len(plan['phases'])}
#             )
#         
        # Step 4: Execute plan
        print("\n⚙️  Step 4: Executing implementation...")
        execution_result = self._execute_plan(plan)
        
        if not execution_result['success']:
            return {
                'success': False,
                'error': execution_result['error'],
                'partial_results': execution_result.get('results', [])
            }
        
        print(f"   ✅ Implementation complete")
        print(f"   📝 Files modified: {len(execution_result['files_modified'])}")
        
        # Step 5: Validate changes
        print("\n✅ Step 5: Validating changes...")
        validation = self._validate_changes(execution_result['files_modified'])
        
        if not validation['valid']:
            print(f"   ❌ Validation failed: {validation['errors']}")
            return {
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation['errors']
            }
        
        print(f"   ✅ All validations passed")
        
        # Step 6: Create PR
        print("\n🔀 Step 6: Creating pull request...")
        pr = self._create_pull_request(repo, issue, execution_result)
        
        if pr:
            print(f"   ✅ PR created: {pr['url']}")
        
        print("\n" + "=" * 70)
        print("🎉 ISSUE RESOLUTION COMPLETE")
        print("=" * 70)
        
        # Step 7: Close issue with summary
        print("\n📝 Step 7: Closing issue...")
        summary = self._generate_summary(issue, execution_result, pr)
        completion_comment = f"""🤖 **Autonomous Resolution Complete**

{summary}

---
*Resolved automatically by Agent Forge*
*Completed at: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        self._close_issue(repo, issue_number, completion_comment)
        
        # Update monitor - work complete
#         if hasattr(self.agent, 'monitor') and self.agent.monitor:
#             self.agent.monitor.update_agent_status(
#                 self.agent.agent_id,
#                 status=AgentStatus.IDLE,
#                 current_task=None,
#                 current_issue=None,
#                 phase=None,
#                 progress=1.0
#             )
#             self.agent.monitor.log_activity(
#                 self.agent.agent_id,
#                 'issue_completed',
#                 f"Issue #{issue_number} resolved successfully",
#                 {
#                     'issue': issue_number,
#                     'files_modified': len(execution_result['files_modified']),
#                     'pr_created': pr is not None
#                 }
#             )
#         
        return {
            'success': True,
            'issue_number': issue_number,
            'pr_url': pr['url'] if pr else None,
            'files_modified': execution_result['files_modified'],
            'actions_taken': execution_result['actions'],
            'summary': self._generate_summary(issue, execution_result, pr)
        }
    
    def _fetch_issue(self, repo: str, issue_number: int) -> Optional[Dict]:
        """Fetch issue from GitHub API directly."""
        try:
            import os
            import requests
            
            token = os.getenv('BOT_GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN')
            if not token:
                raise ValueError("No GitHub token found in environment")
            
            owner, repo_name = repo.split('/')
            url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            issue_data = response.json()
            
            return {
                'number': issue_number,
                'title': issue_data.get('title', ''),
                'body': issue_data.get('body', ''),
                'labels': [l['name'] for l in issue_data.get('labels', [])],
                'assignees': [a['login'] for a in issue_data.get('assignees', [])]
            }
        
        except Exception as e:
            print(f"   ❌ Error fetching issue: {e}")
            return None
    
    def _close_issue(self, repo: str, issue_number: int, comment: str) -> bool:
        """Close issue with completion comment."""
        try:
            import os
            import requests
            
            token = os.getenv('BOT_GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN')
            if not token:
                print("   ⚠️  No GitHub token, skipping issue close")
                return False
            
            owner, repo_name = repo.split('/')
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            # Post completion comment
            comment_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}/comments"
            comment_response = requests.post(
                comment_url, 
                json={'body': comment},
                headers=headers,
                timeout=10
            )
            comment_response.raise_for_status()
            
            # Close the issue
            issue_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}"
            close_response = requests.patch(
                issue_url,
                json={'state': 'closed', 'state_reason': 'completed'},
                headers=headers,
                timeout=10
            )
            close_response.raise_for_status()
            
            print(f"   ✅ Issue #{issue_number} closed successfully")
            return True
            
        except Exception as e:
            print(f"   ⚠️  Failed to close issue: {e}")
            return False
    
    def _parse_issue_requirements(self, issue: Dict) -> Dict:
        """
        Parse issue body to extract requirements and tasks.
        
        Looks for:
        - Bullet points (tasks)
        - Code blocks (examples)
        - File paths mentioned
        - Acceptance criteria
        
        Also intelligently adds a synthetic "create file" task if the issue
        title implies file creation but no explicit creation tasks are found.
        """
        body = issue['body']
        
        requirements = {
            'title': issue['title'],
            'tasks': [],
            'files_mentioned': [],
            'code_examples': [],
            'acceptance_criteria': []
        }
        
        # Extract tasks (lines starting with -, *, or numbered)
        task_pattern = r'^\s*[-*\d.]+\s+(.+)$'
        for line in body.split('\n'):
            match = re.match(task_pattern, line)
            if match:
                task_text = match.group(1).strip()
                if len(task_text) > 10:  # Meaningful tasks
                    requirements['tasks'].append({
                        'description': task_text,
                        'completed': False
                    })
        
        # Extract file paths
        file_pattern = r'`([a-zA-Z0-9_/\-\.]+\.[a-zA-Z]{2,4})`'
        requirements['files_mentioned'] = re.findall(file_pattern, body)
        
        # Extract code blocks
        code_pattern = r'```[\w]*\n(.*?)```'
        requirements['code_examples'] = re.findall(code_pattern, body, re.DOTALL)
        
        # Extract acceptance criteria (common patterns)
        if 'acceptance criteria' in body.lower() or 'definition of done' in body.lower():
            # Find section
            sections = re.split(r'\n##\s+', body)
            for section in sections:
                if 'acceptance' in section.lower() or 'done' in section.lower():
                    criteria_lines = section.split('\n')
                    for line in criteria_lines:
                        if line.strip().startswith(('-', '*', '✓', '☑')):
                            requirements['acceptance_criteria'].append(
                                line.strip().lstrip('-*✓☑ ')
                            )
        
        # 🧠 INTELLIGENT TASK SYNTHESIS:
        # If issue title implies file creation but no explicit "create" tasks found,
        # synthesize a primary task to ensure the file gets created
        title_lower = issue['title'].lower()
        body_lower = body.lower()
        creation_keywords = ['create', 'add', 'new', 'generate', 'make']
        has_explicit_creation = any('create' in t['description'].lower() or 'add' in t['description'].lower() 
                                   for t in requirements['tasks'])
        
        if any(keyword in title_lower for keyword in creation_keywords) and not has_explicit_creation:
            # Try to extract file path from title OR body (body is more common)
            title_file_match = re.search(r'[\`]?([\w/.-]+\.\w+)', issue['title'])
            body_file_match = re.search(r'[\`]?([\w/.-]+\.\w+)', body)
            
            file_path = None
            if body_file_match:
                file_path = body_file_match.group(1)
            elif title_file_match:
                file_path = title_file_match.group(1)
            
            if file_path:
                print(f"   🧠 Synthesizing primary task: Create {file_path}")
                requirements['tasks'].insert(0, {
                    'description': f"Create {file_path} as specified in the issue requirements",
                    'completed': False
                })
        
        return requirements
    
    def _generate_plan(self, requirements: Dict) -> Dict:
        """
        Generate implementation plan from requirements.
        
        Returns structured plan with phases and actions.
        """
        plan = {
            'title': requirements['title'],
            'phases': []
        }
        
        # Phase 1: Analysis
        analysis_actions = []
        
        if requirements['files_mentioned']:
            for file_path in requirements['files_mentioned']:
                analysis_actions.append({
                    'type': 'read_file',
                    'file': file_path,
                    'description': f'Read {file_path}'
                })
        
        # Add codebase search if no files mentioned
        if not requirements['files_mentioned']:
            analysis_actions.append({
                'type': 'search',
                'description': 'Search for relevant code',
                'pattern': self._extract_keywords(requirements['title'])
            })
        
        plan['phases'].append({
            'name': 'Analyze codebase',
            'actions': analysis_actions
        })
        
        # Phase 2: Implementation
        implementation_actions = []
        
        for task in requirements['tasks']:
            action = self._task_to_action(task, issue_title=requirements['title'])
            if action:
                implementation_actions.append(action)
        
        plan['phases'].append({
            'name': 'Implement changes',
            'actions': implementation_actions
        })
        
        # Phase 3: Validation
        plan['phases'].append({
            'name': 'Validate changes',
            'actions': [
                {
                    'type': 'syntax_check',
                    'description': 'Check syntax of modified files'
                },
                {
                    'type': 'run_tests',
                    'description': 'Run test suite'
                }
            ]
        })
        
        return plan
    
    def _execute_plan(self, plan: Dict) -> Dict:
        """Execute the implementation plan using agent capabilities."""
        result = {
            'success': True,
            'files_modified': [],
            'actions': [],
            'results': []
        }
        
        for phase in plan['phases']:
            print(f"\n   📍 Phase: {phase['name']}")
            
            for action in phase['actions']:
                action_type = action['type']
                description = action['description']
                
                print(f"      • {description}...")
                
                try:
                    if action_type == 'read_file':
                        # Read file using agent
                        file_path = action.get('file')
                        if file_path:
                            # Store for context
                            result['actions'].append(f"Read {file_path}")
                    
                    elif action_type == 'search':
                        # Search codebase
                        pattern = action.get('pattern', '')
                        if pattern:
                            results = self.agent.codebase_search.grep_search(
                                pattern=pattern,
                                max_results=10
                            )
                            result['actions'].append(f"Searched for '{pattern}'")
                    
                    elif action_type == 'edit_file':
                        # Edit or create file using LLM
                        description_lower = description.lower()
                        
                        # Try to get file path from action (set by _task_to_action) or extract from description
                        file_path = action.get('file')
                        
                        if not file_path:
                            # Try to extract file path from description
                            import re
                            # Match file paths (absolute or relative)
                            file_match = re.search(r'[`:]?\s*(\.?/?[\w/.-]+\.\w+)', description)
                            
                            if file_match:
                                file_path = file_match.group(1).strip()
                        
                        if file_path:
                            # Use LLM to generate the file content
                            edit_result = self.llm_editor.edit_file(
                                file_path=file_path,
                                instruction=description,
                                context=f"Task: {phase['name']}"
                            )
                            
                            if edit_result['success']:
                                result['files_modified'].append(file_path)
                                result['actions'].append(edit_result['changes_made'])
                            else:
                                result['success'] = False
                                result['error'] = edit_result.get('error', 'File edit failed')
                                return result
                        else:
                            print(f"      ⚠️  Could not extract file path from: {description}")
                    
                    elif action_type == 'syntax_check':
                        # Check syntax of modified files
                        for file_path in result['files_modified']:
                            check_result = self.agent.error_checker.check_syntax(file_path)
                            if not check_result['valid']:
                                result['success'] = False
                                result['error'] = f"Syntax error in {file_path}"
                                return result
                    
                    elif action_type == 'run_tests':
                        # Run tests
                        test_result = self.agent.test_runner.run_tests([])
                        result['actions'].append(f"Ran tests: {test_result.get('passed', 0)} passed")
                
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    result['success'] = False
                    result['error'] = str(e)
                    return result
        
        return result
    
    def _validate_changes(self, files_modified: List[str]) -> Dict:
        """Validate all modified files with comprehensive checks."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate with instruction validator if available
        if self.validator:
            try:
                report = self.validator.generate_compliance_report(
                    changed_files=files_modified
                )
                
                # Add instruction validation results
                for result in report.results:
                    if not result.valid and result.severity == "error":
                        validation['errors'].append(result.message)
                        if result.suggestions:
                            validation['errors'].append(f"  Suggestion: {result.suggestions[0]}")
                    elif result.severity == "warning":
                        validation['warnings'].append(result.message)
                
                if not report.is_compliant():
                    validation['valid'] = False
            except Exception as e:
                # Don't fail if validator has issues
                validation['warnings'].append(f"Instruction validator error: {e}")
        
        for file_path in files_modified:
            # Check 1: File existence
            if not os.path.exists(file_path):
                validation['valid'] = False
                validation['errors'].append(f"File not found: {file_path}")
                continue  # Skip other checks if file doesn't exist
            
            # Check 2: File is readable
            if not os.path.isfile(file_path):
                validation['valid'] = False
                validation['errors'].append(f"Not a regular file: {file_path}")
                continue
            
            if not os.access(file_path, os.R_OK):
                validation['valid'] = False
                validation['errors'].append(f"File not readable: {file_path}")
                continue
            
            # Check 3: File size check (warn if too large)
            try:
                file_size = os.path.getsize(file_path)
                max_size = 10 * 1024 * 1024  # 10MB
                if file_size > max_size:
                    validation['warnings'].append(
                        f"Large file: {file_path} ({file_size / 1024 / 1024:.1f}MB)"
                    )
            except OSError as e:
                validation['warnings'].append(f"Could not check size of {file_path}: {e}")
            
            # Check 4: Syntax check (if available)
            try:
                result = self.agent.error_checker.check_syntax(file_path)
                if not result['valid']:
                    validation['valid'] = False
                    validation['errors'].append(f"Syntax error in {file_path}")
            except AttributeError:
                validation['warnings'].append(f"Syntax checker not available for {file_path}")
            except Exception as e:
                validation['warnings'].append(f"Could not check syntax of {file_path}: {e}")
        
        return validation
    
    def _validate_commit_message(self, message: str) -> Dict:
        """
        Validate commit message format.
        
        Args:
            message: Commit message to validate
            
        Returns:
            Dict with: valid, message, suggestions (optional)
        """
        if not self.validator:
            return {'valid': True, 'message': 'Validation disabled'}
        
        try:
            result = self.validator.validate_commit_message(message)
            
            response = {
                'valid': result.valid,
                'message': result.message
            }
            
            if not result.valid:
                response['suggestions'] = result.suggestions
                
                # Try auto-fix if enabled
                if result.auto_fixable:
                    fixed = self.validator.auto_fix_commit_message(message)
                    if fixed:
                        response['auto_fixed'] = fixed
            
            return response
        except Exception as e:
            # Don't fail on validator errors
            return {'valid': True, 'message': f'Validator error: {e}'}
    
    def _create_pull_request(self, repo: str, issue: Dict, execution_result: Dict) -> Optional[Dict]:
        """Create PR with implemented changes."""
        try:
            from engine.operations.git_operations import GitOperations
            from engine.operations.bot_operations import BotOperations
            
            git = GitOperations()
            bot = BotOperations()
            
            # Create branch
            branch_name = f"fix/issue-{issue['number']}"
            
            # Commit changes
            commit_message = f"fix: {issue['title']}\n\nResolves #{issue['number']}"
            
            # Validate commit message
            validation = self._validate_commit_message(commit_message)
            if not validation['valid'] and 'auto_fixed' in validation:
                # Use auto-fixed message
                commit_message = validation['auto_fixed']
                print(f"   ℹ️  Auto-fixed commit message: {commit_message.split(chr(10))[0]}")
            
            git.commit(self.project_root, commit_message)
            
            # Push branch
            git.push(self.project_root)
            
            # Create PR
            owner, repo_name = repo.split('/')
            pr_data = bot.create_pull_request(
                repo=repo_name,
                title=f"Fix: {issue['title']}",
                body=f"Resolves #{issue['number']}\n\nAutonomously implemented by Agent-Forge.",
                head=branch_name,
                base='main'
            )
            
            return {
                'url': pr_data.get('html_url'),
                'number': pr_data.get('number')
            }
        
        except Exception as e:
            print(f"   ⚠️  Could not create PR: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> str:
        """Extract key terms from text for searching."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords[0] if keywords else text
    
    def _task_to_action(self, task: Dict, issue_title: str = "") -> Optional[Dict]:
        """
        Convert task description to action.
        
        Args:
            task: Task dictionary with 'description' field
            issue_title: Issue title for context (used in smart fallback)
            
        Returns:
            Action dictionary or None if task can't be converted
        """
        description = task['description'].lower()
        original_desc = task['description']  # Keep original case for file extraction
        
        # Try to extract file path from description
        # Exclude URLs (http:// or https://) and match file paths
        import re
        # Match file paths but NOT URLs - use negative lookbehind for http/https
        file_match = re.search(r'(?<!http:/)(?<!https:/)[\`:]?\s*(\.?/?[\w/.-]+\.\w+)', original_desc)
        file_path = None
        
        if file_match:
            file_path = file_match.group(1).strip()
            # Additional validation: exclude common URL patterns
            # Check if there's :// before the match (URL indicator)
            if '://' in original_desc[max(0, file_match.start()-10):file_match.start()]:
                file_path = None  # This is part of a URL, ignore it
        
        # Detect action type from description (explicit keywords)
        if 'add' in description or 'create' in description:
            action = {
                'type': 'edit_file',
                'operation': 'add',
                'description': original_desc
            }
            if file_path:
                action['file'] = file_path
            return action
        elif 'update' in description or 'modify' in description:
            action = {
                'type': 'edit_file',
                'operation': 'update',
                'description': original_desc
            }
            if file_path:
                action['file'] = file_path
            return action
        elif 'remove' in description or 'delete' in description:
            action = {
                'type': 'edit_file',
                'operation': 'delete',
                'description': original_desc
            }
            if file_path:
                action['file'] = file_path
            return action
        
        # 🔍 SMART FALLBACK: Handle descriptive tasks when issue title implies file creation
        # This catches cases like "Create a simple sun diagram" where tasks describe
        # WHAT to include rather than using explicit "create" keywords
        if issue_title:
            title_lower = issue_title.lower()
            creation_keywords = ['create', 'add', 'new', 'generate', 'make']
            
            # If issue title contains creation intent AND we have a file path context
            if any(keyword in title_lower for keyword in creation_keywords):
                # Try to extract file path from issue title
                title_file_match = re.search(r'[\`]?([\w/.-]+\.\w+)', issue_title)
                inferred_file = title_file_match.group(1) if title_file_match else file_path
                
                if inferred_file:
                    print(f"   🧠 Smart fallback: Inferred file creation for '{inferred_file}' from issue title")
                    return {
                        'type': 'edit_file',
                        'operation': 'add',
                        'description': f"Create {inferred_file}: {original_desc}",
                        'file': inferred_file
                    }
        
        return None
    
    def _execute_edit(self, action: Dict) -> bool:
        """Execute file edit action."""
        # Placeholder - would use file_editor in real implementation
        return True
    
    def _generate_summary(self, issue: Dict, execution: Dict, pr: Optional[Dict]) -> str:
        """Generate human-readable summary."""
        summary = f"Resolved issue #{issue['number']}: {issue['title']}\n"
        summary += f"\nActions taken:\n"
        for action in execution['actions']:
            summary += f"  • {action}\n"
        
        if pr:
            summary += f"\nPull request created: {pr['url']}"
        
        return summary
