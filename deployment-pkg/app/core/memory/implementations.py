"""
Memory abstraction layer with vector and structured storage support.
"""
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from core.models import Memory
from utils.logger import get_logger
from utils.errors import MemoryException


logger = get_logger(__name__)


class BaseMemory(ABC):
    """Abstract base class for memory implementations."""
    
    @abstractmethod
    async def store(self, data: Dict[str, Any]) -> str:
        """
        Store data in memory.
        
        Args:
            data: Dictionary containing the data to store
            
        Returns:
            ID of the stored memory entry
        """
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve data from memory based on query.
        
        Args:
            query: Query string or vector
            limit: Maximum number of results
            
        Returns:
            List of matching memory entries
        """
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, data: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory entries."""
        pass


class VectorMemory(BaseMemory):
    """
    Vector memory implementation for semantic search and embeddings.
    TODO: Integrate with vector DB (Pinecone, Weaviate, Qdrant, etc.)
    """
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.memories: Dict[str, Memory] = {}
        self.logger = get_logger(f"{__name__}.VectorMemory")
    
    async def store(self, data: Dict[str, Any]) -> str:
        """Store data with embedding."""
        try:
            memory_id = f"vmem_{len(self.memories)}"
            
            # TODO: Generate embedding using sentence-transformers or OpenAI API
            embedding = self._mock_embedding(str(data))
            
            memory = Memory(
                id=memory_id,
                content=data.get("content", str(data)),
                embedding=embedding,
                metadata=data.get("metadata", {})
            )
            
            self.memories[memory_id] = memory
            
            self.logger.info(f"Stored vector memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            error_msg = f"Failed to store vector memory: {str(e)}"
            self.logger.error(error_msg)
            raise MemoryException(error_msg)
    
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories by similarity."""
        try:
            # TODO: Perform actual vector similarity search
            # For now, return all memories (mock implementation)
            results = [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "metadata": mem.metadata,
                    "similarity": 0.9  # Mock similarity score
                }
                for mem in list(self.memories.values())[:limit]
            ]
            
            self.logger.info(f"Retrieved {len(results)} memories for query: {query}")
            return results
            
        except Exception as e:
            error_msg = f"Failed to retrieve vector memories: {str(e)}"
            self.logger.error(error_msg)
            raise MemoryException(error_msg)
    
    async def update(self, memory_id: str, data: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        try:
            if memory_id not in self.memories:
                raise MemoryException(f"Memory {memory_id} not found")
            
            memory = self.memories[memory_id]
            memory.content = data.get("content", memory.content)
            memory.metadata.update(data.get("metadata", {}))
            memory.updated_at = datetime.utcnow()
            
            self.logger.info(f"Updated vector memory: {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update memory: {str(e)}")
            return False
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        try:
            if memory_id in self.memories:
                del self.memories[memory_id]
                self.logger.info(f"Deleted vector memory: {memory_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete memory: {str(e)}")
            return False
    
    async def clear(self) -> None:
        """Clear all memories."""
        self.memories.clear()
        self.logger.info("Cleared all vector memories")
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding."""
        # TODO: Replace with actual embedding generation
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Generate deterministic mock embedding
        embedding = []
        for i in range(self.dimension):
            value = (hash_int * (i + 1)) % 1000 / 1000.0
            embedding.append(value - 0.5)  # Center around 0
        
        return embedding


class FirestoreMemory(BaseMemory):
    """
    Structured memory implementation using Firebase Firestore.
    TODO: Integrate with actual Firestore client from Firebase Admin SDK
    """
    
    def __init__(self, collection_name: str = "memories"):
        self.collection_name = collection_name
        self.memories: Dict[str, Memory] = {}  # Mock storage
        self.logger = get_logger(f"{__name__}.FirestoreMemory")
    
    async def store(self, data: Dict[str, Any]) -> str:
        """Store data in Firestore."""
        try:
            memory_id = f"fmem_{len(self.memories)}"
            
            memory = Memory(
                id=memory_id,
                content=data.get("content", str(data)),
                metadata=data.get("metadata", {})
            )
            
            self.memories[memory_id] = memory
            
            # TODO: Store to actual Firestore using Firebase Admin SDK
            # db = firestore.client()
            # db.collection(self.collection_name).document(memory_id).set(memory.dict())
            
            self.logger.info(f"Stored Firestore memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            error_msg = f"Failed to store Firestore memory: {str(e)}"
            self.logger.error(error_msg)
            raise MemoryException(error_msg)
    
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories from Firestore."""
        try:
            # TODO: Query Firestore with actual filters
            # db = firestore.client()
            # docs = db.collection(self.collection_name).limit(limit).stream()
            
            results = [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "metadata": mem.metadata,
                    "created_at": mem.created_at.isoformat()
                }
                for mem in list(self.memories.values())[:limit]
            ]
            
            self.logger.info(f"Retrieved {len(results)} Firestore memories")
            return results
            
        except Exception as e:
            error_msg = f"Failed to retrieve Firestore memories: {str(e)}"
            self.logger.error(error_msg)
            raise MemoryException(error_msg)
    
    async def update(self, memory_id: str, data: Dict[str, Any]) -> bool:
        """Update a Firestore memory entry."""
        try:
            if memory_id not in self.memories:
                raise MemoryException(f"Memory {memory_id} not found")
            
            memory = self.memories[memory_id]
            memory.content = data.get("content", memory.content)
            memory.metadata.update(data.get("metadata", {}))
            memory.updated_at = datetime.utcnow()
            
            # TODO: Update in Firestore
            
            self.logger.info(f"Updated Firestore memory: {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update Firestore memory: {str(e)}")
            return False
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a Firestore memory entry."""
        try:
            if memory_id in self.memories:
                del self.memories[memory_id]
                # TODO: Delete from Firestore
                self.logger.info(f"Deleted Firestore memory: {memory_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete Firestore memory: {str(e)}")
            return False
    
    async def clear(self) -> None:
        """Clear all memories."""
        self.memories.clear()
        # TODO: Clear Firestore collection
        self.logger.info("Cleared all Firestore memories")


class HybridMemory(BaseMemory):
    """
    Hybrid memory combining vector and structured storage.
    """
    
    def __init__(self, vector_memory: Optional[VectorMemory] = None,
                 firestore_memory: Optional[FirestoreMemory] = None):
        self.vector_memory = vector_memory or VectorMemory()
        self.firestore_memory = firestore_memory or FirestoreMemory()
        self.logger = get_logger(f"{__name__}.HybridMemory")
    
    async def store(self, data: Dict[str, Any]) -> str:
        """Store in both vector and structured memory."""
        try:
            # Store in both systems
            mem_id = await self.firestore_memory.store(data)
            await self.vector_memory.store(data)
            
            self.logger.info(f"Stored hybrid memory: {mem_id}")
            return mem_id
            
        except Exception as e:
            error_msg = f"Failed to store hybrid memory: {str(e)}"
            self.logger.error(error_msg)
            raise MemoryException(error_msg)
    
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve from vector memory (semantic search)."""
        return await self.vector_memory.retrieve(query, limit)
    
    async def update(self, memory_id: str, data: Dict[str, Any]) -> bool:
        """Update in both systems."""
        success_fs = await self.firestore_memory.update(memory_id, data)
        success_vec = await self.vector_memory.update(memory_id, data)
        return success_fs and success_vec
    
    async def delete(self, memory_id: str) -> bool:
        """Delete from both systems."""
        success_fs = await self.firestore_memory.delete(memory_id)
        success_vec = await self.vector_memory.delete(memory_id)
        return success_fs and success_vec
    
    async def clear(self) -> None:
        """Clear both memory systems."""
        await self.firestore_memory.clear()
        await self.vector_memory.clear()
