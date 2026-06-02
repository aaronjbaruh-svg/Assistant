# All message copy lives here. Edit this file to update Louie's voice.
# Lines marked [COPY TBD] should be updated by Aaron before going live.


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
