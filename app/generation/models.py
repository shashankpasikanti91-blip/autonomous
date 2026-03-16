"""
Core data models for app generation layer.

Defines schemas, blueprints, packages, and runtime containers for generated applications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4


class AppType(str, Enum):
    """Type of generated application."""
    CRM = "crm"
    MARKETING = "marketing"
    SALES = "sales"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"
    WORKFLOW = "workflow"
    DASHBOARD = "dashboard"
    INTERNAL_TOOL = "internal_tool"
    CUSTOM = "custom"


class EntityType(str, Enum):
    """Type of entity in app schema."""
    CONTACT = "contact"
    ACCOUNT = "company"
    DEAL = "deal"
    LEAD = "lead"
    TASK = "task"
    EVENT = "event"
    CAMPAIGN = "campaign"
    CUSTOM = "custom"


class FieldType(str, Enum):
    """Data type for entity fields."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    TEXT = "text"
    CURRENCY = "currency"
    ENUM = "enum"
    JSON = "json"
    ARRAY = "array"
    REFERENCE = "reference"


class UIComponentType(str, Enum):
    """Type of UI component."""
    FORM = "form"
    TABLE = "table"
    DASHBOARD = "dashboard"
    CHART = "chart"
    CARD = "card"
    DETAIL_VIEW = "detail_view"
    LIST_VIEW = "list_view"
    MODAL = "modal"
    SIDEBAR = "sidebar"
    HEADER = "header"


class PermissionType(str, Enum):
    """Type of permission."""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class WorkflowEventType(str, Enum):
    """Events that trigger workflows in generated apps."""
    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_DELETE = "on_delete"
    ON_STATUS_CHANGE = "on_status_change"
    ON_SCHEDULE = "on_schedule"
    ON_USER_ACTION = "on_user_action"
    ON_EXTERNAL_EVENT = "on_external_event"


@dataclass
class EntityField:
    """Field definition for an entity."""
    field_id: str
    name: str
    field_type: FieldType
    description: str
    required: bool = True
    indexed: bool = False
    unique: bool = False
    default_value: Optional[Any] = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    enum_values: Optional[List[str]] = None
    reference_entity: Optional[str] = None  # For REFERENCE type
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """Represents a data entity in the application."""
    entity_id: str
    name: str
    entity_type: EntityType
    description: str
    fields: List[EntityField]
    primary_key: str  # Field name
    timestamps: bool = True  # created_at, updated_at
    soft_delete: bool = True
    permissions: Dict[str, Set[PermissionType]] = field(default_factory=dict)
    relationships: Dict[str, str] = field(default_factory=dict)  # entity_name -> relationship_type
    indexes: List[List[str]] = field(default_factory=list)  # Composite indexes
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowTrigger:
    """Defines what triggers a workflow."""
    trigger_type: WorkflowEventType
    entity_id: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None  # Cron expression for ON_SCHEDULE


@dataclass
class AppWorkflow:
    """Workflow within generated application."""
    workflow_id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    app_workflow_steps: List[Dict[str, Any]]  # Steps as simple task definitions
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIRoute:
    """Auto-generated API route."""
    route_id: str
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    description: str
    entity_id: Optional[str] = None  # Associated entity
    workflow_id: Optional[str] = None  # Associated workflow
    request_schema: Dict[str, Any] = field(default_factory=dict)
    response_schema: Dict[str, Any] = field(default_factory=dict)
    required_permissions: Set[PermissionType] = field(default_factory=set)
    rate_limit_per_minute: Optional[int] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    experimental: bool = False


