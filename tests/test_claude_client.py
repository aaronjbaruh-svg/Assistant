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
    assert len(result.reply) > 0


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
