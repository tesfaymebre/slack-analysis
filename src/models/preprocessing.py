"""Text preprocessing helpers for ML models."""

import re


def clean_text(text):
    """Normalize Slack message text for modelling."""
    if not isinstance(text, str):
        return ''
    text = re.sub(r'<@[A-Z0-9]+>', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s\?\.\,\!\']', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().lower()


def prepare_text_frame(df, text_column='text'):
    """Return a copy of df with a cleaned text column."""
    result = df.copy()
    result['clean_text'] = result[text_column].apply(clean_text)
    result = result[result['clean_text'].str.len() > 0]
    return result
