# Phase 6: Prompt-to-App Generation Layer

## Overview

Phase 6 implements a complete app generation system that converts natural language prompts into fully functional, deployable applications. It builds on the hardened integrations of Phase 4 and the autonomous intelligence of Phase 5 to create a system that can understand requirements and generate entire application stacks.

**Key Capability**: From a simple prompt like "Create a CRM to manage sales leads", generate a complete application with database schema, API routes, UI components, backend services, runtime environment, and built-in analytics.

## System Architecture

```
User Prompt
    ↓
┌─────────────────────────────────────────┐
│ Schema Generator (Phase 6)              │
│ - Entity Extraction                     │
│ - Field Inference                       │
│ - Workflow Generation                   │
└────────────┬────────────────────────────┘
             ↓
      AppBlueprint
             ↓
┌─────────────────────────────────────────┐
│ Multi-Component Generation              │
├─────────────────────────────────────────┤
│ • Backend Builder → API Routes          │
│ • UI Metadata Builder → Forms/Tables    │
│ • Workflow Packager → Modules           │
└────────────┬────────────────────────────┘
             ↓
      AppPackage
             ↓
┌─────────────────────────────────────────┐
│ Runtime Container (Phase 6)             │
│ - Instance Management                   │
│ - Resource Quotas                       │
│ - Execution Isolation                   │
└────────────┬────────────────────────────┘
             ↓
      Running AppInstance
             ↓
┌─────────────────────────────────────────┐
│ Learning System (Phase 6)               │
│ - Usage Analytics                       │
│ - Pattern Detection                     │
│ - Evolution Recommendations             │
└─────────────────────────────────────────┘
```

## Core Components

### 1. Schema Generator (`schema_generator.py`)

Converts natural language prompts into structured application schemas.

**Key Classes**:
- `EntityExtractor`: Identifies data entities (contacts, deals, etc.) from prompt
- `FieldInferencer`: Infers fields for each entity based on context
- `WorkflowInferencer`: Detects workflows and automation rules
- `APIRouteGenerator`: Creates CRUD routes for entities
- `UIComponentGenerator`: Generates form, table, detail view specifications
- `PermissionGenerator`: Creates permission definitions
- `SchemaValidator`: Validates schema completeness

**Usage**:
```python
from app.generation import AppSchemaGeneratorImpl, AppType

generator = AppSchemaGeneratorImpl()
blueprint = generator.generate_from_prompt(
    app_name="My CRM",
    app_type=AppType.CRM,
    prompt="Create a CRM system for managing sales leads and customers"
)

# blueprint.schema contains:
# - entities: [Contact, Company, Deal, etc.]
# - workflows: [auto-assignment, notifications, etc.]
# - api_routes: [GET /contacts, POST /deals, etc.]
# - ui_components: [forms, tables, dashboards]
# - permissions: [read, create, update, delete]
```

### 2. Workflow Packager (`workflow_packager.py`)

Packages application schemas into modular, versioned packages.

**Key Classes**:
- `WorkflowPackager`: Converts workflows into reusable modules
- `VersionManager`: Manages semantic versioning, calendar versioning, or sequential versioning
- `DependencyResolver`: Resolves module dependencies
- `AppPackager`: Creates deployable app packages

**Features**:
- Multiple packaging strategies (by_entity, by_workflow, by_feature)
- Semantic versioning with breaking change tracking
- Dependency specifications and resolution
- Bundle size estimation

**Usage**:
```python
from app.generation import AppPackager

packager = AppPackager()
package = packager.create_package(
    app_name="My CRM",
    schema=blueprint.schema,
    modules=modules,
    version="1.0.0"
)

# package includes:
# - Complete schema
# - Modular components
# - Dependencies list
# - Checksums for integrity
```

### 3. Backend Builder (`backend_builder.py`)

Generates complete backend specifications from app schemas.

**Key Classes**:
- `ServiceLayerGenerator`: Creates service methods (LIST, GET, CREATE, UPDATE, DELETE, SEARCH)
- `DatabaseSchemaGenerator`: Generates SQL table definitions, indexes, migrations
- `BackendBuilder`: Orchestrates backend generation

**Features**:
- Auto-generates CRUD operations for all entities
- Creates SQL migrations
- Generates middleware specifications
- Defines error handling patterns
- Sets up authentication (JWT) and authorization (RBAC)
- Configures caching and rate limiting

