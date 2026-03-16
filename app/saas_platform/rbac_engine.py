"""
Role-Based Access Control (RBAC) system for multi-tenant SaaS platform.

Handles user management, roles, permissions, and API key authentication.
"""

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
import logging

from saas_platform.models import (
    User, UserRole, Permission, RolePermissionMapping, APIKey,
    generate_platform_id
)


logger = logging.getLogger(__name__)


@dataclass
class RBACPolicy:
    """RBAC policy for resource access."""
    policy_id: str
    resource_type: str  # apps, workflows, organizations, etc.
    resource_id: str
    tenant_id: str
    owner_id: str
    read_roles: Set[UserRole] = field(default_factory=set)
    write_roles: Set[UserRole] = field(default_factory=set)
    delete_roles: Set[UserRole] = field(default_factory=set)
    admin_roles: Set[UserRole] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSession:
    """User session tracking."""
    session_id: str
    user_id: str
    tenant_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogEntry:
    """Audit log entry."""
    log_id: str
    tenant_id: str
    user_id: Optional[str] = None
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    status: str = "success"  # success, failure
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PermissionManager:
    """Manages permissions and permission mappings."""
    
    def __init__(self):
        """Initialize permission manager."""
        self.permissions: Dict[str, Permission] = {}
        self.role_permissions: Dict[UserRole, RolePermissionMapping] = {}
        self._init_default_permissions()
    
    def _init_default_permissions(self) -> None:
        """Initialize default permissions."""
        default_permissions = [
            # App permissions
            ("app_read", "apps", "read", "Read apps"),
            ("app_create", "apps", "create", "Create apps"),
            ("app_update", "apps", "update", "Update apps"),
            ("app_delete", "apps", "delete", "Delete apps"),
            
            # Workflow permissions
            ("workflow_read", "workflows", "read", "Read workflows"),
            ("workflow_create", "workflows", "create", "Create workflows"),
            ("workflow_update", "workflows", "update", "Update workflows"),
            ("workflow_delete", "workflows", "delete", "Delete workflows"),
            ("workflow_execute", "workflows", "execute", "Execute workflows"),
            
            # Organization permissions
            ("org_read", "organization", "read", "Read organization"),
            ("org_update", "organization", "update", "Update organization"),
            ("org_manage_users", "organization", "manage", "Manage users"),
            ("org_manage_roles", "organization", "manage", "Manage roles"),
            ("org_manage_api_keys", "organization", "manage", "Manage API keys"),
            
            # Billing permissions
            ("billing_read", "billing", "read", "Read billing info"),
            ("billing_manage", "billing", "manage", "Manage billing"),
            
            # Admin permissions
            ("admin_all", "admin", "manage", "All admin permissions"),
        ]
        
        for perm_id, resource, action, description in default_permissions:
            permission = Permission(
                permission_id=perm_id,
                name=perm_id,
                description=description,
                resource_type=resource,
                action=action
            )
            self.permissions[perm_id] = permission
        
        # Create role permission mappings
        role_perms = {
            UserRole.OWNER: {
                "app_read", "app_create", "app_update", "app_delete",
                "workflow_read", "workflow_create", "workflow_update", "workflow_delete", "workflow_execute",
                "org_read", "org_update", "org_manage_users", "org_manage_roles", "org_manage_api_keys",
                "billing_read", "billing_manage", "admin_all"
            },
            UserRole.ADMIN: {
                "app_read", "app_create", "app_update", "app_delete",
                "workflow_read", "workflow_create", "workflow_update", "workflow_delete", "workflow_execute",
                "org_read", "org_update", "org_manage_users", "org_manage_api_keys",
                "billing_read"
            },
            UserRole.MANAGER: {
                "app_read", "app_create", "app_update",
                "workflow_read", "workflow_create", "workflow_update", "workflow_execute",
                "org_read", "org_manage_users",
                "billing_read"
            },
            UserRole.DEVELOPER: {
                "app_read", "app_create", "app_update",
                "workflow_read", "workflow_create", "workflow_update", "workflow_execute",
                "org_read"
            },
            UserRole.USER: {
                "app_read", "workflow_read", "workflow_execute",
                "org_read"
            },
            UserRole.VIEWER: {
                "app_read", "workflow_read", "org_read"
            }
        }
        
        for role, perm_ids in role_perms.items():
            mapping = RolePermissionMapping(
                role_id=generate_platform_id("role"),
                role=role,
                permissions=perm_ids
            )
            self.role_permissions[role] = mapping
    
    def get_permissions_for_role(self, role: UserRole) -> Set[str]:
        """Get all permissions for role."""
        mapping = self.role_permissions.get(role)
        return mapping.permissions if mapping else set()
    
    def has_permission(
        self,
        user: User,
        permission_id: str
    ) -> bool:
        """Check if user has permission."""
        user_perms = self.get_permissions_for_role(user.role)
        return permission_id in user_perms
    
    def grant_permission_to_role(
        self,
        role: UserRole,
        permission_id: str
    ) -> bool:
        """Grant permission to role."""
        mapping = self.role_permissions.get(role)
        if not mapping:
            logger.error(f"Role not found: {role}")
            return False
        
        mapping.permissions.add(permission_id)
        logger.info(f"Granted {permission_id} to role {role}")
        return True
    
    def revoke_permission_from_role(
        self,
        role: UserRole,
        permission_id: str
    ) -> bool:
        """Revoke permission from role."""
        mapping = self.role_permissions.get(role)
        if not mapping:
            logger.error(f"Role not found: {role}")
            return False
        
        mapping.permissions.discard(permission_id)
        logger.info(f"Revoked {permission_id} from role {role}")
        return True


