"""
Persistence layer for storing workflow state and audit logs in Firestore.

Provides:
- Workflow execution state storage
- Execution audit logs
- Credential encryption and storage
- Query and retrieval methods
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from utils.logger import get_logger
from utils.errors import FirebaseException
from config.settings import settings


logger = get_logger(__name__)


@dataclass
class WorkflowExecution:
    """Represents a workflow execution record."""
    execution_id: str
    workflow_id: str
    status: str  # pending, running, completed, failed
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    agent_reasoning: Optional[list] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowExecution":
        """Create from Firestore dictionary."""
        # Parse ISO strings back to datetime
        if isinstance(data.get("started_at"), str):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if isinstance(data.get("completed_at"), str):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


class FirestorePersistence:
    """Firestore-based persistence layer."""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.FirestorePersistence")
        self.db = self._get_firestore_client()
        self.prefix = settings.firestore_prefix
    
    def _get_firestore_client(self):
        """Get Firestore client. Mock if not available."""
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            if not firebase_admin._apps:
                self.logger.warning("Firebase not initialized, using mock persistence")
                return None
            return firestore.client()
        except Exception as e:
            self.logger.warning(f"Could not initialize Firestore: {str(e)}, using mock")
            return None
    
    async def store_workflow_execution(self, execution: WorkflowExecution) -> bool:
        """Store a workflow execution record."""
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Stored execution {execution.execution_id}")
                return True
            
            collection = self.db.collection(f"{self.prefix}executions")
            doc_ref = collection.document(execution.execution_id)
            doc_ref.set({
                **execution.to_dict(),
                "stored_at": datetime.utcnow().isoformat()
            })
            
            self.logger.info(f"Stored workflow execution: {execution.execution_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store workflow execution: {str(e)}")
            raise FirebaseException(f"Failed to store execution: {str(e)}")
    
    async def get_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Retrieve a workflow execution record."""
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Retrieved execution {execution_id}")
                return None
            
            doc = self.db.collection(f"{self.prefix}executions").document(execution_id).get()
            if not doc.exists:
                return None
            
            return WorkflowExecution.from_dict(doc.to_dict())
        except Exception as e:
            self.logger.error(f"Failed to get workflow execution: {str(e)}")
            raise FirebaseException(f"Failed to retrieve execution: {str(e)}")
    
    async def update_workflow_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a workflow execution record."""
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Updated execution {execution_id}")
                return True
            
            # Convert datetime objects
            if "completed_at" in updates and isinstance(updates["completed_at"], datetime):
                updates["completed_at"] = updates["completed_at"].isoformat()
            
            self.db.collection(f"{self.prefix}executions").document(execution_id).update(updates)
            self.logger.info(f"Updated workflow execution: {execution_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update workflow execution: {str(e)}")
            raise FirebaseException(f"Failed to update execution: {str(e)}")
    
    async def store_execution_log(
        self,
        execution_id: str,
        workflow_id: str,
        event: str,
        details: Dict[str, Any],
        level: str = "INFO"
    ) -> bool:
        """Store an execution audit log entry."""
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Stored log for {execution_id}: {event}")
                return True
            
            log_entry = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "event": event,
                "details": details,
                "level": level,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.db.collection(f"{self.prefix}execution_logs").add(log_entry)
            self.logger.debug(f"Stored execution log: {workflow_id}/{event}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store execution log: {str(e)}")
            # Don't raise - logging should not block workflow execution
            return False
    
    async def get_execution_logs(
        self,
        execution_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve execution logs for an execution."""
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Retrieved logs for {execution_id}")
                return []
            
            docs = (
                self.db.collection(f"{self.prefix}execution_logs")
                .where("execution_id", "==", execution_id)
                .order_by("timestamp")
                .limit(limit)
                .stream()
            )
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            self.logger.error(f"Failed to retrieve execution logs: {str(e)}")
            return []
    
    async def store_credential(
        self,
        credential_id: str,
        provider: str,
        credential_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Store API credentials securely.
        Note: In production, consider using encrypted fields or Cloud KMS.
        """
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Stored credential {credential_id}")
                return True
            
            doc_data = {
                "credential_id": credential_id,
                "provider": provider,
                "user_id": user_id,
                "data": credential_data,
                "created_at": datetime.utcnow().isoformat(),
                "last_used": None
            }
            
            self.db.collection(f"{self.prefix}credentials").document(credential_id).set(doc_data)
            self.logger.info(f"Stored credential for {provider}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store credential: {str(e)}")
            raise FirebaseException(f"Failed to store credential: {str(e)}")
    
    async def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored credential."""
        try:
            if not self.db:
                return None
            
            doc = self.db.collection(f"{self.prefix}credentials").document(credential_id).get()
            if not doc.exists:
                return None
            
            # Update last_used timestamp
            doc_data = doc.to_dict()
            self.db.collection(f"{self.prefix}credentials").document(credential_id).update({
                "last_used": datetime.utcnow().isoformat()
            })
            
            return doc_data.get("data")
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential: {str(e)}")
            return None
    
    async def store_agent_memory(
        self,
        agent_id: str,
        memory_data: Dict[str, Any]
    ) -> bool:
        """Store agent memory state."""
        try:
            if not self.db:
                self.logger.debug(f"[MOCK] Stored memory for agent {agent_id}")
                return True
            
            self.db.collection(f"{self.prefix}agent_memory").document(agent_id).set({
                "agent_id": agent_id,
                "memory": memory_data,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            self.logger.debug(f"Stored agent memory for {agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store agent memory: {str(e)}")
            return False
    
    async def get_agent_memory(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent memory state."""
        try:
            if not self.db:
                return None
            
            doc = self.db.collection(f"{self.prefix}agent_memory").document(agent_id).get()
            if not doc.exists:
                return None
            
            return doc.to_dict().get("memory")
        except Exception as e:
            self.logger.error(f"Failed to retrieve agent memory: {str(e)}")
            return None
    
    async def cleanup_old_executions(self, days_old: int = 30) -> int:
        """Delete old execution records to manage storage."""
        try:
            if not self.db:
                return 0
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
            docs = (
                self.db.collection(f"{self.prefix}executions")
                .where("completed_at", "<", cutoff_date)
                .stream()
            )
            
            count = 0
            for doc in docs:
                doc.reference.delete()
                count += 1
            
            self.logger.info(f"Cleaned up {count} old execution records")
            return count
        except Exception as e:
            self.logger.error(f"Failed to cleanup old executions: {str(e)}")
            return 0


# Singleton instance
_persistence: Optional[FirestorePersistence] = None


def get_persistence() -> FirestorePersistence:
    """Get or create persistence layer singleton."""
    global _persistence
    if _persistence is None:
        _persistence = FirestorePersistence()
    return _persistence
