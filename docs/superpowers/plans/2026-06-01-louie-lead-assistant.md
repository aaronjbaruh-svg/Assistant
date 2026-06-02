# Louie Lead Assistant — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Louie, a FastAPI service that receives GoHighLevel webhooks, uses Claude AI to qualify "Lead In" leads via SMS + email, routes them to three paths (coaching, community, unclear), and notifies Aaron on live replies.

**Architecture:** A Python/FastAPI web server receives two GHL webhooks — one for new opportunities entering "Lead In" stage, one for inbound messages. SQLite tracks lead state and APScheduler drives the Day 1/2/4/7 follow-up cadence. Claude AI classifies each reply and generates Louie's response. All outbound messages are sent via the GHL API.

**Tech Stack:** Python 3.11, FastAPI, Anthropic SDK (`claude-sonnet-4-6`), GHL REST API v2, APScheduler 3.x + SQLAlchemy job store, SQLite, httpx, Railway (hosting)

---

## File Map

| File | Responsibility |
|------|---------------|
| `app/config.py` | Pydantic-settings config — all env vars in one place |
| `app/database.py` | SQLite schema + CRUD for the `leads` table |
| `app/messages.py` | All message copy — initial, follow-ups, paths A/B/C — easy for Aaron to edit |
| `app/ghl_client.py` | GHL API wrapper: send_sms, send_email, get_messages, update_stage, notify_aaron |
| `app/claude_client.py` | Claude API wrapper: classify_reply → `{path, reply}` |
| `app/scheduler.py` | APScheduler init, schedule_followups, cancel_followups |
| `app/deps.py` | Module-level singletons (db, ghl, claude, scheduler) — imported by handlers and main |
| `app/handlers/opportunity.py` | `on_new_lead_in(payload)` — 5-min delay, send initial message |
| `app/handlers/message.py` | `on_inbound_message(payload)` — classify reply, route, notify |
| `app/main.py` | FastAPI app, webhook routes, lifespan (scheduler start/stop) |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/test_database.py` | Database CRUD tests |
| `tests/test_ghl_client.py` | GHL client tests (mocked HTTP) |
| `tests/test_claude_client.py` | Claude client tests (mocked Anthropic SDK) |
| `tests/test_opportunity_handler.py` | Opportunity handler tests |
| `tests/test_message_handler.py` | Message handler tests |
| `requirements.txt` | Pinned dependencies |
| `.env.example` | Documented env var template |
| `Procfile` | Railway process definition |
| `railway.toml` | Railway deployment config |

---

## Task 1: Project Skeleton + Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `app/__init__.py`
- Create: `app/handlers/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
anthropic==0.28.0
httpx==0.27.0
apscheduler==3.10.4
pydantic-settings==2.3.0
sqlalchemy==2.0.30
pytest==8.2.2
pytest-asyncio==0.23.7
pytest-mock==3.14.0
```

- [ ] **Step 2: Create .env.example**

```
# GoHighLevel
GHL_API_KEY=your_location_api_key_here
GHL_LOCATION_ID=r1QR18t7lUyHGd1AOsZ0
GHL_PIPELINE_ID=your_pipeline_id_here
GHL_STAGE_LEAD_IN=your_lead_in_stage_id_here
GHL_STAGE_CONTACTED=your_contacted_stage_id_here
GHL_STAGE_QUALIFIED_COACHING=your_qualified_coaching_stage_id_here
GHL_STAGE_QUALIFIED_COMMUNITY=your_qualified_community_stage_id_here
GHL_STAGE_UNRESPONSIVE=your_unresponsive_stage_id_here
GHL_AARON_CONTACT_ID=aaron_contact_id_in_ghl_here
GHL_FROM_EMAIL=aaron@beyoulouder.com

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# App
AARON_PHONE=+19255251091
COMMUNITY_LINK=https://PLACEHOLDER_COMMUNITY_LINK_TBD
DATABASE_URL=sqlite:///./louie.db
JOBS_DATABASE_URL=sqlite:///./jobs.db
```

- [ ] **Step 3: Add .env to .gitignore**

Append to `.gitignore`:
```
.env
louie.db
jobs.db
```

- [ ] **Step 4: Create empty init files and conftest**

Create `app/__init__.py` — empty file.
Create `app/handlers/__init__.py` — empty file.
Create `tests/__init__.py` — empty file.

Create `tests/conftest.py`:
```python
import pytest
import os

