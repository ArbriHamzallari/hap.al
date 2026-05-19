"""Phase 1b smoke tests. The engine itself is not exercised — Anthropic calls cost money."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.conversation.context_builder import build_system_prompt
from app.conversation.prompts import base_en, onboarding
from app.database.models import Idea, User
from app.main import app


def _user(**kwargs: Any) -> User:
    base: dict[str, Any] = {
        "id": "00000000-0000-0000-0000-000000000001",
        "telegram_id": 1,
        "first_name": "Test",
    }
    base.update(kwargs)
    return User.model_validate(base)


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_base_en_prompt_has_required_sections() -> None:
    assert base_en.IDENTITY.strip()
    assert base_en.RULES.strip()
    assert base_en.LANGUAGE.strip()
    assert base_en.ANTI_INJECTION.strip()
    assert base_en.VERSION


def test_onboarding_prompt_has_version() -> None:
    assert onboarding.ONBOARDING_TASK.strip()
    assert onboarding.VERSION


def test_system_prompt_for_new_user_includes_onboarding() -> None:
    prompt = build_system_prompt(_user(), history=[])
    assert onboarding.ONBOARDING_TASK in prompt
    assert prompt.rstrip().endswith(base_en.ANTI_INJECTION)
    assert "## THEIR CURRENT IDEA" not in prompt


def test_system_prompt_for_onboarded_user_uses_continuing_task() -> None:
    user = _user(onboarding_complete=True, motivation="Wants to escape day job")
    prompt = build_system_prompt(user, history=[])
    assert onboarding.ONBOARDING_TASK not in prompt
    assert "## CURRENT TASK" in prompt
    assert "Wants to escape day job" in prompt


def test_system_prompt_includes_idea_when_present() -> None:
    user = _user(onboarding_complete=True)
    idea = Idea(
        id="00000000-0000-0000-0000-000000000002",
        user_id=user.id,
        title="Coffee catering",
        description="Catering for offices",
        current_stage="exploring",
    )
    prompt = build_system_prompt(user, history=[], idea=idea)
    assert "## THEIR CURRENT IDEA" in prompt
    assert "Coffee catering" in prompt
    assert "exploring" in prompt


def test_about_user_hides_empty_fields() -> None:
    user = _user()  # only first_name populated
    prompt = build_system_prompt(user, history=[])
    assert "Skills" not in prompt
    assert "Financial situation" not in prompt
    assert "Personality notes" not in prompt
