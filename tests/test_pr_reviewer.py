"""
Tests for PR Reviewer

Tests automated code review functionality.
"""

import pytest
from pathlib import Path
from datetime import datetime
from engine.operations.pr_reviewer import PRReviewer, ReviewComment, ReviewCriteria


@pytest.fixture
def reviewer():
    """Create PRReviewer instance."""
    return PRReviewer(
        github_username="test-bot",
        criteria=ReviewCriteria(
            check_code_quality=True,
            check_testing=True,
            check_documentation=True,
            check_security=True,
            require_changelog=True,
            strictness_level="normal"
        )
    )


@pytest.fixture
def sample_pr_data():
    """Sample PR metadata."""
    return {
        'title': 'feat: Add awesome feature',
        'body': 'This PR adds an awesome new feature with comprehensive tests and documentation.',
        'user': {'login': 'contributor'},
        'number': 42,
        'draft': False,
        'labels': []
    }


@pytest.fixture
def sample_file_with_issues():
    """Sample file with code issues."""
    return {
        'filename': 'agents/feature.py',
        'patch': '''@@ -0,0 +1,10 @@
+def process_data(data):
+    password = "hardcoded123"  # Bad!
+    print(data)  # Should use logging
+    try:
+        result = eval(data)  # Dangerous!
+    except:  # Bare except
+        pass
+    # TODO: Add error handling
+    very_long_line_that_exceeds_the_maximum_allowed_length_and_should_trigger_a_warning_about_line_length_issues_that_we_check = 1
+    return result
'''
    }


@pytest.fixture
def sample_file_clean():
    """Sample file with clean code."""
    return {
        'filename': 'agents/utils.py',
        'patch': '''@@ -0,0 +1,5 @@
+import logging
+
+def helper_function(value: str) -> str:
+    """Helper function with proper logging."""
+    logger.info(f"Processing {value}")
+    return value.strip()
'''
    }


