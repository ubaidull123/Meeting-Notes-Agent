"""PostgreSQL database setup using LangChain Postgres integration."""
import os
import psycopg
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver, ConnectionPool

load_dotenv()

# Global pool instance
_pool = None


def get_pool() -> ConnectionPool:
    """Get or create the ConnectionPool."""
    global _pool
    if _pool is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            database_url = (
                f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:"
                f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
                f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
                f"{os.environ.get('POSTGRES_PORT', '5432')}/"
                f"{os.environ.get('POSTGRES_DB', 'meeting_notes')}"
            )
        _pool = ConnectionPool(
            database_url,
            kwargs={"autocommit": True, "prepare_threshold": 0},
            max_size=10,
            open=True,
        )
    return _pool


def get_checkpointer() -> PostgresSaver:
    """Get LangGraph PostgresSaver for checkpointing."""
    pool = get_pool()
    return PostgresSaver(pool)


def get_connection():
    """Get a psycopg connection for raw SQL execution."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = (
            f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:"
            f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
            f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
            f"{os.environ.get('POSTGRES_PORT', '5432')}/"
            f"{os.environ.get('POSTGRES_DB', 'meeting_notes')}"
        )
    return psycopg.connect(database_url)


def init_db() -> None:
    """Initialize database tables using raw SQL."""
    schema = """
    -- Users table (authentication)
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

    -- Add role column to existing tables (migration)
    ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user'));
    -- Remove legacy is_superuser column if it exists
    ALTER TABLE users DROP COLUMN IF EXISTS is_superuser;

    -- Meetings table
    CREATE TABLE IF NOT EXISTS meetings (
        id UUID PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        title VARCHAR(500) NOT NULL,
        meeting_date DATE NOT NULL,
        meeting_time TIME,
        project_name VARCHAR(255),
        audio_file_path TEXT,
        transcript_file_path TEXT,
        transcript_text TEXT,
        raw_transcription TEXT,
        cleaned_transcription TEXT,
        summary TEXT,
        decisions JSONB DEFAULT '[]',
        action_items JSONB DEFAULT '[]',
        redacted_transcription TEXT,
        redacted_summary TEXT,
        redacted_decisions JSONB DEFAULT '[]',
        redacted_action_items JSONB DEFAULT '[]',
        email_draft TEXT,
        email_sent BOOLEAN DEFAULT FALSE,
        email_response JSONB,
        tokens_used INTEGER DEFAULT 0,
        credits_charged BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Support databases created before user ownership was introduced.
    ALTER TABLE meetings ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
    ALTER TABLE meetings ADD COLUMN IF NOT EXISTS tokens_used INTEGER DEFAULT 0;
    ALTER TABLE meetings ADD COLUMN IF NOT EXISTS credits_charged BOOLEAN NOT NULL DEFAULT FALSE;
    CREATE INDEX IF NOT EXISTS idx_meetings_user ON meetings(user_id);

    -- Attendees table
    CREATE TABLE IF NOT EXISTS attendees (
        id SERIAL PRIMARY KEY,
        meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Tasks table
    CREATE TABLE IF NOT EXISTS tasks (
        id VARCHAR(8) PRIMARY KEY,
        meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
        meeting_title VARCHAR(500) NOT NULL,
        title VARCHAR(500) NOT NULL,
        description TEXT,
        status VARCHAR(50) DEFAULT 'todo',
        priority VARCHAR(50) DEFAULT 'medium',
        assignee VARCHAR(255),
        due_date DATE,
        labels JSONB DEFAULT '[]',
        action_item_index INTEGER NOT NULL,
        github_issue_number INTEGER,
        github_issue_url TEXT,
        synced_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- User Quotas table (monthly meeting limits and credit grants)
    CREATE TABLE IF NOT EXISTS user_quotas (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        monthly_meeting_limit INTEGER DEFAULT 20,
        monthly_credits INTEGER DEFAULT 500,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Migration: Add monthly_credits column if it doesn't exist (for existing databases)
    ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS monthly_credits INTEGER DEFAULT 500;

    -- User Credits table (current balance)
    CREATE TABLE IF NOT EXISTS user_credits (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        balance INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- User Usage table (monthly rollup for history)
    CREATE TABLE IF NOT EXISTS user_usage (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        month DATE NOT NULL,  -- First day of month (e.g., '2026-08-01')
        meetings_processed INTEGER DEFAULT 0,
        tokens_used INTEGER DEFAULT 0,
        credits_consumed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(user_id, month)
    );

    CREATE INDEX IF NOT EXISTS idx_user_usage_user_month ON user_usage(user_id, month DESC);

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(meeting_date DESC);
    CREATE INDEX IF NOT EXISTS idx_meetings_project ON meetings(project_name);
    CREATE INDEX IF NOT EXISTS idx_tasks_meeting ON tasks(meeting_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
    CREATE INDEX IF NOT EXISTS idx_attendees_meeting ON attendees(meeting_id);

    -- Updated at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    DROP TRIGGER IF EXISTS update_meetings_updated_at ON meetings;
    CREATE TRIGGER update_meetings_updated_at
        BEFORE UPDATE ON meetings
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
    CREATE TRIGGER update_tasks_updated_at
        BEFORE UPDATE ON tasks
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_user_quotas_updated_at ON user_quotas;
    CREATE TRIGGER update_user_quotas_updated_at
        BEFORE UPDATE ON user_quotas
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_user_credits_updated_at ON user_credits;
    CREATE TRIGGER update_user_credits_updated_at
        BEFORE UPDATE ON user_credits
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_user_usage_updated_at ON user_usage;
    CREATE TRIGGER update_user_usage_updated_at
        BEFORE UPDATE ON user_usage
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """

    with get_connection() as conn:
        conn.execute(schema)
        conn.commit()


def assign_legacy_meeting_owner(meeting_id: str, owner_email: str) -> bool:
    """Assign one pre-ownership meeting to an explicit account.

    This intentionally never guesses an owner or exposes an unowned meeting to
    every user. It is a one-time admin migration helper for records created
    before ``meetings.user_id`` existed.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (owner_email.lower(),))
            owner = cur.fetchone()
            if not owner:
                raise ValueError(f"No user exists for {owner_email}")
            cur.execute(
                "UPDATE meetings SET user_id = %s WHERE id = %s AND user_id IS NULL",
                (owner[0], meeting_id),
            )
            changed = cur.rowcount == 1
        conn.commit()
    return changed


def backfill_user_quotas_and_credits() -> None:
    """Backfill user_quotas and user_credits for existing users."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get all users
            cur.execute("SELECT id FROM users WHERE is_active = TRUE")
            users = cur.fetchall()

            for (user_id,) in users:
                # Insert quota with defaults if not exists
                cur.execute("""
                    INSERT INTO user_quotas (user_id, monthly_meeting_limit, monthly_credits)
                    VALUES (%s, 20, 500)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))

                # Insert credits with default if not exists
                cur.execute("""
                    INSERT INTO user_credits (user_id, balance)
                    VALUES (%s, 500)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))

        conn.commit()


def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool:
        _pool.close()
        _pool = None
