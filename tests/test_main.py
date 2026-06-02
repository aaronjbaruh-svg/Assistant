from fastapi.testclient import TestClient


def test_health_endpoint():
    from app.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_opportunity_webhook_returns_received():
    from app.main import app
    client = TestClient(app)
    payload = {
        "type": "OpportunityStageUpdate",
        "id": "opp_test",
        "contactId": "con_test",
        "pipelineStageId": "stage_other",
        "contact": {"firstName": "Test", "lastName": "User", "phone": "+15105551234", "email": "test@example.com"},
    }
    response = client.post("/webhook/opportunity", json=payload)
    assert response.status_code == 200
    assert response.json()["received"] is True


def test_message_webhook_returns_received():
    from app.main import app
    client = TestClient(app)
    payload = {
        "type": "InboundMessage",
        "contactId": "unknown_contact",
        "messageType": "SMS",
        "message": "Hello",
        "contact": {"firstName": "Test", "lastName": "User"},
    }
    response = client.post("/webhook/message", json=payload)
    assert response.status_code == 200
    assert response.json()["received"] is True
