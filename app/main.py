import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from app.config import settings
from app.deps import db, ghl, claude, scheduler
from app.handlers.opportunity import handle_opportunity_webhook
from app.handlers.message import handle_inbound_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        scheduler.start()
    except Exception:
        pass  # Already started (e.g. in tests)
    logger.info("Louie is live")
    yield
    try:
        scheduler.shutdown()
    except Exception:
        pass


app = FastAPI(title="Louie — Be You Louder Lead Assistant", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhook/opportunity")
async def opportunity_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    background_tasks.add_task(
        handle_opportunity_webhook,
        payload=payload,
        db=db,
        ghl=ghl,
        scheduler=scheduler,
        lead_in_stage_id=settings.ghl_stage_lead_in,
        contacted_stage_id=settings.ghl_stage_contacted,
        initial_delay_seconds=300,
    )
    return {"received": True}


@app.post("/webhook/message")
async def message_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    background_tasks.add_task(
        handle_inbound_message,
        payload=payload,
        db=db,
        ghl=ghl,
        claude=claude,
        scheduler=scheduler,
        stage_coaching=settings.ghl_stage_qualified_coaching,
        stage_community=settings.ghl_stage_qualified_community,
        calendly_link=settings.calendly_link,
        community_link=settings.community_link,
    )
    return {"received": True}
