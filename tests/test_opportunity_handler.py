import pytest
from unittest.mock import MagicMock, patch
from app.handlers.opportunity import handle_opportunity_webhook
from app.database import Database


@pytest.fixture
def db():
    database = Database("sqlite:///:memory:")
    database.create_tables()
    return database


@pytest.fixture
def mock_ghl():
    ghl = MagicMock()
    ghl.get_recent_messages.return_value = [{"direction": "outbound", "body": "Confirmation sent"}]
    return ghl


@pytest.fixture
def mock_scheduler():
    return MagicMock()


LEAD_IN_STAGE_ID = "stage_lead_in"

VALID_PAYLOAD = {
    "type": "OpportunityStageUpdate",
    "id": "opp_001",
    "contactId": "con_001",
    "pipelineStageId": "stage_lead_in",
    "contact": {
        "firstName": "Jane",
        "lastName": "Doe",
        "phone": "+15105551234",
        "email": "jane@example.com",
    },
}


def test_ignores_non_lead_in_stage(db, mock_ghl, mock_scheduler):
    payload = {**VALID_PAYLOAD, "pipelineStageId": "stage_other"}
    handle_opportunity_webhook(
        payload=payload,
        db=db,
        ghl=mock_ghl,
        scheduler=mock_scheduler,
        lead_in_stage_id=LEAD_IN_STAGE_ID,
        contacted_stage_id="stage_contacted",
        initial_delay_seconds=0,
    )
    mock_ghl.send_sms.assert_not_called()


def test_creates_lead_and_sends_initial_message(db, mock_ghl, mock_scheduler):
    handle_opportunity_webhook(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        scheduler=mock_scheduler,
        lead_in_stage_id=LEAD_IN_STAGE_ID,
        contacted_stage_id="stage_contacted",
        initial_delay_seconds=0,
    )
    mock_ghl.send_sms.assert_called_once()
    mock_ghl.send_email.assert_called_once()
    lead = db.get_lead("opp_001")
    assert lead is not None
    assert lead.status == "active"


def test_duplicate_webhook_ignored(db, mock_ghl, mock_scheduler):
    for _ in range(2):
        handle_opportunity_webhook(
            payload=VALID_PAYLOAD,
            db=db,
            ghl=mock_ghl,
            scheduler=mock_scheduler,
            lead_in_stage_id=LEAD_IN_STAGE_ID,
            contacted_stage_id="stage_contacted",
            initial_delay_seconds=0,
        )
    assert mock_ghl.send_sms.call_count == 1


def test_schedules_four_followup_jobs(db, mock_ghl, mock_scheduler):
    handle_opportunity_webhook(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        scheduler=mock_scheduler,
        lead_in_stage_id=LEAD_IN_STAGE_ID,
        contacted_stage_id="stage_contacted",
        initial_delay_seconds=0,
    )
    mock_scheduler.schedule_followups.assert_called_once()
