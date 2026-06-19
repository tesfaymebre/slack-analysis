"""REST API exposing PostgreSQL features and MongoDB messages."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.dashboard.queries import (
    get_channel_summaries,
    get_mongo_overview,
    get_overview_metrics,
    get_recent_messages,
    load_feature_store,
)

app = FastAPI(
    title='Slack Analysis API',
    description='Python backend connecting React to PostgreSQL and MongoDB.',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/api/health')
def health_check():
    """Simple health endpoint for the React app."""
    return {'status': 'ok'}


@app.get('/api/overview')
def overview():
    """Return KPI metrics from PostgreSQL and MongoDB."""
    try:
        features = load_feature_store()
        return {
            'postgres': get_overview_metrics(features),
            'mongo': get_mongo_overview(),
        }
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get('/api/channels')
def list_channels():
    """Return channel activity rows from PostgreSQL."""
    try:
        frame = get_channel_summaries()
        return frame.to_dict(orient='records')
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get('/api/messages/recent')
def recent_messages(
    channel: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Return recent raw messages from MongoDB."""
    try:
        return get_recent_messages(channel=channel, limit=limit)
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
