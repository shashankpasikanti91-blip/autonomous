# Phase 6 API Reference

## GenerationOrchestrator

Main entry point for all app generation functionality.

### Initialization

```python
from app.generation import GenerationOrchestrator

orchestrator = GenerationOrchestrator()
```

### Methods

#### `generate_app_from_prompt(app_name, app_type, prompt)`

Generate app blueprint from natural language prompt.

**Parameters**:
- `app_name` (str): Name of the application
- `app_type` (AppType): Type of app (CRM, MARKETING, SALES, etc.)
- `prompt` (str): Natural language description of requirements

**Returns**: `AppBlueprint`

**Example**:
```python
blueprint = await orchestrator.generate_app_from_prompt(
    app_name="Lead Manager",
    app_type=AppType.SALES,
    prompt="Create a system to track and manage sales leads"
)
```

#### `package_app(blueprint, version, grouping_strategy)`

Convert blueprint into deployable package.

**Parameters**:
- `blueprint` (AppBlueprint): App blueprint to package
- `version` (str, optional): Version string (auto-generated if None)
- `grouping_strategy` (str): "by_entity", "by_workflow", or "by_feature"

**Returns**: `AppPackage`

**Example**:
```python
package = await orchestrator.package_app(
    blueprint,
    version="1.0.0",
    grouping_strategy="by_entity"
)
```

#### `generate_backend(blueprint)`

Generate backend specification from blueprint.

**Parameters**:
- `blueprint` (AppBlueprint): App blueprint

**Returns**: Dict with backend specification

**Example**:
```python
backend = await orchestrator.generate_backend(blueprint)

# Access:
backend["api_routes"]         # All API endpoints
backend["service_layer"]      # Service methods
backend["database"]           # SQL schemas
backend["middleware"]         # Middleware specs
backend["authentication"]     # Auth config
backend["authorization"]      # RBAC config
```

#### `generate_ui_metadata(blueprint)`

Generate UI component metadata from blueprint.

**Parameters**:
- `blueprint` (AppBlueprint): App blueprint

**Returns**: Dict with UI metadata

**Example**:
```python
ui = await orchestrator.generate_ui_metadata(blueprint)

# Access:
ui["forms"]                   # Form definitions
ui["tables"]                  # Table definitions
ui["dashboards"]              # Dashboard definitions
ui["components"]              # Component statistics
```

#### `create_app_instance(package, environment_variables, quota)`

Create and start app instance.

**Parameters**:
- `package` (AppPackage): App package to instantiate
- `environment_variables` (Dict, optional): Environment variables
- `quota` (ResourceQuota, optional): Resource limits

**Returns**: `AppInstance`

**Example**:
```python
from app.generation import ResourceQuota

quota = ResourceQuota(
    max_requests_per_hour=10000,
    max_memory_mb=512
)

instance = await orchestrator.create_app_instance(
    package,
    quota=quota
)

print(f"Instance running: {instance.instance_id}")
```

#### `execute_app_operation(instance_id, operation_name, handler)`

Execute operation within app instance.

**Parameters**:
- `instance_id` (str): ID of app instance
- `operation_name` (str): Name of operation being performed
- `handler` (Callable): Async function to execute

**Returns**: Tuple[bool, Any, Optional[str]] - (success, result, error)

**Example**:
```python
async def create_contact():
    return {"id": "123", "name": "John Doe"}

success, result, error = await orchestrator.execute_app_operation(
    instance_id="app_123",
    operation_name="create_contact",
    handler=create_contact
)

if success:
    print(f"Operation succeeded: {result}")
else:
    print(f"Operation failed: {error}")
```

#### `stop_app(instance_id)`

Stop running app instance.

**Parameters**:
- `instance_id` (str): ID of app instance

**Returns**: Tuple[bool, Optional[str]] - (success, error)

**Example**:
```python
success, error = await orchestrator.stop_app("app_123")
```

#### `analyze_app_performance(instance_id)`

Analyze app performance and get recommendations.

**Parameters**:
- `instance_id` (str): ID of app instance

**Returns**: Dict with analysis, insights, and suggestions

