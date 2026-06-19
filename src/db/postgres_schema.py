"""PostgreSQL feature-store table definitions."""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS user_activity_features (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    user_name VARCHAR(255),
    message_count INTEGER NOT NULL DEFAULT 0,
    reply_count INTEGER NOT NULL DEFAULT 0,
    mention_count INTEGER NOT NULL DEFAULT 0,
    reactions_received INTEGER NOT NULL DEFAULT 0,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS channel_activity_features (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(64) NOT NULL,
    channel VARCHAR(128) NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    reply_total INTEGER NOT NULL DEFAULT 0,
    reaction_total INTEGER NOT NULL DEFAULT 0,
    engagement_total INTEGER NOT NULL DEFAULT 0,
    reply_within_5min_fraction DOUBLE PRECISION,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, channel)
);

CREATE TABLE IF NOT EXISTS message_features (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(64) NOT NULL,
    message_ts VARCHAR(32) NOT NULL,
    msg_id VARCHAR(128),
    channel VARCHAR(128) NOT NULL,
    user_id VARCHAR(64),
    weak_label VARCHAR(64),
    sentiment_score DOUBLE PRECISION,
    days_since_start INTEGER,
    reply_count INTEGER DEFAULT 0,
    reaction_count INTEGER DEFAULT 0,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, channel, message_ts)
);

CREATE TABLE IF NOT EXISTS channel_topic_features (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(64) NOT NULL,
    channel VARCHAR(128) NOT NULL,
    topic_id INTEGER NOT NULL,
    top_words TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, channel, topic_id)
);

CREATE TABLE IF NOT EXISTS daily_sentiment_features (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(64) NOT NULL,
    days_since_start INTEGER NOT NULL,
    sentiment DOUBLE PRECISION NOT NULL,
    message_count INTEGER NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, days_since_start)
);

CREATE TABLE IF NOT EXISTS time_gap_features (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    median_gap_seconds DOUBLE PRECISION,
    mean_gap_seconds DOUBLE PRECISION,
    p95_gap_seconds DOUBLE PRECISION,
    sample_size INTEGER NOT NULL DEFAULT 0,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, event_type)
);
"""

DROP_TABLES_SQL = """
DROP TABLE IF EXISTS user_activity_features CASCADE;
DROP TABLE IF EXISTS channel_activity_features CASCADE;
DROP TABLE IF EXISTS message_features CASCADE;
DROP TABLE IF EXISTS channel_topic_features CASCADE;
DROP TABLE IF EXISTS daily_sentiment_features CASCADE;
DROP TABLE IF EXISTS time_gap_features CASCADE;
"""


def create_tables(connection, reset=False) -> None:
    """Create feature-store tables if they do not already exist."""
    with connection.cursor() as cursor:
        if reset:
            cursor.execute(DROP_TABLES_SQL)
        cursor.execute(CREATE_TABLES_SQL)
    connection.commit()
