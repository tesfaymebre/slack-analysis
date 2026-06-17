"""Tests for time-gap analysis."""

import pandas as pd

from src.analysis.time_gaps import build_event_timeline, get_time_gap_histograms


def test_build_event_timeline_creates_message_events():
    df = pd.DataFrame([
        {
            'channel': 'random',
            'user': 'U1',
            'msg_id': 'm1',
            'ts': '1000.0',
            'replies_meta': None,
            'reactions': None,
        },
        {
            'channel': 'random',
            'user': 'U2',
            'msg_id': 'm2',
            'ts': '1010.0',
            'replies_meta': [{'user': 'U3', 'ts': '1015.0'}],
            'reactions': [{'name': 'thumbsup', 'count': 1, 'users': ['U4']}],
        },
    ])

    timeline = build_event_timeline(df)
    assert not timeline.empty
    assert set(timeline['event_type']) >= {'message', 'reply', 'reaction'}


def test_get_time_gap_histograms_returns_four_series():
    df = pd.DataFrame([
        {'channel': 'random', 'user': 'U1', 'msg_id': 'm1', 'ts': '1000.0',
         'replies_meta': None, 'reactions': None},
        {'channel': 'random', 'user': 'U2', 'msg_id': 'm2', 'ts': '1060.0',
         'replies_meta': None, 'reactions': None},
    ])

    gaps = get_time_gap_histograms(df)
    assert set(gaps.keys()) == {
        'consecutive_messages',
        'consecutive_replies',
        'consecutive_reactions',
        'consecutive_events',
    }
    assert len(gaps['consecutive_messages']) == 1