**Output Structure**:
```python
backend_spec = {
    "api_routes": [...],           # All API endpoints
    "service_layer": {...},        # Service methods
    "database": {...},             # SQL schemas and migrations
    "middleware": [...],           # Authentication, logging, etc.
    "error_handlers": [...],       # Error handling specifications
    "authentication": {...},       # JWT configuration
    "authorization": {...},        # RBAC configuration
    "caching": {...}               # Cache strategy
}
```

### 4. UI Metadata Generator (`ui_metadata.py`)

Generates UI component specifications for frontend auto-generation.

**Key Classes**:
- `UIMetadataGenerator`: Creates form, table, and dashboard specifications
- `UIComponentMetadataBuilder`: Builds complete UI metadata for app

**Features**:
- Generates forms with fields, validation, and layout
- Creates tables with sortable, filterable columns
- Builds dashboards with panels and metrics
- Specifies UI component types and behavior
- Includes accessibility and styling information

**Output**:
```python
ui_metadata = {
    "forms": {
        "contact_create": {...},    # Create form for contacts
        "contact_edit": {...},      # Edit form for contacts
        "contact_view": {...}       # View form for contacts
    },
    "tables": {
        "contact_list": {...},      # Contact listing table
        ...
    },
    "dashboards": {
        "main": {...}               # Main dashboard
    }
}
```

### 5. Runtime Container (`runtime_container.py`)

Executes generated applications with isolation and resource management.

**Key Classes**:
- `AppInstance`: Represents running application
- `ExecutionEnvironment`: Isolated execution context for app operations
- `ResourceMonitor`: Tracks resource usage and quota violations
- `AppRuntimeContainer`: Manages all running instances

**Features**:
- Creates isolated execution environments
- Enforces resource quotas (CPU, memory, requests, storage)
- Monitors resource usage and detects violations
- Executes operations safely within quotas
- Records execution logs and metrics
- Generates evolution suggestions based on usage

**Usage**:
```python
runtime = AppRuntimeContainer()

# Create instance
instance = await runtime.create_instance(
    package=app_package,
    resource_quota=ResourceQuota(
        max_requests_per_hour=10000,
        max_memory_mb=512,
        max_storage_gb=10
    )
)

# Start instance
await runtime.start_instance(instance.instance_id)

# Execute operations
success, result, error = await runtime.execute_in_instance(
    instance.instance_id,
    operation_name="create_contact",
    handler=async_create_contact
)

# Collect analytics
analytics = runtime.collect_analytics(instance.instance_id)

# Get status
status = runtime.get_instance_status(instance.instance_id)
```

### 6. Learning Memory (`learning_memory.py`)

Tracks app usage, detects patterns, and recommends improvements.

**Key Classes**:
- `MetricsCollector`: Collects usage metrics over time
- `PatternDetector`: Detects patterns in usage (peak hours, common routes, errors)
- `ImprovementRecommender`: Generates improvement recommendations
- `AppLearningMemory`: Coordinates learning across all components

**Capabilities**:
- Track response times, error rates, throughput
- Detect usage patterns and anomalies
- Generate actionable improvement recommendations
- Provide insights into app performance
- Recommend optimizations with effort/benefit estimates

**Usage**:
```python
memory = AppLearningMemory()

# Analyze app usage
analysis = await memory.analyze_and_learn(
    instance_id="app_123",
    execution_logs=logs
)

# Get insights
insights = memory.get_app_insights("app_123")

# Output:
# {
#   "patterns_detected": 5,
#   "learnings_by_category": {
#     "performance": [...],
#     "reliability": [...],
#     "scalability": [...]
#   },
#   "top_recommendations": [...]
# }
```

### 7. Generation Orchestrator (`orchestrator.py`)

Unified API coordinating all generation components.

**Main Class**: `GenerationOrchestrator`

**Key Methods**:
- `generate_app_from_prompt()`: Convert prompt to blueprint
- `package_app()`: Convert blueprint to deployable package
- `generate_backend()`: Create backend specification
- `generate_ui_metadata()`: Create UI specification
- `create_app_instance()`: Launch running instance
- `full_app_generation_workflow()`: End-to-end generation
- `analyze_app_performance()`: Analyze running app

**End-to-End Workflow**:
```python
from app.generation import GenerationOrchestrator, AppType

orchestrator = GenerationOrchestrator()

# Complete generation
result = await orchestrator.full_app_generation_workflow(
    app_name="My CRM",
    app_type=AppType.CRM,
    prompt="Create a CRM for managing sales leads and customers",
    auto_start=True
)

# Result includes:
# - blueprint_id
# - package_id
# - Schema with entities, workflows, routes
# - Backend specification
# - UI metadata
# - Running instance details
# - Instance status and uptime
```

