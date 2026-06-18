"""Time-gap analysis for Slack events."""

import pandas as pd


def _to_timestamp(ts):
    """Convert Slack ts values to pandas timestamps."""
    return pd.to_datetime(float(ts), unit='s', utc=True)


def build_event_timeline(df):
    """
    Build a unified timeline of messages, replies, and reactions.

    Returns:
        DataFrame with columns: event_type, ts, channel, user.
    """
    events = []

    for _, row in df.iterrows():
        base = {
            'channel': row['channel'],
            'user': row['user'],
            'msg_id': row.get('msg_id'),
        }
        if pd.notna(row.get('ts')):
            events.append({**base, 'event_type': 'message', 'ts': row['ts']})

        replies_meta = row.get('replies_meta')
        if isinstance(replies_meta, list):
            for reply in replies_meta:
                events.append({
                    **base,
                    'event_type': 'reply',
                    'ts': reply['ts'],
                    'user': reply.get('user'),
                })

        reactions = row.get('reactions')
        if isinstance(reactions, list):
            for reaction in reactions:
                for user in reaction.get('users', []):
                    events.append({
                        **base,
                        'event_type': 'reaction',
                        'ts': row['ts'],
                        'user': user,
                        'reaction_name': reaction.get('name'),
                    })

    timeline = pd.DataFrame(events)
    if timeline.empty:
        return timeline

    timeline['timestamp'] = timeline['ts'].apply(_to_timestamp)
    return timeline.sort_values('timestamp').reset_index(drop=True)


def consecutive_time_gaps(timeline, event_type=None):
    """
    Compute consecutive time differences in seconds for an event type.

    Args:
        timeline: Output from build_event_timeline.
        event_type: Optional filter ('message', 'reply', 'reaction').

    Returns:
        Series of time gaps in seconds.
    """
    data = timeline.copy()
    if event_type is not None:
        data = data[data['event_type'] == event_type]

    if len(data) < 2:
        return pd.Series(dtype=float)

    gaps = data['timestamp'].diff().dt.total_seconds().dropna()
    return gaps[gaps >= 0]


def get_time_gap_histograms(df):
    """
    Return time-gap series for messages, replies, reactions, and all events.

    Returns:
        Dictionary mapping event label to gap series in seconds.
    """
    timeline = build_event_timeline(df)
    return {
        'consecutive_messages': consecutive_time_gaps(timeline, 'message'),
        'consecutive_replies': consecutive_time_gaps(timeline, 'reply'),
        'consecutive_reactions': consecutive_time_gaps(timeline, 'reaction'),
        'consecutive_events': consecutive_time_gaps(timeline),
    }