os.environ.setdefault("GHL_API_KEY", "test_ghl_key")
os.environ.setdefault("GHL_LOCATION_ID", "test_location")
os.environ.setdefault("GHL_PIPELINE_ID", "test_pipeline")
os.environ.setdefault("GHL_STAGE_LEAD_IN", "stage_lead_in")
os.environ.setdefault("GHL_STAGE_CONTACTED", "stage_contacted")
os.environ.setdefault("GHL_STAGE_QUALIFIED_COACHING", "stage_coaching")
os.environ.setdefault("GHL_STAGE_QUALIFIED_COMMUNITY", "stage_community")
os.environ.setdefault("GHL_STAGE_UNRESPONSIVE", "stage_unresponsive")
os.environ.setdefault("GHL_AARON_CONTACT_ID", "aaron_contact_123")
os.environ.setdefault("GHL_FROM_EMAIL", "aaron@beyoulouder.com")
os.environ.setdefault("ANTHROPIC_API_KEY", "test_anthropic_key")
os.environ.setdefault("AARON_PHONE", "+19255251091")
os.environ.setdefault("COMMUNITY_LINK", "https://community.example.com")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_louie.db")
os.environ.setdefault("JOBS_DATABASE_URL", "sqlite:///./test_jobs.db")
```

- [ ] **Step 5: Install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install without error.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore app/__init__.py app/handlers/__init__.py tests/__init__.py tests/conftest.py
git commit -m "feat: project skeleton and dependencies"
```

---

## Task 2: Config Module

**Files:**
- Create: `app/config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_config.py`:
```python
from app.config import settings

def test_settings_loads_from_env():
    assert settings.ghl_api_key == "test_ghl_key"
    assert settings.ghl_location_id == "test_location"
    assert settings.aaron_phone == "+19255251091"
    assert settings.calendly_link == "https://calendly.com/aaron-youlouder/conversation-w-aaron-youlouder"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 3: Implement config.py**

Create `app/config.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: config module with pydantic-settings"
```

---

## Task 3: Database Module

**Files:**
- Create: `app/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_database.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_database.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.database'`

- [ ] **Step 3: Implement database.py**

Create `app/database.py`:
```python
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    lead_id = Column(String, primary_key=True)
    contact_id = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    stage = Column(Integer, default=0)        # 0=initial sent, 1-4=follow-up index
    status = Column(String, default="active") # active | booked | enrolled | unresponsive
    last_contact = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def close(self):
        self.engine.dispose()

    def _session(self) -> Session:
        return self.SessionLocal()

    def create_lead(
        self,
        lead_id: str,
        contact_id: str,
        first_name: str,
        phone: str,
        email: str,
    ) -> Lead:
        with self._session() as session:
            lead = Lead(
                lead_id=lead_id,
                contact_id=contact_id,
                first_name=first_name,
                phone=phone,
                email=email,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            return lead

    def create_lead_if_not_exists(
        self,
        lead_id: str,
        contact_id: str,
        first_name: str,
        phone: str,
        email: str,
    ) -> Optional[Lead]:
        with self._session() as session:
            existing = session.get(Lead, lead_id)
            if existing:
                return None
            lead = Lead(
                lead_id=lead_id,
                contact_id=contact_id,
                first_name=first_name,
                phone=phone,
                email=email,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            return lead

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        with self._session() as session:
            return session.get(Lead, lead_id)

    def get_lead_by_contact_id(self, contact_id: str) -> Optional[Lead]:
        with self._session() as session:
            return session.query(Lead).filter(Lead.contact_id == contact_id).first()

    def update_lead(self, lead_id: str, **kwargs) -> None:
        with self._session() as session:
            lead = session.get(Lead, lead_id)
            if lead:
                for key, value in kwargs.items():
                    setattr(lead, key, value)
                session.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_database.py -v
```

Expected: All 6 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/database.py tests/test_database.py
git commit -m "feat: database module with SQLite lead tracking"
```

---

## Task 4: Message Templates

**Files:**
- Create: `app/messages.py`
- Create: `tests/test_messages.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_messages.py`:
```python
from app.messages import (
    initial_sms,
    initial_email_subject,
    initial_email_html,
    followup_sms,
    followup_email_html,
    path_a_sms,
    path_b_sms,
    aaron_notification_sms,
)


def test_initial_sms_interpolates_name():
    msg = initial_sms("Jane")
    assert "Jane" in msg
    assert "Louie" in msg


def test_path_a_sms_contains_calendly():
    msg = path_a_sms("https://calendly.com/aaron-youlouder/conversation-w-aaron-youlouder")
    assert "calendly.com" in msg


