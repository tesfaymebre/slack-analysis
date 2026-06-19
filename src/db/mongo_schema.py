"""MongoDB collection names and index definitions for Slack data."""

WORKSPACES = 'workspaces'
USERS = 'users'
CHANNELS = 'channels'
MESSAGES = 'messages'
THREAD_REPLIES = 'thread_replies'
REACTIONS = 'reactions'

COLLECTIONS = (
    WORKSPACES,
    USERS,
    CHANNELS,
    MESSAGES,
    THREAD_REPLIES,
    REACTIONS,
)

INDEX_SPECS = {
    WORKSPACES: [
        ('workspace_id', {'unique': True}),
    ],
    USERS: [
        ([('workspace_id', 1), ('user_id', 1)], {'unique': True}),
        ('user_id', {}),
    ],
    CHANNELS: [
        ([('workspace_id', 1), ('channel_id', 1)], {'unique': True}),
        ('name', {}),
    ],
    MESSAGES: [
        ([('workspace_id', 1), ('channel_id', 1), ('ts', 1)], {'unique': True}),
        ('user_id', {}),
        ('export_date', {}),
    ],
    THREAD_REPLIES: [
        ([('workspace_id', 1), ('channel_id', 1), ('ts', 1)], {'unique': True}),
        ('thread_ts', {}),
        ('user_id', {}),
    ],
    REACTIONS: [
        ([('workspace_id', 1), ('channel_id', 1), ('message_ts', 1), ('emoji', 1), ('user_id', 1)], {'unique': True}),
        ('message_ts', {}),
    ],
}


def ensure_indexes(db) -> None:
    """Create indexes that speed up common Slack analytics queries."""
    for collection_name, specs in INDEX_SPECS.items():
        collection = db[collection_name]
        for spec in specs:
            if isinstance(spec[0], list):
                keys, options = spec
            else:
                keys, options = [(spec[0], 1)], spec[1]
            collection.create_index(keys, **options)
