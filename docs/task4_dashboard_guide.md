# Task 4: Dashboard Guide

## What Task 4 teaches

Task 4 connects everything from earlier tasks into **something people can use**:

| Layer | Technology | Role |
|-------|------------|------|
| Analytics UI | **Streamlit** | Main dashboard for stakeholders |
| API | **FastAPI** | Python backend for the React demo |
| Frontend | **React** | Shows fullstack: UI + API + databases |
| SQL data | **PostgreSQL** | Feature tables from Task 3 |
| NoSQL data | **MongoDB** | Raw messages from Task 3 |

```text
Notebooks (Tasks 1–2) → Features → PostgreSQL/MongoDB (Task 3) → Dashboard (Task 4)
```

## Run the Streamlit dashboard

```bash
make db-up          # if not already running
make db-load        # if features not loaded
make dashboard
```

Open: http://localhost:8501

### Pages

1. **Overview** — KPIs + busiest channels
2. **Community EDA** — Task 1 user/channel charts
3. **ML Insights** — sentiment, labels, topics, time gaps

## Run the React fullstack demo

Terminal 1 — API:

```bash
make api
```

Terminal 2 — React:

```bash
cd frontend && npm install && npm run dev
```

Open: http://localhost:5173

## Code map

| Path | Purpose |
|------|---------|
| `dashboard/Home.py` | Streamlit entry + welcome |
| `dashboard/pages/` | Multi-page Streamlit views |
| `src/dashboard/queries.py` | Shared data access (SQL + Mongo) |
| `src/api/main.py` | FastAPI REST endpoints |
| `frontend/src/App.jsx` | React UI |
| `docs/dashboard_wireframe.md` | Wireframe for Figma |

## Task checklist

- [x] Wireframe documented
- [x] Streamlit dashboard (Task 1 & 2 results)
- [x] React app + Python API + SQL + NoSQL

## Suggested commit

```bash
git add dashboard src/dashboard src/api frontend docs/dashboard_wireframe.md docs/task4_dashboard_guide.md requirements.txt Makefile tests/test_dashboard.py .gitignore
git commit -m "feat: add Streamlit dashboard and React fullstack demo for Task 4"
git push -u origin task-4
```