def test_path_b_sms_contains_community_copy():
    msg = path_b_sms("https://community.example.com")
    assert "Be You Louder Community" in msg
    assert "community.example.com" in msg


def test_aaron_notification_coaching():
    msg = aaron_notification_sms("Jane", "Smith", path="A")
    assert "Jane" in msg
    assert "coaching" in msg.lower()


def test_aaron_notification_live_reply():
    msg = aaron_notification_sms("Bob", "Jones", path="C")
    assert "Bob" in msg
    assert "coaching" not in msg.lower()


def test_followup_sms_stage_1(  ):
    msg = followup_sms("Jane", stage=1)
    assert "Jane" in msg


def test_followup_sms_stage_4():
    msg = followup_sms("Jane", stage=4)
    assert "Jane" in msg
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_messages.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.messages'`

- [ ] **Step 3: Implement messages.py**

Create `app/messages.py`:

```python
# ─────────────────────────────────────────────────────────────────────────────
# All message copy lives here. Edit this file to update Louie's voice.
# Lines marked [COPY TBD] should be updated by Aaron before going live.
# ─────────────────────────────────────────────────────────────────────────────


def initial_sms(first_name: str) -> str:
    # [COPY TBD] — Aaron to finalize this opening message
    return (
        f"Hey {first_name}! I'm Louie from the Be You Louder team. "
        "We saw you connected with one of our ads and wanted to reach out personally. "
        "What are you most looking to work on with your public speaking?"
    )


def initial_email_subject() -> str:
    # [COPY TBD] — Aaron to finalize subject line
    return "Quick question from the Be You Louder team"


def initial_email_html(first_name: str) -> str:
    # [COPY TBD] — Aaron to finalize email body
    return f"""
<p>Hey {first_name}!</p>
<p>I'm Louie from the Be You Louder team. We saw you connected with one of our ads
and wanted to reach out personally.</p>
<p>What are you most looking to work on with your public speaking?</p>
<p>— Louie<br>Be You Louder Team</p>
"""


def followup_sms(first_name: str, stage: int) -> str:
    # [COPY TBD] — Aaron to finalize follow-up messages
    messages = {
        1: f"Hey {first_name}! Just wanted to make sure my last message came through. What's on your mind with public speaking?",
        2: f"Hey {first_name} — dropping a quick note. At Be You Louder we help people find their voice and own the room. Curious what brought you to our ad?",
        3: f"Hey {first_name}! Still here if you want to chat. No pressure at all — just want to point you in the right direction if I can.",
        4: f"Hey {first_name}, I don't want to keep bugging you — just wanted to leave the door open. If you ever want to explore what Be You Louder is about, I'm here.",
    }
    return messages.get(stage, f"Hey {first_name}, hope you're well!")


def followup_email_html(first_name: str, stage: int) -> str:
    body = followup_sms(first_name, stage)
    return f"<p>{body}</p><p>— Louie<br>Be You Louder Team</p>"


def path_a_sms(calendly_link: str) -> str:
    # [COPY TBD] — Aaron to finalize coaching path message
    return (
        "That's awesome — sounds like you're ready to really invest in yourself. "
        "The best next step is a quick conversation with Aaron, our head coach, "
        f"to see if 1-on-1 coaching is the right fit. Here's a link to grab a time: {calendly_link}"
    )


def path_a_email_html(calendly_link: str) -> str:
    return f"<p>{path_a_sms(calendly_link)}</p><p>— Louie<br>Be You Louder Team</p>"


def path_b_sms(community_link: str) -> str:
    return (
        "The most common entry point for people who are early on in their public speaking journey "
        "is to start with the Be You Louder Community. You'll get access to the curriculum & attend "
        "two webinars a month. The webinars are a safe place for people like you to learn, practice & grow. "
        f"From there, you might find that upping the reps are an appropriate next step. {community_link}"
    )


def path_b_email_html(community_link: str) -> str:
    return f"<p>{path_b_sms(community_link)}</p><p>— Louie<br>Be You Louder Team</p>"


def path_c_sms() -> str:
    # [COPY TBD] — Aaron to finalize clarifying question
    return (
        "Thanks for getting back to me! Just to make sure I point you in the right direction — "
        "are you looking for something more hands-on like 1-on-1 coaching, or are you more interested "
        "in resources you can work through at your own pace?"
    )


def aaron_notification_sms(first_name: str, last_name: str, path: str) -> str:
    if path == "A":
        return f"Live reply from {first_name} {last_name} — interested in hands-on coaching. Check GHL."
    return f"Live reply from {first_name} {last_name} — check GHL."
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_messages.py -v
```

