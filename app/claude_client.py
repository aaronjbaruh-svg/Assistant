import json
import logging
from dataclasses import dataclass
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
        except Exception as exc:
            logger.error("Claude classification failed: %s — defaulting to Path C", exc)
            return ClassificationResult(
                path="C",
                reply="Thanks for getting back to me! Just to make sure I point you in the right direction — are you looking for something more hands-on like 1-on-1 coaching, or resources you can work through at your own pace?",
            )