**Example**:
```python
analysis = await orchestrator.analyze_app_performance("app_123")

print(f"Status: {analysis['status']}")
print(f"Suggestions: {len(analysis['suggestions'])}")

for suggestion in analysis['suggestions']:
    print(f"- {suggestion['category']}: {suggestion['description']}")
```

#### `full_app_generation_workflow(app_name, app_type, prompt, auto_start)`

Complete end-to-end app generation.

**Parameters**:
- `app_name` (str): Application name
- `app_type` (AppType): Type of application
- `prompt` (str): Natural language requirements
- `auto_start` (bool): Automatically start instance

**Returns**: Dict with complete app information

**Example**:
```python
result = await orchestrator.full_app_generation_workflow(
    app_name="My CRM",
    app_type=AppType.CRM,
    prompt="Track customers, deals, and activities",
    auto_start=True
)

print(f"App generated with {result['schema']['entities']} entities")
print(f"Instance running: {result['instance']['instance_id']}")
```

#### `list_active_apps()`

Get list of all running app instances.

**Returns**: List of Dict

**Example**:
```python
apps = await orchestrator.list_active_apps()

for app in apps:
    print(f"{app['app_name']} v{app['version']} - {app['status']}")
```

#### `get_app_logs(instance_id, limit)`

Get execution logs for app.

**Parameters**:
- `instance_id` (str): ID of app instance
- `limit` (int): Maximum logs to return (default: 100)

**Returns**: List of Dict

**Example**:
```python
logs = await orchestrator.get_app_logs("app_123", limit=50)

for log in logs:
    print(f"{log['timestamp']}: {log['operation']} - {log['status']}")
```

---

## AppBlueprint

Represents a generated application blueprint.

### Attributes

- `blueprint_id` (str): Unique blueprint ID
- `app_name` (str): Application name
- `app_type` (AppType): Type of application
- `user_prompt` (str): Original user prompt
- `schema` (AppSchema): Complete app schema
- `created_at` (datetime): Creation time
- `compiler_version` (str): Version of compiler that generated it

### Example

```python
blueprint = await orchestrator.generate_app_from_prompt(
    app_name="Sales CRM",
    app_type=AppType.CRM,
    prompt="..."
)

# Access schema components
entities = blueprint.schema.entities
workflows = blueprint.schema.workflows
routes = blueprint.schema.api_routes
permissions = blueprint.schema.permissions

# Get entity by name
contact_entity = blueprint.schema.get_entity(entity_id)

# Get routes for entity
contact_routes = blueprint.schema.get_routes_for_entity(entity_id)
```

---

## AppPackage

Represents a packaged, deployable application.

### Attributes

- `package_id` (str): Unique package ID
- `app_name` (str): Application name
- `version` (str): Package version
- `schema` (AppSchema): Complete schema
- `modules` (List[AppModule]): Packaged modules
- `bundle_size_bytes` (int): Total size in bytes
- `dependencies` (Dict[str, str]): Required dependencies
- `checksums` (Dict[str, str]): Integrity checksums

### Example

```python
package = await orchestrator.package_app(blueprint)

print(f"Version: {package.version}")
print(f"Size: {package.bundle_size_bytes / 1024} KB")
print(f"Modules: {len(package.modules)}")
print(f"Dependencies: {package.dependencies}")
```

---

## AppInstance

Represents a running application instance.

### Attributes

- `instance_id` (str): Unique instance ID
- `app_name` (str): Application name
- `version` (str): Application version
- `status` (str): Current status (running, stopped, error, etc.)
- `quota` (ResourceQuota): Resource limits
- `created_at` (datetime): Creation time
- `started_at` (datetime): Start time
- `stopped_at` (datetime): Stop time

### Methods

Instance methods are called through the orchestrator:

```python
# Get instance status
status = orchestrator.runtime.get_instance_status(instance.instance_id)

# Stop instance
await orchestrator.stop_app(instance.instance_id)
```

---

## ResourceQuota

Defines resource limits for app instances.

### Attributes

- `max_requests_per_hour` (int): Request rate limit (default: 10,000)
- `max_entities_per_query` (int): Query size limit (default: 10,000)
- `max_memory_mb` (int): Memory limit in MB (default: 512)
- `max_storage_gb` (int): Storage limit in GB (default: 10)
- `max_concurrent_connections` (int): Connection limit (default: 100)
- `max_workflow_duration_seconds` (int): Workflow timeout (default: 300)

