"""Connection settings for dashboard queries."""

import os

POSTGRES_DSN = os.environ.get(
    'POSTGRES_DSN',
    'postgresql://slack:slack@localhost:5433/slack_features',
)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB = os.environ.get('MONGO_DB', 'slack_analysis')
