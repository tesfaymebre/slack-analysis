"""Load engineered features into PostgreSQL."""

from psycopg2.extras import execute_values

from src.db.postgres_schema import create_tables

TABLE_COLUMNS = {
    'user_activity_features': [
        'workspace_id', 'user_id', 'user_name', 'message_count',
        'reply_count', 'mention_count', 'reactions_received',
    ],
    'channel_activity_features': [
        'workspace_id', 'channel', 'message_count', 'reply_total',
        'reaction_total', 'engagement_total', 'reply_within_5min_fraction',
    ],
    'message_features': [
        'workspace_id', 'message_ts', 'msg_id', 'channel', 'user_id', 'weak_label',
        'sentiment_score', 'days_since_start', 'reply_count', 'reaction_count',
    ],
    'channel_topic_features': [
        'workspace_id', 'channel', 'topic_id', 'top_words',
    ],
    'daily_sentiment_features': [
        'workspace_id', 'days_since_start', 'sentiment', 'message_count',
    ],
    'time_gap_features': [
        'workspace_id', 'event_type', 'median_gap_seconds',
        'mean_gap_seconds', 'p95_gap_seconds', 'sample_size',
    ],
}

UPSERT_CONFLICT = {
    'user_activity_features': '(workspace_id, user_id)',
    'channel_activity_features': '(workspace_id, channel)',
    'message_features': '(workspace_id, channel, message_ts)',
    'channel_topic_features': '(workspace_id, channel, topic_id)',
    'daily_sentiment_features': '(workspace_id, days_since_start)',
    'time_gap_features': '(workspace_id, event_type)',
}

DEDUP_KEYS = {
    'user_activity_features': ['workspace_id', 'user_id'],
    'channel_activity_features': ['workspace_id', 'channel'],
    'message_features': ['workspace_id', 'channel', 'message_ts'],
    'channel_topic_features': ['workspace_id', 'channel', 'topic_id'],
    'daily_sentiment_features': ['workspace_id', 'days_since_start'],
    'time_gap_features': ['workspace_id', 'event_type'],
}


def _upsert_dataframe(cursor, table_name, frame):
    """Insert rows and update existing feature rows on conflict."""
    if frame.empty:
        return 0

    frame = frame.drop_duplicates(subset=DEDUP_KEYS[table_name], keep='last')
    columns = TABLE_COLUMNS[table_name]
    rows = [tuple(row[column] for column in columns) for _, row in frame.iterrows()]
    column_sql = ', '.join(columns)
    conflict_target = UPSERT_CONFLICT[table_name]
    update_columns = [column for column in columns if column != 'workspace_id']
    update_sql = ', '.join(f'{column} = EXCLUDED.{column}' for column in update_columns)

    query = f"""
        INSERT INTO {table_name} ({column_sql})
        VALUES %s
        ON CONFLICT {conflict_target}
        DO UPDATE SET {update_sql}, loaded_at = NOW()
    """
    execute_values(cursor, query, rows, page_size=500)
    return len(rows)


def load_features_to_postgres(connection, features, reset=False):
    """
    Create tables and upsert all feature DataFrames.

    Returns:
        Dictionary mapping table name to number of rows written.
    """
    create_tables(connection, reset=reset)
    counts = {}
    with connection.cursor() as cursor:
        for table_name, frame in features.items():
            counts[table_name] = _upsert_dataframe(cursor, table_name, frame)
    connection.commit()
    return counts
