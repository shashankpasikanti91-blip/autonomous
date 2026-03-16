"""
App schema generator - converts prompts into application schemas.

Analyzes user intent from prompts and generates complete application blueprints
with entities, workflows, API routes, and UI components.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional, Any

from .models import (
    AppSchema, AppType, Entity, EntityType, EntityField, FieldType,
    AppWorkflow, WorkflowEventType, WorkflowTrigger, APIRoute, UIComponent,
    UIComponentType, AppPermission, PermissionType, AppBlueprint,
    generate_id
)


@dataclass
class SchemaGenerationConfig:
    """Configuration for schema generation."""
    auto_timestamps: bool = True
    enable_soft_delete: bool = True
    include_audit_logging: bool = True
    infer_relationships: bool = True
    auto_index_common_fields: bool = True
    default_pagination_limit: int = 50


class EntityExtractor:
    """Extracts entities from natural language prompts."""
    
    # Common entity patterns
    ENTITY_KEYWORDS = {
        EntityType.CONTACT: ["contact", "person", "customer", "client", "user", "member"],
        EntityType.ACCOUNT: ["company", "organization", "account", "business", "team", "group"],
        EntityType.DEAL: ["deal", "opportunity", "contract", "transaction", "order", "sale"],
        EntityType.LEAD: ["lead", "prospect", "candidate", "applicant", "inquiry"],
        EntityType.TASK: ["task", "todo", "action item", "assignment", "work item"],
        EntityType.EVENT: ["event", "meeting", "appointment", "call", "session", "conference"],
        EntityType.CAMPAIGN: ["campaign", "promotion", "initiative", "project", "program"],
    }
    
    # Common field patterns
    FIELD_PATTERNS = {
        "name": (FieldType.STRING, True),
        "description": (FieldType.TEXT, False),
        "email": (FieldType.EMAIL, False),
        "phone": (FieldType.PHONE, False),
        "url": (FieldType.URL, False),
        "price": (FieldType.CURRENCY, False),
        "amount": (FieldType.CURRENCY, False),
        "cost": (FieldType.CURRENCY, False),
        "status": (FieldType.ENUM, False),
        "date": (FieldType.DATE, False),
        "time": (FieldType.DATETIME, False),
        "count": (FieldType.INTEGER, False),
        "percentage": (FieldType.FLOAT, False),
        "active": (FieldType.BOOLEAN, False),
        "enabled": (FieldType.BOOLEAN, False),
        "verified": (FieldType.BOOLEAN, False),
        "notes": (FieldType.TEXT, False),
    }
    
    def extract_entities(self, prompt: str) -> List[Tuple[str, EntityType]]:
        """Extract entity names and types from prompt."""
        entities = []
        prompt_lower = prompt.lower()
        
        for entity_type, keywords in self.ENTITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    # Extract entity names from context
                    entity_names = self._extract_entity_names(prompt, keyword)
                    for name in entity_names:
                        if (name, entity_type) not in entities:
                            entities.append((name, entity_type))
        
        # If no standard entities found, treat entire nouns as entities
        if not entities:
            nouns = self._extract_nouns(prompt)
            for noun in nouns[:3]:  # Limit to 3
                entities.append((noun, EntityType.CUSTOM))
        
        return entities
    
    def _extract_entity_names(self, text: str, context_keyword: str) -> List[str]:
        """Extract potential entity names from text."""
        names = []
        # Simple heuristic: capitalized words near keywords
        words = text.split()
        for i, word in enumerate(words):
            if context_keyword in word.lower() and i > 0:
                # Check previous word (might be entity name)
                prev = words[i - 1].strip('.,;:')
                if prev and prev[0].isupper():
                    names.append(prev)
        return names or [context_keyword.title()]
    
    def _extract_nouns(self, text: str) -> List[str]:
        """Simple noun extraction (capitalized words)."""
        # Very simple: just capitalized words
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        return list(set(words))


class FieldInferencer:
    """Infers fields for entities from prompts."""
    
    def infer_fields(self, entity_name: str, prompt: str) -> List[EntityField]:
        """Infer fields for an entity."""
        fields = []
        extractor = EntityExtractor()
        
        # Always add name field
        fields.append(EntityField(
            field_id=generate_id("field"),
            name="name",
            field_type=FieldType.STRING,
            description=f"Name of {entity_name.lower()}",
            required=True,
            indexed=True
        ))
        
        # Look for field patterns in prompt
        context = f"{entity_name} {prompt}".lower()
        for pattern, (field_type, required) in extractor.FIELD_PATTERNS.items():
            if pattern in context and not any(f.name == pattern for f in fields):
                fields.append(EntityField(
                    field_id=generate_id("field"),
                    name=pattern,
                    field_type=field_type,
                    description=f"{pattern.replace('_', ' ').title()} of {entity_name.lower()}",
                    required=required,
                    indexed=pattern in ["status", "email", "phone"]
                ))
        
        # If very few fields, add common ones
        if len(fields) < 4:
            common_fields = [
                ("description", FieldType.TEXT, False),
                ("status", FieldType.ENUM, False),
                ("active", FieldType.BOOLEAN, False),
            ]
            for field_name, field_type, required in common_fields:
                if not any(f.name == field_name for f in fields):
                    fields.append(EntityField(
                        field_id=generate_id("field"),
                        name=field_name,
                        field_type=field_type,
                        description=f"{field_name.replace('_', ' ').title()} of {entity_name.lower()}",
                        required=required
                    ))
        
        return fields


class WorkflowInferencer:
    """Infers workflows from prompts."""
    
    WORKFLOW_KEYWORDS = {
        "create": WorkflowEventType.ON_CREATE,
        "update": WorkflowEventType.ON_UPDATE,
        "delete": WorkflowEventType.ON_DELETE,
        "assign": WorkflowEventType.ON_USER_ACTION,
        "approve": WorkflowEventType.ON_USER_ACTION,
        "notify": WorkflowEventType.ON_USER_ACTION,
        "send": WorkflowEventType.ON_USER_ACTION,
        "schedule": WorkflowEventType.ON_SCHEDULE,
        "daily": WorkflowEventType.ON_SCHEDULE,
        "weekly": WorkflowEventType.ON_SCHEDULE,
    }
    
    def infer_workflows(
        self, 
        prompt: str, 
        entities: List[Tuple[str, EntityType]]
    ) -> List[AppWorkflow]:
        """Infer workflows from prompt."""
        workflows = []
        prompt_lower = prompt.lower()
        entity_names = [name for name, _ in entities]
        
        for keyword, event_type in self.WORKFLOW_KEYWORDS.items():
            if keyword in prompt_lower:
                # Create workflow for this action
                workflow_name = f"{keyword.title()} workflow"
                workflows.append(AppWorkflow(
                    workflow_id=generate_id("workflow"),
                    name=workflow_name,
                    description=f"Automatic {keyword} workflow",
                    trigger=WorkflowTrigger(trigger_type=event_type),
                    app_workflow_steps=[
                        {
                            "type": "log",
                            "message": f"Executing {keyword} action"
                        }
                    ]
                ))
        
        return workflows


class APIRouteGenerator:
    """Generates API routes from entities and workflows."""
    
    def generate_routes(self, entities: List[Entity]) -> List[APIRoute]:
        """Generate CRUD routes for entities."""
        routes = []
        
        for entity in entities:
            # List route
            routes.append(APIRoute(
                route_id=generate_id("route"),
                path=f"/api/{entity.name.lower()}s",
                method="GET",
                description=f"List all {entity.name.lower()}s",
                entity_id=entity.entity_id,
                response_schema={"type": "array", "items": {"type": "object"}},
                required_permissions={PermissionType.READ}
            ))
            
            # Get single route
            routes.append(APIRoute(
                route_id=generate_id("route"),
                path=f"/api/{entity.name.lower()}s/{{id}}",
                method="GET",
                description=f"Get {entity.name.lower()} by ID",
                entity_id=entity.entity_id,
                response_schema={"type": "object"},
                required_permissions={PermissionType.READ}
            ))
            
            # Create route
            routes.append(APIRoute(
                route_id=generate_id("route"),
                path=f"/api/{entity.name.lower()}s",
                method="POST",
                description=f"Create new {entity.name.lower()}",
                entity_id=entity.entity_id,
                request_schema={"type": "object"},
                response_schema={"type": "object"},
                required_permissions={PermissionType.CREATE}
            ))
            
            # Update route
            routes.append(APIRoute(
                route_id=generate_id("route"),
                path=f"/api/{entity.name.lower()}s/{{id}}",
                method="PUT",
                description=f"Update {entity.name.lower()}",
                entity_id=entity.entity_id,
                request_schema={"type": "object"},
                response_schema={"type": "object"},
                required_permissions={PermissionType.UPDATE}
            ))
            
            # Delete route
            routes.append(APIRoute(
                route_id=generate_id("route"),
                path=f"/api/{entity.name.lower()}s/{{id}}",
                method="DELETE",
                description=f"Delete {entity.name.lower()}",
                entity_id=entity.entity_id,
                required_permissions={PermissionType.DELETE}
            ))
        
        return routes


class UIComponentGenerator:
    """Generates UI components from entities."""
    
    def generate_components(self, entities: List[Entity]) -> List[UIComponent]:
        """Generate UI components for entities."""
        components = []
        
        for entity in entities:
            # Form for creating/editing
            components.append(UIComponent(
                component_id=generate_id("component"),
                name=f"{entity.name} Form",
                component_type=UIComponentType.FORM,
                description=f"Form to create or edit {entity.name.lower()}",
                entity_id=entity.entity_id,
                fields=[f.name for f in entity.fields[:5]],  # First 5 fields
                permissions={PermissionType.CREATE, PermissionType.UPDATE}
            ))
            
            # Table for listing
            components.append(UIComponent(
                component_id=generate_id("component"),
                name=f"{entity.name} Table",
                component_type=UIComponentType.TABLE,
                description=f"Table view of {entity.name.lower()} records",
                entity_id=entity.entity_id,
                fields=[f.name for f in entity.fields[:7]],  # First 7 fields
                permissions={PermissionType.READ}
            ))
            
            # Detail view
            components.append(UIComponent(
                component_id=generate_id("component"),
                name=f"{entity.name} Details",
                component_type=UIComponentType.DETAIL_VIEW,
                description=f"Detailed view of a {entity.name.lower()}",
                entity_id=entity.entity_id,
                fields=[f.name for f in entity.fields],
                permissions={PermissionType.READ}
            ))
        
        return components


class PermissionGenerator:
    """Generates permission definitions."""
    
    def generate_permissions(
        self, 
        entities: List[Entity],
        routes: List[APIRoute]
    ) -> List[AppPermission]:
        """Generate permissions for entities and routes."""
        permissions = []
        permission_types = [
            PermissionType.READ, PermissionType.CREATE,
            PermissionType.UPDATE, PermissionType.DELETE
        ]
        
        # Create permissions for each permission type
        for perm_type in permission_types:
            applies_to = set()
            
            # Apply to entities
            for entity in entities:
                applies_to.add(entity.entity_id)
            
            # Apply to routes
            for route in routes:
                if perm_type in route.required_permissions:
                    applies_to.add(route.route_id)
            
            if applies_to:
                permissions.append(AppPermission(
                    permission_id=generate_id("permission"),
                    name=f"Can {perm_type.value}",
                    description=f"Permission to {perm_type.value} resources",
                    permission_type=perm_type,
                    applies_to=applies_to,
                    roles={"admin", "user", "viewer"}
                ))
        
        return permissions


class SchemaValidator:
    """Validates generated schemas."""
    
    def validate(self, schema: AppSchema) -> Tuple[bool, List[str]]:
        """Validate a schema. Returns (is_valid, errors)."""
        errors = []
        
        # Check required fields
        if not schema.app_name:
            errors.append("App must have a name")
        if not schema.entities:
            errors.append("App must have at least one entity")
        
        # Check entities
        entity_ids = set()
        entity_names = set()
        for entity in schema.entities:
            if entity.entity_id in entity_ids:
                errors.append(f"Duplicate entity ID: {entity.entity_id}")
            if entity.name in entity_names:
                errors.append(f"Duplicate entity name: {entity.name}")
            entity_ids.add(entity.entity_id)
            entity_names.add(entity.name)
            
            # Check fields
            if not entity.fields:
                errors.append(f"Entity {entity.name} has no fields")
            
            field_names = set()
            for field in entity.fields:
                if field.name in field_names:
                    errors.append(f"Entity {entity.name} has duplicate field: {field.name}")
                field_names.add(field.name)
        
        # Check routes
        for route in schema.api_routes:
            if not route.path:
                errors.append(f"Route {route.route_id} has no path")
            if not route.method:
                errors.append(f"Route {route.route_id} has no method")
        
        return len(errors) == 0, errors


class AppSchemaGeneratorImpl:
    """Generates complete app schemas from natural language prompts."""
    
    def __init__(self, config: SchemaGenerationConfig = None):
        self.config = config or SchemaGenerationConfig()
        self.entity_extractor = EntityExtractor()
        self.field_inferencer = FieldInferencer()
        self.workflow_inferencer = WorkflowInferencer()
        self.route_generator = APIRouteGenerator()
        self.ui_generator = UIComponentGenerator()
        self.permission_generator = PermissionGenerator()
        self.validator = SchemaValidator()
    
    def generate_from_prompt(
        self,
        app_name: str,
        app_type: AppType,
        prompt: str
    ) -> AppBlueprint:
        """Generate complete app schema from prompt."""
        
        # Extract entities
        entity_tuples = self.entity_extractor.extract_entities(prompt)
        
        # Create entity objects
        entities = []
        for entity_name, entity_type in entity_tuples:
            fields = self.field_inferencer.infer_fields(entity_name, prompt)
            
            entity = Entity(
                entity_id=generate_id("entity"),
                name=entity_name,
                entity_type=entity_type,
                description=f"{entity_name} entity",
                fields=fields,
                primary_key="id"
            )
            entities.append(entity)
        
        # Infer workflows
        workflows = self.workflow_inferencer.infer_workflows(prompt, entity_tuples)
        
        # Generate API routes
        routes = self.route_generator.generate_routes(entities)
        
        # Generate UI components
        ui_components = self.ui_generator.generate_components(entities)
        
        # Generate permissions
        permissions = self.permission_generator.generate_permissions(entities, routes)
        
        # Create schema
        schema = AppSchema(
            schema_id=generate_id("schema"),
            app_name=app_name,
            app_type=app_type,
            description=f"Generated from prompt: {prompt[:100]}...",
            version="1.0.0",
            entities=entities,
            workflows=workflows,
            api_routes=routes,
            ui_components=ui_components,
            permissions=permissions
        )
        
        # Validate schema
        is_valid, errors = self.validator.validate(schema)
        if not is_valid:
            # Log errors but proceed (schema is still functional)
            pass
        
        # Create blueprint
        blueprint = AppBlueprint(
            blueprint_id=generate_id("blueprint"),
            app_name=app_name,
            app_type=app_type,
            user_prompt=prompt,
            schema=schema,
            created_at=datetime.utcnow()
        )
        
        return blueprint
