"""
Documentation Indexer - Index markdown documentation

Indexes markdown files into RAG system:
1. Scans workspace for markdown files
2. Parses documents into sections
3. Chunks by headings for context
4. Generates embeddings
5. Stores in vector database
"""

import os
import logging
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..embedding_service import EmbeddingService
from ..vector_store import MilvusVectorStore

logger = logging.getLogger(__name__)


@dataclass
class DocChunk:
    """Documentation chunk with metadata."""
    content: str
    file_path: str
    section: str  # Heading hierarchy (e.g., "Setup > Installation")
    level: int  # Heading level (1-6)
    chunk_id: str
    metadata: Dict[str, Any]


class DocsIndexer:
    """Index markdown documentation into RAG system."""
    
    # Directories to exclude
    EXCLUDE_DIRS = {
        '__pycache__', '.git', 'node_modules', 'venv', '.venv',
        'env', '.env', 'build', 'dist', '.pytest_cache', '.tox'
    }
    
    # File patterns to include
    INCLUDE_PATTERNS = [
        '*.md', '*.MD', '*.markdown', '*.MARKDOWN',
        'README', 'CONTRIBUTING', 'CHANGELOG', 'LICENSE'
    ]
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[MilvusVectorStore] = None,
        min_chunk_length: int = 50,
        max_chunk_length: int = 8000
    ):
        """Initialize documentation indexer.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector database instance
            min_chunk_length: Minimum chunk length in characters
            max_chunk_length: Maximum chunk length in characters
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or MilvusVectorStore(
            embedding_dim=self.embedding_service.embedding_dim
        )
        self.min_chunk_length = min_chunk_length
        self.max_chunk_length = max_chunk_length
        
        logger.info("📚 Documentation indexer initialized")
    
    def index_workspace(
        self,
        workspace_path: str,
        additional_paths: Optional[List[str]] = None
    ) -> int:
        """Index all markdown files in workspace.
        
        Args:
            workspace_path: Root workspace directory
            additional_paths: Additional paths to index (absolute or relative)
            
        Returns:
            Number of chunks indexed
        """
        logger.info(f"📂 Indexing documentation from: {workspace_path}")
        
        workspace_path = os.path.abspath(workspace_path)
        all_chunks = []
        
        # Index main workspace
        main_chunks = self._scan_directory(workspace_path)
        all_chunks.extend(main_chunks)
        
        # Index additional paths
        if additional_paths:
            for path in additional_paths:
                if not os.path.isabs(path):
                    path = os.path.join(workspace_path, path)
                
                if os.path.isfile(path):
                    chunks = self._parse_file(path)
                    all_chunks.extend(chunks)
                elif os.path.isdir(path):
                    chunks = self._scan_directory(path)
                    all_chunks.extend(chunks)
        
        # Store chunks
        total_stored = self._store_chunks(all_chunks)
        
        logger.info(f"✅ Indexed {total_stored} documentation chunks")
        return total_stored
    
    def _scan_directory(self, root_path: str) -> List[DocChunk]:
        """Recursively scan directory for markdown files."""
        all_chunks = []
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Remove excluded directories
            dirnames[:] = [d for d in dirnames if d not in self.EXCLUDE_DIRS]
            
            # Process markdown files
            for filename in filenames:
                if self._is_markdown_file(filename):
                    file_path = os.path.join(dirpath, filename)
                    
                    try:
                        chunks = self._parse_file(file_path)
                        all_chunks.extend(chunks)
                        logger.debug(f"📄 Parsed {len(chunks)} chunks from {filename}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse {file_path}: {e}")
        
        return all_chunks
    
    def _is_markdown_file(self, filename: str) -> bool:
        """Check if file is a markdown file."""
        # Check extensions
        if any(filename.endswith(ext.replace('*', '')) for ext in self.INCLUDE_PATTERNS if '*' in ext):
            return True
        
        # Check exact matches (README, etc.)
        base_name = filename.split('.')[0].upper()
        if base_name in ['README', 'CONTRIBUTING', 'CHANGELOG', 'LICENSE']:
            return True
        
        return False
    
    def _parse_file(self, file_path: str) -> List[DocChunk]:
        """Parse markdown file into chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"⚠️ Failed to read {file_path}: {e}")
            return []
        
        # Skip empty or very small files
        if len(content.strip()) < self.min_chunk_length:
            return []
        
        chunks = []
        
        # Split by headings
        sections = self._split_by_headings(content)
        
        for section_data in sections:
            heading = section_data['heading']
            level = section_data['level']
            section_content = section_data['content']
            hierarchy = section_data['hierarchy']
            
            # Skip empty sections
            if len(section_content.strip()) < self.min_chunk_length:
                continue
            
            # Split long sections into smaller chunks
            if len(section_content) > self.max_chunk_length:
                sub_chunks = self._split_long_section(section_content)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk = self._create_chunk(
                        content=sub_chunk,
                        file_path=file_path,
                        section=hierarchy,
                        level=level,
                        chunk_index=i
                    )
                    chunks.append(chunk)
            else:
                chunk = self._create_chunk(
                    content=section_content,
                    file_path=file_path,
                    section=hierarchy,
                    level=level
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_by_headings(self, content: str) -> List[Dict[str, Any]]:
        """Split content by markdown headings."""
        # Regex to match markdown headings
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        sections = []
        current_heading = "Introduction"
        current_level = 1
        current_content = []
        heading_stack = [""]  # Track heading hierarchy
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            match = heading_pattern.match(line)
            
            if match:
                # Save previous section
                if current_content:
                    sections.append({
                        'heading': current_heading,
                        'level': current_level,
                        'content': '\n'.join(current_content).strip(),
                        'hierarchy': ' > '.join(filter(None, heading_stack))
                    })
                    current_content = []
                
                # Start new section
                hashes = match.group(1)
                current_level = len(hashes)
                current_heading = match.group(2).strip()
                
                # Update heading hierarchy
                heading_stack = heading_stack[:current_level]
                if len(heading_stack) < current_level:
                    heading_stack.extend([''] * (current_level - len(heading_stack)))
                heading_stack[current_level - 1] = current_heading
            else:
                current_content.append(line)
            
            i += 1
        
        # Add final section
        if current_content:
            sections.append({
                'heading': current_heading,
                'level': current_level,
                'content': '\n'.join(current_content).strip(),
                'hierarchy': ' > '.join(filter(None, heading_stack))
            })
        
        return sections
    
    def _split_long_section(self, content: str) -> List[str]:
        """Split long section into smaller chunks."""
        chunks = []
        
        # Try to split by paragraphs
        paragraphs = content.split('\n\n')
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > self.max_chunk_length and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length + 2  # +2 for \n\n
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        file_path: str,
        section: str,
        level: int,
        chunk_index: int = 0
    ) -> DocChunk:
        """Create documentation chunk with metadata."""
        # Generate unique ID
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        chunk_id = f"docs_{content_hash}_{chunk_index}"
        
        # Create metadata
        metadata = {
            'file_path': file_path,
            'section': section,
            'level': level,
            'chunk_index': chunk_index,
            'char_count': len(content),
            'file_name': os.path.basename(file_path)
        }
        
        return DocChunk(
            content=content,
            file_path=file_path,
            section=section,
            level=level,
            chunk_id=chunk_id,
            metadata=metadata
        )
    
    def _store_chunks(self, chunks: List[DocChunk]) -> int:
        """Store documentation chunks in vector database."""
        if not chunks:
            return 0
        
        logger.info(f"💾 Storing {len(chunks)} documentation chunks...")
        
        # Prepare data for batch insertion
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
            collection_name="docs",
            ids=ids,
            embeddings=all_embeddings,
            contents=contents,
            metadatas=metadatas
        )
        
        logger.info(f"✅ Stored {len(chunks)} documentation chunks")
        return len(chunks)
    
    def close(self):
        """Clean up resources."""
        self.vector_store.close()
        logger.info("👋 Documentation indexer closed")


# Convenience function for quick indexing
def index_documentation(workspace_path: str, additional_paths: Optional[List[str]] = None) -> int:
    """Quick documentation indexing using default indexer.
    
    Args:
        workspace_path: Root workspace directory
        additional_paths: Additional paths to index
        
    Returns:
        Number of chunks indexed
    """
    indexer = DocsIndexer()
    count = indexer.index_workspace(workspace_path, additional_paths)
    indexer.close()
    return count
