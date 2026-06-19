"""Read Slack analytics from PostgreSQL (features) and MongoDB (raw messages)."""

import pandas as pd
import psycopg2
from pymongo import MongoClient

from src.dashboard.config import MONGO_DB, MONGO_URI, POSTGRES_DSN

FEATURE_TABLES = (
    'user_activity_features',
    'channel_activity_features',
    'message_features',
    'channel_topic_features',
    'daily_sentiment_features',
    'time_gap_features',
)


def get_postgres_connection(dsn=None):
    """Open a PostgreSQL connection using the configured DSN."""
    return psycopg2.connect(dsn or POSTGRES_DSN)


def read_sql_table(table_name, dsn=None):
    """Load one feature-store table into a DataFrame."""
    query = f'SELECT * FROM {table_name}'
    with get_postgres_connection(dsn) as connection:
        return pd.read_sql(query, connection)


def load_feature_store(dsn=None):
    """
    Load every PostgreSQL feature table.

    Returns:
        Dictionary mapping table name to DataFrame.
    """
    return {table: read_sql_table(table, dsn=dsn) for table in FEATURE_TABLES}


def get_overview_metrics(features):
    """Compute top-level KPIs for the dashboard header."""
    channels = features['channel_activity_features']
    users = features['user_activity_features']
    messages = features['message_features']

    return {
        'channel_count': int(len(channels)),
        'user_count': int(len(users)),
        'message_count': int(len(messages)),
        'total_replies': int(channels['reply_total'].sum()) if not channels.empty else 0,
        'total_reactions': int(channels['reaction_total'].sum()) if not channels.empty else 0,
        'avg_sentiment': float(messages['sentiment_score'].mean()) if not messages.empty else 0.0,
    }


def get_mongo_client(uri=None):
    """Return a MongoDB client."""
    return MongoClient(uri or MONGO_URI)


def get_mongo_overview(uri=None, db_name=None):
    """
    Return collection counts from MongoDB.

    Useful for showing the NoSQL side of the fullstack stack.
    """
    client = get_mongo_client(uri)
    database = client[db_name or MONGO_DB]
    return {
        'messages': database['messages'].count_documents({}),
        'thread_replies': database['thread_replies'].count_documents({}),
        'reactions': database['reactions'].count_documents({}),
        'users': database['users'].count_documents({}),
        'channels': database['channels'].count_documents({}),
    }


def get_recent_messages(channel=None, limit=10, uri=None, db_name=None):
    """Fetch recent raw messages from MongoDB for the API/React demo."""
    client = get_mongo_client(uri)
    database = client[db_name or MONGO_DB]
    query = {'channel_name': channel} if channel else {}
    cursor = database['messages'].find(
        query,
        {'_id': 0, 'channel_name': 1, 'user_id': 1, 'text': 1, 'ts': 1},
    ).sort('ts', -1).limit(limit)

    rows = []
    for document in cursor:
        rows.append({
            'channel': document.get('channel_name'),
            'user_id': document.get('user_id'),
            'text': document.get('text', '')[:200],
            'ts': document.get('ts'),
        })
    return rows


def get_channel_summaries(dsn=None):
    """Return channel activity rows sorted by message volume."""
    frame = read_sql_table('channel_activity_features', dsn=dsn)
    if frame.empty:
        return frame
    return frame.sort_values('message_count', ascending=False)
