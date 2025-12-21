# RAG System - Retrieval-Augmented Generation

Complete RAG (Retrieval-Augmented Generation) system for agent-forge. Provides LLM agents with relevant context from codebase, documentation, and issue history to improve code generation quality and problem-solving accuracy.

## 🚀 Quick Start

### 1. Start Milvus Vector Database

```bash
cd /home/flip/agent-forge
docker-compose -f docker-compose-milvus.yml up -d
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Index Your Workspace

```bash
# Index all content (code, docs, and optionally issues)
python scripts/rag_cli.py index-all /home/flip/agent-forge --owner m0nk111 --repo agent-forge

# Or index individually
python scripts/rag_cli.py index-code /home/flip/agent-forge
python scripts/rag_cli.py index-docs /home/flip/agent-forge
python scripts/rag_cli.py index-issues m0nk111 agent-forge --state closed --limit 100
```

### 4. Search for Context

```bash
# Search across all collections
python scripts/rag_cli.py search "how to handle GitHub issues" --top-k 5

# Search specific source
python scripts/rag_cli.py search "code generation" --sources code --top-k 3
```

### 5. View Statistics

```bash
python scripts/rag_cli.py stats
```

## 📦 Components

### Embedding Service (`embedding_service.py`)

Multi-backend embedding generation:
- **sentence-transformers** (default): Local, 768D, **jinaai/jina-embeddings-v2-base-code** model (code-specialized)
  - **Upgraded 2025-11-01**: Previously used all-MiniLM-L6-v2 (384D, general-purpose)
  - **Benefits**: Better semantic understanding of code, 2x dimensionality, code-specific training
  - **Stats**: 100K downloads, 124 likes on HuggingFace, 137M parameters
- **Ollama**: Local, 768D, nomic-embed-text model
- **OpenAI**: Cloud, 1536D, text-embedding-3-small model

```python
from engine.rag.embedding_service import EmbeddingService

# Use default (sentence-transformers with jina-embeddings-v2-base-code)
embedder = EmbeddingService()  # 768D embeddings

# Or specify backend
embedder = EmbeddingService(backend="ollama")

# Generate embeddings
embeddings = embedder.embed(["hello world", "test query"])
```

### Vector Store (`vector_store.py`)

Milvus vector database wrapper with 3 collections:
- **code**: Python functions, classes, modules (768D embeddings)
- **docs**: Markdown documentation sections (768D embeddings)
- **issues**: GitHub issue problem-solution pairs (768D embeddings)

**Note**: All collections use 768D embeddings as of 2025-11-01. If you have old 384D data, you must drop and reindex.

```python
from engine.rag.vector_store import MilvusVectorStore

store = MilvusVectorStore(embedding_dim=768)  # Updated to 768D
```

# Insert vectors
store.insert(
    collection_name="code",
    ids=["chunk1"],
    embeddings=[[0.1, 0.2, ...]],
    contents=["def hello(): ..."],
    metadata=[{"file": "test.py"}]
)

# Search
results = store.search(
    collection_name="code",
    query_embedding=[0.1, 0.2, ...],
    top_k=5
)
```

### Indexers (`indexers/`)

#### Code Indexer (`code_indexer.py`)
- Python AST parsing
- Function/class/module extraction
- Smart chunking (excludes <20 char and >10KB chunks)
- Extracts docstrings and tracks line numbers

```python
from engine.rag.indexers import CodeIndexer
from pathlib import Path

indexer = CodeIndexer(root_dir=Path("/home/flip/agent-forge"))
count = indexer.index_workspace()
indexer.close()
```

#### Documentation Indexer (`docs_indexer.py`)
- Markdown parsing with section detection
- Heading hierarchy tracking
- Handles README, CONTRIBUTING, CHANGELOG, etc.

```python
from engine.rag.indexers import DocsIndexer

indexer = DocsIndexer()
count = indexer.index_workspace("/home/flip/agent-forge")
indexer.close()
```

#### Issue Indexer (`issue_indexer.py`)
- GitHub CLI and REST API integration
- Problem-solution extraction from closed issues
- Metadata: issue number, title, labels, timestamps

```python
from engine.rag.indexers import IssueIndexer

indexer = IssueIndexer()
count = indexer.index_repository(
    owner="m0nk111",
    repo="agent-forge",
    state="closed",
    limit=100
)
indexer.close()
```

### RAG Retriever (`retriever.py`)

Main interface for retrieval:
- Query processing and similarity search
- Result reranking and filtering (min_score: 0.5)
- Context formatting for LLM prompts
- Specialized methods for code generation and issue resolution

```python
from engine.rag.retriever import RAGRetriever

retriever = RAGRetriever(top_k=5)

# General search
results = retriever.retrieve(
    query="how to parse Python code",
    sources=["code", "docs"],
    top_k=5
)

# Code generation context
context = retriever.get_context_for_code_generation(
    task_description="implement a file parser",
    file_path="engine/operations/parser.py",
    max_context_length=3000
)

# Issue resolution context
context = retriever.get_context_for_issue_resolution(
    issue_description="Fix parsing error in code generator",
    max_context_length=4000
)

retriever.close()
```

## 🔌 Integration with Agents

### Code Generator Integration

The RAG system is automatically integrated into `engine/operations/code_generator.py`:

