from app.config import settings

def test_settings_loads_from_env():
    assert settings.ghl_api_key == "test_ghl_key"
    assert settings.ghl_location_id == "test_location"
    assert settings.aaron_phone == "+19255251091"
    assert settings.calendly_link == "https://calendly.com/aaron-youlouder/conversation-w-aaron-youlouder"
