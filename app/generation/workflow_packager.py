"""
Dynamic workflow packaging - converts workflows into reusable modules.

Provides versioning, lifecycle management, and modular app structure.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from .models import (
    AppModule, Entity, AppWorkflow, APIRoute, UIComponent,
    AppPackage, AppSchema, generate_id
)


class ModuleLifecycleStatus(str, Enum):
    """Status of a module in its lifecycle."""
    DRAFT = "draft"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class VersionScheme(str, Enum):
    """Versioning scheme for modules."""
    SEMANTIC = "semantic"  # major.minor.patch
    CALENDAR = "calendar"  # YYYY.MM.DD
    SEQUENTIAL = "sequential"  # 1, 2, 3...


@dataclass
class ModuleVersionInfo:
    """Version information for a module."""
    version: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    released_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    description: str = ""
    breaking_changes: List[str] = field(default_factory=list)
    compatible_versions: List[str] = field(default_factory=list)


@dataclass
class ModuleDependency:
    """Dependency information."""
    module_name: str
    version: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    optional: bool = False


class WorkflowPackager:
    """Packages workflows into reusable modules."""
    
    def create_module_from_workflow(
        self,
        workflow: AppWorkflow,
        entities: List[Entity],
        routes: List[APIRoute],
        components: List[UIComponent],
        module_name: Optional[str] = None
    ) -> AppModule:
        """Create a module from a workflow."""
        
        module_name = module_name or f"{workflow.name} Module"
        
        # Infer entities used by workflow
        related_entities = self._infer_related_entities(workflow, entities)
        
        # Infer routes needed by workflow
        related_routes = self._infer_related_routes(workflow, routes)
        
        # Infer components needed by workflow
        related_components = self._infer_related_components(workflow, components)
        
        module = AppModule(
            module_id=generate_id("module"),
            name=module_name,
            description=workflow.description,
            entities=related_entities,
            workflows=[workflow],
            api_routes=related_routes,
            ui_components=related_components
        )
        
        return module
    
    def _infer_related_entities(
        self,
        workflow: AppWorkflow,
        all_entities: List[Entity]
    ) -> List[Entity]:
        """Infer which entities are related to workflow."""
        related_entity_ids = set()
        
        # Check workflow trigger for entity reference
        if workflow.trigger.entity_id:
            related_entity_ids.add(workflow.trigger.entity_id)
        
        # Look for entity references in steps
        for step in workflow.app_workflow_steps:
            if isinstance(step, dict) and "entity_id" in step:
                related_entity_ids.add(step["entity_id"])
        
        # Return matching entities
        return [
            e for e in all_entities
            if e.entity_id in related_entity_ids
        ]
    
    def _infer_related_routes(
        self,
        workflow: AppWorkflow,
        all_routes: List[APIRoute]
    ) -> List[APIRoute]:
        """Infer which routes are related to workflow."""
        related_routes = []
        
        # Look for workflow references in routes
        for route in all_routes:
            if route.workflow_id == workflow.workflow_id:
                related_routes.append(route)
        
        return related_routes
    
    def _infer_related_components(
        self,
        workflow: AppWorkflow,
        all_components: List[UIComponent]
    ) -> List[UIComponent]:
        """Infer which components are related to workflow."""
        related_components = []
        
        # Look for workflow triggers in components
        for component in all_components:
            if workflow.trigger.entity_id and component.entity_id == workflow.trigger.entity_id:
                related_components.append(component)
        
        return related_components
    
    def package_app_into_modules(
        self,
        schema: AppSchema,
        grouping_strategy: str = "by_entity"
    ) -> List[AppModule]:
        """Package app schema into logical modules."""
        
        if grouping_strategy == "by_entity":
            return self._package_by_entity(schema)
        elif grouping_strategy == "by_workflow":
            return self._package_by_workflow(schema)
        elif grouping_strategy == "by_feature":
            return self._package_by_feature(schema)
        else:
            return self._package_by_entity(schema)  # Default
    
    def _package_by_entity(self, schema: AppSchema) -> List[AppModule]:
        """Group modules by entity."""
        modules = []
        
        for entity in schema.entities:
            # Find routes related to entity
            entity_routes = [r for r in schema.api_routes if r.entity_id == entity.entity_id]
            
            # Find workflows related to entity
            entity_workflows = [
                w for w in schema.workflows
                if w.trigger.entity_id == entity.entity_id
            ]
            
            # Find components related to entity
            entity_components = [
                c for c in schema.ui_components
                if c.entity_id == entity.entity_id
            ]
            
            if entity_routes or entity_workflows or entity_components:
                module = AppModule(
                    module_id=generate_id("module"),
                    name=f"{entity.name} Module",
                    description=f"Module for managing {entity.name.lower()}",
                    entities=[entity],
                    workflows=entity_workflows,
                    api_routes=entity_routes,
                    ui_components=entity_components
                )
                modules.append(module)
        
        return modules
    
    def _package_by_workflow(self, schema: AppSchema) -> List[AppModule]:
        """Group modules by workflow."""
        modules = []
        
        for workflow in schema.workflows:
            related_entities = [
                e for e in schema.entities
                if e.entity_id == workflow.trigger.entity_id or
                   any(step.get("entity_id") == e.entity_id for step in workflow.app_workflow_steps if isinstance(step, dict))
            ]
            
            related_routes = [
                r for r in schema.api_routes
                if r.workflow_id == workflow.workflow_id
            ]
            
            related_components = [
                c for c in schema.ui_components
                if c.entity_id in [e.entity_id for e in related_entities]
            ]
            
            module = AppModule(
                module_id=generate_id("module"),
                name=f"{workflow.name} Module",
                description=f"Module for {workflow.name.lower()}",
                entities=related_entities,
                workflows=[workflow],
                api_routes=related_routes,
                ui_components=related_components
            )
            modules.append(module)
        
        return modules
    
    def _package_by_feature(self, schema: AppSchema) -> List[AppModule]:
        """Group modules by feature (high-level grouping)."""
        # Simple implementation: group similar entities together
        modules = []
        processed_entities = set()
        
        for i, entity in enumerate(schema.entities):
            if entity.entity_id in processed_entities:
                continue
            
            # Group this entity with the next one (simple chunking)
            entity_group = [entity]
            processed_entities.add(entity.entity_id)
            
            if i + 1 < len(schema.entities):
                next_entity = schema.entities[i + 1]
                if next_entity.entity_id not in processed_entities:
                    entity_group.append(next_entity)
                    processed_entities.add(next_entity.entity_id)
            
            # Create module from group
            modules.append(self._create_module_from_entities(schema, entity_group))
        
        return modules
    
    def _create_module_from_entities(
        self,
        schema: AppSchema,
        entities: List[Entity]
    ) -> AppModule:
        """Create module from entity list."""
        entity_ids = {e.entity_id for e in entities}
        
        related_routes = [
            r for r in schema.api_routes
            if r.entity_id in entity_ids
        ]
        
        related_workflows = [
            w for w in schema.workflows
            if w.trigger.entity_id in entity_ids
        ]
        
        related_components = [
            c for c in schema.ui_components
            if c.entity_id in entity_ids
        ]
        
        module_name = " & ".join([e.name for e in entities])
        module = AppModule(
            module_id=generate_id("module"),
            name=module_name,
            description=f"Module for {module_name.lower()}",
            entities=entities,
            workflows=related_workflows,
            api_routes=related_routes,
            ui_components=related_components
        )
        
        return module


class VersionManager:
    """Manages module versioning."""
    
    def __init__(self, scheme: VersionScheme = VersionScheme.SEMANTIC):
        self.scheme = scheme
        self.version_history: Dict[str, List[ModuleVersionInfo]] = {}
    
    def get_next_version(
        self,
        module_name: str,
        release_type: str = "patch"  # major, minor, patch
    ) -> str:
        """Get next version string."""
        if self.scheme == VersionScheme.SEMANTIC:
            return self._get_next_semantic_version(module_name, release_type)
        elif self.scheme == VersionScheme.CALENDAR:
            return self._get_next_calendar_version()
        elif self.scheme == VersionScheme.SEQUENTIAL:
            return self._get_next_sequential_version(module_name)
        else:
            return "1.0.0"
    
    def _get_next_semantic_version(
        self,
        module_name: str,
        release_type: str
    ) -> str:
        """Generate next semantic version."""
        current = "1.0.0"
        
        if module_name in self.version_history and self.version_history[module_name]:
            current = self.version_history[module_name][-1].version
        
        parts = current.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        if release_type == "major":
            major += 1
            minor, patch = 0, 0
        elif release_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _get_next_calendar_version(self) -> str:
        """Generate calendar-based version."""
        return datetime.utcnow().strftime("%Y.%m.%d")
    
    def _get_next_sequential_version(self, module_name: str) -> str:
        """Generate sequential version."""
        current = 1
        if module_name in self.version_history and self.version_history[module_name]:
            current = int(self.version_history[module_name][-1].version) + 1
        return str(current)
    
    def record_version(
        self,
        module_name: str,
        version: str,
        description: str = "",
        breaking_changes: List[str] = None
    ) -> ModuleVersionInfo:
        """Record a new version."""
        version_info = ModuleVersionInfo(
            version=version,
            description=description,
            breaking_changes=breaking_changes or []
        )
        
        if module_name not in self.version_history:
            self.version_history[module_name] = []
        
        self.version_history[module_name].append(version_info)
        return version_info


class DependencyResolver:
    """Resolves module dependencies."""
    
    def __init__(self):
        self.dependency_graph: Dict[str, List[ModuleDependency]] = {}
    
    def add_dependency(
        self,
        module_name: str,
        dependency: ModuleDependency
    ) -> None:
        """Register a dependency."""
        if module_name not in self.dependency_graph:
            self.dependency_graph[module_name] = []
        self.dependency_graph[module_name].append(dependency)
    
    def resolve_dependencies(
        self,
        module_name: str,
        installed_modules: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """Resolve dependencies. Returns (satisfied, missing_dependencies)."""
        if module_name not in self.dependency_graph:
            return True, []
        
        missing = []
        for dep in self.dependency_graph[module_name]:
            if dep.module_name not in installed_modules:
                missing.append(f"{dep.module_name}@{dep.version}")
            else:
                # Check version compatibility
                installed = installed_modules[dep.module_name]
                if not self._version_compatible(installed, dep):
                    missing.append(
                        f"{dep.module_name} (required: {dep.version}, installed: {installed})"
                    )
        
        return len(missing) == 0, missing
    
    def _version_compatible(
        self,
        installed_version: str,
        dependency: ModuleDependency
    ) -> bool:
        """Check if installed version satisfies dependency."""
        # Simple version comparison
        if dependency.min_version and self._compare_versions(installed_version, dependency.min_version) < 0:
            return False
        if dependency.max_version and self._compare_versions(installed_version, dependency.max_version) > 0:
            return False
        return True
    
    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare two semantic versions. Returns -1, 0, or 1."""
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        
        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        
        if len(parts1) < len(parts2):
            return -1
        elif len(parts1) > len(parts2):
            return 1
        return 0