### Example

```python
from app.generation import ResourceQuota

quota = ResourceQuota(
    max_requests_per_hour=50000,
    max_memory_mb=1024,
    max_storage_gb=20,
    max_concurrent_connections=500
)
```

---

## AppType Enum

Application type classification.

**Values**:
- `CRM` - Customer Relationship Management
- `MARKETING` - Marketing automation
- `SALES` - Sales pipeline management
- `OPERATIONS` - Operational management
- `ANALYTICS` - Data analytics and reporting
- `WORKFLOW` - Workflow automation
- `DASHBOARD` - Dashboarding and visualization
- `INTERNAL_TOOL` - Internal business tools
- `CUSTOM` - Custom application

---

## EntityType Enum

Entity classification.

**Values**:
- `CONTACT` - Contact/person entity
- `ACCOUNT` - Company/organization entity
- `DEAL` - Deal/opportunity entity
- `LEAD` - Lead/prospect entity
- `TASK` - Task/action item entity
- `EVENT` - Event/meeting entity
- `CAMPAIGN` - Campaign/initiative entity
- `CUSTOM` - Custom entity

---

## FieldType Enum

Field data type specification.

**Values**:
- `STRING` - Text string (VARCHAR)
- `TEXT` - Long text (TEXT)
- `INTEGER` - Whole number (INT)
- `FLOAT` - Decimal number (DECIMAL)
- `BOOLEAN` - True/false (BOOLEAN)
- `DATE` - Date only (DATE)
- `DATETIME` - Date and time (TIMESTAMP)
- `EMAIL` - Email address (EMAIL)
- `PHONE` - Phone number (PHONE)
- `URL` - Web URL (URL)
- `CURRENCY` - Money amount (CURRENCY)
- `ENUM` - Enumerated choice (ENUM)
- `JSON` - JSON data (JSON)
- `ARRAY` - Array/list (ARRAY)
- `REFERENCE` - Foreign key reference (UUID)

---

## PermissionType Enum

Permission classification.

**Values**:
- `READ` - Read/view permission
- `CREATE` - Create/insert permission
- `UPDATE` - Update/modify permission
- `DELETE` - Delete permission
- `EXECUTE` - Execute/run permission
- `ADMIN` - Administrative permission

---

## Usage Statistics

### Code Files Created
- 8 core implementation files (~4,200 lines)
- 1 integration validation file (~280 lines)
- Total: ~4,480 lines of production code

### Documentation
- Phase 6 Comprehensive Guide (800+ lines)
- API Reference (this file, 500+ lines)
- Integration documentation

### Test Coverage
- Schema generation: ✅
- Backend building: ✅
- UI metadata generation: ✅
- Runtime container: ✅
- Learning system: ✅
- Integration validation: ✅

---

## Troubleshooting

### App fails to generate

**Check**:
1. Prompt is specific enough ("Create a CRM" → too vague)
2. Prompt is in natural language (no code)
3. App type matches requirements

**Solution**:
```python
# More specific prompt
prompt = """Create a CRM system that:
- Tracks contacts with name, email, phone
- Manages companies and their relationships
- Records interactions and meetings
- Assigns tasks to team members
"""

blueprint = await orchestrator.generate_app_from_prompt(
    app_name="Complete CRM",
    app_type=AppType.CRM,
    prompt=prompt
)
```

### Instance won't start

**Check**:
1. Resources available on system
2. Resource quota is reasonable
3. Dependencies are met

**Solution**:
```python
# Reduce quota
quota = ResourceQuota(
    max_memory_mb=256,
    max_storage_gb=5
)

instance = await orchestrator.create_app_instance(package, quota=quota)
```

### Performance degradation

**Check**:
1. Run analysis to get recommendations
2. Review learning suggestions
3. Monitor resource usage

**Solution**:
```python
analysis = await orchestrator.analyze_app_performance(instance_id)

# Implement top recommendations
for rec in analysis['suggestions']:
    print(f"Recommendation: {rec['description']}")
    print(f"Effort: {rec['effort']}, Impact: {rec['impact']}")
```

---

**Phase 6 API Complete**: Full reference for app generation functionality.
