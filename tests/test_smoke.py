"""Smoke tests to verify the project package is importable in CI."""

from src.loader import MESSAGE_COLUMNS, SlackDataLoader


def test_import_loader_module():
    from src.loader import SlackDataLoader as LoaderClass

    assert LoaderClass is SlackDataLoader


def test_import_utils_module():
    import src.utils as utils

    assert hasattr(utils, 'msgs_to_df')
    assert hasattr(utils, 'get_messages_dict')


def test_slack_data_loader_has_expected_methods():
    assert hasattr(SlackDataLoader, 'get_users')
    assert hasattr(SlackDataLoader, 'get_channels')
    assert hasattr(SlackDataLoader, 'get_channel_messages')
    assert hasattr(SlackDataLoader, 'get_all_messages')
    assert hasattr(SlackDataLoader, 'get_user_map')


def test_message_columns_include_channel():
    assert 'channel' in MESSAGE_COLUMNS