```python
# Automatically retrieves relevant code examples before generation
def _generate_implementation(self, spec: ModuleSpec, previous_errors: List[str]):
    # RAG context automatically injected
    rag_context = self._get_rag_context_for_generation(spec)
    # ... rest of implementation
```

### Issue Handler Integration

The RAG system is automatically integrated into `engine/operations/issue_handler.py`:

```python
# Automatically retrieves similar resolved issues before planning
def _generate_plan(self, requirements: Dict, issue: Dict, context_insights: Optional[Dict]):
    # RAG historical context automatically retrieved
    historical_context = self._get_rag_historical_context(issue)
    # ... rest of planning
```

## ⚙️ Configuration

Edit `config/services/rag.yaml` to customize:

```yaml
# Embedding backend
embedding:
  backend: "sentence-transformers"  # or "ollama", "openai"

# Milvus connection
milvus:
  host: "localhost"
  port: 19530

# Retrieval settings
retrieval:
  default_top_k: 5
  min_score: 0.5
  max_context_length:
    code_generation: 3000
    issue_resolution: 4000

# Indexing settings
indexers:
  code:
    max_file_size: 524288  # 512KB
    min_chunk_length: 20
    max_chunk_length: 10240  # 10KB
```

## 📊 CLI Commands

### Indexing

```bash
# Index code
rag_cli.py index-code <workspace_path>

# Index documentation
rag_cli.py index-docs <workspace_path>

# Index GitHub issues
rag_cli.py index-issues <owner> <repo> [--state closed] [--limit 100]

# Index everything
rag_cli.py index-all <workspace_path> [--owner <owner> --repo <repo>]
```

### Search

```bash
# Search all collections
rag_cli.py search "query text" [--sources code,docs,issues] [--top-k 5]
```

### Management

```bash
# Show statistics
rag_cli.py stats

# Clear collections
rag_cli.py clear [--collections code,docs,issues] [--yes]
```

## 🔍 How It Works

### 1. Indexing Phase

```
Source Files → Parser (AST/Markdown) → Chunks → Embeddings → Milvus
```

1. **Code Files**: Python AST parsing extracts functions, classes, docstrings
2. **Docs Files**: Markdown parsing extracts sections with heading hierarchy
3. **Issues**: GitHub API fetches closed issues with problem-solution pairs
4. **Embeddings**: sentence-transformers generates 384D vectors
5. **Storage**: Vectors stored in Milvus with metadata and timestamps

### 2. Retrieval Phase

```
Query → Embedding → Similarity Search → Reranking → Context Formatting → LLM
```

1. **Query**: User query or task description
2. **Embedding**: Query converted to 384D vector
3. **Search**: Cosine similarity search across collections
4. **Filtering**: Results filtered by min_score threshold (0.5)
5. **Ranking**: Results sorted by relevance score
6. **Formatting**: Results formatted with metadata for LLM consumption

### 3. Context Injection

**Code Generator**:
```python
prompt = f"""
{description}
{requirements}

{rag_context}  ← Relevant code examples injected here

{guidelines}
"""
```

**Issue Handler**:
```python
plan = {
    'title': title,
    'phases': phases,
    'historical_context': rag_context  ← Similar resolved issues injected here
}
```

## 🧪 Testing

```bash
# Create test workspace
mkdir -p /tmp/rag-test
echo 'def hello(): return "world"' > /tmp/rag-test/test.py

# Index test workspace
python scripts/rag_cli.py index-code /tmp/rag-test

# Search test
python scripts/rag_cli.py search "hello function" --sources code --top-k 1
```

Expected output:
```
Result 1 - Score: 0.648 - Source: code
### Code from: test.py
Type: function - hello
Lines: 1-1

```python
def hello(): return "world"
```
```

## 🚧 Future Enhancements

- [ ] Incremental indexing (file watching)
- [ ] Git hooks for auto-indexing on commit
- [ ] Performance metrics and monitoring
- [ ] Result reranking with cross-encoder
- [ ] Multi-language support (JavaScript, TypeScript, etc.)
- [ ] Vector database persistence and backup
- [ ] Query expansion and reformulation
- [ ] Context caching for repeated queries

## 📚 Dependencies

- **pymilvus** (>=2.4.0): Milvus vector database client
- **sentence-transformers** (>=2.2.0): Local embedding model
- **torch** (>=2.0.0): PyTorch for sentence-transformers
- **numpy** (>=1.24.0): Numerical computing
- **openai** (>=1.0.0): OpenAI API client (optional)

## 🐛 Troubleshooting

### Milvus Connection Error

```bash
# Check if Milvus is running
docker ps | grep milvus

# Start Milvus
docker-compose -f docker-compose-milvus.yml up -d

# Check logs
docker-compose -f docker-compose-milvus.yml logs
```

### Import Errors

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Low Relevance Scores

- Adjust `min_score` in `config/services/rag.yaml` (default: 0.5)
- Try different embedding backends (Ollama for larger embeddings)
- Index more content for better coverage

### Slow Indexing

- Reduce batch size in config
- Use GPU for sentence-transformers (set `device: cuda`)
- Index in parallel (split workspace into chunks)

## 📄 License

Part of agent-forge project. See root LICENSE file.
