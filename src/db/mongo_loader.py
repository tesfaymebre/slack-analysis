"""Load raw Slack export JSON into a normalized MongoDB schema."""

import glob
import json
import os
from datetime import datetime, timezone

from pymongo import MongoClient

from src.db import mongo_schema as schema
from src.loader import SlackDataLoader


def _export_date_from_filename(filename):
    """Parse YYYY-MM-DD from a daily Slack export filename."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    try:
        return datetime.strptime(stem, '%Y-%m-%d').date().isoformat()
    except ValueError:
        return None


def _workspace_id_from_export(loader):
    """Infer a workspace id from channel metadata or fall back to folder name."""
    channels = loader.get_channels()
    if channels:
        return channels[0].get('context_team_id') or channels[0].get('id', 'default_workspace')
    return 'default_workspace'


def _normalize_user(workspace_id, user):
    """Map a Slack user record to a MongoDB document."""
    profile = user.get('profile', {})
    return {
        'workspace_id': workspace_id,
        'user_id': user['id'],
        'name': user.get('name'),
        'real_name': user.get('real_name') or profile.get('real_name'),
        'display_name': profile.get('display_name'),
        'email': profile.get('email'),
        'is_bot': user.get('is_bot', False),
        'profile': profile,
        'raw': user,
    }


def _normalize_channel(workspace_id, channel):
    """Map a Slack channel record to a MongoDB document."""
    return {
        'workspace_id': workspace_id,
        'channel_id': channel['id'],
        'name': channel.get('name'),
        'topic': channel.get('topic', {}).get('value'),
        'purpose': channel.get('purpose', {}).get('value'),
        'num_members': channel.get('num_members'),
        'is_archived': channel.get('is_archived', False),
        'raw': channel,
    }


def _message_document(workspace_id, channel_id, channel_name, export_date, source_file, msg):
    """Build a message document while keeping the original Slack payload."""
    return {
        'workspace_id': workspace_id,
        'channel_id': channel_id,
        'channel_name': channel_name,
        'export_date': export_date,
        'source_file': source_file,
        'msg_id': msg.get('client_msg_id'),
        'type': msg.get('type', 'message'),
        'subtype': msg.get('subtype'),
        'user_id': msg.get('user'),
        'text': msg.get('text', ''),
        'ts': msg.get('ts'),
        'thread_ts': msg.get('thread_ts'),
        'reply_count': msg.get('reply_count', 0),
        'team': msg.get('team'),
        'blocks': msg.get('blocks'),
        'attachments': msg.get('attachments'),
        'user_profile': msg.get('user_profile'),
        'raw': msg,
    }


def _reply_documents(workspace_id, channel_id, channel_name, parent_msg, replies):
    """Split thread replies into their own collection for efficient lookups."""
    documents = []
    for reply in replies:
        if not isinstance(reply, dict) or 'ts' not in reply:
            continue
        documents.append({
            'workspace_id': workspace_id,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'parent_ts': parent_msg.get('ts'),
            'thread_ts': parent_msg.get('thread_ts') or parent_msg.get('ts'),
            'message_id': parent_msg.get('client_msg_id'),
            'user_id': reply.get('user'),
            'text': reply.get('text', ''),
            'ts': reply['ts'],
            'raw': reply,
        })
    return documents


def _reaction_documents(workspace_id, channel_id, channel_name, msg):
    """Store one document per user reaction instead of nesting under messages."""
    documents = []
    for reaction in msg.get('reactions', []) or []:
        emoji = reaction.get('name')
        for user_id in reaction.get('users', []):
            documents.append({
                'workspace_id': workspace_id,
                'channel_id': channel_id,
                'channel_name': channel_name,
                'message_ts': msg.get('ts'),
                'message_id': msg.get('client_msg_id'),
                'emoji': emoji,
                'user_id': user_id,
                'reaction_count': reaction.get('count', 1),
            })
    return documents


def _upsert_documents(collection, documents, key_fields):
    """Upsert documents one by one so tests work with mongomock too."""
    if not documents:
        return 0

    count = 0
    for document in documents:
        filter_doc = {field: document[field] for field in key_fields}
        collection.update_one(filter_doc, {'$set': document}, upsert=True)
        count += 1
    return count


def load_metadata(db, loader, workspace_id):
    """
    Upsert workspace, user, and channel metadata.

    Returns:
        Mapping of channel folder name to Slack channel id.
    """
    channels = loader.get_channels()
    team_name = channels[0].get('name', 'slack-workspace') if channels else 'slack-workspace'

    db[schema.WORKSPACES].update_one(
        {'workspace_id': workspace_id},
        {'$set': {
            'workspace_id': workspace_id,
            'name': team_name,
            'loaded_at': datetime.now(timezone.utc),
        }},
        upsert=True,
    )

    user_docs = [_normalize_user(workspace_id, user) for user in loader.users]
    _upsert_documents(db[schema.USERS], user_docs, ['workspace_id', 'user_id'])

    channel_name_to_id = {}
    channel_docs = []
    for channel in channels:
        doc = _normalize_channel(workspace_id, channel)
        channel_name_to_id[channel['name']] = channel['id']
        channel_docs.append(doc)
    _upsert_documents(db[schema.CHANNELS], channel_docs, ['workspace_id', 'channel_id'])

    return channel_name_to_id


def load_channel_exports(db, loader, workspace_id, channel_name_to_id):
    """Load daily JSON exports for every channel folder."""
    message_docs = []
    reply_docs = []
    reaction_docs = []

    for channel_name in loader.list_channel_names():
        channel_id = channel_name_to_id.get(channel_name, channel_name)
        channel_path = os.path.join(loader.path, channel_name)
        json_files = sorted(glob.glob(os.path.join(channel_path, '*.json')))

        for json_file in json_files:
            export_date = _export_date_from_filename(json_file)
            with open(json_file, 'r', encoding='utf-8') as handle:
                messages = json.load(handle)

            for msg in messages:
                if msg.get('type') != 'message':
                    continue

                message_doc = _message_document(
                    workspace_id,
                    channel_id,
                    channel_name,
                    export_date,
                    os.path.basename(json_file),
                    msg,
                )
                message_docs.append(message_doc)

                if isinstance(msg.get('replies'), list):
                    reply_docs.extend(
                        _reply_documents(
                            workspace_id, channel_id, channel_name, msg, msg['replies']
                        )
                    )

                reaction_docs.extend(
                    _reaction_documents(workspace_id, channel_id, channel_name, msg)
                )

    counts = {
        'messages': _upsert_documents(
            db[schema.MESSAGES], message_docs, ['workspace_id', 'channel_id', 'ts']
        ),
        'replies': _upsert_documents(
            db[schema.THREAD_REPLIES], reply_docs, ['workspace_id', 'channel_id', 'ts']
        ),
        'reactions': _upsert_documents(
            db[schema.REACTIONS],
            reaction_docs,
            ['workspace_id', 'channel_id', 'message_ts', 'emoji', 'user_id'],
        ),
    }
    return counts


def load_slack_export_to_mongo(
    data_path,
    mongo_uri='mongodb://localhost:27017',
    db_name='slack_analysis',
):
    """
    Load Slack export data into MongoDB.

    Returns:
        Dictionary with workspace_id and document counts per collection.
    """
    loader = SlackDataLoader(data_path)
    workspace_id = _workspace_id_from_export(loader)

    client = MongoClient(mongo_uri)
    db = client[db_name]
    schema.ensure_indexes(db)

    channel_name_to_id = load_metadata(db, loader, workspace_id)
    counts = load_channel_exports(db, loader, workspace_id, channel_name_to_id)

    return {
        'workspace_id': workspace_id,
        'users': db[schema.USERS].count_documents({'workspace_id': workspace_id}),
        'channels': db[schema.CHANNELS].count_documents({'workspace_id': workspace_id}),
        **counts,
    }