Expected: All 7 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/messages.py tests/test_messages.py
git commit -m "feat: message templates module"
```

---

## Task 4b: Shared Dependencies Module

**Why this exists:** APScheduler with SQLAlchemy job store persists jobs to SQLite and calls them in a background thread. It cannot pickle complex objects like `Database` or `GHLClient`. Instead, `send_followup` (and other scheduled functions) must import singleton instances from a module-level `deps.py` rather than receiving them as arguments.

**Files:**
- Create: `app/deps.py`
- Create: `tests/test_deps.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_deps.py`:
```python
from app.deps import db, ghl, claude, scheduler
from app.database import Database
from app.ghl_client import GHLClient
from app.claude_client import ClaudeClient
from app.scheduler import Scheduler


def test_deps_are_correct_types():
    assert isinstance(db, Database)
    assert isinstance(ghl, GHLClient)
    assert isinstance(claude, ClaudeClient)
    assert isinstance(scheduler, Scheduler)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_deps.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.deps'`

- [ ] **Step 3: Implement deps.py**

Create `app/deps.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_deps.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/deps.py tests/test_deps.py
git commit -m "feat: shared dependency singletons module"
```

---

## Task 5: GHL API Client

**Files:**
- Create: `app/ghl_client.py`
- Create: `tests/test_ghl_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ghl_client.py`:
```python
import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from app.ghl_client import GHLClient


@pytest.fixture
def client():
    return GHLClient(
        api_key="test_key",
        location_id="test_loc",
        from_email="aaron@beyoulouder.com",
        aaron_contact_id="aaron_con_123",
    )


def test_send_sms_calls_correct_endpoint(client, respx_mock=None):
    with patch("app.ghl_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "msg_1"})
        result = client.send_sms(contact_id="con_001", message="Hello Jane!")
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "/conversations/messages" in call_kwargs[0][0]
        body = call_kwargs[1]["json"]
        assert body["type"] == "SMS"
        assert body["contactId"] == "con_001"
        assert body["message"] == "Hello Jane!"


def test_send_email_calls_correct_endpoint(client):
    with patch("app.ghl_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "msg_2"})
        client.send_email(
            contact_id="con_001",
            to_email="jane@example.com",
            subject="Hello",
            html="<p>Hi</p>",
        )
        call_kwargs = mock_post.call_args
        body = call_kwargs[1]["json"]
        assert body["type"] == "Email"
        assert body["subject"] == "Hello"


def test_update_opportunity_stage(client):
    with patch("app.ghl_client.httpx.put") as mock_put:
        mock_put.return_value = MagicMock(status_code=200, json=lambda: {})
        client.update_opportunity_stage(
            opportunity_id="opp_001",
            stage_id="stage_contacted",
        )
        call_kwargs = mock_put.call_args
        assert "opp_001" in call_kwargs[0][0]
        body = call_kwargs[1]["json"]
        assert body["pipelineStageId"] == "stage_contacted"


def test_get_recent_messages_returns_list(client):
    with patch("app.ghl_client.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "conversations": [{"id": "conv_001"}],
                "messages": {"messages": [{"body": "Hello", "direction": "inbound"}]},
            },
        )
        # First call: search conversations; second: get messages
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"conversations": [{"id": "conv_001"}]}),
            MagicMock(status_code=200, json=lambda: {"messages": {"messages": [{"body": "Hi", "direction": "inbound"}]}}),
        ]
        messages = client.get_recent_messages(contact_id="con_001")
        assert isinstance(messages, list)


def test_send_sms_retries_on_failure(client):
    with patch("app.ghl_client.httpx.post") as mock_post:
        mock_post.side_effect = [
            httpx.HTTPError("timeout"),
            httpx.HTTPError("timeout"),
            MagicMock(status_code=200, json=lambda: {"id": "msg_3"}),
        ]
        result = client.send_sms("con_001", "Hello")
        assert mock_post.call_count == 3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ghl_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.ghl_client'`

- [ ] **Step 3: Implement ghl_client.py**

