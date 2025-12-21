"""
Vector Store for RAG System using Milvus

Provides vector storage and similarity search capabilities for:
- Code embeddings
- Documentation embeddings
- Issue history embeddings
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result from vector store."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float  # Similarity score (0-1, higher is better)
    collection: str


class MilvusVectorStore:
    """Vector store implementation using Milvus."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        embedding_dim: int = 768  # Default for jina-embeddings-v2-base-code
    ):
        """Initialize Milvus vector store.
        
        Args:
            host: Milvus server host
            port: Milvus server port
            embedding_dim: Dimension of embedding vectors
        """
        self.host = host
        self.port = port
        self.embedding_dim = embedding_dim
        self.client = None
        
        self._connect()
        self._init_collections()
    
    def _connect(self):
        """Connect to Milvus server."""
        try:
            from pymilvus import connections, utility
            
            logger.info(f"🔌 Connecting to Milvus at {self.host}:{self.port}")
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=10
            )
            
            # Test connection
            if not utility.get_server_version():
                raise ConnectionError("Failed to get Milvus server version")
            
            logger.info("✅ Connected to Milvus successfully")
            
        except ImportError:
            logger.error("❌ pymilvus not installed. Install with: pip install pymilvus")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to Milvus: {e}")
            raise
    
    def _init_collections(self):
        """Initialize Milvus collections for different data types."""
        from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, utility
        
        collections_config = {
            "code": "Code snippets from codebase",
            "docs": "Documentation sections",
            "issues": "Historical GitHub issues"
        }
        
        for collection_name, description in collections_config.items():
            if utility.has_collection(collection_name):
                logger.debug(f"📚 Collection '{collection_name}' already exists")
                continue
            
            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="timestamp", dtype=DataType.INT64)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description=description
            )
            
            # Create collection
            collection = Collection(
                name=collection_name,
                schema=schema
            )
            
            # Create index for vector search
            index_params = {
                "metric_type": "IP",  # Inner Product (cosine similarity for normalized vectors)
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info(f"✅ Created collection: {collection_name}")
    
    def insert(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: np.ndarray,
        contents: List[str],
        metadata: List[Dict[str, Any]]
    ) -> int:
        """Insert vectors into collection.
        
        Args:
            collection_name: Target collection
            ids: Unique IDs for each vector
            embeddings: Embedding vectors (shape: [n, embedding_dim])
            contents: Text content for each embedding
            metadata: Metadata dict for each embedding
            
        Returns:
            Number of vectors inserted
        """
        from pymilvus import Collection
        
        if len(ids) != len(embeddings) != len(contents) != len(metadata):
            raise ValueError("All input lists must have the same length")
        
        # Normalize embeddings for cosine similarity
        embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Prepare data
        timestamp = int(datetime.now().timestamp())
        data = [
            ids,
            embeddings_normalized.tolist(),
            contents,
            metadata,
            [timestamp] * len(ids)
        ]
        
        # Insert into collection
        collection = Collection(collection_name)
        collection.insert(data)
        collection.flush()
        
        logger.info(f"✅ Inserted {len(ids)} vectors into '{collection_name}'")
        return len(ids)
    
    def search(
        self,
        collection_name: str,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar vectors.
        
        Args:
            collection_name: Collection to search
            query_embedding: Query vector (shape: [embedding_dim])
            top_k: Number of results to return
            filter_expr: Optional filter expression (Milvus syntax)
            
        Returns:
            List of SearchResult objects, sorted by similarity (highest first)
        """
        from pymilvus import Collection
        
        # Normalize query embedding
        query_normalized = query_embedding / np.linalg.norm(query_embedding)
        
        # Load collection into memory
        collection = Collection(collection_name)
        collection.load()
        
        # Search parameters
        search_params = {
            "metric_type": "IP",
            "params": {"nprobe": 10}
        }
        
        # Perform search
        results = collection.search(
            data=[query_normalized.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["content", "metadata"]
        )
        
        # Parse results
        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append(SearchResult(
                    id=hit.id,
                    content=hit.entity.get('content'),
                    metadata=hit.entity.get('metadata', {}),
                    score=float(hit.score),
                    collection=collection_name
                ))
        
        logger.debug(f"🔍 Found {len(search_results)} results in '{collection_name}'")
        return search_results
    
    def search_all_collections(
        self,
        query_embedding: np.ndarray,
        top_k_per_collection: int = 3
    ) -> List[SearchResult]:
        """Search across all collections and merge results.
        
        Args:
            query_embedding: Query vector
            top_k_per_collection: Results per collection
            
        Returns:
            Merged and sorted list of SearchResult objects
        """
        all_results = []
        
        for collection_name in ["code", "docs", "issues"]:
            try:
                results = self.search(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    top_k=top_k_per_collection
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"⚠️ Search failed for '{collection_name}': {e}")
        
        # Sort by score (highest first)
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        return all_results
    
    def delete(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        expr: Optional[str] = None
    ) -> int:
        """Delete vectors by ID list or filter expression.

        Args:
            collection_name: Target collection
            ids: List of IDs to delete (mutually exclusive with expr)
            expr: Milvus boolean expression selecting entities to delete

        Returns:
            Number of vectors deleted (best-effort estimate)
        """
        from pymilvus import Collection

        if ids is None and expr is None:
            raise ValueError("Either ids or expr must be provided for deletion")

        if ids is not None and expr is not None:
            raise ValueError("Provide either ids or expr, not both")

        collection = Collection(collection_name)

        if expr is None:
            if not ids:
                logger.info("🗑️ No IDs provided for deletion; nothing to delete")
                return 0
            expr = f"id in {ids}"

        logger.info("🗑️ Deleting from '%s' with expr: %s", collection_name, expr)
        result = collection.delete(expr)

        # pymilvus MutationResult exposes delete_count attribute for newer releases
        delete_count = getattr(result, "delete_count", None)
        if delete_count is not None:
            deleted = int(delete_count)
        else:
            # Fallback when delete_count not available
            deleted = len(ids) if ids is not None else 0

        logger.info("✅ Deleted %s vectors from '%s'", deleted, collection_name)
        return deleted
    
    def count(self, collection_name: str) -> int:
        """Get number of vectors in collection.
        
        Args:
            collection_name: Target collection
            
        Returns:
            Number of vectors in collection
        """
        from pymilvus import Collection
        
        collection = Collection(collection_name)
        return collection.num_entities
    
    def close(self):
        """Close connection to Milvus."""
        from pymilvus import connections
        
        connections.disconnect("default")
        logger.info("👋 Disconnected from Milvus")
