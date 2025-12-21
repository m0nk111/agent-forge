"""
RAG (Retrieval-Augmented Generation) System for Agent-Forge

This module provides a complete RAG implementation for augmenting LLM agents
with relevant context from the codebase, documentation, and historical issues.

Architecture:
    - Vector Store: Milvus for efficient similarity search
    - Embeddings: sentence-transformers (local) or Ollama embeddings
    - Indexers: Code, documentation, and issue history indexing
    - Retriever: Query processing and context assembly

Components:
    - embedding_service: Generate embeddings for text/code
    - indexers: Index various data sources into vector store
    - retriever: Search and retrieve relevant context
    - config: RAG system configuration
"""

from .embedding_service import EmbeddingService
from .retriever import RAGRetriever

__all__ = ['EmbeddingService', 'RAGRetriever']
