"""
Tool-driven UI metadata layer - generates UI component specifications.

Produces metadata for forms, tables, dashboards enabling future frontend auto-generation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

from .models import (
    UIComponent, UIComponentType, Entity, EntityField, FieldType,
    APIRoute, PermissionType, generate_id
)


class UIFieldInputType(str, Enum):
    """HTML input type for UI fields."""
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    TEXTAREA = "textarea"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime-local"
    FILE = "file"
    PHONE = "tel"
    URL = "url"
    CURRENCY = "number"
    RICH_TEXT = "rich_text"


class UIValidationType(str, Enum):
    """Type of validation."""
    REQUIRED = "required"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    CUSTOM = "custom"


class UILayoutType(str, Enum):
    """Layout type for UI components."""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    GRID = "grid"
    RESPONSIVE = "responsive"
    TABS = "tabs"
    ACCORDION = "accordion"


@dataclass
class UIFieldDefinition:
    """Definition of a UI field."""
    field_id: str
    name: str
    label: str
    input_type: UIFieldInputType
    description: str = ""
    placeholder: str = ""
    required: bool = False
    disabled: bool = False
    read_only: bool = False
    hidden: bool = False
    default_value: Optional[Any] = None
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    options: Optional[List[Dict[str, str]]] = None  # For select, radio
    help_text: str = ""
    icon: Optional[str] = None
    tooltip: Optional[str] = None
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    pattern: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIFormSchema:
    """Schema for a form component."""
    form_id: str
    name: str
    title: str
    description: str
    entity_id: Optional[str] = None
    fields: List[UIFieldDefinition] = field(default_factory=list)
    layout: UILayoutType = UILayoutType.SINGLE_COLUMN
    submit_button_text: str = "Submit"
    cancel_button_text: str = "Cancel"
    submit_action: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    validation_level: str = "strict"  # loose, normal, strict
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIColumnDefinition:
    """Definition of a table column."""
    column_id: str
    field_name: str
    label: str
    data_type: str
    sortable: bool = True
    filterable: bool = True
    searchable: bool = False
    width: Optional[str] = None
    alignment: str = "left"  # left, center, right
    format: Optional[str] = None  # date format, currency format, etc.
    renderer: Optional[str] = None  # Custom renderer
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UITableSchema:
    """Schema for a table component."""
    table_id: str
    name: str
    title: str
    entity_id: Optional[str] = None
    columns: List[UIColumnDefinition] = field(default_factory=list)
    rows_per_page: int = 20
    pagination: bool = True
    sortable: bool = True
    filterable: bool = True
    searchable: bool = True
    selectable: bool = True
    striped: bool = True
    bordered: bool = True
    actions: List[str] = field(default_factory=list)  # view, edit, delete, etc.
    bulk_actions: List[str] = field(default_factory=list)  # delete, export, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIDashboardPanel:
    """Panel in a dashboard."""
    panel_id: str
    title: str
    panel_type: str  # table, chart, card, metric, etc.
    component_id: Optional[str] = None
    position: Dict[str, int] = field(default_factory=dict)  # x, y, width, height
    refresh_interval_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIDashboardSchema:
    """Schema for a dashboard component."""
    dashboard_id: str
    name: str
    title: str
    description: str = ""
    layout: UILayoutType = UILayoutType.RESPONSIVE
    panels: List[UIDashboardPanel] = field(default_factory=list)
    refresh_interval_seconds: Optional[int] = None
    auto_arrange: bool = True
    filters: List[UIFieldDefinition] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UIMetadataGenerator:
    """Generates UI metadata from entities and components."""
    
    def generate_form_for_entity(
        self,
        entity: Entity,
        form_type: str = "create"  # create, edit, view
    ) -> UIFormSchema:
        """Generate form schema for entity."""
        
        fields = []
        for entity_field in entity.fields:
            ui_field = self._entity_field_to_ui_field(entity_field, form_type)
            if not (form_type == "view" and entity_field.name == "id"):
                fields.append(ui_field)
        
        form_title = {
            "create": f"Create New {entity.name}",
            "edit": f"Edit {entity.name}",
            "view": f"View {entity.name}"
        }.get(form_type, f"Form for {entity.name}")
        
        submit_button = {
            "create": "Create",
            "edit": "Update",
            "view": "Close"
        }.get(form_type, "Submit")
        
        form = UIFormSchema(
            form_id=generate_id("form"),
            name=f"{entity.name.lower()}_{form_type}_form",
            title=form_title,
            description=f"{form_type.capitalize()} form for {entity.name.lower()}",
            entity_id=entity.entity_id,
            fields=fields,
            submit_button_text=submit_button,
            layout=self._determine_form_layout(len(fields))
        )
        
        return form
    
    def generate_table_for_entity(
        self,
        entity: Entity,
        max_columns: int = 7
    ) -> UITableSchema:
        """Generate table schema for entity."""
        
        columns = []
        
        # Add ID column
        columns.append(UIColumnDefinition(
            column_id=generate_id("column"),
            field_name="id",
            label="ID",
            data_type="uuid",
            sortable=True,
            filterable=True,
            width="150px"
        ))
        
        # Add entity fields (limit to max_columns)
        for entity_field in entity.fields[:max_columns-1]:
            column = UIColumnDefinition(
                column_id=generate_id("column"),
                field_name=entity_field.name,
                label=entity_field.name.replace("_", " ").title(),
                data_type=entity_field.field_type.value,
                sortable=entity_field.indexed,
                filterable=entity_field.indexed,
                searchable=entity_field.indexed,
                format=self._get_format_for_field_type(entity_field.field_type)
            )
            columns.append(column)
        
        table = UITableSchema(
            table_id=generate_id("table"),
            name=f"{entity.name.lower()}_table",
            title=f"{entity.name} List",
            entity_id=entity.entity_id,
            columns=columns,
            actions=["view", "edit", "delete"],
            bulk_actions=["delete", "export"]
        )
        
        return table
    
    def generate_dashboard(
        self,
        app_name: str,
        entities: List[Entity],
        tables: List[UITableSchema] = None
    ) -> UIDashboardSchema:
        """Generate dashboard schema for app."""
        
        panels = []
        
        # Add summary cards
        for i, entity in enumerate(entities[:3]):  # Limit to 3
            panel = UIDashboardPanel(
                panel_id=generate_id("panel"),
                title=f"{entity.name} Count",
                panel_type="metric",
                position={"x": i, "y": 0, "width": 1, "height": 1}
            )
            panels.append(panel)
        
        # Add tables as dashboard panels
        if tables:
            for i, table in enumerate(tables[:2]):  # Limit to 2
                panel = UIDashboardPanel(
                    panel_id=generate_id("panel"),
                    title=table.title,
                    panel_type="table",
                    component_id=table.table_id,
                    position={"x": 0, "y": i+1, "width": 3, "height": 2},
                    refresh_interval_seconds=300
                )
                panels.append(panel)
        
        dashboard = UIDashboardSchema(
            dashboard_id=generate_id("dashboard"),
            name=f"{app_name.lower()}_dashboard",
            title=f"{app_name} Dashboard",
            description=f"Main dashboard for {app_name}",
            layout=UILayoutType.RESPONSIVE,
            panels=panels,
            refresh_interval_seconds=300
        )
        
        return dashboard
    
    def _entity_field_to_ui_field(
        self,
        field: EntityField,
        form_type: str = "create"
    ) -> UIFieldDefinition:
        """Convert entity field to UI field definition."""
        
        read_only = form_type == "view" or field.name == "id"
        
        input_type = self._infer_input_type(field.field_type, field.enum_values)
        
        validation_rules = self._infer_validation_rules(field)
        
        ui_field = UIFieldDefinition(
            field_id=generate_id("field"),
            name=field.name,
            label=field.name.replace("_", " ").title(),
            input_type=input_type,
            description=field.description,
            required=field.required,
            read_only=read_only,
            validation_rules=validation_rules,
            options=self._build_options_for_enum(field),
            max_length=field.validation_rules.get("max_length"),
            min_length=field.validation_rules.get("min_length"),
            pattern=field.validation_rules.get("pattern")
        )
        
        return ui_field
    
    def _infer_input_type(
        self,
        field_type: FieldType,
        enum_values: Optional[List[str]] = None
    ) -> UIFieldInputType:
        """Infer UI input type from field type."""
        type_map = {
            FieldType.STRING: UIFieldInputType.TEXT,
            FieldType.TEXT: UIFieldInputType.TEXTAREA,
            FieldType.EMAIL: UIFieldInputType.EMAIL,
            FieldType.PHONE: UIFieldInputType.PHONE,
            FieldType.URL: UIFieldInputType.URL,
            FieldType.INTEGER: UIFieldInputType.NUMBER,
            FieldType.FLOAT: UIFieldInputType.NUMBER,
            FieldType.CURRENCY: UIFieldInputType.CURRENCY,
            FieldType.BOOLEAN: UIFieldInputType.CHECKBOX,
            FieldType.DATE: UIFieldInputType.DATE,
            FieldType.DATETIME: UIFieldInputType.DATETIME,
            FieldType.ENUM: UIFieldInputType.SELECT,
            FieldType.JSON: UIFieldInputType.TEXTAREA,
            FieldType.ARRAY: UIFieldInputType.TEXTAREA
        }
        return type_map.get(field_type, UIFieldInputType.TEXT)
    
    def _infer_validation_rules(self, field: EntityField) -> List[Dict[str, Any]]:
        """Infer validation rules for field."""
        rules = []
        
        if field.required:
            rules.append({"type": UIValidationType.REQUIRED.value})
        
        if field.field_type == FieldType.EMAIL:
            rules.append({"type": UIValidationType.EMAIL.value})
        elif field.field_type == FieldType.PHONE:
            rules.append({"type": UIValidationType.PHONE.value})
        elif field.field_type == FieldType.URL:
            rules.append({"type": UIValidationType.URL.value})
        
        # Add custom rules
        for rule_key, rule_value in field.validation_rules.items():
            if rule_key == "max_length":
                rules.append({
                    "type": UIValidationType.MAX_LENGTH.value,
                    "value": rule_value
                })
            elif rule_key == "min_length":
                rules.append({
                    "type": UIValidationType.MIN_LENGTH.value,
                    "value": rule_value
                })
            elif rule_key == "pattern":
                rules.append({
                    "type": UIValidationType.PATTERN.value,
                    "value": rule_value
                })
        
        return rules
    
    def _build_options_for_enum(
        self,
        field: EntityField
    ) -> Optional[List[Dict[str, str]]]:
        """Build options list for enum fields."""
        if field.enum_values:
            return [
                {"label": val.title(), "value": val}
                for val in field.enum_values
            ]
        return None
    
    def _get_format_for_field_type(self, field_type: FieldType) -> Optional[str]:
        """Get format string for field type."""
        format_map = {
            FieldType.DATE: "YYYY-MM-DD",
            FieldType.DATETIME: "YYYY-MM-DD HH:mm:ss",
            FieldType.CURRENCY: "$#,##0.00",
            FieldType.PHONE: "(XXX) XXX-XXXX"
        }
        return format_map.get(field_type)
    
    def _determine_form_layout(self, field_count: int) -> UILayoutType:
        """Determine appropriate form layout based on field count."""
        if field_count <= 3:
            return UILayoutType.SINGLE_COLUMN
        elif field_count <= 6:
            return UILayoutType.TWO_COLUMN
        else:
            return UILayoutType.RESPONSIVE
    
    def generate_edit_view_pair(
        self,
        entity: Entity
    ) -> tuple[UIFormSchema, UIFormSchema]:
        """Generate create and edit forms for entity."""
        create_form = self.generate_form_for_entity(entity, "create")
        edit_form = self.generate_form_for_entity(entity, "edit")
        return create_form, edit_form


class UIComponentMetadataBuilder:
    """Builds comprehensive UI metadata."""
    
    def __init__(self):
        self.generator = UIMetadataGenerator()
    
    def build_complete_ui_metadata(
        self,
        app_name: str,
        entities: List[Entity]
    ) -> Dict[str, Any]:
        """Build complete UI metadata for app."""
        
        forms = {}
        tables = {}
        dashboards = {}
        
        # Generate forms and tables for each entity
        for entity in entities:
            create_form, edit_form = self.generator.generate_edit_view_pair(entity)
            view_form = self.generator.generate_form_for_entity(entity, "view")
            
            entity_key = entity.name.lower()
            forms[f"{entity_key}_create"] = self._serialize_form(create_form)
            forms[f"{entity_key}_edit"] = self._serialize_form(edit_form)
            forms[f"{entity_key}_view"] = self._serialize_form(view_form)
            
            table = self.generator.generate_table_for_entity(entity)
            tables[f"{entity_key}_list"] = self._serialize_table(table)
        
        # Generate dashboard
        table_schemas = [
            self.generator.generate_table_for_entity(e)
            for e in entities
        ]
        dashboard = self.generator.generate_dashboard(app_name, entities, table_schemas)
        dashboards["main"] = self._serialize_dashboard(dashboard)
        
        metadata = {
            "app_name": app_name,
            "forms": forms,
            "tables": tables,
            "dashboards": dashboards,
            "components": {
                "form_count": len(forms),
                "table_count": len(tables),
                "dashboard_count": len(dashboards)
            }
        }
        
        return metadata
    
    def _serialize_form(self, form: UIFormSchema) -> Dict[str, Any]:
        """Serialize form to dict."""
        return {
            "id": form.form_id,
            "name": form.name,
            "title": form.title,
            "description": form.description,
            "fields": [
                {
                    "name": f.name,
                    "label": f.label,
                    "type": f.input_type.value,
                    "required": f.required,
                    "validation": f.validation_rules
                }
                for f in form.fields
            ],
            "layout": form.layout.value,
            "submit_button": form.submit_button_text
        }
    
    def _serialize_table(self, table: UITableSchema) -> Dict[str, Any]:
        """Serialize table to dict."""
        return {
            "id": table.table_id,
            "name": table.name,
            "title": table.title,
            "columns": [
                {
                    "name": c.field_name,
                    "label": c.label,
                    "sortable": c.sortable,
                    "filterable": c.filterable
                }
                for c in table.columns
            ],
            "pagination": table.pagination,
            "actions": table.actions,
            "bulk_actions": table.bulk_actions
        }
    
    def _serialize_dashboard(self, dashboard: UIDashboardSchema) -> Dict[str, Any]:
        """Serialize dashboard to dict."""
        return {
            "id": dashboard.dashboard_id,
            "name": dashboard.name,
            "title": dashboard.title,
            "layout": dashboard.layout.value,
            "panels": [
                {
                    "title": p.title,
                    "type": p.panel_type,
                    "position": p.position
                }
                for p in dashboard.panels
            ]
        }