class TestPRReviewer:
    """Test PRReviewer class."""
    
    def test_reviewer_initialization(self, reviewer):
        """Test reviewer initializes correctly."""
        assert reviewer.github_username == "test-bot"
        assert reviewer.criteria.check_code_quality is True
        assert reviewer.criteria.strictness_level == "normal"
        assert isinstance(reviewer.reviewed_prs, dict)
    
    @pytest.mark.asyncio
    async def test_review_pr_skip_own_pr(self, reviewer, sample_pr_data):
        """Test reviewer skips own PRs."""
        # Set PR author to self
        pr_data = sample_pr_data.copy()
        pr_data['user'] = {'login': 'test-bot'}
        
        should_approve, summary, comments = await reviewer.review_pr(
            repo="owner/repo",
            pr_number=42,
            pr_data=pr_data,
            files=[]
        )
        
        assert should_approve is True
        assert summary == ""
        assert len(comments) == 0
    
    @pytest.mark.asyncio
    async def test_review_pr_skip_review_tag(self, reviewer, sample_pr_data):
        """Test reviewer skips PRs with [skip-review] tag."""
        pr_data = sample_pr_data.copy()
        pr_data['body'] = "Description with [skip-review] tag"
        
        should_approve, summary, comments = await reviewer.review_pr(
            repo="owner/repo",
            pr_number=42,
            pr_data=pr_data,
            files=[]
        )
        
        assert should_approve is True
        assert summary == ""
    
    @pytest.mark.asyncio
    async def test_review_file_with_issues(self, reviewer, sample_file_with_issues):
        """Test reviewing file with code issues."""
        comments, score = await reviewer._review_file(sample_file_with_issues)
        
        # Should find multiple issues
        assert len(comments) > 0
        assert score < 1.0
        
        # Check specific issues found
        comment_bodies = [c.body for c in comments]
        assert any('credential' in body.lower() for body in comment_bodies)
        assert any('print' in body.lower() for body in comment_bodies)
        assert any('eval' in body.lower() for body in comment_bodies)
    
    @pytest.mark.asyncio
    async def test_review_file_clean_code(self, reviewer, sample_file_clean):
        """Test reviewing clean code."""
        comments, score = await reviewer._review_file(sample_file_clean)
        
        # Clean code should have high score
        assert score >= 0.8
        # May have suggestions but no errors
        errors = [c for c in comments if c.severity == 'error']
        assert len(errors) == 0
    
    def test_check_code_quality_hardcoded_credentials(self, reviewer):
        """Test detection of hardcoded credentials."""
        patch = '+    password = "secret123"'
        comments = reviewer._check_code_quality('test.py', patch)
        
        assert len(comments) > 0
        assert any('credential' in c.body.lower() for c in comments)
        assert any(c.severity == 'error' for c in comments)
    
    def test_check_code_quality_print_statements(self, reviewer):
        """Test detection of print statements."""
        patch = '+    print("debug info")'
        comments = reviewer._check_code_quality('test.py', patch)
        
        assert len(comments) > 0
        assert any('logging' in c.body.lower() for c in comments)
    
    def test_check_code_quality_long_lines(self, reviewer):
        """Test detection of long lines."""
        long_line = '+    ' + 'x' * 130
        comments = reviewer._check_code_quality('test.py', long_line)
        
        assert len(comments) > 0
        assert any('120 characters' in c.body for c in comments)
    
    def test_check_code_quality_bare_except(self, reviewer):
        """Test detection of bare except clauses."""
        patch = '+    except:'
        comments = reviewer._check_code_quality('test.py', patch)
        
        assert len(comments) > 0
        assert any('except:' in c.body for c in comments)
        assert any(c.severity == 'warning' for c in comments)
    
    def test_check_security_sql_injection(self, reviewer):
        """Test detection of SQL injection risks."""
        patch = '+    cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
        comments = reviewer._check_security('test.py', patch)
        
        assert len(comments) > 0
        assert any('sql injection' in c.body.lower() for c in comments)
        assert any(c.severity == 'error' for c in comments)
    
    def test_check_security_eval_usage(self, reviewer):
        """Test detection of eval() usage."""
        patch = '+    result = eval(user_input)'
        comments = reviewer._check_security('test.py', patch)
        
        assert len(comments) > 0
        assert any('eval' in c.body.lower() for c in comments)
        assert any(c.severity == 'error' for c in comments)
    
    def test_check_security_shell_true(self, reviewer):
        """Test detection of shell=True."""
        patch = '+    subprocess.run(cmd, shell=True)'
        comments = reviewer._check_security('test.py', patch)
        
        assert len(comments) > 0
        assert any('shell=true' in c.body.lower() for c in comments)
        assert any(c.severity == 'warning' for c in comments)
    
    def test_check_documentation_no_readme(self, reviewer):
        """Test documentation check when README not updated."""
        files = [
            {'filename': 'agents/feature.py', 'patch': '+code'},
            {'filename': 'agents/utils.py', 'patch': '+code'},
            {'filename': 'agents/helper.py', 'patch': '+code'},
            {'filename': 'agents/main.py', 'patch': '+code'}
        ]
        pr_data = {'title': 'feat: Add feature'}
        
        score = reviewer._check_documentation(files, pr_data)
        
        # Should have lower score due to missing README
        assert score < 1.0
    
    def test_check_documentation_with_readme(self, reviewer):
        """Test documentation check with README update."""
        files = [
            {'filename': 'agents/feature.py', 'patch': '+code'},
            {'filename': 'README.md', 'patch': '+docs'}
        ]
        pr_data = {'title': 'feat: Add feature'}
        
        score = reviewer._check_documentation(files, pr_data)
        
        # Should still penalize for missing CHANGELOG if required
        assert score >= 0.7
    
    def test_check_documentation_no_changelog(self, reviewer):
        """Test documentation check when CHANGELOG missing."""
        files = [
            {'filename': 'agents/feature.py', 'patch': '+code'},
            {'filename': 'tests/test_feature.py', 'patch': '+tests'}
        ]
        pr_data = {'title': 'feat: Add feature'}
        
        score = reviewer._check_documentation(files, pr_data)
        
        # Should penalize for missing CHANGELOG
        assert score < 0.8
    
    def test_check_testing_good_coverage(self, reviewer):
        """Test testing check with good coverage."""
        files = [
            {'filename': 'agents/feature.py', 'patch': '+code'},
            {'filename': 'tests/test_feature.py', 'patch': '+tests'}
        ]
        
        score = reviewer._check_testing(files)
        
        # 1:1 ratio should give high score
        assert score >= 0.8
    
    def test_check_testing_no_tests(self, reviewer):
        """Test testing check with no tests."""
        files = [
            {'filename': 'agents/feature.py', 'patch': '+code'},
            {'filename': 'agents/utils.py', 'patch': '+code'}
        ]
        
        score = reviewer._check_testing(files)
        
        # No tests should give low score
        assert score < 0.6
    
    def test_check_testing_partial_coverage(self, reviewer):
        """Test testing check with partial coverage."""
        files = [
            {'filename': 'agents/feature1.py', 'patch': '+code'},
            {'filename': 'agents/feature2.py', 'patch': '+code'},
            {'filename': 'tests/test_feature1.py', 'patch': '+tests'}
        ]
        
        score = reviewer._check_testing(files)
        
        # 50% coverage
        assert 0.6 <= score <= 0.9
    
    def test_should_approve_strict_mode(self, reviewer):
        """Test approval decision in strict mode."""
        reviewer.criteria.strictness_level = 'strict'
        
        # No issues, high score
        assert reviewer._should_approve(0.85, [], True) is True
        
        # One warning, high score
        comments = [ReviewComment('test.py', 1, 'RIGHT', 'Warning', 'warning')]
        assert reviewer._should_approve(0.85, comments, True) is False
        
        # Low score
        assert reviewer._should_approve(0.7, [], True) is False
    
    def test_should_approve_normal_mode(self, reviewer):
        """Test approval decision in normal mode."""
        reviewer.criteria.strictness_level = 'normal'
        
        # No errors, good score
        assert reviewer._should_approve(0.7, [], True) is True
        
        # Warnings allowed
        comments = [ReviewComment('test.py', 1, 'RIGHT', 'Warning', 'warning')]
        assert reviewer._should_approve(0.7, comments, True) is True
        
        # Errors not allowed
        comments = [ReviewComment('test.py', 1, 'RIGHT', 'Error', 'error')]
        assert reviewer._should_approve(0.7, comments, True) is False
    
    def test_should_approve_relaxed_mode(self, reviewer):
        """Test approval decision in relaxed mode."""
        reviewer.criteria.strictness_level = 'relaxed'
        
        # Allow 1 error
        comments = [ReviewComment('test.py', 1, 'RIGHT', 'Error', 'error')]
        assert reviewer._should_approve(0.6, comments, True) is True
        
        # Too many errors
        comments = [
            ReviewComment('test.py', 1, 'RIGHT', 'Error', 'error'),
            ReviewComment('test.py', 2, 'RIGHT', 'Error', 'error')
        ]
        assert reviewer._should_approve(0.6, comments, True) is False
    
    @pytest.mark.asyncio
    async def test_generate_review_summary(self, reviewer, sample_pr_data):
        """Test review summary generation."""
        files = [{'filename': 'test.py', 'patch': '+code'}]
        comments = [
            ReviewComment('test.py', 1, 'RIGHT', 'Error', 'error'),
            ReviewComment('test.py', 2, 'RIGHT', 'Warning', 'warning'),
            ReviewComment('test.py', 3, 'RIGHT', 'Suggestion', 'suggestion')
        ]
        scores = {
            'code_quality': 0.7,
            'documentation': 0.8,
            'testing': 0.6,
            'overall': 0.7
        }
        
        summary = reviewer._generate_review_summary(
            pr_data=sample_pr_data,
            files=files,
            comments=comments,
            scores=scores,
            changelog_present=True,
            should_approve=False
        )
        
        assert 'Automated Code Review' in summary
        assert 'Quality Scores' in summary
        assert 'Critical Issues' in summary
        assert 'Warnings' in summary
        assert 'Suggestions' in summary
        assert 'CHANGES REQUESTED' in summary
    
    def test_load_criteria_from_yaml(self, tmp_path):
        """Test loading review criteria from YAML."""
        config_file = tmp_path / "criteria.yaml"
        config_file.write_text("""
check_code_quality: false
check_testing: true
strictness_level: "strict"
min_test_coverage: 90
""")
        
        criteria = PRReviewer.load_criteria_from_yaml(config_file)
        
        assert criteria.check_code_quality is False
        assert criteria.check_testing is True
        assert criteria.strictness_level == "strict"
        assert criteria.min_test_coverage == 90