## Integration with Phase 4 & Phase 5

### Phase 4 (Hardened Integrations)

Phase 6 uses Phase 4 for:
- **Adapter Access**: Backend builder queries adapter registry to bind API routes to external services
- **Health Monitoring**: Runtime checks health of integrated services before execution
- **Credential Management**: Apps use Phase 4 credential manager for safe secret handling
- **Error Handling**: Generated backend includes Phase 4 error patterns
- **Rate Limiting**: Runtime enforces service-level rate limits
- **Telemetry**: App operations feed into Phase 4 observability

### Phase 5 (Autonomous Intelligence)

Phase 6 uses Phase 5 for:
- **Orchestration**: Can invoke Phase 5 orchestrator from app workflows
- **Prompt Parsing**: Enhanced intent understanding for schema generation
- **Agent Routing**: App operations can use intelligent task routing
- **Tool Discovery**: Backend generator finds available tools from Phase 5 registry
- **Learning System**: App analytics feed into system-wide learning
- **Adaptive Retry**: Generated services use Phase 5 retry strategies
- **Safety Constraints**: App operations checked against safety policies

## Data Flow Example

**Input**: "Create an invoicing app that tracks unpaid invoices and sends automated reminders"

**Step 1: Schema Generation**
```
Entities detected: Invoice, Customer, Payment
Workflows inferred: SendReminder (on unpaid status), ProcessPayment
Fields inferred: invoice_number, amount, due_date, status, customer_id, etc.
Permissions created: read, create, update, delete
```

**Step 2: Backend Generation**
```
API Routes: 
  GET /api/invoices - list all
  POST /api/invoices - create
  GET /api/invoices/{id} - get one
  PUT /api/invoices/{id} - update
  DELETE /api/invoices/{id} - delete

Service methods:
  list_invoices(pagination)
  get_invoice_by_id(id)
  create_invoice(data)
  update_invoice(id, data)
  delete_invoice(id)
  mark_invoice_paid(id)

Database:
  CREATE TABLE invoices (
    id UUID PRIMARY KEY,
    invoice_number VARCHAR,
    customer_id UUID,
    amount DECIMAL,
    due_date DATE,
    status ENUM,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
  )
```

**Step 3: UI Generation**
```
Forms:
  invoice_create_form - fields: customer, amount, due_date, description
  invoice_edit_form - fields: amount, due_date, status
  invoice_view_form - all fields read-only

Tables:
  invoices_list - columns: number, customer, amount, status, due_date

Dashboard:
  Main dashboard with panels:
    - Total Revenue (metric)
    - Unpaid Invoices (metric)
    - Recent Invoices (table)
    - Payment Status (chart)
```

**Step 4: Packaging**
```
Package v1.0.0:
  - Schema with 3 entities, 2 workflows, 5 API routes, 3 forms, 1 table, 1 dashboard
  - Modules: InvoiceModule, CustomerModule, PaymentModule
  - Dependencies: core@1.0.0, workflows@1.0.0, api-framework@1.0.0
  - Bundle size: 245 KB
```

**Step 5: Runtime**
```
Instance created: app_inv_abc123
Status: running
Quotas:
  - Max requests/hour: 10,000
  - Max memory: 512 MB
  - Max storage: 10 GB
  
Operations executed: 150 in first hour
- 120 successful (GET /invoices)
- 15 successful (POST /invoices)
- 10 failed (validation errors)
- Avg response time: 85ms
```

**Step 6: Learning**
```
Patterns detected:
  - Peak usage 9-11 AM and 3-5 PM
  - Most common operation: list invoices
  - 2 recurring validation errors

Recommendations:
  1. Add caching for invoice list (high confidence, low effort, high impact)
  2. Improve validation error messages (medium confidence, low effort, medium impact)
  3. Add bulk invoice creation (low confidence, high effort, high impact)
```

## Usage Patterns

### Pattern 1: Quick App Generation

```python
orchestrator = GenerationOrchestrator()

result = await orchestrator.full_app_generation_workflow(
    app_name="Simple CRM",
    app_type=AppType.CRM,
    prompt="Track contacts and their interactions"
)

instance_id = result["instance"]["instance_id"]
```

### Pattern 2: Customized Generation

