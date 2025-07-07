import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
import aiofiles
from dataclasses import dataclass, asdict
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

@dataclass
class SearchResult:
    document: Document
    score: float
    rank: int

class VectorSearchService:
    """FAISS-based vector search service with async support"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.documents: List[Document] = []
        self.id_to_index: Dict[str, int] = {}
        
        # Paths
        self.index_path = Path(settings.VECTOR_INDEX_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized VectorSearchService with model: {self.model_name}")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to the vector index"""
        logger.info(f"Adding {len(documents)} documents to vector index...")
        
        new_documents = []
        texts_to_embed = []
        
        for doc_data in documents:
            doc_id = doc_data.get('id', f"doc_{len(self.documents)}")
            
            # Skip if document already exists
            if doc_id in self.id_to_index:
                logger.debug(f"Document {doc_id} already exists, skipping")
                continue
            
            document = Document(
                id=doc_id,
                content=doc_data['content'],
                metadata=doc_data.get('metadata', {})
            )
            
            new_documents.append(document)
            texts_to_embed.append(document.content)
        
        if not new_documents:
            logger.info("No new documents to add")
            return 0
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts_to_embed)} documents...")
        embeddings = await self._generate_embeddings_async(texts_to_embed)
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Add to FAISS index
        start_index = len(self.documents)
        self.index.add(embeddings.astype('float32'))
        
        # Update document storage and mapping
        for i, document in enumerate(new_documents):
            document.embedding = embeddings[i]
            self.documents.append(document)
            self.id_to_index[document.id] = start_index + i
        
        logger.info(f"Successfully added {len(new_documents)} documents to index")
        return len(new_documents)
    
    async def _generate_embeddings_async(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings asynchronously"""
        # Run embedding generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            self.model.encode, 
            texts
        )
        return embeddings
    
    async def search(self, query: str, k: int = 5, filter_metadata: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            logger.warning("Vector index is empty")
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embeddings_async([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), min(k * 2, self.index.ntotal))
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
                
            document = self.documents[idx]
            
            # Apply metadata filtering if specified
            if filter_metadata:
                if not self._matches_filter(document.metadata, filter_metadata):
                    continue
            
            results.append(SearchResult(
                document=document,
                score=float(score),
                rank=i + 1
            ))
            
            if len(results) >= k:
                break
        
        logger.debug(f"Search for '{query}' returned {len(results)} results")
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_criteria: Dict[str, Any]) -> bool:
        """Check if document metadata matches filter criteria"""
        for key, value in filter_criteria.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True
    
    async def search_with_reranking(self, query: str, k: int = 5, rerank_factor: int = 3) -> List[SearchResult]:
        """Search with reranking for better results"""
        # Get more candidates than needed
        initial_k = min(k * rerank_factor, 50)
        initial_results = await self.search(query, initial_k)
        
        if len(initial_results) <= k:
            return initial_results
        
        # Rerank using cross-encoder or more sophisticated scoring
        reranked_results = await self._rerank_results(query, initial_results)
        
        return reranked_results[:k]
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Rerank search results using additional scoring"""
        # Simple reranking based on content length and metadata
        for result in results:
            # Adjust score based on content quality indicators
            content_length_score = min(len(result.document.content) / 1000, 1.0)  # Normalize to 0-1
            
            # Boost score for certain metadata
            metadata_boost = 0.0
            if 'title' in result.document.metadata:
                if query.lower() in result.document.metadata['title'].lower():
                    metadata_boost += 0.1
            
            if 'entity_count' in result.document.metadata:
                entity_density = result.document.metadata['entity_count'] / max(len(result.document.content), 1)
                metadata_boost += min(entity_density * 100, 0.1)  # Boost for entity-rich content
            
            # Combine scores
            result.score = result.score * 0.8 + content_length_score * 0.1 + metadata_boost
        
        # Sort by adjusted score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    async def semantic_search(self, query: str, entity_filter: List[str] = None, k: int = 5) -> List[SearchResult]:
        """Semantic search with entity filtering"""
        filter_metadata = {}
        
        if entity_filter:
            # Filter documents that contain specific entities
            filter_metadata['entities'] = entity_filter
        
        return await self.search(query, k, filter_metadata)
    
    async def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.7) -> List[SearchResult]:
        """Hybrid search combining semantic and keyword matching"""
        # Get semantic search results
        semantic_results = await self.search(query, k * 2)
        
        # Get keyword search results
        keyword_results = await self._keyword_search(query, k * 2)
        
        # Combine and rerank results
        combined_results = self._combine_search_results(
            semantic_results, 
            keyword_results, 
            alpha
        )
        
        return combined_results[:k]
    
    async def _keyword_search(self, query: str, k: int) -> List[SearchResult]:
        """Simple keyword-based search"""
        query_terms = query.lower().split()
        scored_docs = []
        
        for i, document in enumerate(self.documents):
            content_lower = document.content.lower()
            
            # Calculate keyword match score
            matches = sum(1 for term in query_terms if term in content_lower)
            if matches > 0:
                score = matches / len(query_terms)
                scored_docs.append(SearchResult(
                    document=document,
                    score=score,
                    rank=i
                ))
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x.score, reverse=True)
        return scored_docs[:k]
    
    def _combine_search_results(self, semantic_results: List[SearchResult], 
                               keyword_results: List[SearchResult], 
                               alpha: float) -> List[SearchResult]:
        """Combine semantic and keyword search results"""
        # Create a mapping of document ID to results
        doc_scores = {}
        
        # Add semantic scores
        for result in semantic_results:
            doc_id = result.document.id
            doc_scores[doc_id] = {
                'document': result.document,
                'semantic_score': result.score,
                'keyword_score': 0.0
            }
        
        # Add keyword scores
        for result in keyword_results:
            doc_id = result.document.id
            if doc_id in doc_scores:
                doc_scores[doc_id]['keyword_score'] = result.score
            else:
                doc_scores[doc_id] = {
                    'document': result.document,
                    'semantic_score': 0.0,
                    'keyword_score': result.score
                }
        
        # Calculate combined scores
        combined_results = []
        for doc_id, scores in doc_scores.items():
            combined_score = (alpha * scores['semantic_score'] + 
                            (1 - alpha) * scores['keyword_score'])
            
            combined_results.append(SearchResult(
                document=scores['document'],
                score=combined_score,
                rank=0  # Will be set after sorting
            ))
        
        # Sort by combined score and update ranks
        combined_results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(combined_results):
            result.rank = i + 1
        
        return combined_results
    
    async def save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            index_file = self.index_path / "index.faiss"
            faiss.write_index(self.index, str(index_file))
            
            # Save documents and metadata
            metadata_file = self.index_path / "metadata.pkl"
            async with aiofiles.open(metadata_file, 'wb') as f:
                # Convert documents to serializable format
                serializable_docs = []
                for doc in self.documents:
                    doc_dict = asdict(doc)
                    if doc_dict['embedding'] is not None:
                        doc_dict['embedding'] = doc_dict['embedding'].tolist()
                    serializable_docs.append(doc_dict)
                
                await f.write(pickle.dumps({
                    'documents': serializable_docs,
                    'id_to_index': self.id_to_index,
                    'model_name': self.model_name,
                    'dimension': self.dimension
                }))
            
            # Save configuration
            config_file = self.index_path / "config.json"
            config = {
                'model_name': self.model_name,
                'dimension': self.dimension,
                'total_documents': len(self.documents),
                'index_type': 'IndexFlatIP',
                'created_at': str(asyncio.get_event_loop().time())
            }
            
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            logger.info(f"Vector index saved to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save vector index: {e}")
            raise
    
    async def load_index(self):
        """Load FAISS index and metadata from disk"""
        try:
            index_file = self.index_path / "index.faiss"
            metadata_file = self.index_path / "metadata.pkl"
            
            if not (index_file.exists() and metadata_file.exists()):
                logger.info("No existing vector index found")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load metadata
            async with aiofiles.open(metadata_file, 'rb') as f:
                content = await f.read()
                metadata = pickle.loads(content)
            
            # Restore documents
            self.documents = []
            for doc_dict in metadata['documents']:
                if doc_dict['embedding'] is not None:
                    doc_dict['embedding'] = np.array(doc_dict['embedding'])
                
                self.documents.append(Document(**doc_dict))
            
            self.id_to_index = metadata['id_to_index']
            
            # Verify model compatibility
            if metadata['model_name'] != self.model_name:
                logger.warning(f"Model mismatch: saved={metadata['model_name']}, current={self.model_name}")
            
            logger.info(f"Loaded vector index with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load vector index: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector search statistics"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal,
            'dimension': self.dimension,
            'model_name': self.model_name,
            'index_type': type(self.index).__name__,
            'memory_usage_mb': self.index.ntotal * self.dimension * 4 / (1024 * 1024)  # Approximate
        }
    
    async def close(self):
        """Cleanup resources"""
        await self.save_index()
        logger.info("Vector search service closed")