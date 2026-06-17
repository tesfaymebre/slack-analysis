"""Unit tests for SlackDataLoader."""

import os

import pytest

from src.loader import MESSAGE_COLUMNS, SlackDataLoader

DATA_PATH = os.path.join('data', 'anonymized')
HAS_DATA = os.path.isdir(DATA_PATH)


@pytest.fixture
def loader():
    """Create a SlackDataLoader pointed at the local dataset."""
    return SlackDataLoader(DATA_PATH)


@pytest.mark.skipif(not HAS_DATA, reason='Slack data is not available locally')
def test_get_channel_messages_columns(loader):
    """Channel messages should contain the expected parsed columns."""
    df = loader.get_channel_messages('random')
    for column in MESSAGE_COLUMNS:
        assert column in df.columns


@pytest.mark.skipif(not HAS_DATA, reason='Slack data is not available locally')
def test_get_all_messages_includes_multiple_channels(loader):
    """All-messages loader should combine more than one channel."""
    df = loader.get_all_messages()
    assert not df.empty
    assert df['channel'].nunique() > 1


@pytest.mark.skipif(not HAS_DATA, reason='Slack data is not available locally')
def test_get_user_map_returns_bidirectional_lookup(loader):
    """User map should translate ids to names and back."""
    id_to_name, name_to_id = loader.get_user_map()
    assert id_to_name
    sample_id = next(iter(id_to_name))
    sample_name = id_to_name[sample_id]
    assert name_to_id[sample_name] == sample_id