Create `app/ghl_client.py`:
```python
import time
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

GHL_BASE = "https://services.leadconnectorhq.com"
GHL_HEADERS_BASE = {"Version": "2021-07-28", "Content-Type": "application/json"}


class GHLClient:
    def __init__(
        self,
        api_key: str,
        location_id: str,
        from_email: str,
        aaron_contact_id: str,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.location_id = location_id
        self.from_email = from_email
        self.aaron_contact_id = aaron_contact_id
        self.max_retries = max_retries

    def _headers(self) -> dict:
        return {**GHL_HEADERS_BASE, "Authorization": f"Bearer {self.api_key}"}

    def _post(self, path: str, body: dict) -> dict:
        url = f"{GHL_BASE}{path}"
        for attempt in range(self.max_retries):
            try:
                resp = httpx.post(url, headers=self._headers(), json=body, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning("GHL POST %s attempt %d failed: %s. Retrying in %ds", path, attempt + 1, exc, wait)
                time.sleep(wait)
        return {}

    def _put(self, path: str, body: dict) -> dict:
        url = f"{GHL_BASE}{path}"
        for attempt in range(self.max_retries):
            try:
                resp = httpx.put(url, headers=self._headers(), json=body, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning("GHL PUT %s attempt %d failed: %s. Retrying in %ds", path, attempt + 1, exc, wait)
                time.sleep(wait)
        return {}

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{GHL_BASE}{path}"
        resp = httpx.get(url, headers=self._headers(), params=params or {}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def send_sms(self, contact_id: str, message: str) -> dict:
        return self._post("/conversations/messages", {
            "type": "SMS",
            "contactId": contact_id,
            "message": message,
        })

    def send_email(self, contact_id: str, to_email: str, subject: str, html: str) -> dict:
        return self._post("/conversations/messages", {
            "type": "Email",
            "contactId": contact_id,
            "emailTo": to_email,
            "emailFrom": self.from_email,
            "subject": subject,
            "html": html,
        })

    def update_opportunity_stage(self, opportunity_id: str, stage_id: str) -> dict:
        return self._put(f"/opportunities/{opportunity_id}", {
            "pipelineStageId": stage_id,
        })

    def get_recent_messages(self, contact_id: str, limit: int = 20) -> list:
        search = self._get("/conversations/search", {
            "locationId": self.location_id,
            "contactId": contact_id,
        })
        conversations = search.get("conversations", [])
        if not conversations:
            return []
        conv_id = conversations[0]["id"]
        result = self._get(f"/conversations/{conv_id}/messages", {"limit": limit})
        return result.get("messages", {}).get("messages", [])

    def notify_aaron(self, message: str) -> None:
        try:
            self.send_sms(contact_id=self.aaron_contact_id, message=message)
        except Exception as exc:
            logger.error("Failed to notify Aaron: %s", exc)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ghl_client.py -v
```

Expected: All 5 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/ghl_client.py tests/test_ghl_client.py
git commit -m "feat: GoHighLevel API client with retry logic"
```

---

## Task 6: Claude Client

**Files:**
- Create: `app/claude_client.py`
- Create: `tests/test_claude_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_claude_client.py`:
```python
import pytest
import json
from unittest.mock import patch, MagicMock
from app.claude_client import ClaudeClient, ClassificationResult


@pytest.fixture
def client():
    return ClaudeClient(api_key="test_key", community_link="https://community.example.com")


def _mock_claude_response(path: str, reply: str):
    content = json.dumps({"path": path, "reply": reply})
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=content)]
    return mock_msg


def test_classify_coaching_reply(client):
    conversation = [{"direction": "inbound", "body": "I want 1-on-1 coaching please"}]
    with patch.object(client.anthropic.messages, "create", return_value=_mock_claude_response(
        "A", "Awesome! Here's the Calendly link..."
    )):
        result = client.classify_reply(conversation, first_name="Jane")
    assert result.path == "A"
    assert "Calendly" in result.reply or len(result.reply) > 0


def test_classify_community_reply(client):
    conversation = [{"direction": "inbound", "body": "I want to attend webinars and see the curriculum"}]
    with patch.object(client.anthropic.messages, "create", return_value=_mock_claude_response(
        "B", "The most common entry point..."
    )):
        result = client.classify_reply(conversation, first_name="Bob")
    assert result.path == "B"


def test_classify_unclear_reply(client):
    conversation = [{"direction": "inbound", "body": "Not sure what I need yet"}]
    with patch.object(client.anthropic.messages, "create", return_value=_mock_claude_response(
        "C", "Just to make sure I point you in the right direction..."
    )):
        result = client.classify_reply(conversation, first_name="Sue")
    assert result.path == "C"


def test_invalid_json_defaults_to_path_c(client):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="not valid json")]
    with patch.object(client.anthropic.messages, "create", return_value=mock_msg):
        result = client.classify_reply([{"direction": "inbound", "body": "..."}], first_name="Tim")
    assert result.path == "C"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.claude_client'`

