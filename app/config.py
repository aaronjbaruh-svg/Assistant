from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ghl_api_key: str
    ghl_location_id: str = "r1QR18t7lUyHGd1AOsZ0"
    ghl_pipeline_id: str
    ghl_stage_lead_in: str
    ghl_stage_contacted: str
    ghl_stage_qualified_coaching: str
    ghl_stage_qualified_community: str
    ghl_stage_unresponsive: str
    ghl_aaron_contact_id: str
    ghl_from_email: str = "aaron@beyoulouder.com"
    anthropic_api_key: str
    aaron_phone: str = "+19255251091"
    calendly_link: str = "https://calendly.com/aaron-youlouder/conversation-w-aaron-youlouder"
    community_link: str
    database_url: str = "sqlite:///./louie.db"
    jobs_database_url: str = "sqlite:///./jobs.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
