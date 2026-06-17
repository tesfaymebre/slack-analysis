"""Slack exported data loader."""

import argparse
import json
import os

import pandas as pd

from src.utils import get_messages_from_channel

MESSAGE_COLUMNS = [
    'msg_id',
    'text',
    'user',
    'mentions',
    'emojis',
    'reactions',
    'replies',
    'replies_to',
    'ts',
    'links',
    'link_count',
    'reply_count',
    'reaction_count',
    'replies_meta',
    'channel',
]


class SlackDataLoader:
    """Load and parse anonymized Slack export data."""

    def __init__(self, path):
        """
        Initialize the loader.

        Args:
            path: Path to the slack exported data folder.
        """
        self.path = path
        self.channels = self.get_channels()
        self.users = self.get_users()

    def get_users(self):
        """Load all users from users.json."""
        with open(os.path.join(self.path, 'users.json'), 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_channels(self):
        """Load all channels from channels.json."""
        with open(os.path.join(self.path, 'channels.json'), 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_channel_names(self):
        """Return folder names for channels that contain message JSON files."""
        return sorted(
            name
            for name in os.listdir(self.path)
            if os.path.isdir(os.path.join(self.path, name))
        )

    def get_channel_messages(self, channel_name):
        """
        Load all messages from a single channel folder.

        Args:
            channel_name: Name of the channel directory under the data path.

        Returns:
            DataFrame of parsed messages with a channel column.
        """
        channel_path = os.path.join(self.path, channel_name)
        if not os.path.isdir(channel_path):
            raise ValueError(f"Channel folder not found: {channel_name}")

        df = get_messages_from_channel(channel_path)
        df['channel'] = channel_name
        return df

    def get_all_messages(self):
        """Load messages from every channel folder and concatenate them."""
        frames = [
            self.get_channel_messages(channel_name)
            for channel_name in self.list_channel_names()
        ]
        if not frames:
            return pd.DataFrame(columns=MESSAGE_COLUMNS)
        return pd.concat(frames, ignore_index=True)

    def get_user_map(self):
        """
        Build mappings between Slack user ids and display names.

        Returns:
            Tuple of (id_to_name, name_to_id) dictionaries.
        """
        id_to_name = {}
        name_to_id = {}
        for user in self.users:
            id_to_name[user['id']] = user['name']
            name_to_id[user['name']] = user['id']
        return id_to_name, name_to_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Slack history')
    parser.add_argument('--zip', help="Name of a zip file to import")
    parser.parse_args()