class TestReviewComment:
    """Test ReviewComment dataclass."""
    
    def test_review_comment_creation(self):
        """Test creating ReviewComment."""
        comment = ReviewComment(
            path="test.py",
            line=42,
            side="RIGHT",
            body="This is a comment",
            severity="warning"
        )
        
        assert comment.path == "test.py"
        assert comment.line == 42
        assert comment.side == "RIGHT"
        assert comment.body == "This is a comment"
        assert comment.severity == "warning"
    
    def test_review_comment_defaults(self):
        """Test ReviewComment default values."""
        comment = ReviewComment(
            path="test.py",
            line=1
        )
        
        assert comment.side == "RIGHT"
        assert comment.body == ""
        assert comment.severity == "suggestion"


class TestReviewCriteria:
    """Test ReviewCriteria dataclass."""
    
    def test_criteria_creation(self):
        """Test creating ReviewCriteria."""
        criteria = ReviewCriteria(
            check_code_quality=False,
            check_testing=True,
            check_documentation=True,
            check_security=False,
            require_changelog=False,
            min_test_coverage=70,
            strictness_level="relaxed"
        )
        
        assert criteria.check_code_quality is False
        assert criteria.check_testing is True
        assert criteria.min_test_coverage == 70
        assert criteria.strictness_level == "relaxed"
    
    def test_criteria_defaults(self):
        """Test ReviewCriteria default values."""
        criteria = ReviewCriteria()
        
        assert criteria.check_code_quality is True
        assert criteria.check_testing is True
        assert criteria.check_documentation is True
        assert criteria.check_security is True
        assert criteria.require_changelog is True
        assert criteria.min_test_coverage == 80
        assert criteria.strictness_level == "normal"