- [ ] **Step 3: Implement claude_client.py**

Create `app/claude_client.py`:
```python
import json
import logging
from dataclasses import dataclass
from typing import Optional
import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Louie, a warm and conversational team member at Be You Louder — a public speaking coaching company. Your job is to qualify leads who came in from a Meta/Instagram ad and figure out the best next step for them.

You have three paths to route each lead:
- Path A: They want hands-on, 1-on-1 coaching with Aaron (the head coach)
- Path B: They want to learn at their own pace — curriculum, webinars, or community
- Path C: Their reply is unclear or ambiguous — ask ONE clarifying question before routing

Rules:
1. Always be warm, genuine, and conversational. Never robotic.
2. Never pretend to be Aaron. You are Louie from the team.
3. If routing to Path B, use this EXACT copy (replace {community_link}):
   "The most common entry point for people who are early on in their public speaking journey is to start with the Be You Louder Community. You'll get access to the curriculum & attend two webinars a month. The webinars are a safe place for people like you to learn, practice & grow. From there, you might find that upping the reps are an appropriate next step. {community_link}"
4. If routing to Path A, mention Aaron as "our head coach" and include the Calendly link.
5. Respond ONLY with valid JSON in this exact format: {{"path": "A" | "B" | "C", "reply": "your message here"}}
6. No markdown, no explanation outside the JSON object."""


@dataclass
class ClassificationResult:
    path: str   # "A", "B", or "C"
    reply: str  # the message to send to the lead


class ClaudeClient:
    def __init__(self, api_key: str, community_link: str):
        self.anthropic = anthropic.Anthropic(api_key=api_key)
        self.community_link = community_link

    def classify_reply(
        self,
        conversation: list[dict],
        first_name: str,
    ) -> ClassificationResult:
        thread = "\n".join(
            f"[{'LEAD' if m.get('direction') == 'inbound' else 'LOUIE'}]: {m.get('body', '')}"
            for m in conversation
        )
        system = SYSTEM_PROMPT.replace("{community_link}", self.community_link)
        user_msg = f"Lead's first name: {first_name}\n\nConversation so far:\n{thread}\n\nClassify the lead's latest reply and provide your response."

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = response.content[0].text.strip()
            data = json.loads(raw)
            path = data.get("path", "C")
            if path not in ("A", "B", "C"):
                path = "C"
            return ClassificationResult(path=path, reply=data.get("reply", ""))
        except (json.JSONDecodeError, KeyError, IndexError, Exception) as exc:
            logger.error("Claude classification failed: %s — defaulting to Path C", exc)
            return ClassificationResult(
                path="C",
                reply="Thanks for getting back to me! Just to make sure I point you in the right direction — are you looking for something more hands-on like 1-on-1 coaching, or resources you can work through at your own pace?",
            )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_claude_client.py -v
```

Expected: All 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/claude_client.py tests/test_claude_client.py
git commit -m "feat: Claude client for reply classification"
```

---

## Task 7: Scheduler

**Files:**
- Create: `app/scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_scheduler.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from app.scheduler import Scheduler


@pytest.fixture
def scheduler():
    sched = Scheduler(jobs_db_url="sqlite:///:memory:")
    sched.start()
    yield sched
    sched.shutdown()


def test_schedule_followups_creates_four_jobs(scheduler):
    mock_fn = MagicMock()
    scheduler.schedule_followups(
        lead_id="opp_001",
        fn=mock_fn,
        fn_kwargs={"lead_id": "opp_001"},
    )
    jobs = scheduler.get_jobs_for_lead("opp_001")
    assert len(jobs) == 4


def test_cancel_followups_removes_all_jobs(scheduler):
    mock_fn = MagicMock()
    scheduler.schedule_followups(
        lead_id="opp_001",
        fn=mock_fn,
        fn_kwargs={"lead_id": "opp_001"},
    )
    scheduler.cancel_followups("opp_001")
    jobs = scheduler.get_jobs_for_lead("opp_001")
    assert len(jobs) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scheduler.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.scheduler'`

- [ ] **Step 3: Implement scheduler.py**

