"""Tests for dashboard helpers and API."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.queries import get_overview_metrics


def test_get_overview_metrics_from_sample_frames():
    """Overview KPIs should aggregate feature tables."""
    features = {
        'channel_activity_features': pd.DataFrame({
            'channel': ['a', 'b'],
            'reply_total': [10, 5],
            'reaction_total': [3, 2],
        }),
        'user_activity_features': pd.DataFrame({'user_id': ['U1', 'U2']}),
        'message_features': pd.DataFrame({'sentiment_score': [0.2, 0.4]}),
    }

    metrics = get_overview_metrics(features)

    assert metrics['channel_count'] == 2
    assert metrics['user_count'] == 2
    assert metrics['message_count'] == 2
    assert metrics['total_replies'] == 15
    assert metrics['avg_sentiment'] == pytest.approx(0.3)


def test_health_endpoint():
    """API health check should return ok."""
    client = TestClient(app)
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
