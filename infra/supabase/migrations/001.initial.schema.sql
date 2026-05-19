-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'sq')),
    onboarding_complete BOOLEAN DEFAULT FALSE,
    skills TEXT[],
    experience_level TEXT CHECK (experience_level IN ('none', 'beginner', 'some', 'experienced')),
    financial_situation TEXT,  -- Encrypted (Fernet)
    time_availability TEXT CHECK (time_availability IN ('few_hours_week', 'part_time', 'full_time')),
    has_day_job BOOLEAN,
    location TEXT,
    personality_notes TEXT,   -- Encrypted (Fernet)
    motivation TEXT,
    fears TEXT,               -- Encrypted (Fernet)
    timezone TEXT DEFAULT 'Europe/Tirane',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW()
);

-- Ideas table
CREATE TABLE ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    description TEXT,
    target_customer TEXT,
    problem_solved TEXT,
    business_model TEXT,
    unique_advantage TEXT,
    current_stage TEXT DEFAULT 'raw_idea' 
        CHECK (current_stage IN ('raw_idea', 'exploring', 'validating', 'building', 'pivoted', 'abandoned')),
    validation_score INTEGER DEFAULT 0 CHECK (validation_score BETWEEN 0 AND 100),
    strengths TEXT[],
    weaknesses TEXT[],
    pivot_history JSONB DEFAULT '[]'::JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    idea_id UUID REFERENCES ideas(id) ON DELETE SET NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'general' 
        CHECK (message_type IN ('onboarding', 'idea_exploration', 'homework_update', 'follow_up', 'general')),
    language TEXT DEFAULT 'en',
    prompt_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Homework table
CREATE TABLE homework (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    idea_id UUID REFERENCES ideas(id) ON DELETE CASCADE,
    task_description TEXT NOT NULL,
    reasoning TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending' 
        CHECK (status IN ('pending', 'completed', 'skipped', 'overdue')),
    completion_notes TEXT,
    follow_up_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Journey events table
CREATE TABLE journey_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    idea_id UUID REFERENCES ideas(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL 
        CHECK (event_type IN ('pivot', 'validation_feedback', 'customer_interview', 'milestone', 'score_change', 'insight')),
    description TEXT,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analytics events table (no PII)
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_hash TEXT NOT NULL,
    event_name TEXT NOT NULL,
    properties JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_ideas_user_id ON ideas(user_id);
CREATE INDEX idx_ideas_active ON ideas(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created ON conversations(user_id, created_at DESC);
CREATE INDEX idx_homework_pending ON homework(due_date, follow_up_sent) 
    WHERE status = 'pending' AND follow_up_sent = FALSE;
CREATE INDEX idx_analytics_event ON analytics_events(event_name, created_at);

-- Enable Row Level Security on ALL tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE homework ENABLE ROW LEVEL SECURITY;
ALTER TABLE journey_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- RLS is enabled above with NO permissive policies. This is intentional:
--   * The Supabase `service_role` key bypasses RLS (BYPASSRLS attribute) — backend has full access.
--   * `anon` and `authenticated` roles are denied all access on every table.
-- Matches §9.5 of CLAUDE.md: service-role-only, no public/anon access.
-- The previous version of this file used `CREATE POLICY ... USING (TRUE)`, which silently
-- granted full access to anon and authenticated. Do not re-introduce that pattern.
-- For post-MVP Mini App access, the backend will mediate via initData; do NOT add an
-- `authenticated` policy here until that work is scoped, or we re-open the door.