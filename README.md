# Birge API

FastAPI backend for Birge — AI-powered demand aggregation.

## Architecture

Current: FastAPI-only backend.

No frontend. No Next.js.

## Setup

```bash
python -m pip install -e ".[dev]"
```

## Run dev server

```bash
uvicorn app.main:app --reload
```

## Run tests

```bash
python -m pytest
```

## Lint

```bash
python -m ruff check .
```

## Type check

```bash
python -m mypy app
```

## Status

This is Phase 2: minimal scaffold.

Only `/health` endpoint is implemented.

Product API endpoints (`/api/intent/parse`, `/api/pools/match`, etc.) are NOT implemented yet.
