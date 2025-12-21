"""
RAG Retriever - Query and retrieve relevant context

Main interface for the RAG system. Handles:
1. Query processing and embedding
2. Vector search across collections
3. Result reranking and filtering
4. Context formatting for LLM prompts
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from .embedding_service import EmbeddingService
from .vector_store import MilvusVectorStore, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Enhanced search result with formatted context."""
    content: str
    source: str  # 'code', 'docs', or 'issues'
    metadata: Dict[str, Any]
    score: float
    formatted_context: str  # Ready-to-use context for LLM


class RAGRetriever:
    """Main RAG retrieval interface."""
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[MilvusVectorStore] = None,
        top_k: int = 5,
        min_score: float = 0.5
    ):
        """Initialize RAG retriever.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector database instance
            top_k: Number of results to retrieve
            min_score: Minimum similarity score threshold
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or MilvusVectorStore(
            embedding_dim=self.embedding_service.embedding_dim
        )
        self.top_k = top_k
        self.min_score = min_score
        
        logger.info("✅ RAG Retriever initialized")
    
    def retrieve(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        include_metadata: bool = True
    ) -> List[RetrievalResult]:
        """Retrieve relevant context for query.
        
        Args:
            query: Search query (natural language)
            sources: Filter by sources (['code', 'docs', 'issues']). None = all
            top_k: Override default top_k
            include_metadata: Include metadata in formatted context
            
        Returns:
            List of RetrievalResult objects, sorted by relevance
        """
        logger.info(f"🔍 Retrieving context for query: '{query[:100]}...'")
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed(query)[0]
        
        # Determine which collections to search
        sources = sources or ["code", "docs", "issues"]
        top_k = top_k or self.top_k
        
        # Search collections
        all_results = []
        for source in sources:
            try:
                results = self.vector_store.search(
                    collection_name=source,
                    query_embedding=query_embedding,
                    top_k=top_k
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"⚠️ Search failed for '{source}': {e}")
        
        # Filter by score
        filtered_results = [r for r in all_results if r.score >= self.min_score]
        
        # Sort by score
        filtered_results.sort(key=lambda x: x.score, reverse=True)
        
        # Take top K overall
        final_results = filtered_results[:top_k]
        
        # Format results
        retrieval_results = [
            self._format_result(r, include_metadata)
            for r in final_results
        ]
        
        logger.info(f"✅ Retrieved {len(retrieval_results)} relevant results")
        return retrieval_results
    
    def _format_result(
        self,
        result: SearchResult,
        include_metadata: bool
    ) -> RetrievalResult:
        """Format search result for LLM consumption."""
        # Format based on source type
        if result.collection == "code":
            formatted = self._format_code_result(result, include_metadata)
        elif result.collection == "docs":
            formatted = self._format_docs_result(result, include_metadata)
        elif result.collection == "issues":
            formatted = self._format_issues_result(result, include_metadata)
        else:
            formatted = result.content
        
        return RetrievalResult(
            content=result.content,
            source=result.collection,
            metadata=result.metadata,
            score=result.score,
            formatted_context=formatted
        )
    
    def _format_code_result(self, result: SearchResult, include_metadata: bool) -> str:
        """Format code search result."""
        parts = []
        
        if include_metadata:
            metadata = result.metadata
            parts.append(f"### Code from: {metadata.get('file_path', 'unknown')}")
            parts.append(f"Type: {metadata.get('chunk_type', 'unknown')} - {metadata.get('name', 'unnamed')}")
            
            if metadata.get('docstring'):
                parts.append(f"Description: {metadata['docstring'][:150]}...")
            
            parts.append(f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}")
            parts.append(f"Relevance: {result.score:.2f}\n")
        
        parts.append("```python")
        parts.append(result.content)
        parts.append("```")
        
        return "\n".join(parts)
    
    def _format_docs_result(self, result: SearchResult, include_metadata: bool) -> str:
        """Format documentation search result."""
        parts = []
        
        if include_metadata:
            metadata = result.metadata
            parts.append(f"### Documentation: {metadata.get('file_path', 'unknown')}")
            
            if metadata.get('section'):
                parts.append(f"Section: {metadata['section']}")
            
            parts.append(f"Relevance: {result.score:.2f}\n")
        
        parts.append(result.content)
        
        return "\n".join(parts)
    
    def _format_issues_result(self, result: SearchResult, include_metadata: bool) -> str:
        """Format issue history search result."""
        parts = []
        
        if include_metadata:
            metadata = result.metadata
            parts.append(f"### Similar Issue: #{metadata.get('issue_number', '?')}")
            parts.append(f"Title: {metadata.get('title', 'Unknown')}")
            parts.append(f"Status: {metadata.get('state', 'unknown')}")
            parts.append(f"Relevance: {result.score:.2f}\n")
        
        parts.append("**Problem:**")
        parts.append(metadata.get('problem', result.content[:200]))
        
        if metadata.get('solution'):
            parts.append("\n**Solution:**")
            parts.append(metadata['solution'][:300])
        
        return "\n".join(parts)
    
    def get_context_for_code_generation(
        self,
        task_description: str,
        file_path: Optional[str] = None,
        max_context_length: int = 3000
    ) -> str:
        """Get relevant context for code generation task.
        
        Args:
            task_description: Description of code to generate
            file_path: Target file path (for finding related code)
            max_context_length: Maximum context length in characters
            
        Returns:
            Formatted context string ready for LLM prompt
        """
        logger.info(f"📝 Getting code generation context for: {task_description[:100]}")
        
        # Retrieve relevant code
        results = self.retrieve(
            query=task_description,
            sources=["code"],
            top_k=5
        )
        
        # Build context
        context_parts = ["# Relevant Code Examples\n"]
        
        current_length = len(context_parts[0])
        for result in results:
            formatted = result.formatted_context
            
            if current_length + len(formatted) > max_context_length:
                break
            
            context_parts.append(formatted)
            context_parts.append("\n---\n")
            current_length += len(formatted) + 6
        
        return "\n".join(context_parts)
    
    def get_context_for_issue_resolution(
        self,
        issue_description: str,
        max_context_length: int = 4000
    ) -> str:
        """Get relevant context for issue resolution.
        
        Combines similar resolved issues and relevant code/docs.
        
        Args:
            issue_description: Issue description
            max_context_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        logger.info(f"🔧 Getting issue resolution context")
        
        # Search all sources
        results = self.retrieve(
            query=issue_description,
            sources=["issues", "code", "docs"],
            top_k=8
        )
        
        # Group by source
        by_source = {"issues": [], "code": [], "docs": []}
        for r in results:
            by_source[r.source].append(r)
        
        # Build context with sections
        context_parts = []
        current_length = 0
        
        # 1. Similar resolved issues (highest priority)
        if by_source["issues"]:
            context_parts.append("# Similar Resolved Issues\n")
            for result in by_source["issues"][:2]:
                if current_length + len(result.formatted_context) > max_context_length:
                    break
                context_parts.append(result.formatted_context)
                context_parts.append("\n---\n")
                current_length += len(result.formatted_context) + 6
        
        # 2. Relevant code
        if by_source["code"] and current_length < max_context_length * 0.7:
            context_parts.append("\n# Relevant Code\n")
            for result in by_source["code"][:3]:
                if current_length + len(result.formatted_context) > max_context_length:
                    break
                context_parts.append(result.formatted_context)
                context_parts.append("\n---\n")
                current_length += len(result.formatted_context) + 6
        
        # 3. Documentation
        if by_source["docs"] and current_length < max_context_length * 0.9:
            context_parts.append("\n# Relevant Documentation\n")
            for result in by_source["docs"][:2]:
                if current_length + len(result.formatted_context) > max_context_length:
                    break
                context_parts.append(result.formatted_context)
                current_length += len(result.formatted_context)
        
        return "\n".join(context_parts)
    
    def close(self):
        """Clean up resources."""
        self.vector_store.close()
        logger.info("👋 RAG Retriever closed")


# Convenience function for quick retrieval
def retrieve_context(query: str, sources: Optional[List[str]] = None, top_k: int = 5) -> str:
    """Quick context retrieval using default retriever.
    
    Args:
        query: Search query
        sources: Filter by sources (['code', 'docs', 'issues'])
        top_k: Number of results
        
    Returns:
        Formatted context string
    """
    retriever = RAGRetriever(top_k=top_k)
    results = retriever.retrieve(query, sources=sources)
    
    context = "\n\n".join(r.formatted_context for r in results)
    retriever.close()
    
    return context
