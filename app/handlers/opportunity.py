import time
import logging
from datetime import datetime, timezone
from app.database import Database
from app.ghl_client import GHLClient
from app.scheduler import Scheduler
from app import messages

logger = logging.getLogger(__name__)


def handle_opportunity_webhook(
    payload: dict,
    db: Database,
    ghl: GHLClient,
    scheduler: Scheduler,
    lead_in_stage_id: str,
    contacted_stage_id: str,
    initial_delay_seconds: int = 300,
) -> None:
    stage_id = payload.get("pipelineStageId", "")
    if stage_id != lead_in_stage_id:
        return

    opportunity_id = payload.get("id", "")
    contact = payload.get("contact", {})
    contact_id = payload.get("contactId", "")
    first_name = contact.get("firstName", "there")
    last_name = contact.get("lastName", "")
    phone = contact.get("phone", "")
    email = contact.get("email", "")

    lead = db.create_lead_if_not_exists(
        lead_id=opportunity_id,
        contact_id=contact_id,
        first_name=first_name,
        phone=phone,
        email=email,
    )
    if lead is None:
        logger.info("Duplicate webhook for opportunity %s — skipping", opportunity_id)
        return

    if initial_delay_seconds > 0:
        time.sleep(initial_delay_seconds)

    try:
        ghl.send_sms(contact_id=contact_id, message=messages.initial_sms(first_name))
        ghl.send_email(
            contact_id=contact_id,
            to_email=email,
            subject=messages.initial_email_subject(),
            html=messages.initial_email_html(first_name),
        )
        ghl.update_opportunity_stage(opportunity_id=opportunity_id, stage_id=contacted_stage_id)
        db.update_lead(
            lead_id=opportunity_id,
            last_contact=datetime.now(timezone.utc),
        )
        scheduler.schedule_followups(
            lead_id=opportunity_id,
            fn=send_followup,
            fn_kwargs={
                "lead_id": opportunity_id,
                "contact_id": contact_id,
                "first_name": first_name,
                "email": email,
            },
        )
        logger.info("Initial outreach sent to %s %s (opp: %s)", first_name, last_name, opportunity_id)
    except Exception as exc:
        logger.error("Failed initial outreach for opportunity %s: %s", opportunity_id, exc)
        raise


def send_followup(
    lead_id: str,
    contact_id: str,
    first_name: str,
    email: str,
    followup_stage: int,
) -> None:
    from app.deps import db, ghl  # imported here to avoid pickle issues with APScheduler

    lead = db.get_lead(lead_id)
    if lead is None or lead.status != "active":
        logger.info("Lead %s is not active — skipping follow-up stage %d", lead_id, followup_stage)
        return

    sms = messages.followup_sms(first_name, stage=followup_stage)
    ghl.send_sms(contact_id=contact_id, message=sms)
    ghl.send_email(
        contact_id=contact_id,
        to_email=email,
        subject=messages.initial_email_subject(),
        html=messages.followup_email_html(first_name, stage=followup_stage),
    )
    db.update_lead(
        lead_id=lead_id,
        stage=followup_stage,
        last_contact=datetime.now(timezone.utc),
    )

    if followup_stage == 4:
        db.update_lead(lead_id=lead_id, status="unresponsive")
        logger.info("Lead %s marked unresponsive after final follow-up", lead_id)
