"""
Services Module

Provides orchestration, connectors, webhooks, and real service implementations 
for production deployment.
"""

# Lazy imports to avoid circular dependencies during initialization
def _lazy_import_services():
    """Lazy load service implementations to avoid circular imports."""
    from services.connectors import (
        EmailConnector,
        GmailConnector,
        MessagingConnector,
        WhatsAppConnector,
        CalendarConnector,
        GoogleCalendarConnector,
        PayrollConnector,
        PayrollProcessor,
        InvoiceConnector,
        InvoiceGenerator,
        CRMConnector,
        HubSpotConnector,
        VisaMonitoringConnector,
        VisaMonitor,
        ServiceConnectorFactory,
        ServiceProvider
    )

    from services.orchestration import (
        AgentOrchestrationService,
        OrchestrationContext,
        ExecutionStrategy,
        RetryPolicy
    )

    from services.n8n_webhooks import (
        N8NWebhookHandler,
        N8NWebhookResponse,
        N8NWorkflowInput,
        N8NWebhookDefinition,
        N8NWorkflowRegistry
    )

    # Real service implementations  
    from services.email_service import EmailService, get_email_service
    from services.messaging_service import WhatsAppService, get_whatsapp_service
    from services.calendar_service import GoogleCalendarService, get_google_calendar_service
    from services.crm_service import CRMService, get_crm_service
    from services.payroll_engine import PayrollEngine, PayrollDeduction, get_payroll_engine
    from services.invoice_service import InvoiceLineItem, get_invoice_generator
    from services.scheduler import (
        JobScheduler, ScheduledJob, JobStatus, JobFrequency,
        get_scheduler,
        visa_status_check_job,
        payroll_cycle_job,
        follow_up_reminder_job,
        sales_lead_nurturing_job
    )

    return {
        'EmailConnector': EmailConnector,
        'GmailConnector': GmailConnector,
        'MessagingConnector': MessagingConnector,
        'WhatsAppConnector': WhatsAppConnector,
        'CalendarConnector': CalendarConnector,
        'GoogleCalendarConnector': GoogleCalendarConnector,
        'PayrollConnector': PayrollConnector,
        'PayrollProcessor': PayrollProcessor,
        'InvoiceConnector': InvoiceConnector,
        'InvoiceGenerator': InvoiceGenerator,
        'CRMConnector': CRMConnector,
        'HubSpotConnector': HubSpotConnector,
        'VisaMonitoringConnector': VisaMonitoringConnector,
        'VisaMonitor': VisaMonitor,
        'ServiceConnectorFactory': ServiceConnectorFactory,
        'ServiceProvider': ServiceProvider,
        'AgentOrchestrationService': AgentOrchestrationService,
        'OrchestrationContext': OrchestrationContext,
        'ExecutionStrategy': ExecutionStrategy,
        'RetryPolicy': RetryPolicy,
        'N8NWebhookHandler': N8NWebhookHandler,
        'N8NWebhookResponse': N8NWebhookResponse,
        'N8NWorkflowInput': N8NWorkflowInput,
        'N8NWebhookDefinition': N8NWebhookDefinition,
        'N8NWorkflowRegistry': N8NWorkflowRegistry,
        'EmailService': EmailService,
        'get_email_service': get_email_service,
        'WhatsAppService': WhatsAppService,
        'get_whatsapp_service': get_whatsapp_service,
        'GoogleCalendarService': GoogleCalendarService,
        'get_google_calendar_service': get_google_calendar_service,
        'CRMService': CRMService,
        'get_crm_service': get_crm_service,
        'PayrollEngine': PayrollEngine,
        'PayrollDeduction': PayrollDeduction,
        'get_payroll_engine': get_payroll_engine,
        'InvoiceLineItem': InvoiceLineItem,
        'get_invoice_generator': get_invoice_generator,
        'JobScheduler': JobScheduler,
        'ScheduledJob': ScheduledJob,
        'JobStatus': JobStatus,
        'JobFrequency': JobFrequency,
        'get_scheduler': get_scheduler,
        'visa_status_check_job': visa_status_check_job,
        'payroll_cycle_job': payroll_cycle_job,
        'follow_up_reminder_job': follow_up_reminder_job,
        'sales_lead_nurturing_job': sales_lead_nurturing_job,
    }

# Lazy load on first access
_services_cache = None

def __getattr__(name):
    global _services_cache
    if _services_cache is None:
        _services_cache = _lazy_import_services()
    if name in _services_cache:
        return _services_cache[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Mock Connectors (kept for backward compatibility)
    "EmailConnector",
    "GmailConnector",
    "MessagingConnector",
    "WhatsAppConnector",
    "CalendarConnector",
    "GoogleCalendarConnector",
    "PayrollConnector",
    "PayrollProcessor",
    "InvoiceConnector",
    "InvoiceGenerator",
    "CRMConnector",
    "HubSpotConnector",
    "VisaMonitoringConnector",
    "VisaMonitor",
    "ServiceConnectorFactory",
    "ServiceProvider",
    # Orchestration
    "AgentOrchestrationService",
    "OrchestrationContext",
    "ExecutionStrategy",
    "RetryPolicy",
    # N8N
    "N8NWebhookHandler",
    "N8NWebhookResponse",
    "N8NWorkflowInput",
    "N8NWebhookDefinition",
    "N8NWorkflowRegistry",
    # Real Services (production implementations)
    "EmailService",
    "get_email_service",
    "WhatsAppService",
    "get_whatsapp_service",
    "GoogleCalendarService",
    "get_google_calendar_service",
    "CRMService",
    "get_crm_service",
    "PayrollEngine",
    "PayrollDeduction",
    "get_payroll_engine",
    "InvoiceLineItem",
    "get_invoice_generator",
    # Scheduler
    "JobScheduler",
    "ScheduledJob",
    "JobStatus",
    "JobFrequency",
    "get_scheduler",
    "visa_status_check_job",
    "payroll_cycle_job",
    "follow_up_reminder_job",
    "sales_lead_nurturing_job",
]
