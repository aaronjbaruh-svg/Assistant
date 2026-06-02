import pytest
from datetime import datetime, timezone
from app.database import Database, Lead


@pytest.fixture
def db():
    database = Database("sqlite:///:memory:")
    database.create_tables()
    yield database
    database.close()


def test_create_lead(db):
    lead = db.create_lead(
        lead_id="opp_001",
        contact_id="con_001",
        first_name="Jane",
        phone="+15105551234",
        email="jane@example.com",
    )
    assert lead.lead_id == "opp_001"
    assert lead.status == "active"
    assert lead.stage == 0


def test_get_lead(db):
    db.create_lead("opp_002", "con_002", "Bob", "+15105559999", "bob@example.com")
    lead = db.get_lead("opp_002")
    assert lead is not None
    assert lead.first_name == "Bob"


def test_get_lead_by_contact_id(db):
    db.create_lead("opp_003", "con_003", "Sue", "+15105558888", "sue@example.com")
    lead = db.get_lead_by_contact_id("con_003")
    assert lead is not None
    assert lead.lead_id == "opp_003"


def test_update_lead_stage(db):
    db.create_lead("opp_004", "con_004", "Tim", "+15105557777", "tim@example.com")
    db.update_lead(lead_id="opp_004", stage=2, status="active")
    lead = db.get_lead("opp_004")
    assert lead.stage == 2


def test_update_lead_status(db):
    db.create_lead("opp_005", "con_005", "Ana", "+15105556666", "ana@example.com")
    db.update_lead(lead_id="opp_005", status="unresponsive")
    lead = db.get_lead("opp_005")
    assert lead.status == "unresponsive"


def test_duplicate_lead_ignored(db):
    db.create_lead("opp_006", "con_006", "Lee", "+15105555555", "lee@example.com")
    result = db.create_lead_if_not_exists("opp_006", "con_006", "Lee", "+15105555555", "lee@example.com")
    assert result is None  # already exists, not created again
