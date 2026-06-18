"""Tests for topic modelling helpers."""

import pandas as pd

from src.models.topic_model import build_channel_corpus, get_top_topics_by_channel, train_channel_lda


def test_train_channel_lda_skips_empty_documents():
    """LDA should not crash when documents have no usable tokens."""
    lda_model, dictionary = train_channel_lda([[], [], [], [], []], num_topics=10)
    assert lda_model is None
    assert dictionary is None


def test_train_channel_lda_handles_repetitive_tiny_channel():
    """Small repetitive channels should train or skip without raising."""
    documents = [['thanks', 'team'] for _ in range(5)]
    lda_model, dictionary = train_channel_lda(documents, num_topics=10)
    assert lda_model is None or lda_model.num_topics >= 2
    assert dictionary is None or len(dictionary) > 0

def test_get_top_topics_by_channel_runs_on_sample_frame():
    """Topic extraction should skip channels that cannot be modelled."""
    df = pd.DataFrame({
        'channel': ['busy'] * 8 + ['tiny'] * 5,
        'text': [
            'python machine learning model training data pipeline',
            'docker kubernetes deployment server api error',
            'pandas numpy dataframe analysis visualization',
            'sql database postgres query optimization',
            'git github pull request code review merge',
            'pytest unit test coverage continuous integration',
            'aws terraform infrastructure cloud deployment',
            'kafka streaming pipeline event processing',
            'ok',
            'thanks',
            'yes',
            'no',
            'hi',
        ],
    })

    result = get_top_topics_by_channel(df, num_topics=3, experiment_name='test-topic-modelling')

    assert not result.empty
    assert 'busy' in set(result['channel'])
    assert 'tiny' not in set(result['channel'])
    assert result['top_words'].str.len().gt(0).all()
