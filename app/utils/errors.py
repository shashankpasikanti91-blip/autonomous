"""
Custom exception classes for the platform.
"""


class PlatformException(Exception):
    """Base exception for all platform errors."""
    
    def __init__(self, message: str, code: str = "PLATFORM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AgentException(PlatformException):
    """Exception raised for agent-related errors."""
    
    def __init__(self, message: str, code: str = "AGENT_ERROR"):
        super().__init__(message, code)


class WorkflowException(PlatformException):
    """Exception raised for workflow-related errors."""
    
    def __init__(self, message: str, code: str = "WORKFLOW_ERROR"):
        super().__init__(message, code)


class ToolException(PlatformException):
    """Exception raised for tool execution errors."""
    
    def __init__(self, message: str, code: str = "TOOL_ERROR"):
        super().__init__(message, code)


class MemoryException(PlatformException):
    """Exception raised for memory operations."""
    
    def __init__(self, message: str, code: str = "MEMORY_ERROR"):
        super().__init__(message, code)


class FirebaseException(PlatformException):
    """Exception raised for Firebase operations."""
    
    def __init__(self, message: str, code: str = "FIREBASE_ERROR"):
        super().__init__(message, code)


class ServiceException(PlatformException):
    """Exception raised for service-related errors."""
    
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        super().__init__(message, code)


class AuthenticationException(PlatformException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        super().__init__(message, code)
