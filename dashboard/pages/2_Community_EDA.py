"""Community engagement visuals: users, channels, and reply patterns."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import path_setup  # noqa: F401

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.queries import load_feature_store

st.header('Community EDA')
st.caption('Who participates most, which channels are busiest, and how quickly threads get replies.')

try:
    features = load_feature_store()
except Exception as error:
    st.error(f'Could not load features: {error}')
    st.stop()

users = features['user_activity_features']
channels = features['channel_activity_features'].copy()
channels['message_count'] = pd.to_numeric(channels['message_count'], errors='coerce')
channels['engagement_total'] = pd.to_numeric(channels['engagement_total'], errors='coerce')

left, right = st.columns(2)

with left:
    st.subheader('Top 10 users by messages')
    top_users = users.sort_values('message_count', ascending=False).head(10)
    st.bar_chart(top_users.set_index('user_name')['message_count'])

with right:
    st.subheader('Top 10 users by replies sent')
    top_repliers = users.sort_values('reply_count', ascending=False).head(10)
    st.bar_chart(top_repliers.set_index('user_name')['reply_count'])

st.subheader('Channel activity scatter')
st.caption('Hover any dot to see channel name, messages, replies, and reactions.')

if not channels.empty:
    scatter_df = channels.sort_values('message_count', ascending=False).reset_index(drop=True)
    for column in ('reply_total', 'reaction_total'):
        scatter_df[column] = pd.to_numeric(scatter_df[column], errors='coerce')

    tab_all, tab_zoom = st.tabs(['All channels', 'Without busiest channel'])

    def _build_hover_scatter(frame, title):
        """Altair scatter with built-in hover tooltips (works reliably in Streamlit)."""
        return (
            alt.Chart(frame)
            .mark_circle(size=100, opacity=0.85, color='#2563eb')
            .encode(
                x=alt.X('message_count:Q', title='Message count', scale=alt.Scale(zero=True)),
                y=alt.Y('engagement_total:Q', title='Replies + reactions', scale=alt.Scale(zero=True)),
                tooltip=[
                    alt.Tooltip('channel', title='Channel'),
                    alt.Tooltip('message_count', title='Messages', format=','),
                    alt.Tooltip('reply_total', title='Replies', format=','),
                    alt.Tooltip('reaction_total', title='Reactions', format=','),
                    alt.Tooltip('engagement_total', title='Engagement', format=','),
                ],
            )
            .properties(title=title, height=450)
            .interactive()
        )

    with tab_all:
        st.altair_chart(
            _build_hover_scatter(scatter_df, 'All channels — hover a dot for details'),
            use_container_width=True,
        )

    with tab_zoom:
        zoomed = scatter_df.iloc[1:].reset_index(drop=True)
        st.caption(
            f'Excludes **{scatter_df.iloc[0]["channel"]}** '
            f'({int(scatter_df.iloc[0]["message_count"]):,} messages) so the cluster is easier to read.'
        )
        st.altair_chart(
            _build_hover_scatter(zoomed, 'Zoomed cluster — hover a dot for details'),
            use_container_width=True,
        )

    with st.expander('Full channel table'):
        st.dataframe(
            scatter_df[
                ['channel', 'message_count', 'reply_total', 'reaction_total', 'engagement_total']
            ],
            use_container_width=True,
            hide_index=True,
        )

st.subheader('Reply speed by channel')
reply_speed = channels.sort_values('reply_within_5min_fraction', ascending=False)
st.bar_chart(reply_speed.set_index('channel')['reply_within_5min_fraction'])
