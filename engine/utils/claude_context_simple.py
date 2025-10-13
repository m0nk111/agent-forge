#!/usr/bin/env python3
"""
Simplified Claude Context Integration for Agent-Forge

This is a simpler, working wrapper that uses the actual exported
TypeScript function instead of trying to call non-existent methods.

Usage:
    from engine.utils.claude_context_simple import SimpleClaudeContext
    
    context = SimpleClaudeContext()
    results = context.search_code(
        codebase_path='engine/operations',
        query='GitHub authentication'
    )
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SimpleClaudeContext:
    """
    Simplified Claude Context wrapper.
    
    Uses the exported testContextEndToEnd() function from TypeScript
    instead of trying to call non-existent individual methods.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        milvus_address: Optional[str] = None,
        milvus_token: Optional[str] = None
    ):
        """
        Initialize Claude Context wrapper.
        
        Args:
            openai_api_key: OpenAI API key (defaults to loading from secrets)
            milvus_address: Milvus server address (defaults to localhost:19530)
            milvus_token: Milvus token for authentication (for Zilliz Cloud)
        """
        # Load API keys from secrets if not provided
        self.openai_api_key = openai_api_key or self._load_openai_key()
        self.milvus_address = milvus_address or os.getenv('MILVUS_ADDRESS', 'localhost:19530')
        self.milvus_token = milvus_token or os.getenv('MILVUS_TOKEN', '')
        
        # Path to claude-context installation
        self.claude_context_root = Path(__file__).parent.parent.parent / 'tools' / 'claude-context'
        self.python_bridge = self.claude_context_root / 'python'
        
        # Validate installation
        if not self.claude_context_root.exists():
            raise FileNotFoundError(
                f"Claude Context not found at {self.claude_context_root}"
            )
        
        if not self.python_bridge.exists():
            raise FileNotFoundError(
                f"Python bridge not found at {self.python_bridge}"
            )
        
        logger.debug(f"🔍 Claude Context initialized")
        logger.debug(f"   Root: {self.claude_context_root}")
        logger.debug(f"   Milvus: {self.milvus_address}")
    
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
    
    def _call_typescript(
        self,
        codebase_path: str,
        search_query: str
    ) -> Dict[str, Any]:
        """
        Call TypeScript testContextEndToEnd function directly.
        
        Args:
            codebase_path: Path to codebase
            search_query: Search query
            
        Returns:
            Result dictionary from TypeScript
        """
        try:
            # Create wrapper script that calls testContextEndToEnd
            # IMPORTANT: Use dense-only mode to avoid BM25 sparse vector issues
            wrapper_code = f"""
import {{ testContextEndToEnd }} from './test_context';

// Disable hybrid mode - use dense vectors only
// This avoids BM25 sparse vector generation issues in Milvus
process.env.HYBRID_MODE = 'false';

async function main() {{
    const result = await testContextEndToEnd({{
        openaiApiKey: '{self.openai_api_key}',
        milvusAddress: '{self.milvus_address}',
        codebasePath: '{codebase_path}',
        searchQuery: '{search_query}'
    }});
    
    console.log(JSON.stringify(result, null, 2));
}}

main().catch(console.error);
"""
            
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.ts',
                dir=str(self.python_bridge),
                delete=False
            ) as f:
                f.write(wrapper_code)
                temp_file = f.name
            
            try:
                # Execute with ts-node
                result = subprocess.run(
                    ['npx', 'ts-node', temp_file],
                    cwd=str(self.claude_context_root),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    logger.error(f"TypeScript error: {result.stderr}")
                    raise RuntimeError(f"TypeScript execution failed: {result.stderr}")
                
                # Debug: Print raw output
                logger.debug(f"🔍 Raw stdout length: {len(result.stdout)} chars")
                if result.stderr:
                    logger.debug(f"🔍 Stderr: {result.stderr[:500]}")
                
                # Parse JSON output - extract ONLY the final JSON result
                # The TypeScript script logs various messages, then prints final JSON
                # We need to find where the JSON starts and extract from there
                output = result.stdout
                
                # Find the last occurrence of '🎉 End-to-end test completed!' 
                # JSON starts after this message
                marker = '🎉 End-to-end test completed!'
                json_start_idx = output.rfind(marker)
                
                if json_start_idx != -1:
                    # Skip past the marker and newline
                    json_start_idx = output.find('\n', json_start_idx) + 1
                    output = output[json_start_idx:]
                
                # Now extract just the JSON part (from first { to last })
                first_brace = output.find('{')
                last_brace = output.rfind('}')
                
                if first_brace == -1 or last_brace == -1:
                    logger.error(f"❌ No JSON braces found")
                    logger.error(f"Output sample: {output[:500]}")
                    raise ValueError("No JSON object found in TypeScript output")
                
                json_str = output[first_brace:last_brace+1]
                logger.debug(f"🔍 Extracted JSON: {len(json_str)} chars")
                
                return json.loads(json_str)
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ TypeScript execution failed: {e}")
            raise
    
    def search_code(
        self,
        codebase_path: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search codebase using semantic search.
        
        Args:
            codebase_path: Path to the codebase to search
            query: Natural language search query
            limit: Maximum number of results (not used, kept for API compat)
            
        Returns:
            List of search results with code snippets, file paths, and scores
        """
        logger.info(f"🔎 Searching: '{query}' in {codebase_path}")
        
        try:
            result = self._call_typescript(codebase_path, query)
            
            if not result.get('success'):
                raise RuntimeError(f"Search failed: {result.get('error')}")
            
            # Extract search results
            search_results = result.get('searchResults', [])
            
            logger.info(f"✅ Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise


if __name__ == '__main__':
    # Simple CLI test
    import argparse
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Simple Claude Context CLI')
    parser.add_argument('--path', default='engine/operations', help='Codebase path')
    parser.add_argument('--query', default='GitHub authentication', help='Search query')
    
    args = parser.parse_args()
    
    context = SimpleClaudeContext()
    results = context.search_code(args.path, args.query)
    
    print(f"\n🔎 Search Results for: '{args.query}'")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('relativePath')} (score: {result.get('score', 0):.3f})")
        print(f"   Lines {result.get('startLine')}-{result.get('endLine')}")
        print(f"   Language: {result.get('language')}")
        print(f"   Preview: {result.get('contentPreview', '')[:100]}...")
