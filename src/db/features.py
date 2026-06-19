"""Build ML and EDA feature tables for PostgreSQL."""

import pandas as pd

from src.analysis.time_gaps import get_time_gap_histograms
from src.models.classifier import build_labeled_frame
from src.models.sentiment import add_days_since_start, score_text
from src.models.topic_model import get_top_topics_by_channel
from src.utils import (
    count_mentions_by_user,
    count_reactions_received_by_user,
    count_replies_by_user,
    fraction_replied_within_minutes,
    get_channel_activity,
)


def build_user_activity_features(df, users, workspace_id='default_workspace'):
    """Aggregate per-user activity metrics from Task 1 EDA helpers."""
    message_counts = df['user'].value_counts().to_dict()
    reply_counts = count_replies_by_user(df)
    mention_counts = count_mentions_by_user(df)
    reaction_counts = count_reactions_received_by_user(df)

    user_ids = set(message_counts) | set(reply_counts) | set(mention_counts) | set(reaction_counts)
    id_to_name = {user['id']: user.get('real_name', user.get('name')) for user in users}

    rows = []
    for user_id in user_ids:
        rows.append({
            'workspace_id': workspace_id,
            'user_id': user_id,
            'user_name': id_to_name.get(user_id),
            'message_count': message_counts.get(user_id, 0),
            'reply_count': reply_counts.get(user_id, 0),
            'mention_count': mention_counts.get(user_id, 0),
            'reactions_received': reaction_counts.get(user_id, 0),
        })

    return pd.DataFrame(rows)


def build_channel_activity_features(df, workspace_id='default_workspace'):
    """Aggregate per-channel activity and reply-speed metrics."""
    activity = get_channel_activity(df).reset_index()
    rows = []
    for _, row in activity.iterrows():
        channel_df = df[df['channel'] == row['channel']]
        rows.append({
            'workspace_id': workspace_id,
            'channel': row['channel'],
            'message_count': int(row['message_count']),
            'reply_total': int(row['reply_total']),
            'reaction_total': int(row['reaction_total']),
            'engagement_total': int(row['engagement_total']),
            'reply_within_5min_fraction': float(
                fraction_replied_within_minutes(channel_df, minutes=5)
            ),
        })
    return pd.DataFrame(rows)


def build_message_features(df, workspace_id='default_workspace'):
    """Build per-message labels and sentiment scores for modelling."""
    labeled = build_labeled_frame(df)
    enriched = add_days_since_start(labeled)
    enriched['sentiment_score'] = enriched['text'].fillna('').astype(str).apply(score_text)
    enriched['workspace_id'] = workspace_id
    enriched['message_ts'] = enriched['ts'].astype(str)

    features = enriched.rename(columns={'label': 'weak_label', 'user': 'user_id'})[[
        'workspace_id',
        'message_ts',
        'msg_id',
        'channel',
        'user_id',
        'weak_label',
        'sentiment_score',
        'days_since_start',
        'reply_count',
        'reaction_count',
    ]]
    return features.drop_duplicates(
        subset=['workspace_id', 'channel', 'message_ts'],
        keep='last',
    )


def build_channel_topic_features(df, workspace_id='default_workspace', num_topics=10):
    """Run LDA per channel and return topic feature rows."""
    topics = get_top_topics_by_channel(
        df,
        num_topics=num_topics,
        experiment_name='postgres-feature-store',
    )
    if topics.empty:
        return pd.DataFrame(columns=['workspace_id', 'channel', 'topic_id', 'top_words'])

    topics = topics.rename(columns={'top_words': 'top_words'})
    topics['workspace_id'] = workspace_id
    return topics[['workspace_id', 'channel', 'topic_id', 'top_words']]


def build_daily_sentiment_features(df, workspace_id='default_workspace'):
    """Aggregate daily sentiment trend features."""
    enriched = add_days_since_start(df)
    enriched['sentiment_score'] = enriched['text'].fillna('').astype(str).apply(score_text)
    daily = enriched.groupby('days_since_start').agg(
        sentiment=('sentiment_score', 'mean'),
        message_count=('msg_id', 'count'),
    ).reset_index()
    daily['workspace_id'] = workspace_id
    return daily


def build_time_gap_features(df, workspace_id='default_workspace'):
    """Summarize consecutive event time gaps from Task 2 analysis."""
    gap_map = {
        'consecutive_messages': 'message',
        'consecutive_replies': 'reply',
        'consecutive_reactions': 'reaction',
        'consecutive_events': 'all_events',
    }
    histograms = get_time_gap_histograms(df)
    rows = []
    for key, event_type in gap_map.items():
        gaps = histograms[key]
        rows.append({
            'workspace_id': workspace_id,
            'event_type': event_type,
            'median_gap_seconds': float(gaps.median()) if not gaps.empty else None,
            'mean_gap_seconds': float(gaps.mean()) if not gaps.empty else None,
            'p95_gap_seconds': float(gaps.quantile(0.95)) if not gaps.empty else None,
            'sample_size': int(len(gaps)),
        })
    return pd.DataFrame(rows)


def build_all_features(df, users, workspace_id='default_workspace', include_topics=True):
    """
    Build every PostgreSQL feature table from Tasks 1 and 2.

    Returns:
        Dictionary mapping table name to DataFrame.
    """
    features = {
        'user_activity_features': build_user_activity_features(df, users, workspace_id),
        'channel_activity_features': build_channel_activity_features(df, workspace_id),
        'message_features': build_message_features(df, workspace_id),
        'daily_sentiment_features': build_daily_sentiment_features(df, workspace_id),
        'time_gap_features': build_time_gap_features(df, workspace_id),
    }
    if include_topics:
        features['channel_topic_features'] = build_channel_topic_features(df, workspace_id)
    else:
        features['channel_topic_features'] = pd.DataFrame(
            columns=['workspace_id', 'channel', 'topic_id', 'top_words']
        )
    return features
