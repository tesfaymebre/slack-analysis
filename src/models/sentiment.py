"""Sentiment analysis over Slack messages."""

import mlflow
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer

from src.models.preprocessing import clean_text

_analyzer = None


def get_sentiment_analyzer():
    """Return a cached VADER sentiment analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def score_text(text):
    """Return compound sentiment score for a text string."""
    cleaned = clean_text(text)
    if not cleaned:
        return 0.0
    return get_sentiment_analyzer().polarity_scores(cleaned)['compound']


def add_days_since_start(df, ts_column='ts'):
    """Add day index relative to the earliest message timestamp."""
    result = df.copy()
    timestamps = pd.to_datetime(result[ts_column].astype(float), unit='s', utc=True)
    start_date = timestamps.min().normalize()
    result['message_date'] = timestamps.dt.normalize()
    result['days_since_start'] = (result['message_date'] - start_date).dt.days
    return result


def daily_sentiment_trend(df, experiment_name='slack-sentiment'):
    """
    Aggregate daily message sentiment and log results with MLflow.

    Returns:
        DataFrame with days_since_start, sentiment, and message_count.
    """
    enriched = add_days_since_start(df)
    enriched['sentiment'] = enriched['text'].fillna('').astype(str).apply(score_text)

    daily = enriched.groupby('days_since_start').agg(
        sentiment=('sentiment', 'mean'),
        message_count=('msg_id', 'count'),
        combined_text=('text', lambda texts: ' '.join(texts.fillna('').astype(str))),
    ).reset_index()

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name='daily_sentiment'):
        mlflow.log_metric('days_covered', len(daily))
        mlflow.log_metric('avg_sentiment', daily['sentiment'].mean())
        mlflow.log_text(daily.to_csv(index=False), 'daily_sentiment.csv')

    return daily
