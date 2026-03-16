"""
Agent-powered backend builder - auto-generates API routes and service layers.

Integrates with Phase 5 intelligence orchestrator for dynamic backend generation.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

from .models import (
    Entity, EntityField, APIRoute, AppWorkflow, AppSchema,
    PermissionType, generate_id
)


class ServiceMethodType(str, Enum):
    """Type of service method."""
    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    BATCH_CREATE = "batch_create"
    BULK_UPDATE = "bulk_update"
    EXECUTE_WORKFLOW = "execute_workflow"


@dataclass
class ServiceMethod:
    """Service layer method definition."""
    method_id: str
    method_type: ServiceMethodType
    name: str
    description: str
    entity_id: Optional[str] = None
    input_schema: Dict[str, Any] = None
    output_schema: Dict[str, Any] = None
    pagination: bool = False
    caching_ttl_seconds: Optional[int] = None
    requires_transaction: bool = False
    
    def __post_init__(self):
        if self.input_schema is None:
            self.input_schema = {}
        if self.output_schema is None:
            self.output_schema = {}


@dataclass
class DatabaseSchema:
    """Generated database schema."""
    schema_id: str
    tables: Dict[str, Dict[str, Any]]  # table_name -> schema
    indexes: Dict[str, List[str]]  # table_name -> indexed_columns
    foreign_keys: Dict[str, List[Dict[str, str]]]  # table_name -> [FK definitions]
    migrations: List[str] = None  # SQL migrations
    
    def __post_init__(self):
        if self.migrations is None:
            self.migrations = []


class ServiceLayerGenerator:
    """Generates service layer methods from entities."""
    
    def generate_methods(self, entity: Entity) -> List[ServiceMethod]:
        """Generate service methods for an entity."""
        methods = []
        
        # LIST method
        methods.append(ServiceMethod(
            method_id=generate_id("method"),
            method_type=ServiceMethodType.LIST,
            name=f"list_{entity.name.lower()}s",
            description=f"List all {entity.name.lower()}s with pagination",
            entity_id=entity.entity_id,
            output_schema={
                "type": "array",
                "items": {"type": "object"},
                "pagination": True
            },
            pagination=True,
            caching_ttl_seconds=300
        ))
        
        # GET method
        methods.append(ServiceMethod(
            method_id=generate_id("method"),
            method_type=ServiceMethodType.GET,
            name=f"get_{entity.name.lower()}_by_id",
            description=f"Get {entity.name.lower()} by ID",
            entity_id=entity.entity_id,
            input_schema={"id": {"type": "string", "required": True}},
            output_schema={"type": "object"},
            caching_ttl_seconds=600
        ))
        
        # CREATE method
        methods.append(ServiceMethod(
            method_id=generate_id("method"),
            method_type=ServiceMethodType.CREATE,
            name=f"create_{entity.name.lower()}",
            description=f"Create new {entity.name.lower()}",
            entity_id=entity.entity_id,
            input_schema=self._build_input_schema(entity.fields),
            output_schema={"type": "object"},
            requires_transaction=True
        ))
        
        # UPDATE method
        methods.append(ServiceMethod(
            method_id=generate_id("method"),
            method_type=ServiceMethodType.UPDATE,
            name=f"update_{entity.name.lower()}",
            description=f"Update {entity.name.lower()}",
            entity_id=entity.entity_id,
            input_schema={
                "id": {"type": "string", "required": True},
                **self._build_input_schema(entity.fields, required=False)
            },
            output_schema={"type": "object"},
            requires_transaction=True
        ))
        
        # DELETE method
        methods.append(ServiceMethod(
            method_id=generate_id("method"),
            method_type=ServiceMethodType.DELETE,
            name=f"delete_{entity.name.lower()}",
            description=f"Delete {entity.name.lower()}",
            entity_id=entity.entity_id,
            input_schema={"id": {"type": "string", "required": True}},
            requires_transaction=True
        ))
        
        # SEARCH method (if entity has many searchable fields)
        searchable_fields = [f for f in entity.fields if f.indexed]
        if searchable_fields:
            methods.append(ServiceMethod(
                method_id=generate_id("method"),
                method_type=ServiceMethodType.SEARCH,
                name=f"search_{entity.name.lower()}s",
                description=f"Search {entity.name.lower()}s",
                entity_id=entity.entity_id,
                input_schema={
                    "query": {"type": "string", "required": True},
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                output_schema={"type": "array", "items": {"type": "object"}},
                pagination=True
            ))
        
        return methods
    
    def _build_input_schema(
        self,
        fields: List[EntityField],
        required: bool = True
    ) -> Dict[str, Any]:
        """Build input schema from entity fields."""
        schema = {}
        for field in fields:
            field_schema = {"type": field.field_type.value}
            if field.enum_values:
                field_schema["enum"] = field.enum_values
            if not required:
                field_schema["required"] = False
            else:
                field_schema["required"] = field.required
            schema[field.name] = field_schema
        return schema


class DatabaseSchemaGenerator:
    """Generates database schemas from entities."""
    
    def generate_schema(self, entities: List[Entity]) -> DatabaseSchema:
        """Generate complete database schema."""
        
        tables = {}
        indexes = {}
        foreign_keys = {}
        migrations = []
        
        for entity in entities:
            # Generate table definition
            table_def = self._generate_table_definition(entity)
            tables[entity.name.lower()] = table_def
            
            # Generate indexes
            table_indexes = self._generate_indexes(entity)
            indexes[entity.name.lower()] = table_indexes
            
            # Generate migration SQL
            create_table_sql = self._generate_create_table_sql(entity)
            migrations.append(create_table_sql)
        
        # Generate foreign keys for relationships
        for entity in entities:
            if entity.relationships:
                fk_list = []
                for rel_name, rel_type in entity.relationships.items():
                    fk_def = {
                        "column": f"{rel_name}_id",
                        "references": rel_name.lower(),
                        "type": rel_type
                    }
                    fk_list.append(fk_def)
                if fk_list:
                    foreign_keys[entity.name.lower()] = fk_list
        
        schema = DatabaseSchema(
            schema_id=generate_id("db_schema"),
            tables=tables,
            indexes=indexes,
            foreign_keys=foreign_keys,
            migrations=migrations
        )
        
        return schema
    
    def _generate_table_definition(self, entity: Entity) -> Dict[str, Any]:
        """Generate table definition for entity."""
        columns = {}
        
        # Add ID column
        columns["id"] = {
            "type": "UUID",
            "primary_key": True,
            "auto_generate": True
        }
        
        # Add entity fields
        for field in entity.fields:
            columns[field.name] = {
                "type": self._map_field_type_to_sql(field.field_type),
                "required": field.required,
                "indexed": field.indexed,
                "unique": field.unique
            }
        
        # Add timestamps if enabled
        if entity.timestamps:
            columns["created_at"] = {
                "type": "TIMESTAMP",
                "default": "CURRENT_TIMESTAMP"
            }
            columns["updated_at"] = {
                "type": "TIMESTAMP",
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP"
            }
        
        # Add soft delete if enabled
        if entity.soft_delete:
            columns["deleted_at"] = {
                "type": "TIMESTAMP",
                "nullable": True
            }
        
        return {
            "name": entity.name.lower(),
            "columns": columns,
            "primary_key": "id"
        }
    
    def _map_field_type_to_sql(self, field_type) -> str:
        """Map field type to SQL type."""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INT",
            "float": "DECIMAL(10,2)",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "email": "VARCHAR(255)",
            "phone": "VARCHAR(20)",
            "url": "VARCHAR(2048)",
            "currency": "DECIMAL(12,2)",
            "enum": "VARCHAR(50)",
            "json": "JSON",
            "array": "JSON",
            "reference": "UUID"
        }
        return type_map.get(field_type.value, "VARCHAR(255)")
    
    def _generate_indexes(self, entity: Entity) -> List[str]:
        """Generate index definitions for entity."""
        indexes = []
        
        # Index primary key
        indexes.append(f"{entity.name.lower()}_id_idx")
        
        # Index all indexed fields
        for field in entity.fields:
            if field.indexed:
                indexes.append(f"{entity.name.lower()}_{field.name}_idx")
        
        # Composite indexes from entity definition
        for composite_index in entity.indexes:
            index_name = f"{entity.name.lower()}_{'_'.join(composite_index)}_idx"
            indexes.append(index_name)
        
        return indexes
    
    def _generate_create_table_sql(self, entity: Entity) -> str:
        """Generate SQL CREATE TABLE statement."""
        table_name = entity.name.lower()
        
        columns = ["id UUID PRIMARY KEY DEFAULT uuid_generate_v4()"]
        
        for field in entity.fields:
            sql_type = self._map_field_type_to_sql(field.field_type)
            col_def = f"{field.name} {sql_type}"
            
            if field.required:
                col_def += " NOT NULL"
            
            if field.unique:
                col_def += " UNIQUE"
            
            if field.default_value is not None:
                col_def += f" DEFAULT {field.default_value}"
            
            columns.append(col_def)
        
        if entity.timestamps:
            columns.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        if entity.soft_delete:
            columns.append("deleted_at TIMESTAMP")
        
        sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns) + "\n);"
        
        return sql


class BackendBuilder:
    """Builds complete backend from app schema."""
    
    def __init__(self):
        self.service_generator = ServiceLayerGenerator()
        self.db_generator = DatabaseSchemaGenerator()
    
    def generate_backend(self, schema: AppSchema) -> Dict[str, Any]:
        """Generate complete backend specification."""
        
        # Generate service methods
        service_methods = []
        for entity in schema.entities:
            methods = self.service_generator.generate_methods(entity)
            service_methods.extend(methods)
        
        # Generate database schema
        db_schema = self.db_generator.generate_schema(schema.entities)
        
        # Generate API routes with enhanced metadata
        enhanced_routes = self._enhance_routes(schema.api_routes, service_methods, db_schema)
        
        # Generate middleware specifications
        middleware = self._generate_middleware()
        
        # Generate error handling
        error_handlers = self._generate_error_handlers()
        
        backend_spec = {
            "app_name": schema.app_name,
            "version": schema.version,
            "api_routes": enhanced_routes,
            "service_layer": {
                "methods": [
                    {
                        "id": m.method_id,
                        "type": m.method_type.value,
                        "name": m.name,
                        "entity_id": m.entity_id,
                        "requires_transaction": m.requires_transaction
                    }
                    for m in service_methods
                ]
            },
            "database": {
                "tables": db_schema.tables,
                "indexes": db_schema.indexes,
                "migrations": db_schema.migrations
            },
            "middleware": middleware,
            "error_handlers": error_handlers,
            "authentication": self._generate_auth_config(),
            "authorization": self._generate_authz_config(schema),
            "caching": self._generate_cache_config(service_methods)
        }
        
        return backend_spec
    
    def _enhance_routes(
        self,
        routes: List[APIRoute],
        service_methods: List[ServiceMethod],
        db_schema: DatabaseSchema
    ) -> List[Dict[str, Any]]:
        """Enhance routes with service and database information."""
        enhanced = []
        
        for route in routes:
            # Find associated service method
            service_method = None
            if route.entity_id:
                for sm in service_methods:
                    if sm.entity_id == route.entity_id:
                        service_method = sm
                        break
            
            enhanced_route = {
                "id": route.route_id,
                "path": route.path,
                "method": route.method,
                "description": route.description,
                "entity_id": route.entity_id,
                "service_method": service_method.name if service_method else None,
                "requires_permissions": list(route.required_permissions),
                "request_schema": route.request_schema,
                "response_schema": route.response_schema,
                "rate_limit": route.rate_limit_per_minute,
                "experimental": route.experimental
            }
            enhanced.append(enhanced_route)
        
        return enhanced
    
    def _generate_middleware(self) -> List[Dict[str, Any]]:
        """Generate middleware specifications."""
        return [
            {
                "name": "authentication",
                "description": "JWT token validation",
                "priority": 100
            },
            {
                "name": "authorization",
                "description": "Permission-based access control",
                "priority": 90
            },
            {
                "name": "rate_limiting",
                "description": "Request rate limiting",
                "priority": 80
            },
            {
                "name": "request_logging",
                "description": "Request/response logging",
                "priority": 10
            },
            {
                "name": "error_handling",
                "description": "Global error handler",
                "priority": 5
            }
        ]
    
    def _generate_error_handlers(self) -> List[Dict[str, Any]]:
        """Generate error handling specifications."""
        return [
            {
                "error_type": "ValidationError",
                "status_code": 400,
                "message": "Invalid request parameters"
            },
            {
                "error_type": "AuthenticationError",
                "status_code": 401,
                "message": "Authentication required"
            },
            {
                "error_type": "AuthorizationError",
                "status_code": 403,
                "message": "Insufficient permissions"
            },
            {
                "error_type": "NotFoundError",
                "status_code": 404,
                "message": "Resource not found"
            },
            {
                "error_type": "ConflictError",
                "status_code": 409,
                "message": "Resource conflict"
            },
            {
                "error_type": "InternalError",
                "status_code": 500,
                "message": "Internal server error"
            }
        ]
    
    def _generate_auth_config(self) -> Dict[str, Any]:
        """Generate authentication configuration."""
        return {
            "type": "JWT",
            "secret_key_env": "JWT_SECRET",
            "token_expiration_hours": 24,
            "refresh_token_expiration_days": 30,
            "algorithms": ["HS256"],
            "token_claims": ["sub", "iat", "exp", "permissions"]
        }
    
    def _generate_authz_config(self, schema: AppSchema) -> Dict[str, Any]:
        """Generate authorization configuration."""
        return {
            "type": "RBAC",
            "roles": ["admin", "user", "viewer", "guest"],
            "permissions": [
                {"type": p.permission_type.value, "entities": p.applies_to}
                for p in schema.permissions
            ],
            "default_role": "guest"
        }
    
    def _generate_cache_config(self, methods: List[ServiceMethod]) -> Dict[str, Any]:
        """Generate caching configuration."""
        cached_methods = [m for m in methods if m.caching_ttl_seconds]
        
        return {
            "backend": "redis",
            "default_ttl_seconds": 300,
            "methods": [
                {
                    "name": m.name,
                    "ttl_seconds": m.caching_ttl_seconds
                }
                for m in cached_methods
            ]
        }
