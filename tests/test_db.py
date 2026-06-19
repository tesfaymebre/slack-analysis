"""Tests for Task 3 database modules."""

import json
import os

import pandas as pd
import pytest

from src.db import mongo_schema
from src.db.features import (
    build_channel_activity_features,
    build_daily_sentiment_features,
    build_time_gap_features,
    build_user_activity_features,
)
from src.db.mongo_loader import (
    _message_document,
    _reaction_documents,
    _reply_documents,
    load_channel_exports,
    load_metadata,
)
from src.db.postgres_schema import CREATE_TABLES_SQL


@pytest.fixture
def sample_messages():
    """Small in-memory message frame for feature tests."""
    return pd.DataFrame({
        'msg_id': ['m1', 'm2', 'm3'],
        'text': ['How do I use python?', 'Thanks team', 'Docker deployment help'],
        'user': ['U1', 'U2', 'U1'],
        'mentions': [[], [], ['U2']],
        'reactions': [None, [{'name': 'thumbsup', 'count': 1, 'users': ['U2']}], None],
        'replies': [None, None, ['U2']],
        'replies_to': [None, None, None],
        'replies_meta': [
            None,
            None,
            [{'user': 'U2', 'ts': '1001.0', 'text': 'check docs'}],
        ],
        'ts': ['1000.0', '1000.5', '1001.0'],
        'links': [[], [], []],
        'link_count': [0, 0, 0],
        'reply_count': [0, 0, 1],
        'reaction_count': [0, 1, 0],
        'channel': ['general', 'general', 'dev'],
    })


@pytest.fixture
def sample_users():
    """Minimal Slack user list."""
    return [
        {'id': 'U1', 'name': 'alice', 'real_name': 'Alice'},
        {'id': 'U2', 'name': 'bob', 'real_name': 'Bob'},
    ]


def test_message_document_keeps_raw_payload():
    """Mongo message docs should preserve the original Slack JSON."""
    msg = {'client_msg_id': 'abc', 'type': 'message', 'text': 'hello', 'user': 'U1', 'ts': '1.0'}
    doc = _message_document('ws1', 'C1', 'general', '2022-08-12', '2022-08-12.json', msg)
    assert doc['workspace_id'] == 'ws1'
    assert doc['raw'] == msg


def test_reply_documents_split_thread_replies():
    """Thread replies should become separate Mongo documents."""
    parent = {'client_msg_id': 'parent', 'ts': '10.0', 'thread_ts': '10.0'}
    replies = [{'user': 'U2', 'ts': '11.0', 'text': 'reply text'}]
    docs = _reply_documents('ws1', 'C1', 'general', parent, replies)
    assert len(docs) == 1
    assert docs[0]['thread_ts'] == '10.0'


def test_reaction_documents_create_per_user_rows():
    """Each reacting user should get its own reaction document."""
    msg = {
        'client_msg_id': 'm1',
        'ts': '10.0',
        'reactions': [{'name': 'heart', 'count': 2, 'users': ['U1', 'U2']}],
    }
    docs = _reaction_documents('ws1', 'C1', 'general', msg)
    assert len(docs) == 2
    assert {doc['user_id'] for doc in docs} == {'U1', 'U2'}


def test_mongo_loader_writes_metadata_and_messages(tmp_path):
    """Mongo loader should upsert users, channels, and messages."""
    mongomock = pytest.importorskip('mongomock')
    data_path = tmp_path / 'anonymized'
    data_path.mkdir()

    users = [{'id': 'U1', 'name': 'alice', 'real_name': 'Alice'}]
    channels = [{'id': 'C1', 'name': 'general', 'context_team_id': 'T1'}]
    with open(data_path / 'users.json', 'w', encoding='utf-8') as handle:
        json.dump(users, handle)
    with open(data_path / 'channels.json', 'w', encoding='utf-8') as handle:
        json.dump(channels, handle)

    channel_dir = data_path / 'general'
    channel_dir.mkdir()
    messages = [{'type': 'message', 'text': 'hello', 'user': 'U1', 'ts': '1.0'}]
    with open(channel_dir / '2022-08-12.json', 'w', encoding='utf-8') as handle:
        json.dump(messages, handle)

    from src.loader import SlackDataLoader

    loader = SlackDataLoader(str(data_path))
    client = mongomock.MongoClient()
    db = client['test_db']
    mongo_schema.ensure_indexes(db)

    channel_map = load_metadata(db, loader, 'T1')
    counts = load_channel_exports(db, loader, 'T1', channel_map)

    assert db[mongo_schema.USERS].count_documents({}) == 1
    assert db[mongo_schema.CHANNELS].count_documents({}) == 1
    assert db[mongo_schema.MESSAGES].count_documents({}) == 1
    assert counts['messages'] >= 1


def test_build_user_activity_features(sample_messages, sample_users):
    """User feature table should include message and reply counts."""
    features = build_user_activity_features(sample_messages, sample_users, workspace_id='ws1')
    alice = features.loc[features['user_id'] == 'U1'].iloc[0]
    assert alice['message_count'] == 2
    assert alice['reply_count'] == 0


def test_build_channel_activity_features(sample_messages):
    """Channel feature table should aggregate activity per channel."""
    features = build_channel_activity_features(sample_messages, workspace_id='ws1')
    assert set(features['channel']) == {'general', 'dev'}
    assert features['message_count'].sum() == 3


def test_build_daily_sentiment_features(sample_messages):
    """Daily sentiment table should have one row per day index."""
    features = build_daily_sentiment_features(sample_messages, workspace_id='ws1')
    assert 'days_since_start' in features.columns
    assert 'sentiment' in features.columns


def test_build_time_gap_features(sample_messages):
    """Time-gap table should summarize each event type."""
    features = build_time_gap_features(sample_messages, workspace_id='ws1')
    assert set(features['event_type']) == {'message', 'reply', 'reaction', 'all_events'}


def test_postgres_schema_defines_all_feature_tables():
    """DDL should include every feature-store table."""
    for table in (
        'user_activity_features',
        'channel_activity_features',
        'message_features',
        'channel_topic_features',
        'daily_sentiment_features',
        'time_gap_features',
    ):
        assert table in CREATE_TABLES_SQL
