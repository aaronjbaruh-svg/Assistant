import pytest
from unittest.mock import MagicMock
from app.handlers.message import handle_inbound_message
from app.database import Database
from app.claude_client import ClassificationResult


@pytest.fixture
def db():
    database = Database("sqlite:///:memory:")
    database.create_tables()
    database.create_lead(
        lead_id="opp_001",
        contact_id="con_001",
        first_name="Jane",
        phone="+15105551234",
        email="jane@example.com",
    )
    return database


@pytest.fixture
def mock_ghl():
    ghl = MagicMock()
    ghl.get_recent_messages.return_value = [
        {"direction": "outbound", "body": "Hey Jane!"},
        {"direction": "inbound", "body": "I want 1-on-1 coaching"},
    ]
    return ghl


@pytest.fixture
def mock_claude():
    claude = MagicMock()
    claude.classify_reply.return_value = ClassificationResult(
        path="A", reply="Awesome! Here's Aaron's calendar..."
    )
    return claude


VALID_PAYLOAD = {
    "type": "InboundMessage",
    "contactId": "con_001",
    "messageType": "SMS",
    "message": "I want 1-on-1 coaching",
    "contact": {"firstName": "Jane", "lastName": "Doe"},
}


def test_sends_reply_on_inbound_message(db, mock_ghl, mock_claude):
    handle_inbound_message(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        claude=mock_claude,
        scheduler=MagicMock(),
        stage_coaching="stage_coaching",
        stage_community="stage_community",
        calendly_link="https://calendly.com/test",
        community_link="https://community.example.com",
    )
    mock_ghl.send_sms.assert_called_once()


def test_notifies_aaron_on_any_reply(db, mock_ghl, mock_claude):
    handle_inbound_message(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        claude=mock_claude,
        scheduler=MagicMock(),
        stage_coaching="stage_coaching",
        stage_community="stage_community",
        calendly_link="https://calendly.com/test",
        community_link="https://community.example.com",
    )
    mock_ghl.notify_aaron.assert_called_once()


def test_cancels_followups_on_reply(db, mock_ghl, mock_claude):
    mock_scheduler = MagicMock()
    handle_inbound_message(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        claude=mock_claude,
        scheduler=mock_scheduler,
        stage_coaching="stage_coaching",
        stage_community="stage_community",
        calendly_link="https://calendly.com/test",
        community_link="https://community.example.com",
    )
    mock_scheduler.cancel_followups.assert_called_once_with("opp_001")


def test_updates_stage_to_coaching_on_path_a(db, mock_ghl, mock_claude):
    handle_inbound_message(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        claude=mock_claude,
        scheduler=MagicMock(),
        stage_coaching="stage_coaching",
        stage_community="stage_community",
        calendly_link="https://calendly.com/test",
        community_link="https://community.example.com",
    )
    mock_ghl.update_opportunity_stage.assert_called_once_with(
        opportunity_id="opp_001", stage_id="stage_coaching"
    )


def test_reactivates_unresponsive_lead(db, mock_ghl, mock_claude):
    db.update_lead(lead_id="opp_001", status="unresponsive")
    handle_inbound_message(
        payload=VALID_PAYLOAD,
        db=db,
        ghl=mock_ghl,
        claude=mock_claude,
        scheduler=MagicMock(),
        stage_coaching="stage_coaching",
        stage_community="stage_community",
        calendly_link="https://calendly.com/test",
        community_link="https://community.example.com",
    )
    lead = db.get_lead("opp_001")
    assert lead.status == "active"
    mock_ghl.notify_aaron.assert_called()


def test_ignores_unknown_contact(db, mock_ghl, mock_claude):
    payload = {**VALID_PAYLOAD, "contactId": "unknown_contact"}
    handle_inbound_message(
        payload=payload,
        db=db,
        ghl=mock_ghl,
        claude=mock_claude,
        scheduler=MagicMock(),
        stage_coaching="stage_coaching",
        stage_community="stage_community",
        calendly_link="https://calendly.com/test",
        community_link="https://community.example.com",
    )
    mock_ghl.send_sms.assert_not_called()
