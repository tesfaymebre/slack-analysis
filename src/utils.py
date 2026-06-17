"""Utility functions for parsing and analyzing Slack messages."""

import datetime
import glob
import json
import os
import re
from collections import Counter

import pandas as pd


def break_combined_weeks(combined_weeks):
    """
    Break combined weeks into separate plus-one and minus-one week lists.

    Args:
        combined_weeks: List of week tuples to combine.

    Returns:
        Tuple of (plus_one_week, minus_one_week) lists.
    """
    plus_one_week = []
    minus_one_week = []

    for week in combined_weeks:
        if week[0] < week[1]:
            plus_one_week.append(week[0])
            minus_one_week.append(week[1])
        else:
            minus_one_week.append(week[0])
            plus_one_week.append(week[1])

    return plus_one_week, minus_one_week


def get_msgs_df_info(df):
    """Return per-user counts for messages, replies, mentions, and links."""
    msgs_count_dict = df['user'].value_counts().to_dict()
    replies_count_dict = dict(
        Counter(user for replies in df['replies'] if replies for user in replies)
    )
    mentions_count_dict = dict(
        Counter(user for mentions in df['mentions'] if mentions for user in mentions)
    )
    links_count_dict = df.groupby('user')['link_count'].sum().to_dict()
    return msgs_count_dict, replies_count_dict, mentions_count_dict, links_count_dict


def _extract_reply_users(replies):
    """Extract user ids from a Slack replies metadata list."""
    if not replies:
        return []
    return [reply['user'] for reply in replies if isinstance(reply, dict) and 'user' in reply]


def _count_reactions(reactions):
    """Count total reactions from a Slack reactions list."""
    if not reactions:
        return 0
    return sum(reaction.get('count', 0) for reaction in reactions)


def get_messages_dict(msgs):
    """Parse a list of Slack message dicts into column lists."""
    msg_list = {
        'msg_id': [],
        'text': [],
        'user': [],
        'mentions': [],
        'emojis': [],
        'reactions': [],
        'replies': [],
        'replies_to': [],
        'ts': [],
        'links': [],
        'link_count': [],
        'reply_count': [],
        'reaction_count': [],
        'replies_meta': [],
    }

    for msg in msgs:
        if 'subtype' in msg:
            continue

        msg_list['msg_id'].append(msg.get('client_msg_id'))
        msg_list['text'].append(msg.get('text', ''))
        msg_list['user'].append(msg.get('user'))
        msg_list['ts'].append(msg.get('ts'))
        msg_list['reactions'].append(msg.get('reactions'))
        msg_list['reply_count'].append(msg.get('reply_count', 0))
        msg_list['reaction_count'].append(_count_reactions(msg.get('reactions')))

        if 'parent_user_id' in msg:
            msg_list['replies_to'].append(msg.get('ts'))
        else:
            msg_list['replies_to'].append(None)

        if 'thread_ts' in msg and 'replies' in msg:
            msg_list['replies'].append(_extract_reply_users(msg['replies']))
            msg_list['replies_meta'].append(msg['replies'])
        else:
            msg_list['replies'].append(None)
            msg_list['replies_meta'].append(None)

        if msg.get('blocks'):
            emoji_list = []
            mention_list = []
            link_count = 0
            links = []

            for blk in msg['blocks']:
                if 'elements' not in blk:
                    continue
                for elm in blk['elements']:
                    if 'elements' not in elm:
                        continue
                    for element in elm['elements']:
                        element_type = element.get('type')
                        if element_type == 'emoji':
                            emoji_list.append(element['name'])
                        elif element_type == 'user':
                            mention_list.append(element['user_id'])
                        elif element_type == 'link':
                            link_count += 1
                            links.append(element['url'])

            msg_list['emojis'].append(emoji_list)
            msg_list['mentions'].append(mention_list)
            msg_list['links'].append(links)
            msg_list['link_count'].append(link_count)
        else:
            msg_list['emojis'].append(None)
            msg_list['mentions'].append(None)
            msg_list['links'].append(None)
            msg_list['link_count'].append(0)

    return msg_list


def from_msg_get_replies(msg):
    """Extract threaded reply metadata from a single message."""
    replies = []
    if 'thread_ts' in msg and 'replies' in msg:
        for reply in msg.get('replies', []):
            reply_copy = dict(reply)
            reply_copy['thread_ts'] = msg['thread_ts']
            reply_copy['message_id'] = msg.get('client_msg_id')
            replies.append(reply_copy)
    return replies


def msgs_to_df(msgs):
    """Convert a list of Slack messages to a DataFrame."""
    return pd.DataFrame(get_messages_dict(msgs))


def process_msgs(msg):
    """Select important columns from a single Slack message."""
    keys = [
        'client_msg_id',
        'type',
        'text',
        'user',
        'ts',
        'team',
        'thread_ts',
        'reply_count',
        'reply_users_count',
    ]
    msg_list = {key: msg[key] for key in keys if key in msg}
    reply_list = from_msg_get_replies(msg)
    return msg_list, reply_list


def get_messages_from_channel(channel_path):
    """Load and parse all JSON message files from a channel directory."""
    json_files = sorted(glob.glob(os.path.join(channel_path, '*.json')))
    frames = []

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            msgs = json.load(f)
        frames.append(pd.DataFrame(get_messages_dict(msgs)))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def convert_2_timestamp(column, data):
    """
    Convert a unix timestamp column to readable timestamps.

    Args:
        column: Column name containing unix timestamps.
        data: DataFrame containing the column.

    Returns:
        List of formatted timestamp strings.
    """
    if column not in data.columns:
        print(f"{column} not in data")
        return []

    timestamps = []
    for time_unix in data[column]:
        if time_unix in (0, None):
            timestamps.append(0)
        else:
            dt = datetime.datetime.fromtimestamp(float(time_unix))
            timestamps.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
    return timestamps


