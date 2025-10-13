# Claude Context Integration Guide for Agent-Forge

Complete guide for integrating semantic code search capabilities into Agent-Forge using Claude Context.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Integration with Agent-Forge](#integration-with-agent-forge)
- [MCP Server Setup](#mcp-server-setup)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)

---

## Overview

**Claude Context** is an MCP (Model Context Protocol) plugin that provides semantic code search capabilities. It allows AI agents to:

- **Index entire codebases** semantically using vector embeddings
- **Search code** using natural language queries
- **Find relevant context** across millions of lines of code
- **Reduce LLM costs** by only loading relevant code snippets

### Architecture

```
┌─────────────────────┐
│  Agent-Forge Bot    │
│                     │
│  ┌──────────────┐   │
│  │ Code Agent   │   │
│  └──────┬───────┘   │
│         │           │
└─────────┼───────────┘
          │
          ▼
┌─────────────────────┐
│ Claude Context      │
│ (Python Wrapper)    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ TypeScript Bridge   │
│ (MCP Server)        │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐     ┌──────────────┐
│ Milvus Vector DB    │────▶│  OpenAI API  │
│ (Zilliz Cloud)      │     │  (Embeddings)│
└─────────────────────┘     └──────────────┘
```

### Key Components

1. **Python Wrapper** (`engine/utils/claude_context_wrapper.py`)
   - High-level Python API
   - Integrates with Agent-Forge secrets management
   - CLI tool for testing

2. **TypeScript MCP Server** (`tools/claude-context/`)
   - Core indexing and search logic
   - Vector database integration
   - Embedding generation

3. **Milvus Vector Database**
   - Stores code embeddings
   - Fast semantic search
   - Can be local or cloud (Zilliz)

---

## Prerequisites

### Required

- **Python 3.10+** (Agent-Forge)
- **Node.js 20-23** (for Claude Context MCP server)
- **pnpm 10+** (Node.js package manager)
- **OpenAI API Key** (for embeddings)
- **Milvus Vector Database** (local or Zilliz Cloud)

### Optional

- **Zilliz Cloud Account** (free tier available, easier than local Milvus)

---

## Installation

### Step 1: Clone Claude Context Repository

Already done! The repo is cloned at:
```bash
tools/claude-context/
```

### Step 2: Install Node.js Dependencies

```bash
cd tools/claude-context
pnpm install
pnpm build
```

**Verify installation:**
```bash
npx @zilliz/claude-context-mcp@latest --version
```

### Step 3: Install Python Dependencies

No additional Python packages are required — the wrapper uses the TypeScript executor from `tools/claude-context/python/`.

### Step 4: Set Up Vector Database

#### Option A: Zilliz Cloud (Recommended)

1. Sign up at [Zilliz Cloud](https://cloud.zilliz.com/signup)
2. Create a free cluster
3. Copy your **Public Endpoint** and **API Key**
4. Save credentials:

```bash
# Add to .env or export
export MILVUS_ADDRESS="https://in03-xxxx.cloud.zilliz.com"
export MILVUS_TOKEN="your-zilliz-api-key"
```

#### Option B: Local Milvus (Advanced)

```bash
# Using Docker
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest \
  milvus run standalone

# Verify
curl http://localhost:9091/healthz
```

---

## Configuration

### API Keys

Ensure your OpenAI API key is stored in secrets:

```bash
# Verify key exists
ls -l secrets/keys/openai.key

# If not, create it
echo "sk-proj-your-openai-key" > secrets/keys/openai.key
chmod 600 secrets/keys/openai.key
```

### Environment Variables

Create or update `.env` in project root:

```bash
# OpenAI (for embeddings)
OPENAI_API_KEY=sk-proj-your-key

# Milvus (local or cloud)
MILVUS_ADDRESS=localhost:19530          # or https://your-cluster.cloud.zilliz.com
MILVUS_TOKEN=                            # only for Zilliz Cloud

# Optional: embedding model
EMBEDDING_MODEL=text-embedding-3-small   # or text-embedding-3-large
```

---

## Usage Examples

### Example 1: Index Agent-Forge Codebase

```python
from engine.utils.claude_context_wrapper import ClaudeContextWrapper

# Initialize wrapper (loads API keys from secrets)
wrapper = ClaudeContextWrapper()

# Index the entire engine directory
result = wrapper.index_codebase(
    codebase_path='engine/',
    collection_name='agent_forge_engine'
)

print(f"Indexed {result['filesIndexed']} files")
print(f"Created {result['chunksCreated']} chunks")
```

**Expected output:**
```
📚 Indexing codebase: engine/
✅ Indexing complete: 87 files, 1,234 chunks
```

### Example 2: Semantic Code Search

```python
# Search for authentication-related code
results = wrapper.search_code(
    query='GitHub authentication and token management',
    collection_name='agent_forge_engine',
    limit=5
)

# Display results
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['file']} (score: {result['score']:.3f})")
    print(f"   {result['content'][:150]}...")
```

**Expected output:**
```
🔎 Searching: 'GitHub authentication and token management'
✅ Found 5 results

1. engine/operations/github_api_helper.py (score: 0.892)
   def get_github_token(self) -> str:
       """Load GitHub token from secrets."""
       token_file = Path('secrets/agents/...

2. engine/core/service_manager.py (score: 0.845)
   class ServiceManager:
       def authenticate_github(self, token: str):
           """Authenticate with GitHub API using token."""...
```

### Example 3: CLI Usage

The wrapper includes a CLI tool for quick testing:

```bash
# Index a directory
python -m engine.utils.claude_context_wrapper index \
  --path engine/operations \
  --collection operations

# Search
python -m engine.utils.claude_context_wrapper search \
  --query "file editing and git commits" \
  --collection operations \
  --limit 3

# List all collections
python -m engine.utils.claude_context_wrapper list

# Clear a collection
python -m engine.utils.claude_context_wrapper clear \
  --collection operations
```

### Example 4: Integration with Code Agent

```python
# In engine/operations/code_agent.py

from engine.utils.claude_context_wrapper import ClaudeContextWrapper

class CodeAgent:
    def __init__(self):
        self.context = ClaudeContextWrapper()
        
        # Index codebase on startup (or cache check)
        if not self._is_indexed('agent_forge'):
            self.context.index_codebase(
                codebase_path='.',
                collection_name='agent_forge'
            )
    
    def get_relevant_context(self, task_description: str) -> str:
        """
        Get relevant code context for a task using semantic search.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Relevant code snippets as context
        """
        results = self.context.search_code(
            query=task_description,
            collection_name='agent_forge',
            limit=10
        )
        
        # Format results as context for LLM
        context_parts = []
        for r in results:
            context_parts.append(
                f"File: {r['file']}\n"
                f"Score: {r['score']:.3f}\n"
                f"```python\n{r['content']}\n```\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def solve_issue(self, issue_description: str):
        """Solve GitHub issue with semantic code context."""
        # Get relevant code context
        context = self.get_relevant_context(issue_description)
        
        # Build LLM prompt with context
        prompt = f"""
You are solving this issue:
{issue_description}

Here is relevant code from the codebase:
{context}

Provide a solution...
"""
        
        # Send to LLM...
        return self.llm.generate(prompt)
```

---

## Integration with Agent-Forge

### Polling Service Integration

Enhance issue detection with semantic search:

```python
# In engine/runners/polling_service.py

from engine.utils.claude_context_wrapper import ClaudeContextWrapper

class PollingService:
    def __init__(self):
        self.context = ClaudeContextWrapper()
        # Index monitored repositories
        for repo in self.monitored_repos:
            self._ensure_indexed(repo)
    
    def _ensure_indexed(self, repo: str):
        """Ensure repository is indexed."""
        collection_name = repo.replace('/', '_')
        
        # Check if collection exists
        collections = self.context.list_collections()
        if collection_name not in collections:
            logger.info(f"Indexing {repo}...")
            # Clone and index repo
            self._clone_and_index(repo, collection_name)
    
    def process_issue(self, issue: dict):
        """Process issue with semantic code context."""
        repo = issue['repository']['full_name']
        collection_name = repo.replace('/', '_')
        
        # Get relevant code context
        context = self.context.search_code(
            query=issue['title'] + '\n' + issue['body'],
            collection_name=collection_name,
            limit=5
        )
        
        # Enhance issue data with context
        issue['relevant_code'] = context
        
        # Continue with existing logic...
        return self.issue_handler.handle(issue)
```

### Issue Handler Enhancement

```python
# In engine/operations/issue_handler.py

def _build_context(self, issue: dict) -> str:
    """Build context for LLM with semantic search."""
    
    # Get relevant code snippets
    if 'relevant_code' in issue:
        code_context = "\n\n".join([
            f"File: {r['file']}\n```\n{r['content']}\n```"
            for r in issue['relevant_code']
        ])
        
        return f"""
Issue: {issue['title']}
Description: {issue['body']}

Relevant Code Context:
{code_context}

Requirements:
{self._parse_requirements(issue)}
"""
    
    return self._build_basic_context(issue)
```

---

## MCP Server Setup

To use Claude Context with Claude Code, Cursor, or other MCP-compatible tools:

### Claude Code Configuration

```bash
# Add MCP server
claude mcp add claude-context \
  -e OPENAI_API_KEY=sk-your-key \
  -e MILVUS_TOKEN=your-zilliz-token \
  -- npx @zilliz/claude-context-mcp@latest
```

### Continue Extension (VS Code)

Edit `~/.continue/config.json`:

```json
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "MILVUS_ADDRESS": "your-milvus-address",
        "MILVUS_TOKEN": "your-token"
      }
    }
  }
}
```

### Qwen Code Configuration

Edit `~/.qwen/settings.json`:

```json
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "MILVUS_ADDRESS": "your-milvus-address",
        "MILVUS_TOKEN": "your-token"
      }
    }
  }
}
```

---

## Troubleshooting

### Node.js Version Issues

**Problem:** Claude Context requires Node.js 20-23 (not compatible with 24+)

```bash
# Check version
node --version

# If >= 24, downgrade
nvm install 22
nvm use 22
```

### OpenAI API Errors

**Problem:** `401 Unauthorized` or `429 Rate Limit`

**Solution:**
- Verify API key is correct in `secrets/keys/openai.key`
- Check billing on OpenAI platform
- Reduce concurrent indexing operations

### Milvus Connection Errors

**Problem:** `Connection refused` or timeout

**Solutions:**

**Local Milvus:**
```bash
# Check if running
docker ps | grep milvus

# Restart
docker restart milvus-standalone
```

**Zilliz Cloud:**
- Verify endpoint URL is correct
- Check API token is valid
- Ensure firewall allows outbound HTTPS

### Indexing Takes Too Long

**Problem:** Large codebase indexing is slow

**Solutions:**
1. **Use file patterns** to index only relevant files:
   ```python
   wrapper.index_codebase(
       codebase_path='.',
       file_patterns=['**/*.py', '**/*.ts']  # Only Python and TypeScript
   )
   ```

2. **Increase batch size** (edit TypeScript config)

3. **Use faster embedding model:**
   ```python
   wrapper = ClaudeContextWrapper(
       embedding_model='text-embedding-3-small'  # Faster than -large
   )
   ```

### TypeScript Executor Errors

**Problem:** `ts-node not found` or TypeScript execution fails

**Solution:**
```bash
cd tools/claude-context
pnpm install
pnpm build

# Verify ts-node is available
npx ts-node --version
```

---

## Performance Tips

### 1. Optimize Embedding Model Selection

| Model | Dimensions | Speed | Quality | Cost |
|-------|------------|-------|---------|------|
| `text-embedding-3-small` | 1536 | Fast | Good | Low |
| `text-embedding-3-large` | 3072 | Slow | Excellent | High |
| `text-embedding-ada-002` | 1536 | Medium | Good | Medium |

**Recommendation:** Use `text-embedding-3-small` for development/testing, `text-embedding-3-large` for production.

### 2. Batch Indexing

Index large codebases in batches:

```python
# Index by subdirectory
for subdir in ['engine', 'api', 'frontend']:
    wrapper.index_codebase(
        codebase_path=subdir,
        collection_name=f'agent_forge_{subdir}'
    )
```

### 3. Cache Search Results

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def search_cached(query: str, collection: str) -> tuple:
    """Cache search results for repeated queries."""
    results = wrapper.search_code(query, collection)
    return tuple(json.dumps(r) for r in results)
```

### 4. Incremental Updates

Re-index only changed files:

```python
# Get list of changed files from git
changed_files = subprocess.check_output(
    ['git', 'diff', '--name-only', 'HEAD~1'],
    text=True
).splitlines()

# Re-index only those files (requires custom implementation)
# Or clear and re-index the entire collection periodically
```

### 5. Monitor Vector DB Size

```python
# Check collection statistics
stats = wrapper.list_collections()
print(f"Total collections: {len(stats)}")

# Clear unused collections
wrapper.clear_index('old_collection_name')
```

---

## Example: Complete Integration Test

```python
#!/usr/bin/env python3
"""
Complete integration test for Claude Context in Agent-Forge.
"""

import logging
from pathlib import Path
from engine.utils.claude_context_wrapper import ClaudeContextWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integration():
    """Run complete integration test."""
    
    # Initialize
    logger.info("🚀 Starting Claude Context integration test")
    wrapper = ClaudeContextWrapper()
    
    # Index codebase
    logger.info("📚 Indexing Agent-Forge codebase...")
    result = wrapper.index_codebase(
        codebase_path='engine/operations',
        collection_name='test_operations'
    )
    logger.info(f"✅ Indexed {result.get('filesIndexed', 0)} files")
    
    # Test search queries
    test_queries = [
        "GitHub API authentication and token management",
        "File editing and git commit operations",
        "Issue detection and parsing requirements",
        "WebSocket monitoring and live logs"
    ]
    
    for query in test_queries:
        logger.info(f"\n🔎 Testing query: '{query}'")
        results = wrapper.search_code(
            query=query,
            collection_name='test_operations',
            limit=3
        )
        
        for i, r in enumerate(results, 1):
            logger.info(f"  {i}. {r.get('file', 'unknown')} "
                       f"(score: {r.get('score', 0):.3f})")
    
    # Cleanup
    logger.info("\n🗑️  Cleaning up test collection...")
    wrapper.clear_index('test_operations')
    
    logger.info("\n✅ Integration test complete!")

if __name__ == '__main__':
    test_integration()
```

Save this as `scripts/test_claude_context_integration.py` and run:

```bash
python3 scripts/test_claude_context_integration.py
```

---

## Next Steps

1. **Index your codebase:** Run indexing on Agent-Forge
2. **Test search queries:** Verify semantic search works
3. **Integrate with agents:** Enhance Code Agent and Issue Handler
4. **Monitor performance:** Track indexing time and search quality
5. **Scale up:** Use Zilliz Cloud for production

## Resources

- [Claude Context GitHub](https://github.com/zilliztech/claude-context)
- [Milvus Documentation](https://milvus.io/docs)
- [Zilliz Cloud](https://cloud.zilliz.com/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

**Questions or issues?** Check the [Claude Context Discussions](https://github.com/zilliztech/claude-context/discussions) or open an issue in this repo.

Happy coding! 🚀
