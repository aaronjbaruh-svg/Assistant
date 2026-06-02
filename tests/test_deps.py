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
