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

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{GHL_BASE}{path}"
        for attempt in range(self.max_retries):
            try:
                resp = httpx.get(url, headers=self._headers(), params=params or {}, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
                if attempt == self.max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning("GHL GET %s attempt %d failed: %s. Retrying in %ds", path, attempt + 1, exc, wait)
                time.sleep(wait)

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
            logger.error("Failed to notify Aaron: %s: %s", type(exc).__name__, exc)
