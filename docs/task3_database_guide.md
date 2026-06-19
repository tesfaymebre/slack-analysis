# Task 3: Databases Guide

This guide explains the Task 3 database work in this repository.

## The big picture

Task 3 uses **two database types** for two different jobs:

| Database | Type | Role in this project |
|----------|------|----------------------|
| MongoDB | NoSQL (document store) | Store **raw Slack JSON** close to the original export |
| PostgreSQL | SQL (relational) | Store **ML features** for analytics and dashboards |

Think of MongoDB as your **data lake for messages** and PostgreSQL as your **feature store**.

```text
Slack JSON files
      |
      v
MongoDB  ---> messages, replies, reactions (query-friendly collections)
      |
      v
pandas / ML code (Tasks 1 & 2)
      |
      v
PostgreSQL ---> user stats, channel stats, sentiment, topics
```

## Why two databases?

**MongoDB** is good when:
- Documents are nested and semi-structured (Slack messages have blocks, threads, reactions)
- You want flexible schema across workspaces
- You ingest data continuously (streaming-friendly writes)

**PostgreSQL** is good when:
- You need stable columns for ML features
- Dashboards run SQL aggregations (`GROUP BY`, `JOIN`, `AVG`)
- You want constraints and reproducible feature tables

This is a common real-world pattern: raw events in NoSQL, curated features in SQL.

## MongoDB schema

We reverse-engineered Slack export JSON into **six collections**:

1. `workspaces` — supports multiple Slack workspaces later
2. `users` — user profiles from `users.json`
3. `channels` — channel metadata from `channels.json`
4. `messages` — parent messages (one document per message)
5. `thread_replies` — replies stored separately for fast thread queries
6. `reactions` — one document per user reaction

### Why split messages / replies / reactions?

If we nested everything inside one message document:
- Thread-heavy channels would create huge documents
- Reaction queries would require scanning entire message payloads
- Streaming ingestion would constantly rewrite large documents

Separate collections keep writes append-only and queries targeted.

Each document also stores a `raw` field so you keep the original Slack payload.

## PostgreSQL feature store

Tables map directly to Task 1 and Task 2 outputs:

| Table | Source |
|-------|--------|
| `user_activity_features` | EDA user rankings |
| `channel_activity_features` | Channel activity + reply speed |
| `message_features` | Weak labels + sentiment |
| `channel_topic_features` | LDA topics per channel |
| `daily_sentiment_features` | Sentiment trend by day |
| `time_gap_features` | Histogram stats from Task 2 |

Schema diagram: `docs/database_schema.dbml` (paste into [dbdiagram.io](https://dbdiagram.io)).

## How to run it locally

### 1. Start databases

```bash
docker compose up -d
```

This starts:
- MongoDB on `localhost:27017`
- PostgreSQL on `localhost:5433` (`slack` / `slack` / `slack_features`)

### 2. Load data

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.db.cli --data-path data/anonymized
```

Useful flags:
- `--skip-topics` — faster load, skips LDA
- `--skip-mongo` — only PostgreSQL
- `--skip-postgres` — only MongoDB

### 3. Verify in MongoDB

```bash
mongosh
use slack_analysis
db.messages.countDocuments()
db.thread_replies.find().limit(3)
```

### 4. Verify in PostgreSQL

```bash
psql postgresql://slack:slack@localhost:5433/slack_features
\dt
SELECT channel, message_count FROM channel_activity_features ORDER BY message_count DESC LIMIT 5;
```

## Code map

| File | Purpose |
|------|---------|
| `src/db/mongo_schema.py` | Collection names + indexes |
| `src/db/mongo_loader.py` | Load raw JSON into MongoDB |
| `src/db/features.py` | Build feature DataFrames |
| `src/db/postgres_schema.py` | `CREATE TABLE` SQL |
| `src/db/postgres_loader.py` | Upsert features into PostgreSQL |
| `src/db/cli.py` | One command to run the full load |

## Task checklist

- [x] Load raw Slack export into MongoDB
- [x] Design multi-workspace NoSQL schema
- [x] Split interactions into separate collections
- [x] Design PostgreSQL feature-store schema
- [x] Create schema diagram (`docs/database_schema.dbml`)
- [x] Create tables with Python
- [x] Load Task 1 & 2 features into PostgreSQL

## Suggested commit workflow

```bash
git add src/db docs/database_schema.dbml docs/task3_database_guide.md docker-compose.yml requirements.txt Makefile tests/test_db.py
git commit -m "feat: add MongoDB raw store and PostgreSQL feature store for Task 3"
git push -u origin task-3
```

Then open a PR from `task-3` → `main`.