Create `app/scheduler.py`:
```python
from datetime import datetime, timedelta, timezone
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# Follow-up offsets from the initial contact time (in days)
FOLLOWUP_DAYS = [1, 2, 4, 7]


class Scheduler:
    def __init__(self, jobs_db_url: str):
        jobstores = {"default": SQLAlchemyJobStore(url=jobs_db_url)}
        self._scheduler = BackgroundScheduler(jobstores=jobstores)

    def start(self):
        self._scheduler.start()

    def shutdown(self):
        self._scheduler.shutdown(wait=False)

    def schedule_followups(
        self,
        lead_id: str,
        fn: Callable,
        fn_kwargs: dict,
    ) -> None:
        now = datetime.now(timezone.utc)
        for i, days in enumerate(FOLLOWUP_DAYS, start=1):
            run_at = now + timedelta(days=days)
            job_id = f"followup_{lead_id}_{i}"
            self._scheduler.add_job(
                fn,
                trigger="date",
                run_date=run_at,
                id=job_id,
                kwargs={**fn_kwargs, "followup_stage": i},
                replace_existing=True,
            )

    def cancel_followups(self, lead_id: str) -> None:
        for i in range(1, len(FOLLOWUP_DAYS) + 1):
            job_id = f"followup_{lead_id}_{i}"
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)

    def get_jobs_for_lead(self, lead_id: str) -> list:
        prefix = f"followup_{lead_id}_"
        return [j for j in self._scheduler.get_jobs() if j.id.startswith(prefix)]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scheduler.py -v
```

Expected: Both tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/scheduler.py tests/test_scheduler.py
git commit -m "feat: APScheduler with persistent follow-up job management"
```

---

## Task 8: Opportunity Webhook Handler

**Files:**
- Create: `app/handlers/opportunity.py`
- Create: `tests/test_opportunity_handler.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_opportunity_handler.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_opportunity_handler.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.handlers.opportunity'`

- [ ] **Step 3: Implement handlers/opportunity.py**

Create `app/handlers/opportunity.py`:
```python
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
    initial_delay_seconds: int = 300,  # 5 minutes
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_opportunity_handler.py -v
```

Expected: All 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/handlers/opportunity.py tests/test_opportunity_handler.py
git commit -m "feat: opportunity webhook handler with initial outreach"
```

---

## Task 9: Inbound Message Handler

**Files:**
- Create: `app/handlers/message.py`
- Create: `tests/test_message_handler.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_message_handler.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_message_handler.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.handlers.message'`

- [ ] **Step 3: Implement handlers/message.py**

Create `app/handlers/message.py`:
```python
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
        db.update_lead(lead_id=lead.lead_id, status="booked")
        notification = messages.aaron_notification_sms(first_name, last_name, path="A")
    elif result.path == "B":
        reply = messages.path_b_sms(community_link)
        ghl.update_opportunity_stage(opportunity_id=lead.lead_id, stage_id=stage_community)
        db.update_lead(lead_id=lead.lead_id, status="enrolled")
        notification = messages.aaron_notification_sms(first_name, last_name, path="B")
    else:
        reply = result.reply or messages.path_c_sms()
        notification = messages.aaron_notification_sms(first_name, last_name, path="C")

    ghl.send_sms(contact_id=contact_id, message=reply)
    ghl.notify_aaron(notification)
    db.update_lead(lead_id=lead.lead_id, last_contact=datetime.now(timezone.utc))
    logger.info("Handled inbound reply from %s — routed to Path %s", first_name, result.path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_message_handler.py -v
```

Expected: All 6 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/handlers/message.py tests/test_message_handler.py
git commit -m "feat: inbound message handler with Claude routing"
```

---

## Task 10: FastAPI Main App

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_main.py`:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_health_endpoint():
    with patch("app.main.settings") as mock_settings:
        mock_settings.ghl_api_key = "test"
        mock_settings.ghl_location_id = "loc"
        mock_settings.ghl_pipeline_id = "pip"
        mock_settings.ghl_stage_lead_in = "s1"
        mock_settings.ghl_stage_contacted = "s2"
        mock_settings.ghl_stage_qualified_coaching = "s3"
        mock_settings.ghl_stage_qualified_community = "s4"
        mock_settings.ghl_stage_unresponsive = "s5"
        mock_settings.ghl_aaron_contact_id = "a1"
        mock_settings.ghl_from_email = "test@test.com"
        mock_settings.anthropic_api_key = "ant"
        mock_settings.aaron_phone = "+1925"
        mock_settings.calendly_link = "https://cal.test"
        mock_settings.community_link = "https://comm.test"
        mock_settings.database_url = "sqlite:///:memory:"
        mock_settings.jobs_database_url = "sqlite:///:memory:"

        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Implement main.py**

Create `app/main.py`:
```python
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
    scheduler.start()
    logger.info("Louie is live")
    yield
    scheduler.shutdown()


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
```