```python
# Generate blueprint
blueprint = await orchestrator.generate_app_from_prompt(
    app_name="Advanced CRM",
    app_type=AppType.CRM,
    prompt="..."
)

# Customize schema if needed
blueprint.schema.entities.append(custom_entity)

# Package with custom grouping
package = await orchestrator.package_app(
    blueprint,
    grouping_strategy="by_feature"
)

# Create with custom quotas
quota = ResourceQuota(
    max_requests_per_hour=50000,
    max_memory_mb=1024
)
instance = await orchestrator.create_app_instance(package, quota=quota)

# Start and monitor
await orchestrator.runtime.start_instance(instance.instance_id)
```

### Pattern 3: App Analysis and Learning

```python
# Let app run for period of time
# ...

# Analyze performance
analysis = await orchestrator.analyze_app_performance(instance_id)

# Review recommendations
for rec in analysis["suggestions"]:
    print(f"{rec['category']}: {rec['description']}")

# Implement improvements
# Generate next version of app with improvements
```

## Configuration

### Resource Quotas

```python
quota = ResourceQuota(
    quota_id=generate_id("quota"),
    max_requests_per_hour=10000,
    max_entities_per_query=1000,
    max_memory_mb=512,
    max_storage_gb=10,
    max_concurrent_connections=100,
    max_workflow_duration_seconds=300
)
```

### Schema Generation

```python
config = SchemaGenerationConfig(
    auto_timestamps=True,           # Add created_at, updated_at
    enable_soft_delete=True,        # Add deleted_at field
    include_audit_logging=True,     # Track changes
    infer_relationships=True,       # Detect relationships
    auto_index_common_fields=True   # Index name, email, status
)

generator = AppSchemaGeneratorImpl(config)
```

## Monitoring & Observability

### Instance Status

```python
status = orchestrator.runtime.get_instance_status(instance_id)

# Includes:
# - status: running/stopped/error
# - uptime_seconds
# - resource_usage: CPU, memory, storage
# - quota: limits
# - analytics: requests, response times, errors
```

### Execution Logs

```python
logs = await orchestrator.get_app_logs(instance_id, limit=100)

# Each log includes:
# - timestamp
# - operation
# - status: success/error/blocked
# - duration_ms
# - error message if failed
```

### Performance Metrics

```python
insights = orchestrator.learning_memory.get_app_insights(instance_id)

# Provides:
# - Total patterns detected
# - Patterns by type (peak hours, common routes, errors)
# - Learnings by category (performance, reliability, scalability)
# - Top recommendations with confidence scores
```

## Phase 6 Deliverables

✅ **App Schema Generator** (schema_generator.py)
- Entity extraction from natural language
- Field and workflow inference
- API route generation
- UI component generation
- Permission definition
- Schema validation

✅ **Dynamic Workflow Packaging** (workflow_packager.py)
- Module creation from workflows
- Semantic versioning system
- Dependency resolution
- Package creation with checksums

✅ **Agent-Powered Backend Builder** (backend_builder.py)
- Service layer generation
- Database schema generation
- CRUD operation templates
- Middleware specifications
- Authentication/Authorization setup

✅ **UI Metadata Generator** (ui_metadata.py)
- Form schema generation with validation
- Table schema generation with features
- Dashboard specification
- Component metadata for frontend

✅ **App Runtime Container** (runtime_container.py)
- Instance management
- Resource quota enforcement
- Execution environment isolation
- Health monitoring
- Performance analytics

✅ **App Learning Memory** (learning_memory.py)
- Usage metrics collection
- Pattern detection
- Evolution recommendations
- Performance analysis

✅ **Generation Orchestrator** (orchestrator.py)
- Unified API for all generation
- End-to-end workflow management
- Instance lifecycle management

✅ **Integration Validation** (integration_validation.py)
- Phase 4 integration verification
- Phase 5 integration verification
- Cross-phase workflow examples

## Next Steps

### For Users
1. Try generating a simple app with `full_app_generation_workflow()`
2. Analyze performance with `analyze_app_performance()`
3. Review learning recommendations
4. Iterate on app design based on usage patterns

### For Developers
1. Extend schema generator for domain-specific entities
2. Add custom packaging strategies
3. Implement custom metrics collectors
4. Create domain-specific UI templates
5. Integrate custom service backends

## References

- Phase 4: Hardened Integrations - adapter registry, health monitoring
- Phase 5: Autonomous Intelligence - orchestrator, tool routing, learning
- Models: All data structures are in `models.py`
- Configuration: Customize behavior in generator configs

---

**Phase 6 Complete**: Prompt-to-App generation layer enabling creation of full-stack applications from natural language descriptions.
