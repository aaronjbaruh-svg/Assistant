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


def test_followup_sms_stage_1():
    msg = followup_sms("Jane", stage=1)
    assert "Jane" in msg


def test_followup_sms_stage_4():
    msg = followup_sms("Jane", stage=4)
    assert "Jane" in msg
