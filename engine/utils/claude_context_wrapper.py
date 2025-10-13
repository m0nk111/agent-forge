#!/usr/bin/env python3
"""
Claude Context Integration Wrapper for Agent-Forge

This module provides a Python interface to the Claude Context MCP server,
enabling semantic code search and codebase indexing capabilities.

Architecture:
- Uses the TypeScript executor from tools/claude-context/python/
- Connects to Milvus vector database (local or Zilliz Cloud)
- Uses OpenAI embeddings for semantic search
- Integrates with Agent-Forge's secret management

Usage:
    from engine.utils.claude_context_wrapper import ClaudeContextWrapper
    
    wrapper = ClaudeContextWrapper()
    wrapper.index_codebase('/path/to/codebase')
    results = wrapper.search_code('authentication functions')
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ClaudeContextWrapper:
    """
    Wrapper for Claude Context semantic code search.
    
    Provides Python interface to the Claude Context TypeScript codebase,
    enabling semantic indexing and search of code repositories.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        milvus_address: Optional[str] = None,
        milvus_token: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize Claude Context wrapper.
        
        Args:
            openai_api_key: OpenAI API key (defaults to loading from secrets)
            milvus_address: Milvus server address (defaults to localhost:19530)
            milvus_token: Milvus token for authentication (for Zilliz Cloud)
            embedding_model: OpenAI embedding model to use
        """
        # Load API keys from secrets if not provided
        self.openai_api_key = openai_api_key or self._load_openai_key()
        self.milvus_address = milvus_address or os.getenv('MILVUS_ADDRESS', 'localhost:19530')
        self.milvus_token = milvus_token or os.getenv('MILVUS_TOKEN', '')
        self.embedding_model = embedding_model
        
        # Path to claude-context installation
        self.claude_context_root = Path(__file__).parent.parent.parent / 'tools' / 'claude-context'
        self.python_bridge = self.claude_context_root / 'python'
        
        # Validate installation
        if not self.claude_context_root.exists():
            raise FileNotFoundError(
                f"Claude Context not found at {self.claude_context_root}. "
                "Run: git clone https://github.com/zilliztech/claude-context.git tools/claude-context"
            )
        
        if not self.python_bridge.exists():
            raise FileNotFoundError(
                f"Python bridge not found at {self.python_bridge}"
            )
        
        logger.debug(f"🔍 Claude Context initialized")
        logger.debug(f"   Root: {self.claude_context_root}")
        logger.debug(f"   Milvus: {self.milvus_address}")
        logger.debug(f"   Embedding: {self.embedding_model}")
    
    def _load_openai_key(self) -> str:
        """Load OpenAI API key from secrets directory."""
        try:
            key_file = Path('secrets/keys/openai.key')
            if key_file.exists():
                return key_file.read_text().strip()
            
            # Fallback to environment variable
            key = os.getenv('OPENAI_API_KEY', '')
            if key:
                return key
            
            raise ValueError(
                "OpenAI API key not found. Please create secrets/keys/openai.key "
                "or set OPENAI_API_KEY environment variable."
            )
        except Exception as e:
            logger.error(f"❌ Failed to load OpenAI API key: {e}")
            raise
    
    def _execute_typescript(
        self,
        script_name: str,
        method_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        Execute TypeScript method via Python bridge.
        
        Args:
            script_name: Name of the TypeScript script file
            method_name: Method to call in the script
            params: Parameters to pass to the method
            
        Returns:
            Result from TypeScript execution
        """
        try:
            # Add Python bridge to path
            sys.path.insert(0, str(self.python_bridge))
            from ts_executor import TypeScriptExecutor
            
            executor = TypeScriptExecutor()
            script_path = self.python_bridge / script_name
            
            logger.debug(f"🔧 Executing TS: {method_name} from {script_name}")
            result = executor.call_method(str(script_path), method_name, params)
            
            return result
        except Exception as e:
            logger.error(f"❌ TypeScript execution failed: {e}")
            raise
        finally:
            # Clean up path
            if str(self.python_bridge) in sys.path:
                sys.path.remove(str(self.python_bridge))
    
    def index_codebase(
        self,
        codebase_path: str,
        collection_name: Optional[str] = None,
        file_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Index a codebase for semantic search.
        
        Args:
            codebase_path: Path to the codebase to index
            collection_name: Name for the Milvus collection (defaults to sanitized path)
            file_patterns: File patterns to include (e.g., ['**/*.py', '**/*.js'])
            
        Returns:
            Indexing statistics (files processed, chunks created, etc.)
        """
        logger.info(f"📚 Indexing codebase: {codebase_path}")
        
        # Sanitize collection name from path if not provided
        if not collection_name:
            collection_name = Path(codebase_path).name.replace('-', '_').replace('.', '_')
        
        params = {
            'openaiApiKey': self.openai_api_key,
            'milvusAddress': self.milvus_address,
            'milvusToken': self.milvus_token,
            'codebasePath': codebase_path,
            'collectionName': collection_name,
            'embeddingModel': self.embedding_model
        }
        
        if file_patterns:
            params['filePatterns'] = file_patterns
        
        try:
            result = self._execute_typescript(
                'test_context.ts',
                'indexCodebase',
                params
            )
            
            logger.info(f"✅ Indexing complete: {result.get('filesIndexed', 0)} files, "
                       f"{result.get('chunksCreated', 0)} chunks")
            return result
        except Exception as e:
            logger.error(f"❌ Indexing failed: {e}")
            raise
    
    def search_code(
        self,
        query: str,
        collection_name: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search codebase using semantic search.
        
        Args:
            query: Natural language search query
            collection_name: Name of the collection to search
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of search results with code snippets, file paths, and scores
        """
        logger.info(f"🔎 Searching: '{query}'")
        
        params = {
            'openaiApiKey': self.openai_api_key,
            'milvusAddress': self.milvus_address,
            'milvusToken': self.milvus_token,
            'searchQuery': query,
            'limit': limit,
            'scoreThreshold': score_threshold
        }
        
        if collection_name:
            params['collectionName'] = collection_name
        
        try:
            results = self._execute_typescript(
                'test_context.ts',
                'searchCode',
                params
            )
            
            logger.info(f"✅ Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise
    
    def clear_index(self, collection_name: str) -> None:
        """
        Clear/delete an indexed collection.
        
        Args:
            collection_name: Name of the collection to delete
        """
        logger.info(f"🗑️  Clearing index: {collection_name}")
        
        params = {
            'milvusAddress': self.milvus_address,
            'milvusToken': self.milvus_token,
            'collectionName': collection_name
        }
        
        try:
            self._execute_typescript(
                'test_context.ts',
                'clearIndex',
                params
            )
            logger.info(f"✅ Index cleared: {collection_name}")
        except Exception as e:
            logger.error(f"❌ Clear index failed: {e}")
            raise
    
    def list_collections(self) -> List[str]:
        """
        List all indexed collections in Milvus.
        
        Returns:
            List of collection names
        """
        logger.debug(f"📋 Listing collections")
        
        params = {
            'milvusAddress': self.milvus_address,
            'milvusToken': self.milvus_token
        }
        
        try:
            collections = self._execute_typescript(
                'test_context.ts',
                'listCollections',
                params
            )
            logger.debug(f"✅ Found {len(collections)} collections")
            return collections
        except Exception as e:
            logger.error(f"❌ List collections failed: {e}")
            raise


def load_api_key(service: str) -> str:
    """
    Load API key for a specific service from secrets directory.
    
    Args:
        service: Service name (e.g., 'openai', 'openrouter')
        
    Returns:
        API key string
    """
    key_file = Path(f'secrets/keys/{service}.key')
    if not key_file.exists():
        raise FileNotFoundError(f"Key file not found: {key_file}")
    return key_file.read_text().strip()


if __name__ == '__main__':
    # Simple CLI test
    import argparse
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Claude Context CLI')
    parser.add_argument('action', choices=['index', 'search', 'list', 'clear'])
    parser.add_argument('--path', help='Codebase path to index')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--collection', help='Collection name')
    parser.add_argument('--limit', type=int, default=5, help='Max results')
    
    args = parser.parse_args()
    
    wrapper = ClaudeContextWrapper()
    
    if args.action == 'index':
        if not args.path:
            print("Error: --path required for indexing")
            sys.exit(1)
        result = wrapper.index_codebase(args.path, args.collection)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search")
            sys.exit(1)
        results = wrapper.search_code(args.query, args.collection, args.limit)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('file')} (score: {result.get('score', 0):.3f})")
            print(f"   {result.get('content', '')[:200]}...")
    
    elif args.action == 'list':
        collections = wrapper.list_collections()
        print(f"Collections: {', '.join(collections)}")
    
    elif args.action == 'clear':
        if not args.collection:
            print("Error: --collection required for clear")
            sys.exit(1)
        wrapper.clear_index(args.collection)
        print(f"Cleared collection: {args.collection}")
