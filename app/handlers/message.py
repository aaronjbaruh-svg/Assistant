import logging
from datetime import datetime, timezone
from app.database import Database
from app.ghl_client import GHLClient
from app.claude_client import ClaudeClient
from app.scheduler import Scheduler
from app import messages

logger = logging.getLogger(__name__)


def handle_inbound_message(
    payload: dict,
    db: Database,
    ghl: GHLClient,
    claude: ClaudeClient,
    scheduler: Scheduler,
    stage_coaching: str,
    stage_community: str,
    calendly_link: str,
    community_link: str,
) -> None:
    contact_id = payload.get("contactId", "")
    contact = payload.get("contact", {})
    first_name = contact.get("firstName", "there")
    last_name = contact.get("lastName", "")

    lead = db.get_lead_by_contact_id(contact_id)
    if lead is None:
        logger.info("Inbound message from unknown contact %s — ignoring", contact_id)
        return

    was_unresponsive = lead.status == "unresponsive"
    if was_unresponsive:
        db.update_lead(lead_id=lead.lead_id, status="active")
        ghl.notify_aaron(
            f"Re-engaged! {first_name} {last_name} replied after being marked unresponsive. Check GHL."
        )
        logger.info("Lead %s reactivated after unresponsive reply", lead.lead_id)

    scheduler.cancel_followups(lead.lead_id)

    conversation = ghl.get_recent_messages(contact_id=contact_id)
    result = claude.classify_reply(conversation=conversation, first_name=first_name)

    if result.path == "A":
        reply = messages.path_a_sms(calendly_link)
        ghl.update_opportunity_stage(opportunity_id=lead.lead_id, stage_id=stage_coaching)
        if not was_unresponsive:
            db.update_lead(lead_id=lead.lead_id, status="booked")
        notification = messages.aaron_notification_sms(first_name, last_name, path="A")
    elif result.path == "B":
        reply = messages.path_b_sms(community_link)
        ghl.update_opportunity_stage(opportunity_id=lead.lead_id, stage_id=stage_community)
        if not was_unresponsive:
            db.update_lead(lead_id=lead.lead_id, status="enrolled")
        notification = messages.aaron_notification_sms(first_name, last_name, path="B")
    else:
        reply = result.reply or messages.path_c_sms()
        notification = messages.aaron_notification_sms(first_name, last_name, path="C")

    ghl.send_sms(contact_id=contact_id, message=reply)
    ghl.notify_aaron(notification)
    db.update_lead(lead_id=lead.lead_id, last_contact=datetime.now(timezone.utc))
    logger.info("Handled inbound reply from %s — routed to Path %s", first_name, result.path)
