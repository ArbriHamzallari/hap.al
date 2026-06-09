from app.conversation.prompts import base_sq
from app.i18n.detector import language_from_telegram_code, resolve_language
from app.i18n.loader import t


def test_language_from_telegram_code() -> None:
    assert language_from_telegram_code("sq-AL") == "sq"
    assert language_from_telegram_code("en-US") == "en"


def test_resolve_language_prefers_stored() -> None:
    assert resolve_language(stored="sq", telegram_code="en-US", first_message="hello") == "sq"


def test_loader_en_and_sq() -> None:
    assert "/start" in t("commands.help", "en")
    assert "ide" in t("commands.no_idea", "sq").lower()


def test_base_sq_prompt_sections() -> None:
    prompt = base_sq.build_base_prompt()
    assert "GJUHA" in prompt or "shqip" in prompt.lower()
    assert base_sq.VERSION
