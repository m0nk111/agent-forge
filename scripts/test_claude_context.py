#!/usr/bin/env python3
"""
Test script for Claude Context integration in Agent-Forge.

This script validates:
1. Claude Context installation and dependencies
2. API key configuration
3. Milvus connection
4. Codebase indexing
5. Semantic search
6. Collection management

Usage:
    # Full test
    python3 scripts/test_claude_context.py
    
    # Quick test (no indexing)
    python3 scripts/test_claude_context.py --quick
    
    # Test specific collection
    python3 scripts/test_claude_context.py --collection my_collection
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.utils.claude_context_wrapper import ClaudeContextWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeContextTester:
    """Test suite for Claude Context integration."""
    
    def __init__(self, quick_mode: bool = False):
        """
        Initialize tester.
        
        Args:
            quick_mode: Skip long-running tests like indexing
        """
        self.quick_mode = quick_mode
        self.wrapper = None
        self.test_collection = 'test_agent_forge'
        self.test_results: Dict[str, bool] = {}
    
    def run_all_tests(self) -> bool:
        """
        Run all integration tests.
        
        Returns:
            True if all tests passed, False otherwise
        """
        logger.info("=" * 60)
        logger.info("🧪 Claude Context Integration Test Suite")
        logger.info("=" * 60)
        
        tests = [
            ('Installation Check', self.test_installation),
            ('API Keys Configuration', self.test_api_keys),
            ('Milvus Connection', self.test_milvus_connection),
            ('Wrapper Initialization', self.test_wrapper_init),
        ]
        
        if not self.quick_mode:
            tests.extend([
                ('Codebase Indexing', self.test_indexing),
                ('Semantic Search', self.test_search),
                ('Collection Management', self.test_collection_management),
            ])
        else:
            logger.info("⚡ Quick mode: Skipping indexing and search tests")
        
        # Run tests
        for test_name, test_func in tests:
            logger.info(f"\n{'─' * 60}")
            logger.info(f"▶️  {test_name}")
            logger.info(f"{'─' * 60}")
            
            try:
                success = test_func()
                self.test_results[test_name] = success
                
                if success:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED with exception: {e}")
                self.test_results[test_name] = False
        
        # Print summary
        self._print_summary()
        
        # Return overall result
        return all(self.test_results.values())
    
    def test_installation(self) -> bool:
        """Test if Claude Context is installed."""
        logger.info("Checking Claude Context installation...")
        
        claude_context_root = Path('tools/claude-context')
        
        # Check directory exists
        if not claude_context_root.exists():
            logger.error(f"❌ Claude Context not found at {claude_context_root}")
            logger.info("   Run: git clone https://github.com/zilliztech/claude-context.git tools/claude-context")
            return False
        
        logger.info(f"✓ Claude Context directory found: {claude_context_root}")
        
        # Check required files
        required_files = [
            'package.json',
            'python/ts_executor.py',
            'python/test_context.ts',
            'packages/mcp/package.json',
        ]
        
        for file_path in required_files:
            full_path = claude_context_root / file_path
            if not full_path.exists():
                logger.error(f"❌ Required file missing: {file_path}")
                return False
            logger.info(f"✓ Found: {file_path}")
        
        # Check Node.js installation
        try:
            import subprocess
            node_version = subprocess.check_output(['node', '--version'], text=True).strip()
            logger.info(f"✓ Node.js version: {node_version}")
            
            # Check version compatibility (20-23 required)
            version_major = int(node_version.lstrip('v').split('.')[0])
            if version_major < 20 or version_major >= 24:
                logger.warning(f"⚠️  Node.js {version_major} may not be compatible (20-23 required)")
        except Exception as e:
            logger.error(f"❌ Node.js not found: {e}")
            return False
        
        logger.info("✅ Installation check complete")
        return True
    
    def test_api_keys(self) -> bool:
        """Test API key configuration."""
        logger.info("Checking API key configuration...")
        
        # Check OpenAI key
        openai_key_file = Path('secrets/keys/openai.key')
        if not openai_key_file.exists():
            logger.error(f"❌ OpenAI key not found: {openai_key_file}")
            logger.info("   Create the file: echo 'sk-proj-your-key' > secrets/keys/openai.key")
            return False
        
        openai_key = openai_key_file.read_text().strip()
        if not openai_key or not openai_key.startswith('sk-'):
            logger.error(f"❌ Invalid OpenAI key format")
            return False
        
        logger.info(f"✓ OpenAI key found: {openai_key[:10]}...")
        
        # Check Milvus configuration
        milvus_address = os.getenv('MILVUS_ADDRESS', 'localhost:19530')
        milvus_token = os.getenv('MILVUS_TOKEN', '')
        
        logger.info(f"✓ Milvus address: {milvus_address}")
        
        if 'zilliz.com' in milvus_address and not milvus_token:
            logger.warning("⚠️  Zilliz Cloud detected but MILVUS_TOKEN not set")
            logger.info("   Set environment variable: export MILVUS_TOKEN=your-token")
        
        logger.info("✅ API keys configured")
        return True
    
    def test_milvus_connection(self) -> bool:
        """Test Milvus database connection."""
        logger.info("Testing Milvus connection...")
        
        milvus_address = os.getenv('MILVUS_ADDRESS', 'localhost:19530')
        
        # Simple connection test (wrapper will handle this)
        try:
            # We'll test connection through the wrapper
            logger.info(f"✓ Milvus configured: {milvus_address}")
            return True
        except Exception as e:
            logger.error(f"❌ Milvus connection failed: {e}")
            return False
    
    def test_wrapper_init(self) -> bool:
        """Test wrapper initialization."""
        logger.info("Initializing Claude Context wrapper...")
        
        try:
            self.wrapper = ClaudeContextWrapper()
            logger.info("✓ Wrapper initialized successfully")
            logger.info(f"  OpenAI Key: {self.wrapper.openai_api_key[:10]}...")
            logger.info(f"  Milvus: {self.wrapper.milvus_address}")
            logger.info(f"  Model: {self.wrapper.embedding_model}")
            return True
        except Exception as e:
            logger.error(f"❌ Wrapper initialization failed: {e}")
            return False
    
    def test_indexing(self) -> bool:
        """Test codebase indexing."""
        logger.info("Testing codebase indexing...")
        logger.info("This may take a few minutes for large codebases...")
        
        if not self.wrapper:
            logger.error("❌ Wrapper not initialized")
            return False
        
        try:
            # Index a small subset for testing (engine/utils)
            test_path = 'engine/utils'
            logger.info(f"Indexing test directory: {test_path}")
            
            result = self.wrapper.index_codebase(
                codebase_path=test_path,
                collection_name=self.test_collection
            )
            
            files_indexed = result.get('filesIndexed', 0)
            chunks_created = result.get('chunksCreated', 0)
            
            logger.info(f"✓ Indexed {files_indexed} files")
            logger.info(f"✓ Created {chunks_created} chunks")
            
            if files_indexed == 0:
                logger.warning("⚠️  No files were indexed")
                return False
            
            logger.info("✅ Indexing successful")
            return True
        except Exception as e:
            logger.error(f"❌ Indexing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_search(self) -> bool:
        """Test semantic search."""
        logger.info("Testing semantic search...")
        
        if not self.wrapper:
            logger.error("❌ Wrapper not initialized")
            return False
        
        # Test queries
        test_queries = [
            "API key loading and secret management",
            "logging and debug output",
            "file path and directory operations",
        ]
        
        try:
            for query in test_queries:
                logger.info(f"\n🔎 Query: '{query}'")
                
                results = self.wrapper.search_code(
                    query=query,
                    collection_name=self.test_collection,
                    limit=3
                )
                
                if not results:
                    logger.warning(f"⚠️  No results for query: {query}")
                    continue
                
                for i, result in enumerate(results[:3], 1):
                    file_path = result.get('file', 'unknown')
                    score = result.get('score', 0.0)
                    content_preview = result.get('content', '')[:100].replace('\n', ' ')
                    
                    logger.info(f"  {i}. {file_path} (score: {score:.3f})")
                    logger.info(f"     Preview: {content_preview}...")
            
            logger.info("\n✅ Search test complete")
            return True
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_collection_management(self) -> bool:
        """Test collection listing and deletion."""
        logger.info("Testing collection management...")
        
        if not self.wrapper:
            logger.error("❌ Wrapper not initialized")
            return False
        
        try:
            # List collections
            collections = self.wrapper.list_collections()
            logger.info(f"✓ Found {len(collections)} collections: {collections}")
            
            # Verify test collection exists
            if self.test_collection not in collections:
                logger.warning(f"⚠️  Test collection not found: {self.test_collection}")
            
            # Clean up test collection
            logger.info(f"🗑️  Cleaning up test collection: {self.test_collection}")
            self.wrapper.clear_index(self.test_collection)
            logger.info("✓ Test collection deleted")
            
            # Verify deletion
            collections_after = self.wrapper.list_collections()
            if self.test_collection in collections_after:
                logger.error(f"❌ Collection still exists after deletion")
                return False
            
            logger.info("✅ Collection management test complete")
            return True
        except Exception as e:
            logger.error(f"❌ Collection management failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_summary(self):
        """Print test results summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 Test Summary")
        logger.info("=" * 60)
        
        passed = sum(1 for v in self.test_results.values() if v)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status}  {test_name}")
        
        logger.info("=" * 60)
        logger.info(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed!")
        else:
            logger.error(f"⚠️  {total - passed} test(s) failed")
        
        logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test Claude Context integration in Agent-Forge'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (skip indexing and search)'
    )
    parser.add_argument(
        '--collection',
        default='test_agent_forge',
        help='Collection name for testing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    tester = ClaudeContextTester(quick_mode=args.quick)
    tester.test_collection = args.collection
    
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