class AppPackager:
    """Creates app packages from schemas and modules."""
    
    def __init__(self):
        self.version_manager = VersionManager()
        self.dependency_resolver = DependencyResolver()
    
    def create_package(
        self,
        app_name: str,
        schema: AppSchema,
        modules: List[AppModule],
        version: Optional[str] = None
    ) -> AppPackage:
        """Create app package."""
        
        if version is None:
            version = self.version_manager.get_next_version(app_name)
        else:
            self.version_manager.record_version(app_name, version)
        
        # Calculate bundle size (rough estimate)
        bundle_size = self._estimate_bundle_size(schema, modules)
        
        # Gather dependencies
        dependencies = self._gather_dependencies(modules)
        
        # Create checksums for integrity
        checksums = self._calculate_checksums(schema, modules)
        
        package = AppPackage(
            package_id=generate_id("package"),
            app_name=app_name,
            version=version,
            schema=schema,
            modules=modules,
            bundle_size_bytes=bundle_size,
            dependencies=dependencies,
            checksums=checksums
        )
        
        return package
    
    def _estimate_bundle_size(
        self,
        schema: AppSchema,
        modules: List[AppModule]
    ) -> int:
        """Estimate bundle size in bytes."""
        # Rough estimate based on number of entities, workflows, etc.
        size = 0
        
        size += len(schema.entities) * 2000  # ~2KB per entity definition
        size += len(schema.workflows) * 1500  # ~1.5KB per workflow
        size += len(schema.api_routes) * 500  # ~500B per route
        size += len(schema.ui_components) * 1000  # ~1KB per component
        
        return size
    
    def _gather_dependencies(self, modules: List[AppModule]) -> Dict[str, str]:
        """Gather module dependencies."""
        dependencies = {}
        
        # Standard dependencies for all apps
        dependencies["core"] = "1.0.0"
        dependencies["intelligence"] = "1.0.0"
        
        # Add module-specific dependencies based on complexity
        for module in modules:
            if len(module.workflows) > 0:
                dependencies["workflows"] = "1.0.0"
            if len(module.api_routes) > 5:
                dependencies["api-framework"] = "1.0.0"
            if len(module.ui_components) > 5:
                dependencies["ui-framework"] = "1.0.0"
        
        return dependencies
    
    def _calculate_checksums(
        self,
        schema: AppSchema,
        modules: List[AppModule]
    ) -> Dict[str, str]:
        """Calculate checksums for package integrity."""
        import hashlib
        
        checksums = {}
        
        # Checksum of schema
        schema_json = json.dumps({
            "entities": len(schema.entities),
            "workflows": len(schema.workflows),
            "routes": len(schema.api_routes)
        })
        checksums["schema"] = hashlib.md5(schema_json.encode()).hexdigest()
        
        # Checksum of modules
        module_json = json.dumps({
            "count": len(modules),
            "total_routes": sum(len(m.api_routes) for m in modules)
        })
        checksums["modules"] = hashlib.md5(module_json.encode()).hexdigest()
        
        return checksums