# ==================== LLM INTEGRATION TESTS ====================

class TestLLMReviewIntegration:
    """Test LLM-powered code review."""
    
    @pytest.mark.asyncio
    async def test_generate_review_prompt(self, reviewer):
        """Test review prompt generation."""
        filename = "engine/test.py"
        patch = "+def hello():\n+    return 'world'"
        
        prompt = reviewer._generate_review_prompt(filename, patch)
        
        # Check prompt contains key sections
        assert filename in prompt
        assert patch in prompt
        assert "Python" in prompt  # Language detection
        assert "Logic & Correctness" in prompt
        assert "Security" in prompt
        assert "Performance" in prompt
    
    def test_guess_language(self, reviewer):
        """Test language detection from file extension."""
        assert reviewer._guess_language('.py') == 'Python'
        assert reviewer._guess_language('.js') == 'JavaScript'
        assert reviewer._guess_language('.ts') == 'TypeScript'
        assert reviewer._guess_language('.go') == 'Go'
        assert reviewer._guess_language('.rs') == 'Rust'
        assert reviewer._guess_language('.unknown') == 'code'
    
    @pytest.mark.asyncio
    async def test_llm_review_file_no_agent(self, reviewer):
        """Test LLM review gracefully handles missing agent."""
        # Reviewer has no llm_agent configured
        comments = await reviewer._llm_review_file('test.py', '+print("hello")')
        
        assert comments == []  # Should return empty list, not crash
    
    @pytest.mark.asyncio
    async def test_llm_review_with_mock_agent(self):
        """Test LLM review with mock agent."""
        class MockLLMAgent:
            async def generate(self, prompt):
                return """
                Line 5: Consider using logging instead of print() for better debugging.
                Line 12: This loop could be optimized using list comprehension.
                """
        
        reviewer = PRReviewer(
            github_username="test-bot",
            llm_agent=MockLLMAgent()
        )
        
        patch = "+print('test')\n+for x in range(10):\n+    result.append(x*2)"
        comments = await reviewer._llm_review_file('test.py', patch)
        
        # Should parse LLM response into comments
        assert len(comments) == 2
        assert comments[0].line == 5
        assert "logging" in comments[0].body
        assert comments[1].line == 12
        assert "comprehension" in comments[1].body


