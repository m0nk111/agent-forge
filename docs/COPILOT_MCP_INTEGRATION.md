# GitHub Copilot MCP Integration with Claude Context

**Date**: 2025-10-14  
**Status**: ✅ **CONFIGURED** - Claude Context MCP server active in GitHub Copilot

Complete guide for using Claude Context semantic search directly in GitHub Copilot chat.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Usage in Copilot](#usage-in-copilot)
- [Available MCP Tools](#available-mcp-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What is MCP?

**MCP (Model Context Protocol)** is a protocol that allows AI assistants to use external tools and services. With MCP, GitHub Copilot can:

- Access semantic code search via Claude Context
- Query your indexed codebase with natural language
- Get relevant code snippets automatically
- Use hybrid search (BM25 + dense vectors)

### Benefits

**Before MCP**:
- Copilot only sees files you have open
- Limited context from workspace
- Manual file searching needed

**After MCP with Claude Context**:
- 🔍 **Semantic search** across entire codebase
- 🎯 **Hybrid search** (BM25 + OpenAI embeddings)
- 💬 **Natural language queries** in Copilot chat
- 🚀 **Auto-indexed** codebase with vector embeddings

---

## Configuration

### Prerequisites

1. **GitHub Copilot** subscription active
2. **Node.js** 20-23 installed (not 24+)
3. **Milvus** running (localhost:19530 or Zilliz Cloud)
4. **OpenAI API key** in `/home/flip/agent-forge/secrets/keys/openai.key`
5. **Codebase indexed** with Claude Context

### MCP Configuration File

**Location**: `~/.vscode-server/data/User/globalStorage/github.copilot-chat/mcp.json`

**Configuration**:
```json
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key",
        "MILVUS_ADDRESS": "localhost:19530",
        "HYBRID_MODE": "true"
      }
    }
  }
}
```

**Environment Variables**:
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `MILVUS_ADDRESS`: Milvus connection string
  - Local: `localhost:19530`
  - Zilliz Cloud: `https://in03-xxxxx.api.gcp-us-west1.zillizcloud.com`
- `MILVUS_TOKEN`: (Optional) Zilliz Cloud API token
- `HYBRID_MODE`: `"true"` for BM25 + dense hybrid search

### Installation Steps

**1. Create MCP config**:
```bash
# Navigate to Copilot chat directory
cd ~/.vscode-server/data/User/globalStorage/github.copilot-chat/

# Create mcp.json with your OpenAI key
cat > mcp.json << 'EOF'
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-key-here",
        "MILVUS_ADDRESS": "localhost:19530",
        "HYBRID_MODE": "true"
      }
    }
  }
}
EOF
```

**2. Restart VS Code** or reload window:
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "Reload Window"
- Press Enter

**3. Verify MCP server loaded**:
- Open Copilot chat
- Type `@` and you should see MCP tools available

---

## Usage in Copilot

### Basic Semantic Search

**In Copilot Chat**:
```
@workspace Search for "GitHub API authentication" in my codebase
```

Copilot will use the Claude Context MCP server to:
1. Generate query embedding (OpenAI)
2. Generate BM25 sparse vector
3. Execute hybrid search in Milvus
4. Return top relevant code snippets

### Natural Language Queries

**Find implementation patterns**:
```
Show me how we handle error retries in API calls
```

**Find specific features**:
```
Where is the OAuth authentication implemented?
```

**Architectural queries**:
```
How does our agent coordinator work?
```

### Context-Aware Development

**Before implementing**:
```
I need to add user authentication. Show me similar implementations in our codebase.
```

**For refactoring**:
```
Find all places where we call the GitHub API
```

**For debugging**:
```
Search for error handling in the polling service
```

---

## Available MCP Tools

### 1. `semantic_search`

**Purpose**: Search codebase with natural language query

**Parameters**:
- `query` (string): Natural language search query
- `codebasePath` (string): Path to search in (default: workspace root)
- `topK` (number): Number of results (default: 5)

**Example**:
```typescript
{
  "tool": "semantic_search",
  "params": {
    "query": "GitHub API authentication",
    "codebasePath": "/home/flip/agent-forge/engine/operations",
    "topK": 5
  }
}
```

**Returns**:
```json
[
  {
    "relativePath": "pr_github_client.py",
    "startLine": 20,
    "endLine": 82,
    "score": 0.0193,
    "contentPreview": "class GitHubAPIClient:..."
  }
]
```

### 2. `index_codebase`

**Purpose**: Index a codebase for semantic search

**Parameters**:
- `codebasePath` (string): Path to codebase
- `force` (boolean): Force reindex (default: false)

**Example**:
```typescript
{
  "tool": "index_codebase",
  "params": {
    "codebasePath": "/home/flip/agent-forge",
    "force": false
  }
}
```

**Returns**:
```json
{
  "status": "completed",
  "indexedFiles": 38,
  "totalChunks": 606
}
```

### 3. `list_collections`

**Purpose**: List all indexed codebases

**Returns**:
```json
[
  "code_chunks_637c7a0f",
  "code_chunks_abc123ef"
]
```

---

## Examples

### Example 1: Finding Authentication Code

**Copilot Chat**:
```
I need to understand how we handle GitHub authentication. 
Can you search our codebase and explain the implementation?
```

**What happens**:
1. Copilot invokes `semantic_search` MCP tool
2. Query: "GitHub authentication implementation"
3. Claude Context returns relevant files:
   - `pr_github_client.py` (score: 0.0193)
   - `github_api_helper.py` (score: 0.0145)
   - `bot_operations.py` (score: 0.0098)
4. Copilot reads those files and explains

### Example 2: Before Implementing New Feature

**Copilot Chat**:
```
I want to add rate limiting to API calls. 
Show me if we already have similar implementations.
```

**What happens**:
1. MCP tool searches: "rate limiting API calls"
2. Finds:
   - Existing rate limit handling in `pr_review_agent.py`
   - Retry logic in `github_api_helper.py`
3. Copilot suggests using existing patterns

### Example 3: Debugging

**Copilot Chat**:
```
We're getting errors in the polling service. 
Search for error handling in that component.
```

**What happens**:
1. Query: "error handling polling service"
2. Returns relevant error handling code
3. Copilot analyzes and suggests fixes

### Example 4: Architecture Understanding

**Copilot Chat**:
```
Explain how our multi-agent system coordinates tasks
```

**What happens**:
1. Searches: "agent coordination task management"
2. Finds:
   - `coordinator_agent.py`
   - `agent_registry.py`
   - `task_queue.py`
3. Copilot provides architectural overview

---

## Troubleshooting

### Issue: MCP Tools Not Available

**Symptom**: `@` in Copilot chat doesn't show MCP tools

**Causes**:
1. MCP config file not in correct location
2. VS Code not reloaded after config change
3. Syntax error in mcp.json

**Solution**:
```bash
# Verify config exists
cat ~/.vscode-server/data/User/globalStorage/github.copilot-chat/mcp.json

# Check for JSON syntax errors
python3 -m json.tool ~/.vscode-server/data/User/globalStorage/github.copilot-chat/mcp.json

# Reload VS Code
# Ctrl+Shift+P → "Reload Window"
```

### Issue: "Claude Context MCP Server Failed"

**Symptom**: Error message when trying to use MCP tool

**Causes**:
1. Milvus not running
2. Invalid OpenAI API key
3. Node.js version incompatible (24+)

**Solution**:
```bash
# Check Milvus
docker ps | grep milvus

# Check OpenAI key
cat /home/flip/agent-forge/secrets/keys/openai.key | wc -c
# Should be ~200+ characters

# Check Node.js version
node --version
# Should be v20.x - v23.x (NOT v24+)
```

### Issue: No Results Returned

**Symptom**: Search returns empty results

**Causes**:
1. Codebase not indexed
2. Collection name mismatch
3. Milvus connection issue

**Solution**:
```bash
# Index codebase
cd /home/flip/agent-forge/tools/claude-context
OPENAI_API_KEY=$(cat /home/flip/agent-forge/secrets/keys/openai.key) \
  npx ts-node test_indexing.ts

# Check Milvus collections
python3 << 'EOF'
from pymilvus import connections, utility
connections.connect(host="localhost", port=19530)
print(utility.list_collections())
EOF
```

### Issue: Slow Search Performance

**Symptom**: MCP tool takes >5 seconds to respond

**Causes**:
1. Auto-fit encoder on first search (~500ms)
2. Large collection (>10k entities)
3. Network latency (Zilliz Cloud)

**Solution**:
- First search is slower (auto-fit vocabulary)
- Subsequent searches should be fast (<500ms)
- Consider caching or persistent vocabulary

### Issue: "HYBRID_MODE not supported"

**Symptom**: Error about hybrid mode

**Cause**: Using older version of Claude Context

**Solution**:
```bash
# Update to latest version
npx @zilliz/claude-context-mcp@latest --version

# Should be using submodule with BM25 fix
cd /home/flip/agent-forge/tools/claude-context
git log --oneline -1
# Should show: "feat(bm25): implement client-side BM25..."
```

---

## Advanced Configuration

### Using Zilliz Cloud

**mcp.json with Zilliz Cloud**:
```json
{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "MILVUS_ADDRESS": "https://in03-xxxxx.api.gcp-us-west1.zillizcloud.com",
        "MILVUS_TOKEN": "your-zilliz-cloud-api-key",
        "HYBRID_MODE": "true"
      }
    }
  }
}
```

### Multiple Codebases

**Index multiple projects**:
```json
{
  "mcpServers": {
    "claude-context-project1": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "...",
        "MILVUS_ADDRESS": "localhost:19530",
        "CODEBASE_PATH": "/home/user/project1"
      }
    },
    "claude-context-project2": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "env": {
        "OPENAI_API_KEY": "...",
        "MILVUS_ADDRESS": "localhost:19530",
        "CODEBASE_PATH": "/home/user/project2"
      }
    }
  }
}
```

### Custom Embedding Model

**Use different OpenAI model**:
```json
{
  "env": {
    "OPENAI_API_KEY": "...",
    "OPENAI_EMBEDDING_MODEL": "text-embedding-3-large",
    "MILVUS_ADDRESS": "localhost:19530"
  }
}
```

---

## Best Practices

### 1. Keep Codebase Indexed

**Re-index after major changes**:
```bash
# Force reindex
cd /home/flip/agent-forge/tools/claude-context
OPENAI_API_KEY=$(cat /home/flip/agent-forge/secrets/keys/openai.key) \
  npx ts-node test_indexing.ts
```

### 2. Use Specific Queries

**Good queries**:
- "GitHub API authentication with retry logic"
- "Error handling in polling service"
- "OAuth token refresh implementation"

**Bad queries**:
- "code"
- "function"
- "help"

### 3. Leverage Hybrid Search

Hybrid search (HYBRID_MODE=true) combines:
- Semantic similarity (dense vectors)
- Keyword matching (BM25 sparse vectors)
- Best of both worlds!

### 4. Context-Aware Prompts

**Instead of**:
```
How do I implement authentication?
```

**Try**:
```
Search our codebase for authentication implementations, 
then suggest how to add OAuth2 support
```

---

## Summary

### What We Configured

✅ **GitHub Copilot MCP integration** with Claude Context  
✅ **Hybrid search enabled** (BM25 + dense vectors)  
✅ **Semantic code search** in Copilot chat  
✅ **Auto-indexed codebase** with 606 entities  
✅ **Natural language queries** supported

### Usage

**In Copilot Chat, just ask**:
- "Search for [topic] in our codebase"
- "Show me how we implement [feature]"
- "Find [pattern] examples"

Copilot will automatically use the MCP server to search semantically!

### Benefits

🔍 **Better Context**: Copilot sees entire codebase  
💰 **Cost Efficient**: Only loads relevant code  
🎯 **Accurate**: Hybrid search finds exact + similar code  
⚡ **Fast**: Sub-second search with indexed vectors  

---

**Next Steps**:
1. Reload VS Code window
2. Open Copilot chat
3. Try: "Search for GitHub authentication in our codebase"
4. Watch the magic happen! ✨

**Documentation**: See also
- [BM25_HYBRID_SEARCH.md](BM25_HYBRID_SEARCH.md)
- [CLAUDE_CONTEXT_INTEGRATION.md](CLAUDE_CONTEXT_INTEGRATION.md)
- [CLAUDE_CONTEXT_STATUS.md](CLAUDE_CONTEXT_STATUS.md)
