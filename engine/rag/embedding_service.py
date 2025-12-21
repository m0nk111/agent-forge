"""
Embedding Service for RAG System

Generates vector embeddings for text and code using either:
1. sentence-transformers (local, fast, free)
2. Ollama embeddings (local LLM)
3. OpenAI embeddings (cloud, highest quality)

Default: sentence-transformers with all-MiniLM-L6-v2 model
"""

import logging
from typing import List, Optional, Union
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings for text and code."""
    
    def __init__(
        self,
        backend: str = "sentence-transformers",
        model_name: Optional[str] = None,
        device: str = "cpu",
        cache_dir: Optional[Path] = None
    ):
        """Initialize embedding service.
        
        Args:
            backend: Embedding backend ('sentence-transformers', 'ollama', 'openai')
            model_name: Model to use (backend-specific defaults if None)
            device: Device for computation ('cpu', 'cuda')
            cache_dir: Directory for caching models/embeddings
        """
        self.backend = backend
        self.device = device
        self.cache_dir = cache_dir or Path.home() / ".cache" / "agent-forge" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Model initialization
        self.model = None
        self.embedding_dim = None
        
        if backend == "sentence-transformers":
            self._init_sentence_transformers(model_name or "jinaai/jina-embeddings-v2-base-code")
        elif backend == "ollama":
            self._init_ollama(model_name or "nomic-embed-text")
        elif backend == "openai":
            self._init_openai(model_name or "text-embedding-3-small")
        else:
            raise ValueError(f"Unsupported backend: {backend}")
        
        logger.info(f"✅ Embedding service initialized: {backend} ({self.embedding_dim}D)")
    
    def _init_sentence_transformers(self, model_name: str):
        """Initialize sentence-transformers backend."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"📥 Loading sentence-transformers model: {model_name}")
            self.model = SentenceTransformer(model_name, device=self.device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
        except ImportError:
            logger.error("❌ sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
    
    def _init_ollama(self, model_name: str):
        """Initialize Ollama embeddings backend."""
        try:
            import requests
            
            # Test Ollama connection
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Ollama server not reachable")
            
            self.model = model_name
            # Get embedding dimension by generating a test embedding
            test_embedding = self._ollama_embed(["test"])[0]
            self.embedding_dim = len(test_embedding)
            
            logger.info(f"✅ Ollama embeddings ready: {model_name}")
            
        except Exception as e:
            logger.error(f"❌ Ollama initialization failed: {e}")
            raise
    
    def _init_openai(self, model_name: str):
        """Initialize OpenAI embeddings backend."""
        try:
            import openai
            import os
            
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.model = model_name
            # Embedding dimensions for OpenAI models
            dim_map = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536
            }
            self.embedding_dim = dim_map.get(model_name, 1536)
            
            logger.info(f"✅ OpenAI embeddings ready: {model_name}")
            
        except ImportError:
            logger.error("❌ openai package not installed. Install with: pip install openai")
            raise
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts to embed
            
        Returns:
            numpy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        if self.backend == "sentence-transformers":
            return self._sentence_transformers_embed(texts)
        elif self.backend == "ollama":
            return self._ollama_embed(texts)
        elif self.backend == "openai":
            return self._openai_embed(texts)
    
    def _sentence_transformers_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using sentence-transformers."""
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
            batch_size=32
        )
        return embeddings
    
    def _ollama_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using Ollama."""
        import requests
        
        embeddings = []
        for text in texts:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        
        return np.array(embeddings)
    
    def _openai_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI."""
        import openai
        
        response = openai.embeddings.create(
            model=self.model,
            input=texts
        )
        
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)
    
    def embed_code(self, code: str, language: str = "python") -> np.ndarray:
        """Generate embedding for code with language-specific preprocessing.
        
        Args:
            code: Source code to embed
            language: Programming language (for preprocessing)
            
        Returns:
            numpy array embedding (shape: [embedding_dim])
        """
        # Preprocess code for better embeddings
        processed = self._preprocess_code(code, language)
        return self.embed(processed)[0]
    
    def _preprocess_code(self, code: str, language: str) -> str:
        """Preprocess code for embedding generation.
        
        Adds language context and cleans up code for better semantic matching.
        """
        # Remove excessive whitespace
        lines = [line.rstrip() for line in code.split('\n') if line.strip()]
        code_clean = '\n'.join(lines)
        
        # Add language context
        return f"# {language} code:\n{code_clean}"
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Convenience functions for quick embedding generation
_default_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create default embedding service (singleton pattern)."""
    global _default_service
    
    if _default_service is None:
        _default_service = EmbeddingService()
    
    return _default_service


def embed_text(text: str) -> np.ndarray:
    """Quick text embedding using default service."""
    service = get_embedding_service()
    return service.embed(text)[0]


def embed_code(code: str, language: str = "python") -> np.ndarray:
    """Quick code embedding using default service."""
    service = get_embedding_service()
    return service.embed_code(code, language)