@dataclass
class UIComponent:
    """Metadata for a UI component."""
    component_id: str
    name: str
    component_type: UIComponentType
    description: str
    entity_id: Optional[str] = None  # Associated entity
    fields: List[str] = field(default_factory=list)  # Field names to display
    layout: Dict[str, Any] = field(default_factory=dict)  # Layout config
    actions: List[str] = field(default_factory=list)  # Available actions
    styling: Dict[str, Any] = field(default_factory=dict)  # CSS/styling
    permissions: Set[PermissionType] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppPermission:
    """Permission definition in app."""
    permission_id: str
    name: str
    description: str
    permission_type: PermissionType
    applies_to: Set[str]  # entity_ids or route_ids
    roles: Set[str]  # Role names this permission can be assigned to
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppSchema:
    """Complete schema of a generated application."""
    schema_id: str
    app_name: str
    app_type: AppType
    description: str
    version: str
    entities: List[Entity]
    workflows: List[AppWorkflow]
    api_routes: List[APIRoute]
    ui_components: List[UIComponent]
    permissions: List[AppPermission]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        return None
    
    def get_workflow(self, workflow_id: str) -> Optional[AppWorkflow]:
        """Get workflow by ID."""
        for workflow in self.workflows:
            if workflow.workflow_id == workflow_id:
                return workflow
        return None
    
    def get_routes_for_entity(self, entity_id: str) -> List[APIRoute]:
        """Get all routes for an entity."""
        return [r for r in self.api_routes if r.entity_id == entity_id]


@dataclass
class AppModule:
    """Reusable module within an application."""
    module_id: str
    name: str
    description: str
    entities: List[Entity]
    workflows: List[AppWorkflow]
    api_routes: List[APIRoute]
    ui_components: List[UIComponent]
    dependencies: List[str] = field(default_factory=list)  # Other module IDs
    exports: List[str] = field(default_factory=list)  # What this module exports


@dataclass
class AppPackage:
    """Packaged version of an application."""
    package_id: str
    app_name: str
    version: str
    schema: AppSchema
    modules: List[AppModule]
    bundle_size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    build_metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, str] = field(default_factory=dict)  # package -> version
    checksums: Dict[str, str] = field(default_factory=dict)  # file -> checksum


@dataclass
class ResourceQuota:
    """Resource quota for an app instance."""
    quota_id: str
    max_requests_per_hour: int = 10000
    max_entities_per_query: int = 10000
    max_memory_mb: int = 512
    max_storage_gb: int = 10
    max_concurrent_connections: int = 100
    max_workflow_duration_seconds: int = 300


@dataclass
class AppInstance:
    """Runtime instance of a generated app."""
    instance_id: str
    package_id: str
    app_name: str
    version: str
    status: str  # running, stopped, error
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    quota: ResourceQuota = field(default_factory=ResourceQuota)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    data_store: Dict[str, Any] = field(default_factory=dict)  # In-memory storage
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppExecutionLog:
    """Log of app execution."""
    log_id: str
    instance_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    operation: str  # route called, workflow executed, etc.
    status: str  # success, failure, error
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppAnalytics:
    """Analytics for a running app."""
    analytics_id: str
    instance_id: str
    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    most_used_routes: Dict[str, int] = field(default_factory=dict)
    most_used_entities: Dict[str, int] = field(default_factory=dict)
    active_users: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppEvolutionSuggestion:
    """Suggestion for app improvement."""
    suggestion_id: str
    instance_id: str
    category: str  # performance, usability, security, feature
    priority: str  # low, medium, high, critical
    description: str
    implementation_effort: str  # low, medium, high
    estimated_impact: str  # low, medium, high
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppBlueprint:
    """Blueprint for an application."""
    blueprint_id: str
    app_name: str
    app_type: AppType
    user_prompt: str  # Original user intent
    schema: AppSchema
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    compiler_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppBlueprintRegistry:
    """Registry of app blueprints."""
    blueprints: Dict[str, AppBlueprint] = field(default_factory=dict)
    type_index: Dict[AppType, Set[str]] = field(default_factory=dict)  # type -> blueprint_ids
    
    def add_blueprint(self, blueprint: AppBlueprint) -> None:
        """Register a blueprint."""
        self.blueprints[blueprint.blueprint_id] = blueprint
        if blueprint.app_type not in self.type_index:
            self.type_index[blueprint.app_type] = set()
        self.type_index[blueprint.app_type].add(blueprint.blueprint_id)
    
    def get_blueprints_by_type(self, app_type: AppType) -> List[AppBlueprint]:
        """Get blueprints by app type."""
        blueprint_ids = self.type_index.get(app_type, set())
        return [self.blueprints[bid] for bid in blueprint_ids if bid in self.blueprints]


def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"
