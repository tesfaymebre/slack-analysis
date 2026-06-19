# Task 4 Dashboard Wireframe

This document describes the dashboard layout before implementation.
You can recreate it in Figma using these sections as frames.

## Information architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  SIDEBAR                    │  MAIN CONTENT                 │
│  ─────────                  │                               │
│  • Overview                 │  [Page title]                 │
│  • Community EDA            │  [KPI cards row]              │
│  • ML Insights              │  [Charts / tables]            │
│                             │                               │
└─────────────────────────────────────────────────────────────┘
```

## Page 1 — Overview

**Goal:** Answer "how big is this Slack workspace?" in 5 seconds.

| Zone | Widget | Data source |
|------|--------|-------------|
| Header | 6 KPI cards: channels, users, messages, replies, reactions, avg sentiment | PostgreSQL |
| Section 2 | 5 MongoDB count cards | MongoDB |
| Table | Busiest channels sortable table | PostgreSQL `channel_activity_features` |

## Page 2 — Community EDA (Task 1)

**Goal:** Show who is active and which channels drive engagement.

| Zone | Widget | Task 1 question answered |
|------|--------|--------------------------|
| Left chart | Top 10 users by message count | Top users by messages |
| Right chart | Top 10 users by reply count | Top users by replies |
| Scatter | Messages vs engagement by channel | Highest-activity channel plot |
| Bar chart | Reply-within-5-min fraction by channel | Response speed |

## Page 3 — ML Insights (Task 2)

**Goal:** Surface model outputs without re-running notebooks.

| Zone | Widget | Task 2 output |
|------|--------|---------------|
| Line chart | Sentiment over `days_since_start` | Sentiment time series |
| Bar chart | Weak label distribution | Message classification |
| Bar chart | Median time gaps by event type | Time-gap histograms |
| Table + filter | LDA topics per channel | Topic modelling |

## Fullstack React demo (separate from Streamlit)

```text
React (browser)
    │  HTTP fetch /api/*
    ▼
FastAPI (Python)
    ├── PostgreSQL → channel summaries, KPIs
    └── MongoDB    → recent raw messages
```

**React page sections:**
1. KPI cards (postgres + mongo)
2. Channel table (postgres)
3. Recent messages list (mongo)

## Design notes

- **Wide layout** — Streamlit `layout="wide"` for side-by-side charts
- **Progressive disclosure** — channel topic table behind a selectbox
- **Fail gracefully** — show connection errors if `make db-up` was not run
- **Color** — Streamlit default theme for main app; dark theme for React demo

## Figma tip

Create 3 frames (Overview, EDA, ML) plus 1 frame for the React page.
Use auto-layout rows for KPI cards and placeholder rectangles for charts.
