"""
App Generation Layer - Phase 6 of the Emergentic AI system.

Converts natural language prompts into complete, deployable applications.
Integrates with Phase 5 intelligence for smart app generation and optimization.

Main Components:
- Schema Generator: Converts prompts to app schemas with entities, workflows, permissions
- Workflow Packager: Packages app schemas into versioned, modular packages
- Backend Builder: Auto-generates API routes, service layers, database schemas
- UI Metadata: Generates form, table, dashboard specifications for frontend
- Runtime Container: Isolates app instances with resource quotas and monitoring
- Learning Memory: Tracks usage, detects patterns, recommends improvements
- Orchestrator: Unified API coordinating all generation components

Usage:
    from app.generation import GenerationOrchestrator, AppType
    
    orchestrator = GenerationOrchestrator()
    
    # Full end-to-end generation
    result = await orchestrator.full_app_generation_workflow(
        app_name="My CRM",
        app_type=AppType.CRM,
        prompt="Create a CRM system for managing sales leads and customers"
    )
"""

from .models import (
    # Enums
    AppType,
    EntityType,
    FieldType,
    UIComponentType,
    PermissionType,
    WorkflowEventType,
    
    # Data classes
    Entity,
    EntityField,
    AppSchema,
    AppWorkflow,
    APIRoute,
    UIComponent,
    AppPermission,
    AppModule,
    AppPackage,
    AppInstance,
    ResourceQuota,
    AppBlueprint,
    AppBlueprintRegistry,
    
    # Utilities
    generate_id,
)

from .schema_generator import (
    AppSchemaGeneratorImpl,
    SchemaGenerationConfig,
    EntityExtractor,
    FieldInferencer,
    WorkflowInferencer,
    APIRouteGenerator,
    UIComponentGenerator,
    PermissionGenerator,
    SchemaValidator,
)

from .workflow_packager import (
    WorkflowPackager,
    VersionManager,
    DependencyResolver,
    AppPackager,
    ModuleLifecycleStatus,
    VersionScheme,
)

from .backend_builder import (
    BackendBuilder,
    ServiceLayerGenerator,
    DatabaseSchemaGenerator,
    ServiceMethodType,
    ServiceMethod,
    DatabaseSchema,
)

from .ui_metadata import (
    UIMetadataGenerator,
    UIComponentMetadataBuilder,
    UIFormSchema,
    UITableSchema,
    UIDashboardSchema,
    UIFieldDefinition,
    UILayoutType,
    UIFieldInputType,
)

from .runtime_container import (
    AppRuntimeContainer,
    ExecutionEnvironment,
    ResourceMonitor,
    AppInstanceStatus,
    ResourceUsage,
)

from .learning_memory import (
    AppLearningMemory,
    MetricsCollector,
    PatternDetector,
    ImprovementRecommender,
    AppMetricType,
    ImprovementCategory,
)

from .orchestrator import GenerationOrchestrator

__all__ = [
    # Orchestrator (main entry point)
    "GenerationOrchestrator",
    
    # Enums
    "AppType",
    "EntityType",
    "FieldType",
    "UIComponentType",
    "PermissionType",
    "WorkflowEventType",
    "ModuleLifecycleStatus",
    "VersionScheme",
    "ServiceMethodType",
    "UILayoutType",
    "UIFieldInputType",
    "AppInstanceStatus",
    "AppMetricType",
    "ImprovementCategory",
    
    # Core data models
    "Entity",
    "EntityField",
    "AppSchema",
    "AppWorkflow",
    "APIRoute",
    "UIComponent",
    "AppPermission",
    "AppModule",
    "AppPackage",
    "AppInstance",
    "ResourceQuota",
    "AppBlueprint",
    "AppBlueprintRegistry",
    
    # Schema generation
    "AppSchemaGeneratorImpl",
    "SchemaGenerationConfig",
    "EntityExtractor",
    "FieldInferencer",
    "WorkflowInferencer",
    "APIRouteGenerator",
    "UIComponentGenerator",
    "PermissionGenerator",
    "SchemaValidator",
    
    # Packaging
    "WorkflowPackager",
    "VersionManager",
    "DependencyResolver",
    "AppPackager",
    
    # Backend generation
    "BackendBuilder",
    "ServiceLayerGenerator",
    "DatabaseSchemaGenerator",
    "ServiceMethod",
    "DatabaseSchema",
    
    # UI generation
    "UIMetadataGenerator",
    "UIComponentMetadataBuilder",
    "UIFormSchema",
    "UITableSchema",
    "UIDashboardSchema",
    "UIFieldDefinition",
    
    # Runtime
    "AppRuntimeContainer",
    "ExecutionEnvironment",
    "ResourceMonitor",
    "ResourceUsage",
    
    # Learning
    "AppLearningMemory",
    "MetricsCollector",
    "PatternDetector",
    "ImprovementRecommender",
    
    # Utilities
    "generate_id",
]

# Version info
__version__ = "1.0.0"
__phase__ = "Phase 6: Prompt-to-App Generation"
__description__ = "App generation layer for Emergentic AI system"