# ==================== GITHUB POSTING TESTS ====================

class TestGitHubReviewPosting:
    """Test posting reviews to GitHub."""
    
    @pytest.mark.asyncio
    async def test_post_review_no_api_client(self, reviewer):
        """Test posting review gracefully handles missing API client."""
        # Reviewer has no github_api configured
        result = await reviewer.post_review_to_github(
            repo="owner/repo",
            pr_number=42,
            should_approve=True,
            summary="Looks good!",
            comments=[]
        )
        
        assert result is False  # Should return False, not crash
    
    @pytest.mark.asyncio
    async def test_post_review_with_mock_api(self):
        """Test posting review with mock GitHub API."""
        class MockGitHubAPI:
            def __init__(self):
                self.posted_reviews = []
            
            def get_pull_request(self, owner, repo, pr_number):
                return {
                    'head': {'sha': 'abc123def456'}
                }
            
            def create_pull_request_review(self, owner, repo, pr_number, body, event, comments):
                self.posted_reviews.append({
                    'repo': f"{owner}/{repo}",
                    'pr_number': pr_number,
                    'body': body,
                    'event': event,
                    'comments': comments
                })
        
        mock_api = MockGitHubAPI()
        reviewer = PRReviewer(
            github_username="test-bot",
            github_api=mock_api
        )
        
        comments = [
            ReviewComment(
                path='test.py',
                line=10,
                body='Good improvement!',
                severity='suggestion'
            )
        ]
        
        result = await reviewer.post_review_to_github(
            repo="owner/repo",
            pr_number=42,
            should_approve=True,
            summary="Great work!",
            comments=comments,
            pr_head_sha='abc123'
        )
        
        assert result is True
        assert len(mock_api.posted_reviews) == 1
        posted = mock_api.posted_reviews[0]
        assert posted['repo'] == "owner/repo"
        assert posted['pr_number'] == 42
        assert posted['event'] == "APPROVE"
        assert posted['body'] == "Great work!"
        assert len(posted['comments']) == 1
        assert posted['comments'][0]['path'] == 'test.py'
    
    @pytest.mark.asyncio
    async def test_post_review_limits_comments(self):
        """Test that posting review limits number of comments."""
        class MockGitHubAPI:
            def __init__(self):
                self.posted_reviews = []
            
            def get_pull_request(self, owner, repo, pr_number):
                return {'head': {'sha': 'abc123'}}
            
            def create_pull_request_review(self, owner, repo, pr_number, body, event, comments):
                self.posted_reviews.append({'comments': comments})
        
        mock_api = MockGitHubAPI()
        reviewer = PRReviewer(
            github_username="test-bot",
            github_api=mock_api
        )
        
        # Create 15 comments (should be limited to 10)
        comments = [
            ReviewComment(path='test.py', line=i, body=f'Comment {i}')
            for i in range(1, 16)
        ]
        
        await reviewer.post_review_to_github(
            repo="owner/repo",
            pr_number=42,
            should_approve=False,
            summary="Many issues found",
            comments=comments,
            pr_head_sha='abc123'
        )
        
        # Should limit to 10 comments
        assert len(mock_api.posted_reviews[0]['comments']) == 10

