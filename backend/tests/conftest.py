"""Test-time setup. Loaded by pytest before any `app` import.

We blank out SENTRY_DSN so unit tests don't ship events to the live project, and we
provide deterministic placeholder values for the secrets that `Settings` requires.
ENCRYPTION_KEY is generated fresh per test run.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet

os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("TELEGRAM_ID_HASH_SALT", "test-salt")
os.environ.setdefault("SUPABASE_URL", "http://test.local")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-supabase-key")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