class UserManager:
    """Manages users within tenants."""
    
    def __init__(self, permission_manager: PermissionManager):
        """Initialize user manager."""
        self.users: Dict[str, User] = {}
        self.users_by_tenant: Dict[str, Set[str]] = {}
        self.permission_manager = permission_manager
    
    def create_user(
        self,
        tenant_id: str,
        email: str,
        name: str,
        role: UserRole = UserRole.USER,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """Create user in tenant."""
        user_id = generate_platform_id("user")
        
        user = User(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            name=name,
            role=role,
            metadata=metadata or {}
        )
        
        self.users[user_id] = user
        
        if tenant_id not in self.users_by_tenant:
            self.users_by_tenant[tenant_id] = set()
        self.users_by_tenant[tenant_id].add(user_id)
        
        logger.info(f"Created user: {user_id} ({email}) in tenant {tenant_id}")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_users_for_tenant(self, tenant_id: str) -> List[User]:
        """Get all users in tenant."""
        user_ids = self.users_by_tenant.get(tenant_id, set())
        return [self.users[uid] for uid in user_ids if uid in self.users]
    
    def update_user_role(
        self,
        user_id: str,
        new_role: UserRole
    ) -> bool:
        """Update user role."""
        user = self.users.get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return False
        
        old_role = user.role
        user.role = new_role
        
        logger.info(f"Updated user {user_id} role from {old_role} to {new_role}")
        return True
    
    def disable_user(self, user_id: str) -> bool:
        """Disable user."""
        user = self.users.get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return False
        
        user.disabled = True
        logger.info(f"Disabled user: {user_id}")
        return True
    
    def enable_user(self, user_id: str) -> bool:
        """Enable user."""
        user = self.users.get(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return False
        
        user.disabled = False
        logger.info(f"Enabled user: {user_id}")
        return True
    
    def check_user_permission(
        self,
        user_id: str,
        permission_id: str
    ) -> bool:
        """Check if user has permission."""
        user = self.users.get(user_id)
        if not user or user.disabled:
            return False
        
        return self.permission_manager.has_permission(user, permission_id)


class APIKeyManager:
    """Manages API keys for tenant authentication."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.api_keys: Dict[str, APIKey] = {}
        self.keys_by_tenant: Dict[str, Set[str]] = {}
        self.key_prefix_to_id: Dict[str, str] = {}
    
    def generate_api_key(
        self,
        tenant_id: str,
        name: str,
        scopes: Optional[Set[str]] = None,
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """Generate new API key. Returns (key_object, plain_key_string)."""
        key_id = generate_platform_id("key")
        
        # Generate API key
        raw_key = f"{key_id}_{generate_platform_id('secret')}"
        key_prefix = f"sb_pk_{raw_key[:12]}"
        key_hash = self._hash_key(raw_key)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        api_key = APIKey(
            key_id=key_id,
            tenant_id=tenant_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            expires_at=expires_at,
            scopes=scopes or {"read", "write"}
        )
        
        self.api_keys[key_id] = api_key
        self.key_prefix_to_id[key_prefix] = key_id
        
        if tenant_id not in self.keys_by_tenant:
            self.keys_by_tenant[tenant_id] = set()
        self.keys_by_tenant[tenant_id].add(key_id)
        
        logger.info(f"Generated API key: {key_prefix} for tenant {tenant_id}")
        return api_key, raw_key
    
    def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Verify API key and return if valid."""
        key_prefix = raw_key.split('_')[0:3]
        key_prefix = '_'.join(key_prefix)
        
        key_id = self.key_prefix_to_id.get(key_prefix)
        if not key_id:
            return None
        
        api_key = self.api_keys.get(key_id)
        if not api_key:
            return None
        
        # Check if revoked
        if api_key.revoked:
            logger.warning(f"Attempted use of revoked API key: {key_prefix}")
            return None
        
        # Check if expired
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            logger.warning(f"Attempted use of expired API key: {key_prefix}")
            return None
        
        # Verify key hash
        key_hash = self._hash_key(raw_key)
        if not hmac.compare_digest(key_hash, api_key.key_hash):
            logger.warning(f"Invalid API key hash: {key_prefix}")
            return None
        
        # Update last used
        api_key.last_used = datetime.utcnow()
        
        return api_key
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        api_key = self.api_keys.get(key_id)
        if not api_key:
            logger.error(f"API key not found: {key_id}")
            return False
        
        api_key.revoked = True
        logger.info(f"Revoked API key: {key_id}")
        return True
    
    def get_tenant_api_keys(self, tenant_id: str) -> List[APIKey]:
        """Get all API keys for tenant."""
        key_ids = self.keys_by_tenant.get(tenant_id, set())
        return [self.api_keys[kid] for kid in key_ids if kid in self.api_keys]
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()


class SessionManager:
    """Manages user sessions."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}
        self.session_timeout_minutes = 60
    
    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create user session."""
        session_id = generate_platform_id("session")
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"Created session: {session_id} for user {user_id}")
        return session
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session is still active."""
        session = self.sessions.get(session_id)
        if not session or not session.active:
            return False
        
        # Check timeout
        timeout = timedelta(minutes=self.session_timeout_minutes)
        if datetime.utcnow() - session.last_activity > timeout:
            session.active = False
            logger.info(f"Session expired: {session_id}")
            return False
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        return True
    
    def end_session(self, session_id: str) -> bool:
        """End user session."""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return False
        
        session.active = False
        logger.info(f"Ended session: {session_id}")
        return True
    
    def end_user_sessions(self, user_id: str) -> int:
        """End all sessions for user."""
        session_ids = self.user_sessions.get(user_id, set())
        count = 0
        
        for sid in session_ids:
            if self.end_session(sid):
                count += 1
        
        logger.info(f"Ended {count} sessions for user {user_id}")
        return count


class AuditLogger:
    """Logs all audit events."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.logs: Dict[str, AuditLogEntry] = {}
        self.tenant_logs: Dict[str, List[str]] = {}
        self.user_logs: Dict[str, List[str]] = {}
    
    def log_action(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str = "",
        user_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """Log audit action."""
        log_id = generate_platform_id("audit")
        
        log_entry = AuditLogEntry(
            log_id=log_id,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            error_message=error_message,
            changes=changes or {}
        )
        
        self.logs[log_id] = log_entry
        
        if tenant_id not in self.tenant_logs:
            self.tenant_logs[tenant_id] = []
        self.tenant_logs[tenant_id].append(log_id)
        
        if user_id:
            if user_id not in self.user_logs:
                self.user_logs[user_id] = []
            self.user_logs[user_id].append(log_id)
        
        level = "INFO" if status == "success" else "WARNING"
        logger.log(
            logging.INFO if level == "INFO" else logging.WARNING,
            f"[AUDIT] {action} on {resource_type} - {status}"
        )
        
        return log_entry
    
    def get_tenant_audit_logs(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit logs for tenant."""
        log_ids = self.tenant_logs.get(tenant_id, [])
        logs = [self.logs[lid] for lid in log_ids[-limit:] if lid in self.logs]
        return list(reversed(logs))
    
    def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit logs for user."""
        log_ids = self.user_logs.get(user_id, [])
        logs = [self.logs[lid] for lid in log_ids[-limit:] if lid in self.logs]
        return list(reversed(logs))


class AuthorizationEngine:
    """Enforces RBAC policies."""
    
    def __init__(
        self,
        permission_manager: PermissionManager,
        user_manager: UserManager,
        audit_logger: AuditLogger
    ):
        """Initialize authorization engine."""
        self.permission_manager = permission_manager
        self.user_manager = user_manager
        self.audit_logger = audit_logger
        self.policies: Dict[str, RBACPolicy] = {}
    
    def check_access(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = "",
        tenant_id: Optional[str] = None
    ) -> bool:
        """Check if user can perform action on resource."""
        user = self.user_manager.get_user(user_id)
        if not user or user.disabled:
            return False
        
        # Owner/Admin can do anything
        if user.role in (UserRole.OWNER, UserRole.ADMIN):
            return True
        
        # Map action to permission
        permission_map = {
            "read": f"{resource_type}_read",
            "create": f"{resource_type}_create",
            "update": f"{resource_type}_update",
            "delete": f"{resource_type}_delete",
            "execute": f"{resource_type}_execute",
            "manage": f"{resource_type}_manage"
        }
        
        permission_id = permission_map.get(action)
        if not permission_id:
            return False
        
        return self.user_manager.check_user_permission(user_id, permission_id)
    
    def create_policy(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        owner_id: str
    ) -> RBACPolicy:
        """Create RBAC policy for resource."""
        policy_id = generate_platform_id("policy")
        
        policy = RBACPolicy(
            policy_id=policy_id,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            read_roles={UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER},
            write_roles={UserRole.OWNER, UserRole.ADMIN, UserRole.DEVELOPER},
            delete_roles={UserRole.OWNER, UserRole.ADMIN},
            admin_roles={UserRole.OWNER, UserRole.ADMIN}
        )
        
        self.policies[policy_id] = policy
        return policy
