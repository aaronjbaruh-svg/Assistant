from app.deps import db, ghl, claude
from app.database import Database
from app.ghl_client import GHLClient
from app.claude_client import ClaudeClient


def test_deps_are_correct_types():
    assert isinstance(db, Database)
    assert isinstance(ghl, GHLClient)
    assert isinstance(claude, ClaudeClient)
