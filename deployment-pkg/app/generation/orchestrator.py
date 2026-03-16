"""
Generation orchestrator - unified API for app generation.

Coordinates all generation components: schema generation, packaging, backend building,
UI generation, runtime execution, and learning from app usage.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Coroutine
from datetime import datetime

from .models import (
    AppType, AppBlueprint, AppBlueprint, AppPackage, ResourceQuota,
    AppBlueprintRegistry, generate_id
)
from .schema_generator import (
    AppSchemaGeneratorImpl, SchemaGenerationConfig
)
from .workflow_packager import (
    WorkflowPackager, AppPackager, VersionScheme
)
from .backend_builder import BackendBuilder
from .ui_metadata import UIComponentMetadataBuilder
from .runtime_container import AppRuntimeContainer, AppInstance
from .learning_memory import AppLearningMemory


class GenerationOrchestrator:
    """Orchestrates all app generation functionality."""
    
    def __init__(self):
        # Core generators
        self.schema_generator = AppSchemaGeneratorImpl(SchemaGenerationConfig())
        self.workflow_packager = WorkflowPackager()
        self.app_packager = AppPackager()
        self.backend_builder = BackendBuilder()
        self.ui_builder = UIComponentMetadataBuilder()
        
        # Runtime and learning
        self.runtime = AppRuntimeContainer()
        self.learning_memory = AppLearningMemory()
        
        # Registry
        self.blueprint_registry = AppBlueprintRegistry()
        self.active_instances: Dict[str, AppInstance] = {}
    
    async def generate_app_from_prompt(
        self,
        app_name: str,
        app_type: AppType,
        prompt: str
    ) -> AppBlueprint:
        """
        Generate complete app from natural language prompt.
        
        Main entry point for the generation system.
        Returns app blueprint that can be packaged and deployed.
        """
        
        # Step 1: Generate schema from prompt
        blueprint = self.schema_generator.generate_from_prompt(
            app_name,
            app_type,
            prompt
        )
        
        # Store blueprint
        self.blueprint_registry.add_blueprint(blueprint)
        
        return blueprint
    
    async def package_app(
        self,
        blueprint: AppBlueprint,
        version: Optional[str] = None,
        grouping_strategy: str = "by_entity"
    ) -> AppPackage:
        """
        Package app blueprint into deployable package.
        
        Converts schema into versioned modules and packages.
        """
        
        # Generate modules from schema
        modules = self.workflow_packager.package_app_into_modules(
            blueprint.schema,
            grouping_strategy
        )
        
        # Create package
        package = self.app_packager.create_package(
            blueprint.app_name,
            blueprint.schema,
            modules,
            version
        )
        
        return package
    
    async def generate_backend(
        self,
        blueprint: AppBlueprint
    ) -> Dict[str, Any]:
        """
        Generate backend specification from blueprint.
        
        Creates API routes, service layer, database schema, etc.
        """
        
        backend_spec = self.backend_builder.generate_backend(blueprint.schema)
        
        return backend_spec
    
    async def generate_ui_metadata(
        self,
        blueprint: AppBlueprint
    ) -> Dict[str, Any]:
        """
        Generate UI metadata for frontend generation.
        
        Creates forms, tables, dashboards, component specs.
        """
        
        ui_metadata = self.ui_builder.build_complete_ui_metadata(
            blueprint.app_name,
            blueprint.schema.entities
        )
        
        return ui_metadata
    
    async def create_app_instance(
        self,
        package: AppPackage,
        environment_variables: Optional[Dict[str, str]] = None,
        quota: Optional[ResourceQuota] = None
    ) -> AppInstance:
        """
        Create runtime instance of packaged app.
        
        Starts app container with resource quotas and monitoring.
        """
        
        # Create instance
        instance = await self.runtime.create_instance(
            package,
            environment_variables,
            quota
        )
        
        # Start instance
        success, error = await self.runtime.start_instance(instance.instance_id)
        if success:
            self.active_instances[instance.instance_id] = instance
        
        return instance
    
    async def execute_app_operation(
        self,
        instance_id: str,
        operation_name: str,
        handler: Callable[[], Coroutine]
    ) -> tuple[bool, Any, Optional[str]]:
        """
        Execute operation within app instance.
        
        Operations are isolated, monitored, and quota-checked.
        """
        
        return await self.runtime.execute_in_instance(
            instance_id,
            operation_name,
            handler
        )
    
    async def stop_app(self, instance_id: str) -> tuple[bool, Optional[str]]:
        """Stop running app instance."""
        success, error = await self.runtime.stop_instance(instance_id)
        if success and instance_id in self.active_instances:
            del self.active_instances[instance_id]
        return success, error
    
    async def analyze_app_performance(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Analyze app performance and health.
        
        Collects metrics, analytics, and suggestions.
        """
        
        # Get instance status
        status = self.runtime.get_instance_status(instance_id)
        
        # Get execution environment
        if instance_id not in self.runtime.environments:
            return {"error": "Instance not found"}
        
        environment = self.runtime.environments[instance_id]
        execution_logs = environment.execution_logs
        
        # Analyze and learn
        learning_analysis = await self.learning_memory.analyze_and_learn(
            instance_id,
            execution_logs
        )
        
        # Get insights
        insights = self.learning_memory.get_app_insights(instance_id)
        
        # Generate suggestions
        suggestions = self.runtime.generate_evolution_suggestions(instance_id)
        
        analysis = {
            "status": status,
            "learning_analysis": learning_analysis,
            "insights": insights,
            "suggestions": [
                {
                    "category": s.category,
                    "priority": s.priority,
                    "description": s.description,
                    "effort": s.implementation_effort,
                    "impact": s.estimated_impact
                }
                for s in suggestions
            ]
        }
        
        return analysis
    
    async def get_app_logs(
        self,
        instance_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution logs for app."""
        
        if instance_id not in self.runtime.environments:
            return []
        
        environment = self.runtime.environments[instance_id]
        logs = environment.execution_logs[-limit:]
        
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "operation": log.operation,
                "status": log.status,
                "duration_ms": log.duration_ms,
                "error": log.error
            }
            for log in logs
        ]
    
    async def full_app_generation_workflow(
        self,
        app_name: str,
        app_type: AppType,
        prompt: str,
        auto_start: bool = True
    ) -> Dict[str, Any]:
        """
        Complete, end-to-end app generation workflow.
        
        Generates schema, packages app, creates instance, starts running.
        """
        
        # Step 1: Generate blueprint
        blueprint = await self.generate_app_from_prompt(
            app_name,
            app_type,
            prompt
        )
        
        # Step 2: Generate backend
        backend = await self.generate_backend(blueprint)
        
        # Step 3: Generate UI
        ui = await self.generate_ui_metadata(blueprint)
        
        # Step 4: Package app
        package = await self.package_app(blueprint)
        
        # Step 5: Create instance
        instance = None
        if auto_start:
            instance = await self.create_app_instance(package)
        
        result = {
            "app_name": app_name,
            "app_type": app_type.value,
            "blueprint_id": blueprint.blueprint_id,
            "package_id": package.package_id,
            "schema": {
                "entities": len(blueprint.schema.entities),
                "workflows": len(blueprint.schema.workflows),
                "api_routes": len(blueprint.schema.api_routes),
                "ui_components": len(blueprint.schema.ui_components)
            },
            "backend": {
                "routes": len(backend.get("api_routes", [])),
                "service_methods": len(backend.get("service_layer", {}).get("methods", [])),
                "database_tables": len(backend.get("database", {}).get("tables", {}))
            },
            "ui": {
                "forms": len(ui.get("forms", {})),
                "tables": len(ui.get("tables", {})),
                "dashboards": len(ui.get("dashboards", {}))
            },
            "package": {
                "version": package.version,
                "bundle_size_kb": package.bundle_size_bytes // 1024,
                "modules": len(package.modules)
            },
            "instance": {
                "instance_id": instance.instance_id if instance else None,
                "status": instance.status if instance else "not_started"
            }
        }
        
        return result
    
    async def list_active_apps(self) -> List[Dict[str, Any]]:
        """List all active app instances."""
        
        apps = []
        for instance_id, instance in self.active_instances.items():
            status = self.runtime.get_instance_status(instance_id)
            apps.append({
                "instance_id": instance_id,
                "app_name": instance.app_name,
                "version": instance.version,
                "status": instance.status,
                "created_at": instance.created_at.isoformat(),
                "uptime_seconds": status.get("uptime_seconds", 0) if status else 0
            })
        
        return apps
    
    def get_blueprint(self, blueprint_id: str) -> Optional[AppBlueprint]:
        """Get blueprint by ID."""
        return self.blueprint_registry.blueprints.get(blueprint_id)
    
    def list_blueprints(
        self,
        app_type: Optional[AppType] = None
    ) -> List[AppBlueprint]:
        """List blueprints."""
        if app_type:
            return self.blueprint_registry.get_blueprints_by_type(app_type)
        return list(self.blueprint_registry.blueprints.values())
