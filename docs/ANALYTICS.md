# Analytics (Hap v1)

Events are written to the `analytics_events` Supabase table from the backend. No third-party trackers.

## Key events

| Event | When |
|-------|------|
| `bot_started` | `/start` |
| `onboarding_completed` | `[ONBOARDING_DONE]` profile extraction |
| `idea_created` | First `[IDEA_DETECTED]` for user |
| `homework_completed` | `[HOMEWORK_DONE]` |
| `homework_skipped` | `[HOMEWORK_SKIPPED]` |
| `user_deleted_data` | `/deletedata` confirmed |

`user_hash` is SHA256(telegram_id + salt). No message content is stored.

## Weekly review

See CLAUDE.md §17 for funnel and retention metrics to watch manually in SQL or Supabase dashboard.
