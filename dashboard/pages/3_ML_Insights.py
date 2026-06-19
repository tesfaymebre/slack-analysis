"""ML-powered Slack insights: sentiment, labels, topics, and event timing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import path_setup  # noqa: F401

import streamlit as st

from src.dashboard.queries import load_feature_store

st.header('ML Insights')
st.caption('Classification, sentiment trends, channel topics, and conversation pacing across the programme.')

try:
    features = load_feature_store()
except Exception as error:
    st.error(f'Could not load features: {error}')
    st.stop()

messages = features['message_features']
sentiment = features['daily_sentiment_features']
topics = features['channel_topic_features']
gaps = features['time_gap_features']

st.subheader('Daily sentiment trend')
if not sentiment.empty:
    chart_data = sentiment.sort_values('days_since_start').set_index('days_since_start')
    st.line_chart(chart_data['sentiment'])
    st.caption('Average message sentiment over days since the programme started.')
else:
    st.warning('No sentiment data loaded yet. Run `make db-load` with topics enabled.')

st.subheader('Message label distribution')
if not messages.empty:
    label_counts = messages['weak_label'].value_counts()
    st.bar_chart(label_counts)
else:
    st.warning('No message features found.')

left, right = st.columns(2)

with left:
    st.subheader('Time between events (median seconds)')
    if not gaps.empty:
        gap_view = gaps.set_index('event_type')[['median_gap_seconds']]
        st.bar_chart(gap_view)
    else:
        st.info('No time-gap stats yet.')

with right:
    st.subheader('Channel topics (LDA)')
    if topics.empty:
        st.info('No topic features. Re-run `make db-load` without `--skip-topics`.')
    else:
        selected_channel = st.selectbox(
            'Choose channel',
            sorted(topics['channel'].unique()),
        )
        channel_topics = topics.loc[topics['channel'] == selected_channel].copy()
        channel_topics = channel_topics.sort_values(by='topic_id')
        st.dataframe(channel_topics[['topic_id', 'top_words']], hide_index=True, use_container_width=True)
