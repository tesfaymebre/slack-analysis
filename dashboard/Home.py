"""Slack Analysis Dashboard — Streamlit entry point."""

import path_setup  # noqa: F401  # adds project root to sys.path

import streamlit as st

st.set_page_config(
    page_title='Slack Analysis Dashboard',
    page_icon='💬',
    layout='wide',
)

st.title('10 Academy Slack Analysis')
st.markdown(
    """
Welcome to the **Slack community analytics dashboard** for Batch 6.

This app surfaces insights from the anonymized workspace export:

- **PostgreSQL** → curated features (engagement stats, sentiment, topics, labels)
- **MongoDB** → raw message archive (messages, replies, reactions)

Use the sidebar to explore **Overview**, **Community EDA**, and **ML Insights**.

For the companion web app, start the API (`make api`) and frontend (`make frontend`).
"""
)

st.info('Make sure databases are running: `make db-up` then `make db-load`')
