#!/usr/bin/env python3
"""
RAG CLI - Command-line interface for RAG system

Commands:
- index: Index workspace content (code, docs, issues)
- search: Search for relevant context
- stats: Show RAG statistics
- clear: Clear collections
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.rag.embedding_service import EmbeddingService
from engine.rag.vector_store import MilvusVectorStore
from engine.rag.indexers import CodeIndexer, DocsIndexer, IssueIndexer
from engine.rag.retriever import RAGRetriever

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_index_code(args):
    """Index Python code."""
    logger.info(f"📦 Indexing code from: {args.workspace}")
    
    indexer = CodeIndexer(root_dir=Path(args.workspace))
    count = indexer.index_workspace()
    indexer.close()
    
    print(f"\n✅ Indexed {count} code chunks")


def cmd_index_docs(args):
    """Index markdown documentation."""
    logger.info(f"📚 Indexing documentation from: {args.workspace}")
    
    indexer = DocsIndexer()
    count = indexer.index_workspace(args.workspace)
    indexer.close()
    
    print(f"\n✅ Indexed {count} documentation chunks")


def cmd_index_issues(args):
    """Index GitHub issues."""
    logger.info(f"🐙 Indexing issues from: {args.owner}/{args.repo}")
    
    indexer = IssueIndexer()
    count = indexer.index_repository(
        owner=args.owner,
        repo=args.repo,
        state=args.state,
        limit=args.limit
    )
    indexer.close()
    
    print(f"\n✅ Indexed {count} issues")


def cmd_index_all(args):
    """Index everything."""
    logger.info("🚀 Indexing all content...")
    
    # Index code
    print("\n📦 Indexing code...")
    code_indexer = CodeIndexer(root_dir=Path(args.workspace))
    code_count = code_indexer.index_workspace()
    code_indexer.close()
    print(f"✅ Indexed {code_count} code chunks")
    
    # Index docs
    print("\n📚 Indexing documentation...")
    docs_indexer = DocsIndexer()
    docs_count = docs_indexer.index_workspace(args.workspace)
    docs_indexer.close()
    print(f"✅ Indexed {docs_count} documentation chunks")
    
    # Index issues (if repo specified)
    if args.owner and args.repo:
        print(f"\n🐙 Indexing issues from {args.owner}/{args.repo}...")
        issue_indexer = IssueIndexer()
        issue_count = issue_indexer.index_repository(
            owner=args.owner,
            repo=args.repo,
            state=args.state,
            limit=args.limit
        )
        issue_indexer.close()
        print(f"✅ Indexed {issue_count} issues")
    
    print(f"\n🎉 Total: {code_count + docs_count} chunks indexed")


def cmd_search(args):
    """Search for relevant context."""
    logger.info(f"🔍 Searching for: {args.query}")
    
    retriever = RAGRetriever(top_k=args.top_k)
    
    # Parse sources
    sources = args.sources.split(',') if args.sources else None
    
    results = retriever.retrieve(
        query=args.query,
        sources=sources,
        top_k=args.top_k
    )
    
    retriever.close()
    
    # Display results
    print(f"\n🔍 Found {len(results)} relevant results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{'='*80}")
        print(f"Result {i} - Score: {result.score:.3f} - Source: {result.source}")
        print(f"{'='*80}")
        print(result.formatted_context)
        print()


def cmd_stats(args):
    """Show RAG statistics."""
    logger.info("📊 Gathering statistics...")
    
    vector_store = MilvusVectorStore()
    
    print("\n📊 RAG Statistics\n")
    print(f"{'='*80}")
    
    for collection in ["code", "docs", "issues"]:
        try:
            count = vector_store.count(collection)
            print(f"{collection.capitalize():.<30} {count:>10} chunks")
        except Exception as e:
            print(f"{collection.capitalize():.<30} {'ERROR':>10}")
            logger.error(f"Failed to get count for {collection}: {e}")
    
    print(f"{'='*80}\n")
    
    vector_store.close()


def cmd_clear(args):
    """Clear collections."""
    collections = args.collections.split(',') if args.collections else ["code", "docs", "issues"]
    
    print(f"\n⚠️  WARNING: This will delete all data from collections: {', '.join(collections)}")
    
    if not args.yes:
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Aborted")
            return
    
    vector_store = MilvusVectorStore()
    
    for collection in collections:
        try:
            # Delete all entities
            vector_store.delete(collection, expr="id != ''")
            print(f"✅ Cleared collection: {collection}")
        except Exception as e:
            print(f"❌ Failed to clear {collection}: {e}")
    
    vector_store.close()
    print("\n✅ Done")


def main():
    parser = argparse.ArgumentParser(
        description="RAG CLI - Manage RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Index code
    index_code_parser = subparsers.add_parser('index-code', help='Index Python code')
    index_code_parser.add_argument('workspace', help='Workspace path')
    index_code_parser.set_defaults(func=cmd_index_code)
    
    # Index docs
    index_docs_parser = subparsers.add_parser('index-docs', help='Index documentation')
    index_docs_parser.add_argument('workspace', help='Workspace path')
    index_docs_parser.set_defaults(func=cmd_index_docs)
    
    # Index issues
    index_issues_parser = subparsers.add_parser('index-issues', help='Index GitHub issues')
    index_issues_parser.add_argument('owner', help='Repository owner')
    index_issues_parser.add_argument('repo', help='Repository name')
    index_issues_parser.add_argument('--state', default='closed', choices=['open', 'closed', 'all'])
    index_issues_parser.add_argument('--limit', type=int, help='Maximum issues to fetch')
    index_issues_parser.set_defaults(func=cmd_index_issues)
    
    # Index all
    index_all_parser = subparsers.add_parser('index-all', help='Index everything')
    index_all_parser.add_argument('workspace', help='Workspace path')
    index_all_parser.add_argument('--owner', help='Repository owner (for issues)')
    index_all_parser.add_argument('--repo', help='Repository name (for issues)')
    index_all_parser.add_argument('--state', default='closed', choices=['open', 'closed', 'all'])
    index_all_parser.add_argument('--limit', type=int, default=100, help='Max issues to fetch')
    index_all_parser.set_defaults(func=cmd_index_all)
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search for context')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--sources', help='Filter by sources (code,docs,issues)')
    search_parser.add_argument('--top-k', type=int, default=5, help='Number of results')
    search_parser.set_defaults(func=cmd_search)
    
    # Stats
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Clear
    clear_parser = subparsers.add_parser('clear', help='Clear collections')
    clear_parser.add_argument('--collections', help='Collections to clear (comma-separated)')
    clear_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    clear_parser.set_defaults(func=cmd_clear)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        args.func(args)
        return 0
    except Exception as e:
        logger.error(f"❌ Command failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
