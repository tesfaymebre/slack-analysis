"""CLI for loading Slack data into MongoDB and PostgreSQL."""

import argparse
import os

import psycopg2

from src.db.features import build_all_features
from src.db.mongo_loader import load_slack_export_to_mongo
from src.db.postgres_loader import load_features_to_postgres
from src.loader import SlackDataLoader


def parse_args():
    """Parse database loading CLI arguments."""
    parser = argparse.ArgumentParser(description='Load Slack data into MongoDB and PostgreSQL')
    parser.add_argument(
        '--data-path',
        default=os.environ.get('SLACK_DATA_PATH', 'data/anonymized'),
        help='Path to anonymized Slack export folder',
    )
    parser.add_argument(
        '--mongo-uri',
        default=os.environ.get('MONGO_URI', 'mongodb://localhost:27017'),
        help='MongoDB connection URI',
    )
    parser.add_argument(
        '--mongo-db',
        default=os.environ.get('MONGO_DB', 'slack_analysis'),
        help='MongoDB database name',
    )
    parser.add_argument(
        '--postgres-dsn',
        default=os.environ.get(
            'POSTGRES_DSN',
            'postgresql://slack:slack@localhost:5433/slack_features',
        ),
        help='PostgreSQL connection string',
    )
    parser.add_argument(
        '--skip-mongo',
        action='store_true',
        help='Only load PostgreSQL features',
    )
    parser.add_argument(
        '--skip-postgres',
        action='store_true',
        help='Only load MongoDB raw data',
    )
    parser.add_argument(
        '--skip-topics',
        action='store_true',
        help='Skip slow LDA topic modelling when building PostgreSQL features',
    )
    parser.add_argument(
        '--reset-postgres',
        action='store_true',
        help='Drop and recreate PostgreSQL feature tables before loading',
    )
    return parser.parse_args()


def main():
    """Load raw Slack data to MongoDB and ML features to PostgreSQL."""
    args = parse_args()
    loader = SlackDataLoader(args.data_path)
    df = loader.get_all_messages()

    if not args.skip_mongo:
        mongo_counts = load_slack_export_to_mongo(
            args.data_path,
            mongo_uri=args.mongo_uri,
            db_name=args.mongo_db,
        )
        print('MongoDB load complete:', mongo_counts)

    if not args.skip_postgres:
        workspace_id = 'default_workspace'
        features = build_all_features(
            df,
            loader.users,
            workspace_id=workspace_id,
            include_topics=not args.skip_topics,
        )
        with psycopg2.connect(args.postgres_dsn) as connection:
            postgres_counts = load_features_to_postgres(
                connection,
                features,
                reset=args.reset_postgres,
            )
        print('PostgreSQL load complete:', postgres_counts)


if __name__ == '__main__':
    main()
