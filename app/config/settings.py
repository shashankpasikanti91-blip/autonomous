"""
Configuration management for the HR platform.

Handles all configuration from environment variables including:
- API settings
- Database configuration
- Service provider credentials (Email, Calendar, CRM, etc.)
- N8N integration
- AI Model settings
- Memory configuration
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic import ConfigDict

# Lazy import to avoid circular dependencies
logger = None

def get_logger_instance():
    global logger
    if logger is None:
        from utils.logger import get_logger
        logger = get_logger(__name__)
    return logger



class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================================================================
    # Environment & API
    # ============================================================================
    
    env: str = Field(default="development", validation_alias="ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    api_reload: bool = Field(default=True, validation_alias="API_RELOAD")
    base_url: str = Field(default="http://localhost:8000", validation_alias="BASE_URL")
    api_key_required: bool = Field(default=False, validation_alias="API_KEY_REQUIRED")
    
    # ============================================================================
    # PostgreSQL — Primary Database (local development)
    # ============================================================================

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/hr_multitenant",
        validation_alias="DATABASE_URL",
    )
    # Set DATABASE_ECHO=true to print all SQL statements (debug only)
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")

    # ============================================================================
    # Firebase & Database (legacy — kept for backward compat)
    # ============================================================================
    
    firebase_project_id: str = Field(default="", validation_alias="FIREBASE_PROJECT_ID")
    firebase_private_key_id: str = Field(default="", validation_alias="FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: str = Field(default="", validation_alias="FIREBASE_PRIVATE_KEY")
    firebase_client_email: str = Field(default="", validation_alias="FIREBASE_CLIENT_EMAIL")
    firebase_client_id: str = Field(default="", validation_alias="FIREBASE_CLIENT_ID")
    firebase_auth_uri: str = Field(
        default="https://accounts.google.com/o/oauth2/auth",
        validation_alias="FIREBASE_AUTH_URI"
    )
    firebase_token_uri: str = Field(
        default="https://oauth2.googleapis.com/token",
        validation_alias="FIREBASE_TOKEN_URI"
    )
    firebase_auth_provider_x509_cert_url: str = Field(
        default="https://www.googleapis.com/oauth2/v1/certs",
        validation_alias="FIREBASE_AUTH_PROVIDER_X509_CERT_URL"
    )
    firebase_client_x509_cert_url: str = Field(
        default="",
        validation_alias="FIREBASE_CLIENT_X509_CERT_URL"
    )
    firestore_prefix: str = Field(default="platform_", validation_alias="FIRESTORE_PREFIX")
    realtime_enabled: bool = Field(default=True, validation_alias="REALTIME_ENABLED")
    
    # ============================================================================
    # Email Service
    # ============================================================================
    
    email_provider: str = Field(default="smtp", validation_alias="EMAIL_PROVIDER")
    
    # SMTP Configuration
    smtp_host: str = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_username: str = Field(default="", validation_alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_from_address: str = Field(default="noreply@company.com", validation_alias="SMTP_FROM_ADDRESS")
    
    # Gmail API Configuration
    gmail_service_account_key: str = Field(default="", validation_alias="GMAIL_SERVICE_ACCOUNT_KEY")
    gmail_from_address: str = Field(default="", validation_alias="GMAIL_FROM_ADDRESS")
    gmail_oauth_client_id: str = Field(default="", validation_alias="GMAIL_OAUTH_CLIENT_ID")
    gmail_oauth_client_secret: str = Field(default="", validation_alias="GMAIL_OAUTH_CLIENT_SECRET")
    
    # SendGrid Configuration
    sendgrid_api_key: str = Field(default="", validation_alias="SENDGRID_API_KEY")
    sendgrid_from_address: str = Field(default="", validation_alias="SENDGRID_FROM_ADDRESS")
    
    # ============================================================================
    # Messaging Service
    # ============================================================================
    
    whatsapp_api_token: str = Field(default="", validation_alias="WHATSAPP_API_TOKEN")
    whatsapp_business_account_id: str = Field(default="", validation_alias="WHATSAPP_BUSINESS_ACCOUNT_ID")
    twilio_account_sid: str = Field(default="", validation_alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", validation_alias="TWILIO_AUTH_TOKEN")
    
    # ============================================================================
    # Calendar Service
    # ============================================================================
    
    calendar_provider: str = Field(default="google", validation_alias="CALENDAR_PROVIDER")
    google_calendar_key: str = Field(default="", validation_alias="GOOGLE_CALENDAR_KEY")
    calendar_client_id: str = Field(default="", validation_alias="CALENDAR_CLIENT_ID")
    calendar_client_secret: str = Field(default="", validation_alias="CALENDAR_CLIENT_SECRET")
    
    # ============================================================================
    # Payroll Configuration
    # ============================================================================
    
    payroll_tax_rate: float = Field(default=0.15, validation_alias="PAYROLL_TAX_RATE")
    health_insurance_deduction: float = Field(default=200.0, validation_alias="HEALTH_INSURANCE")
    pension_rate: float = Field(default=0.05, validation_alias="PENSION_RATE")
    
    # ============================================================================
    # Invoice Configuration
    # ============================================================================
    
    business_name: str = Field(default="Your Company", validation_alias="BUSINESS_NAME")
    tax_id: str = Field(default="", validation_alias="TAX_ID")
    invoice_prefix: str = Field(default="INV", validation_alias="INVOICE_PREFIX")
    payment_terms_days: int = Field(default=30, validation_alias="PAYMENT_TERMS_DAYS")
    
    # ============================================================================
    # CRM Configuration
    # ============================================================================
    
    crm_provider: str = Field(default="hubspot", validation_alias="CRM_PROVIDER")
    # HubSpot OAuth
    hubspot_api_key: str = Field(default="", validation_alias="HUBSPOT_API_KEY")
    hubspot_oauth_client_id: str = Field(default="", validation_alias="HUBSPOT_OAUTH_CLIENT_ID")
    hubspot_oauth_client_secret: str = Field(default="", validation_alias="HUBSPOT_OAUTH_CLIENT_SECRET")
    # Generic CRM fields
    crm_api_key: str = Field(default="", validation_alias="CRM_API_KEY")
    crm_client_id: str = Field(default="", validation_alias="CRM_CLIENT_ID")
    crm_client_secret: str = Field(default="", validation_alias="CRM_CLIENT_SECRET")
    
    # ============================================================================
    # N8N Integration
    # ============================================================================
    
    n8n_url: str = Field(default="http://localhost:5678", validation_alias="N8N_URL")
    n8n_api_key: str = Field(default="", validation_alias="N8N_API_KEY")
    n8n_webhook_url: str = Field(default="http://localhost:5678/webhook", validation_alias="N8N_WEBHOOK_URL")
    webhook_secret_key: str = Field(default="", validation_alias="WEBHOOK_SECRET_KEY")
    
    # ============================================================================
    # AI Model & Reasoning
    # ============================================================================
    
    pydantic_ai_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        validation_alias="PYDANTIC_AI_MODEL"
    )
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    
    # ============================================================================
    # Memory Configuration
    # ============================================================================
    
    use_vector_memory: bool = Field(default=True, validation_alias="USE_VECTOR_MEMORY")
    use_firestore_memory: bool = Field(default=True, validation_alias="USE_FIRESTORE_MEMORY")
    vector_db_dimension: int = Field(default=1536, validation_alias="VECTOR_DB_DIMENSION")
    
    # ============================================================================
    # Application Settings
    # ============================================================================
    
    max_workers: int = Field(default=10, validation_alias="MAX_WORKERS")
    request_timeout_seconds: int = Field(default=30, validation_alias="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, validation_alias="MAX_RETRIES")
    retry_delay_ms: int = Field(default=100, validation_alias="RETRY_DELAY_MS")

    # ============================================================================
    # CORS & Security
    # ============================================================================
    # Comma-separated list of allowed origins. For production add your domains:
    # e.g. https://hr.yourdomain.com,https://*.hr.yourdomain.com
    allowed_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        validation_alias="ALLOWED_ORIGINS",
    )
    trust_proxy_headers: bool = Field(default=True, validation_alias="TRUST_PROXY_HEADERS")
    secret_key: str = Field(
        default="change-me-in-production-use-a-long-random-string",
        validation_alias="SECRET_KEY",
    )

    # ============================================================================
    # Platform Identity
    # ============================================================================
    platform_name: str = Field(default="HR Autonomous OS", validation_alias="PLATFORM_NAME")
    platform_domain: str = Field(
        default="hr.local", validation_alias="PLATFORM_DOMAIN"
    )

    @property
    def allowed_origins(self) -> List[str]:
        """Return list of allowed CORS origins from comma-separated env value."""
        return [o.strip() for o in self.allowed_origins_str.split(",") if o.strip()]

    model_config = ConfigDict(env_file=".env", case_sensitive=False, populate_by_name=True)


# Global settings instance
settings = Settings()

get_logger_instance().info(f"Settings initialized for environment: {settings.env}")