- [ ] **Step 4: Run all tests**

```bash
pytest -v
```

Expected: All tests `PASSED`

- [ ] **Step 5: Verify app starts locally**

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health` — should return `{"status": "ok"}`.

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_main.py
git commit -m "feat: FastAPI app with webhook routes and lifespan scheduler"
```

---

## Task 11: Railway Deployment

**Files:**
- Create: `Procfile`
- Create: `railway.toml`

- [ ] **Step 1: Create Procfile**

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: Create railway.toml**

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

- [ ] **Step 3: Set up Railway project**

1. Go to [railway.app](https://railway.app) and create a new project
2. Choose "Deploy from GitHub repo" → select `aaronjbaruh-svg/Assistant`
3. Set the root directory to `/` (default)
4. Add all environment variables from `.env.example` in the Railway dashboard under "Variables"
5. Railway will auto-deploy on every push to `main`

- [ ] **Step 4: Note your Railway public URL**

After deploying, Railway gives you a URL like `https://assistant-production-xxxx.up.railway.app`. Save this — you'll use it for GHL webhook configuration.

- [ ] **Step 5: Configure GHL webhooks**

In GoHighLevel → Settings → Integrations → Webhooks:

Add two webhooks pointing to your Railway URL:
- **Opportunity webhook:** `https://your-railway-url.up.railway.app/webhook/opportunity`
  - Event: `OpportunityStageUpdate`
- **Message webhook:** `https://your-railway-url.up.railway.app/webhook/message`
  - Event: `InboundMessage`

- [ ] **Step 6: Commit**

```bash
git add Procfile railway.toml
git commit -m "feat: Railway deployment config"
```

---

## Task 12: End-to-End Smoke Test

**Goal:** Verify the full Louie flow works with a real test contact before going live on actual leads.

- [ ] **Step 1: Identify your GHL pipeline stage IDs**

In GHL, go to your Opportunities pipeline settings and note the IDs for:
- Lead In
- Contacted
- Qualified (Coaching)
- Qualified (Community)
- Unresponsive

These go in your `.env` and Railway environment variables.

- [ ] **Step 2: Find Aaron's GHL contact ID**

In GHL → Contacts, find Aaron's own contact record and copy his Contact ID. This is `GHL_AARON_CONTACT_ID`.

- [ ] **Step 3: Create a test contact in GHL**

- Name: Test Lead
- Phone: Aaron's 925 number (for testing SMS delivery to yourself)
- Email: aaronjbaruh@gmail.com

- [ ] **Step 4: Move test contact to "Lead In" stage**

Manually set the test contact's opportunity to "Lead In" in the pipeline. This fires the GHL webhook.

- [ ] **Step 5: Verify initial outreach**

Wait 5 minutes. Confirm:
- SMS received at 925 number with Louie's opening message
- Email received at aaronjbaruh@gmail.com with Louie's opening message
- GHL opportunity stage changed to "Contacted"

- [ ] **Step 6: Test Path A**

Reply to the SMS with: `"I'm looking for 1-on-1 coaching"`

Confirm:
- Louie replies with the Calendly link
- Aaron gets notified at 925-525-1091: "Live reply from Test Lead — interested in hands-on coaching"
- GHL opportunity stage changed to "Qualified (Coaching)"

- [ ] **Step 7: Test Path B**

Create a second test contact and repeat Steps 3–5. Reply with: `"I want to see the curriculum and maybe attend a webinar"`

Confirm:
- Louie replies with the Be You Louder Community copy + community link
- Aaron gets notified
- GHL opportunity stage changed to "Qualified (Community)"

- [ ] **Step 8: Test follow-up cadence (abbreviated)**

Create a third test contact and move to Lead In. Do not reply. Check Railway logs to confirm scheduled jobs exist for Day 1, 2, 4, 7. (Full cadence test can be done with a shortened delay in dev.)

- [ ] **Step 9: Push final state to dev**

```bash
git push origin dev
```

---

## Open Items (before go-live)

- [ ] Aaron finalizes message copy in `app/messages.py` (all `[COPY TBD]` lines)
- [ ] Community enrollment link obtained and added to `.env` as `COMMUNITY_LINK`
- [ ] GHL pipeline stage IDs collected and added to `.env` and Railway vars
- [ ] Aaron's GHL contact ID added as `GHL_AARON_CONTACT_ID`
- [ ] Railway account set up and connected to GitHub repo
- [ ] GHL webhooks configured to point to Railway URL
