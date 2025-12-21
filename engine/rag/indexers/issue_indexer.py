"""
Issue History Indexer - Index resolved GitHub issues

Indexes closed GitHub issues as problem-solution pairs:
1. Fetches closed issues via GitHub API
2. Extracts problem description and resolution
3. Links to related PRs and commits
4. Generates embeddings
5. Stores in vector database
"""

import os
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..embedding_service import EmbeddingService
from ..vector_store import MilvusVectorStore

logger = logging.getLogger(__name__)


@dataclass
class IssueChunk:
    """Issue history chunk with metadata."""
    content: str  # Combined problem + solution
    issue_number: int
    title: str
    state: str
    chunk_id: str
    metadata: Dict[str, Any]


class IssueIndexer:
    """Index GitHub issue history into RAG system."""
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[MilvusVectorStore] = None,
        github_token: Optional[str] = None
    ):
        """Initialize issue indexer.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector database instance
            github_token: GitHub API token (uses GITHUB_TOKEN env if not provided)
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or MilvusVectorStore(
            embedding_dim=self.embedding_service.embedding_dim
        )
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
        if not self.github_token:
            logger.warning("⚠️ No GitHub token provided - API rate limits will apply")
        
        logger.info("🐙 Issue indexer initialized")
    
    def index_repository(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        limit: Optional[int] = None
    ) -> int:
        """Index issues from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state ('open', 'closed', 'all')
            limit: Maximum number of issues to fetch
            
        Returns:
            Number of issues indexed
        """
        logger.info(f"📂 Indexing issues from {owner}/{repo} (state={state})")
        
        # Fetch issues using GitHub CLI or API
        issues = self._fetch_issues(owner, repo, state, limit)
        
        if not issues:
            logger.warning("⚠️ No issues found to index")
            return 0
        
        # Convert to chunks
        chunks = []
        for issue_data in issues:
            chunk = self._create_chunk(issue_data, owner, repo)
            if chunk:
                chunks.append(chunk)
        
        # Store chunks
        total_stored = self._store_chunks(chunks)
        
        logger.info(f"✅ Indexed {total_stored} issues from {owner}/{repo}")
        return total_stored
    
    def _fetch_issues(
        self,
        owner: str,
        repo: str,
        state: str,
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub.
        
        Uses GitHub CLI (gh) if available, otherwise falls back to REST API.
        """
        # Try GitHub CLI first
        try:
            import subprocess
            
            cmd = [
                'gh', 'issue', 'list',
                '--repo', f"{owner}/{repo}",
                '--state', state,
                '--json', 'number,title,body,state,createdAt,closedAt,labels,assignees,url'
            ]
            
            if limit:
                cmd.extend(['--limit', str(limit)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
            
            logger.info(f"✅ Fetched {len(issues)} issues via GitHub CLI")
            return issues
            
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"⚠️ GitHub CLI failed, trying REST API: {e}")
            return self._fetch_issues_api(owner, repo, state, limit)
    
    def _fetch_issues_api(
        self,
        owner: str,
        repo: str,
        state: str,
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Fetch issues via GitHub REST API."""
        try:
            import requests
            
            headers = {
                'Accept': 'application/vnd.github.v3+json'
            }
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            url = f'https://api.github.com/repos/{owner}/{repo}/issues'
            params = {
                'state': state,
                'per_page': min(limit or 100, 100)
            }
            
            all_issues = []
            page = 1
            
            while True:
                params['page'] = page
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                issues = response.json()
                
                if not issues:
                    break
                
                # Filter out pull requests (they appear as issues in API)
                issues = [i for i in issues if 'pull_request' not in i]
                all_issues.extend(issues)
                
                if limit and len(all_issues) >= limit:
                    all_issues = all_issues[:limit]
                    break
                
                if len(issues) < params['per_page']:
                    break
                
                page += 1
            
            logger.info(f"✅ Fetched {len(all_issues)} issues via REST API")
            return all_issues
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch issues via API: {e}")
            return []
    
    def _create_chunk(
        self,
        issue_data: Dict[str, Any],
        owner: str,
        repo: str
    ) -> Optional[IssueChunk]:
        """Create issue chunk from GitHub issue data."""
        # Extract basic info
        number = issue_data.get('number')
        title = issue_data.get('title', '')
        body = issue_data.get('body', '')
        state = issue_data.get('state', 'unknown')
        
        if not number or not title:
            return None
        
        # Skip issues without body (usually invalid)
        if not body or len(body.strip()) < 20:
            logger.debug(f"⏭️ Skipping issue #{number} (no body)")
            return None
        
        # Extract problem and solution
        problem = self._extract_problem(title, body)
        solution = self._extract_solution(issue_data)
        
        # Combine for content
        content_parts = [f"**Title:** {title}"]
        
        if problem:
            content_parts.append(f"\n**Problem:**\n{problem}")
        
        if solution:
            content_parts.append(f"\n**Solution:**\n{solution}")
        
        content = "\n".join(content_parts)
        
        # Generate unique ID
        content_hash = hashlib.md5(f"{owner}/{repo}#{number}".encode()).hexdigest()[:8]
        chunk_id = f"issue_{owner}_{repo}_{number}_{content_hash}"
        
        # Build metadata
        metadata = {
            'issue_number': number,
            'title': title,
            'state': state,
            'repository': f"{owner}/{repo}",
            'url': issue_data.get('url', f"https://github.com/{owner}/{repo}/issues/{number}"),
            'problem': problem[:500] if problem else '',
            'solution': solution[:500] if solution else '',
            'created_at': issue_data.get('createdAt', ''),
            'closed_at': issue_data.get('closedAt', ''),
            'labels': [label.get('name', '') for label in issue_data.get('labels', [])],
            'char_count': len(content)
        }
        
        return IssueChunk(
            content=content,
            issue_number=number,
            title=title,
            state=state,
            chunk_id=chunk_id,
            metadata=metadata
        )
    
    def _extract_problem(self, title: str, body: str) -> str:
        """Extract problem description from issue."""
        # Try to find problem section
        problem_markers = [
            '## Problem', '## Description', '## Issue',
            '### Problem', '### Description', '### Issue',
            '**Problem:**', '**Description:**'
        ]
        
        lower_body = body.lower()
        
        for marker in problem_markers:
            marker_lower = marker.lower()
            idx = lower_body.find(marker_lower)
            
            if idx != -1:
                # Extract text after marker
                start = idx + len(marker)
                
                # Find next section or end
                next_section = body.find('\n##', start)
                if next_section == -1:
                    next_section = body.find('\n###', start)
                
                if next_section != -1:
                    problem_text = body[start:next_section].strip()
                else:
                    problem_text = body[start:start + 1000].strip()
                
                return problem_text
        
        # Fallback: use first paragraph or title + first 300 chars
        first_para = body.split('\n\n')[0] if '\n\n' in body else body[:300]
        return f"{title}\n\n{first_para}".strip()
    
    def _extract_solution(self, issue_data: Dict[str, Any]) -> str:
        """Extract solution from issue (comments, linked PRs, etc.)."""
        # For now, just indicate resolution status
        state = issue_data.get('state')
        
        if state == 'closed':
            closed_at = issue_data.get('closedAt', '')
            
            solution_parts = []
            
            if closed_at:
                solution_parts.append(f"Issue closed at {closed_at}")
            
            # TODO: In future, fetch comments and linked PRs for detailed solution
            # For now, just basic status
            solution_parts.append("See issue comments and linked PRs for resolution details.")
            
            return "\n".join(solution_parts)
        
        return ""
    
    def _store_chunks(self, chunks: List[IssueChunk]) -> int:
        """Store issue chunks in vector database."""
        if not chunks:
            return 0
        
        logger.info(f"💾 Storing {len(chunks)} issue chunks...")
        
        # Prepare data
        ids = []
        contents = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk.chunk_id)
            contents.append(chunk.content)
            metadatas.append(chunk.metadata)
        
        # Generate embeddings in batches
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]
            embeddings = self.embedding_service.embed(batch)
            all_embeddings.extend(embeddings)
            
            logger.debug(f"📊 Embedded batch {i // batch_size + 1}/{(len(contents) + batch_size - 1) // batch_size}")
        
        # Insert into vector store
        self.vector_store.insert(
            collection_name="issues",
            ids=ids,
            embeddings=all_embeddings,
            contents=contents,
            metadatas=metadatas
        )
        
        logger.info(f"✅ Stored {len(chunks)} issue chunks")
        return len(chunks)
    
    def close(self):
        """Clean up resources."""
        self.vector_store.close()
        logger.info("👋 Issue indexer closed")


# Convenience function for quick indexing
def index_issues(owner: str, repo: str, state: str = "closed", limit: Optional[int] = None) -> int:
    """Quick issue indexing using default indexer.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state ('open', 'closed', 'all')
        limit: Maximum number of issues to fetch
        
    Returns:
        Number of issues indexed
    """
    indexer = IssueIndexer()
    count = indexer.index_repository(owner, repo, state, limit)
    indexer.close()
    return count
