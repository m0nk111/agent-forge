"""
Code Indexer for RAG System

Indexes Python source code by:
1. Parsing files with AST
2. Extracting functions, classes, and docstrings
3. Chunking code intelligently
4. Generating embeddings
5. Storing in vector database

Supports incremental updates and file watching.
"""

import logging
import ast
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import hashlib

from ..embedding_service import EmbeddingService
from ..vector_store import MilvusVectorStore


logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    id: str  # Unique identifier (hash of file path + chunk position)
    content: str  # Source code
    file_path: str
    chunk_type: str  # 'function', 'class', 'module'
    name: str  # Function/class name
    docstring: Optional[str]
    start_line: int
    end_line: int
    language: str = "python"


class CodeIndexer:
    """Index Python code for RAG retrieval."""
    
    def __init__(
        self,
        root_dir: Path,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[MilvusVectorStore] = None
    ):
        """Initialize code indexer.
        
        Args:
            root_dir: Root directory to index
            embedding_service: EmbeddingService instance (creates default if None)
            vector_store: MilvusVectorStore instance (creates default if None)
        """
        self.root_dir = Path(root_dir)
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or MilvusVectorStore(
            embedding_dim=self.embedding_service.embedding_dim or 384
        )
        
        # Tracking
        self.indexed_files: Dict[str, str] = {}  # file_path -> hash
        self.total_chunks = 0
    
    def index_workspace(
        self,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size_kb: int = 500
    ) -> int:
        """Index all Python files in workspace.
        
        Args:
            exclude_patterns: Patterns to exclude (e.g., ['*/tests/*', '*/venv/*'])
            max_file_size_kb: Skip files larger than this
            
        Returns:
            Number of chunks indexed
        """
        logger.info(f"🔍 Indexing Python files in {self.root_dir}")
        
        exclude_patterns = exclude_patterns or [
            "**/venv/**", "**/.venv/**", "**/env/**",
            "**/__pycache__/**", "**/.git/**",
            "**/node_modules/**", "**/site-packages/**"
        ]
        
        python_files = self._find_python_files(exclude_patterns, max_file_size_kb)
        
        all_chunks = []
        for file_path in python_files:
            try:
                chunks = self._parse_file(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse {file_path}: {e}")
        
        if all_chunks:
            self._store_chunks(all_chunks)
        
        logger.info(f"✅ Indexed {len(python_files)} files, {len(all_chunks)} chunks")
        self.total_chunks = len(all_chunks)
        
        return len(all_chunks)
    
    def _find_python_files(
        self,
        exclude_patterns: List[str],
        max_size_kb: int
    ) -> List[Path]:
        """Find all Python files in workspace."""
        files = []
        
        # Convert patterns to string parts for matching
        exclude_parts = ['venv', '.venv', 'env', '__pycache__', '.git', 'node_modules', 'site-packages']
        
        for path in self.root_dir.rglob("*.py"):
            # Check exclusions (simple string matching)
            path_str = str(path)
            if any(part in path_str for part in exclude_parts):
                continue
            
            # Check size
            if path.stat().st_size > max_size_kb * 1024:
                logger.debug(f"⏭️ Skipping large file: {path}")
                continue
            
            files.append(path)
        
        return files
    
    def _parse_file(self, file_path: Path) -> List[CodeChunk]:
        """Parse Python file and extract code chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=str(file_path))
            chunks = []
            
            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = self._extract_function(node, source, file_path)
                    if chunk:
                        chunks.append(chunk)
                
                elif isinstance(node, ast.ClassDef):
                    chunk = self._extract_class(node, source, file_path)
                    if chunk:
                        chunks.append(chunk)
            
            # Also add module-level docstring if exists
            module_doc = ast.get_docstring(tree)
            if module_doc:
                chunks.append(self._create_module_chunk(source, file_path, module_doc))
            
            return chunks
            
        except SyntaxError as e:
            logger.warning(f"⚠️ Syntax error in {file_path}: {e}")
            return []
    
    def _extract_function(
        self,
        node: ast.FunctionDef,
        source: str,
        file_path: Path
    ) -> Optional[CodeChunk]:
        """Extract function definition as code chunk."""
        try:
            # Get source code for this function
            lines = source.split('\n')
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            function_source = '\n'.join(lines[start_line:end_line])
            
            # Skip very small or very large functions
            if len(function_source) < 20 or len(function_source) > 10000:
                return None
            
            # Generate unique ID
            chunk_id = self._generate_chunk_id(file_path, start_line, "function")
            
            return CodeChunk(
                id=chunk_id,
                content=function_source,
                file_path=str(file_path.relative_to(self.root_dir)),
                chunk_type="function",
                name=node.name,
                docstring=ast.get_docstring(node),
                start_line=start_line + 1,
                end_line=end_line,
                language="python"
            )
        except Exception as e:
            logger.debug(f"Failed to extract function: {e}")
            return None
    
    def _extract_class(
        self,
        node: ast.ClassDef,
        source: str,
        file_path: Path
    ) -> Optional[CodeChunk]:
        """Extract class definition as code chunk."""
        try:
            lines = source.split('\n')
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            class_source = '\n'.join(lines[start_line:end_line])
            
            # Skip very large classes (will be indexed via methods)
            if len(class_source) > 15000:
                return None
            
            chunk_id = self._generate_chunk_id(file_path, start_line, "class")
            
            return CodeChunk(
                id=chunk_id,
                content=class_source,
                file_path=str(file_path.relative_to(self.root_dir)),
                chunk_type="class",
                name=node.name,
                docstring=ast.get_docstring(node),
                start_line=start_line + 1,
                end_line=end_line,
                language="python"
            )
        except Exception as e:
            logger.debug(f"Failed to extract class: {e}")
            return None
    
    def _create_module_chunk(
        self,
        source: str,
        file_path: Path,
        docstring: str
    ) -> CodeChunk:
        """Create chunk for module-level docstring."""
        chunk_id = self._generate_chunk_id(file_path, 0, "module")
        
        # Include docstring + first 500 chars of module
        content = docstring + "\n\n" + source[:500]
        
        return CodeChunk(
            id=chunk_id,
            content=content,
            file_path=str(file_path.relative_to(self.root_dir)),
            chunk_type="module",
            name=file_path.stem,
            docstring=docstring,
            start_line=1,
            end_line=1,
            language="python"
        )
    
    def _generate_chunk_id(self, file_path: Path, line: int, chunk_type: str) -> str:
        """Generate unique ID for code chunk."""
        content = f"{file_path}:{line}:{chunk_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _store_chunks(self, chunks: List[CodeChunk]):
        """Generate embeddings and store chunks in vector database."""
        logger.info(f"📦 Storing {len(chunks)} code chunks...")
        
        # Prepare data for batch insertion
        ids = []
        contents = []
        metadata_list = []
        
        for chunk in chunks:
            # Create rich content for embedding (code + docstring + context)
            embedding_content = self._create_embedding_content(chunk)
            
            ids.append(chunk.id)
            contents.append(embedding_content)
            metadata_list.append({
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "docstring": chunk.docstring or "",
                "language": chunk.language
            })
        
        # Generate embeddings in batch
        logger.info("🧠 Generating embeddings...")
        embeddings = self.embedding_service.embed(contents)
        
        # Store in vector database
        self.vector_store.insert(
            collection_name="code",
            ids=ids,
            embeddings=embeddings,
            contents=contents,
            metadata=metadata_list
        )
    
    def _create_embedding_content(self, chunk: CodeChunk) -> str:
        """Create rich content for embedding generation.
        
        Combines code, docstring, and context for better semantic search.
        """
        parts = []
        
        # File context
        parts.append(f"# File: {chunk.file_path}")
        
        # Type context
        parts.append(f"# Type: {chunk.chunk_type} - {chunk.name}")
        
        # Docstring (if available)
        if chunk.docstring:
            parts.append(f"# Description: {chunk.docstring[:200]}")
        
        # Actual code
        parts.append(chunk.content)
        
        return "\n".join(parts)
    
    def update_file(self, file_path: Path) -> int:
        """Update index for a single file.
        
        Args:
            file_path: Path to file that changed
            
        Returns:
            Number of chunks updated
        """
        logger.info(f"🔄 Updating index for {file_path}")
        
        # Remove old chunks for this file
        # (In production, would query by file_path metadata and delete)
        
        # Re-index file
        chunks = self._parse_file(file_path)
        if chunks:
            self._store_chunks(chunks)
        
        return len(chunks)
    
    def close(self):
        """Clean up resources."""
        self.vector_store.close()
        logger.info("👋 Code indexer closed")


# Convenience function for quick indexing
def index_code(workspace_path: str) -> int:
    """Quick code indexing using default indexer.
    
    Args:
        workspace_path: Root workspace directory
        
    Returns:
        Number of chunks indexed
    """
    indexer = CodeIndexer(root_dir=Path(workspace_path))
    count = indexer.index_workspace()
    indexer.close()
    return count

