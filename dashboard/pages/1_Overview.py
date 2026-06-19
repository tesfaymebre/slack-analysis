"""Overview KPIs from PostgreSQL and MongoDB."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import path_setup  # noqa: F401

import streamlit as st

from src.dashboard.queries import get_mongo_overview, get_overview_metrics, load_feature_store

st.header('Overview')
st.caption('Workspace-wide KPIs from the feature store and message archive.')

try:
    features = load_feature_store()
    metrics = get_overview_metrics(features)
    mongo_stats = get_mongo_overview()
except Exception as error:
    st.error(f'Could not connect to databases: {error}')
    st.stop()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric('Channels', metrics['channel_count'])
col2.metric('Active users', metrics['user_count'])
col3.metric('Indexed messages', metrics['message_count'])
col4.metric('Replies', metrics['total_replies'])
col5.metric('Reactions', metrics['total_reactions'])
col6.metric('Avg sentiment', f"{metrics['avg_sentiment']:.2f}")

st.subheader('Message archive (MongoDB)')
mongo_col1, mongo_col2, mongo_col3, mongo_col4, mongo_col5 = st.columns(5)
mongo_col1.metric('Messages', mongo_stats['messages'])
mongo_col2.metric('Thread replies', mongo_stats['thread_replies'])
mongo_col3.metric('Reactions', mongo_stats['reactions'])
mongo_col4.metric('Users', mongo_stats['users'])
mongo_col5.metric('Channels', mongo_stats['channels'])

st.subheader('Busiest channels')
channels = features['channel_activity_features'].sort_values('message_count', ascending=False)
st.dataframe(
    channels[['channel', 'message_count', 'reply_total', 'reaction_total', 'engagement_total']],
    use_container_width=True,
    hide_index=True,
)
