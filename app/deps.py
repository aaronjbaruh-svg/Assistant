from app.config import settings
from app.database import Database
from app.ghl_client import GHLClient
from app.claude_client import ClaudeClient
from app.scheduler import Scheduler

db = Database(settings.database_url)
db.create_tables()

ghl = GHLClient(
    api_key=settings.ghl_api_key,
    location_id=settings.ghl_location_id,
    from_email=settings.ghl_from_email,
    aaron_contact_id=settings.ghl_aaron_contact_id,
)

claude = ClaudeClient(
    api_key=settings.anthropic_api_key,
    community_link=settings.community_link,
)

scheduler = Scheduler(jobs_db_url=settings.jobs_database_url)
