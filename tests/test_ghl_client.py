import pytest
import httpx
from unittest.mock import patch, MagicMock
from app.ghl_client import GHLClient


@pytest.fixture
def client():
    return GHLClient(
        api_key="test_key",
        location_id="test_loc",
        from_email="aaron@beyoulouder.com",
        aaron_contact_id="aaron_con_123",
    )


def test_send_sms_calls_correct_endpoint(client):
    with patch("app.ghl_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "msg_1"})
        mock_post.return_value.raise_for_status = MagicMock()
        client.send_sms(contact_id="con_001", message="Hello Jane!")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/conversations/messages" in call_args[0][0]
        body = call_args[1]["json"]
        assert body["type"] == "SMS"
        assert body["contactId"] == "con_001"
        assert body["message"] == "Hello Jane!"


def test_send_email_calls_correct_endpoint(client):
    with patch("app.ghl_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "msg_2"})
        mock_post.return_value.raise_for_status = MagicMock()
        client.send_email(
            contact_id="con_001",
            to_email="jane@example.com",
            subject="Hello",
            html="<p>Hi</p>",
        )
        body = mock_post.call_args[1]["json"]
        assert body["type"] == "Email"
        assert body["subject"] == "Hello"


def test_update_opportunity_stage(client):
    with patch("app.ghl_client.httpx.put") as mock_put:
        mock_put.return_value = MagicMock(status_code=200, json=lambda: {})
        mock_put.return_value.raise_for_status = MagicMock()
        client.update_opportunity_stage(
            opportunity_id="opp_001",
            stage_id="stage_contacted",
        )
        call_args = mock_put.call_args
        assert "opp_001" in call_args[0][0]
        body = call_args[1]["json"]
        assert body["pipelineStageId"] == "stage_contacted"


def test_get_recent_messages_returns_list(client):
    with patch("app.ghl_client.httpx.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"conversations": [{"id": "conv_001"}]}, raise_for_status=MagicMock()),
            MagicMock(status_code=200, json=lambda: {"messages": {"messages": [{"body": "Hi", "direction": "inbound"}]}}, raise_for_status=MagicMock()),
        ]
        messages = client.get_recent_messages(contact_id="con_001")
        assert isinstance(messages, list)
        assert len(messages) == 1


def test_send_sms_retries_on_failure(client):
    with patch("app.ghl_client.httpx.post") as mock_post:
        with patch("app.ghl_client.time.sleep"):
            success = MagicMock(status_code=200, json=lambda: {"id": "msg_3"})
            success.raise_for_status = MagicMock()
            mock_post.side_effect = [
                httpx.HTTPError("timeout"),
                httpx.HTTPError("timeout"),
                success,
            ]
            client.send_sms("con_001", "Hello")
            assert mock_post.call_count == 3