def get_tagged_users(df, text_column='text'):
    """Extract @-mentions from message text."""
    return df[text_column].map(lambda text: re.findall(r'@U\w+', str(text)))


def get_community_participation(path):
    """Count how often each user appears in thread replies for a channel."""
    participation = {}
    json_files = glob.glob(os.path.join(path, '*.json'))

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)

        for msg in messages:
            if 'replies' not in msg:
                continue
            for reply in msg['replies']:
                user_id = reply['user']
                participation[user_id] = participation.get(user_id, 0) + 1

    return participation


def parse_slack_reactions(path, channel):
    """Parse reaction records from all JSON files in a channel path."""
    reaction_name = []
    reaction_count = []
    reaction_users = []
    message_text = []
    user_id = []

    for json_file in glob.glob(os.path.join(path, '*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)

        for msg in messages:
            if 'reactions' not in msg:
                continue
            for reaction in msg['reactions']:
                message_text.append(msg.get('text', ''))
                user_id.append(msg.get('user'))
                reaction_name.append(reaction['name'])
                reaction_count.append(reaction['count'])
                reaction_users.append(','.join(reaction.get('users', [])))

    df_reaction = pd.DataFrame({
        'reaction_name': reaction_name,
        'reaction_count': reaction_count,
        'reaction_users': reaction_users,
        'message': message_text,
        'user_id': user_id,
    })
    df_reaction['channel'] = channel
    return df_reaction


def map_userid_2_realname(users, counts, plot=False):
    """
    Map Slack user ids to real names for a count dictionary.

    Args:
        users: List of Slack user records.
        counts: Dictionary mapping user id to a numeric count.
        plot: Unused here; plotting should happen in notebooks.

    Returns:
        DataFrame with user names and counts sorted descending.
    """
    id_to_name = {user['id']: user.get('real_name', user.get('name')) for user in users}
    mapped = {
        id_to_name[user_id]: value
        for user_id, value in counts.items()
        if user_id in id_to_name
    }
    result = pd.DataFrame({
        'user_name': list(mapped.keys()),
        'count': list(mapped.values()),
    }).sort_values('count', ascending=False)
    return result


def count_replies_by_user(df):
    """Count how many thread replies each user contributed."""
    return Counter(
        user
        for replies in df['replies']
        if isinstance(replies, list)
        for user in replies
    )


def count_mentions_by_user(df):
    """Count how many times each user was mentioned."""
    return Counter(
        user
        for mentions in df['mentions']
        if isinstance(mentions, list)
        for user in mentions
    )


def count_reactions_by_user(df):
    """Count how many reactions each user received on their messages."""
    counts = Counter()
    for reactions in df['reactions']:
        if not isinstance(reactions, list):
            continue
        for reaction in reactions:
            counts[reaction.get('name', 'unknown')] += reaction.get('count', 0)
    return counts


def count_reactions_received_by_user(df):
    """Count reactions received by message authors."""
    counts = Counter()
    for _, row in df.iterrows():
        reactions = row.get('reactions')
        if not isinstance(reactions, list):
            continue
        for reaction in reactions:
            for user in reaction.get('users', []):
                counts[user] += 1
    return counts


def top_and_bottom_users(series, n=10):
    """Return the top and bottom n users from a count series."""
    sorted_series = series.sort_values(ascending=False)
    return sorted_series.head(n), sorted_series.tail(n)


def get_channel_activity(df):
    """Aggregate message, reply, and reaction activity by channel."""
    grouped = df.groupby('channel').agg(
        message_count=('msg_id', 'count'),
        reply_total=('reply_count', 'sum'),
        reaction_total=('reaction_count', 'sum'),
    )
    grouped['engagement_total'] = grouped['reply_total'] + grouped['reaction_total']
    return grouped.sort_values('message_count', ascending=False)


def get_first_reply_delay_seconds(message_ts, replies_metadata):
    """Return seconds between a parent message and its first reply."""
    if not replies_metadata:
        return None

    first_reply_ts = min(float(reply['ts']) for reply in replies_metadata)
    return first_reply_ts - float(message_ts)


def add_reply_timing_columns(df):
    """Add first-reply delay and hour-of-day columns to a message DataFrame."""
    result = df.copy()

    delays = []
    for _, row in result.iterrows():
        replies_meta = row.get('replies_meta')
        if not isinstance(replies_meta, list) or not replies_meta:
            delays.append(None)
            continue
        delays.append(get_first_reply_delay_seconds(row['ts'], replies_meta))

    result['first_reply_delay_sec'] = delays
    result['hour_of_day'] = pd.to_numeric(result['ts'], errors='coerce').apply(
        lambda ts: datetime.datetime.fromtimestamp(float(ts)).hour if pd.notna(ts) else None
    )
    return result


def fraction_replied_within_minutes(df, minutes=5):
    """Return the fraction of threaded messages replied to within N minutes."""
    timed_df = add_reply_timing_columns(df)
    delays = timed_df['first_reply_delay_sec'].dropna()
    if delays.empty:
        return 0.0
    threshold_seconds = minutes * 60
    return (delays <= threshold_seconds).mean()
