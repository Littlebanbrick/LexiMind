# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

LexiMind is a local web app for TOEFL learners. Users type **strict command-prefixed inputs** (e.g. `$ abandon`, `$$ take part in`, `$$$ essay text`, `daily-reading`, `> question`); the backend parses the command, rejects anything that doesn't match a pattern, calls DeepSeek-V3 (via SiliconCloud), logs the result to SQLite, and returns it. The command system and fixed prompt templates are the whole point — they keep token usage low and outputs predictable.

## Repository layout — there are two parallel trees

This is the most important thing to understand before editing anything:

- **`LexiMind_development/`** — the Docker-based development tree. Backend is API-only (sits behind nginx, which serves the frontend). Adds `Dockerfile`, `docker-compose.yml`, `nginx/`.
- **`Distribution/`** — the end-user tree (no Docker). `backend/app.py` here *also serves the static frontend* and has extra routes (`/`, `/<path:filename>`, `/favicon.ico`). It also ships `run.py` (launcher) and `uninstall.py`.

The two `backend/app.py` files **diverge intentionally**: the dev one has no static-serving routes. `README.md` claims the core code is "identical across all distribution folders" — that is not accurate for `app.py`.

`sync.py` copies `backend/` and `frontend/` from `LexiMind_development/` → `Distribution/`, but it **excludes `app.py`** (and `.env`, `*.db`, `__pycache__`, Docker files). So `app.py` is hand-maintained per tree and **will not be propagated by sync**. If you change backend logic, edit it in `LexiMind_development/backend/` (and any shared modules like `command_parser.py`, `llm_client.py`, `database.py`, `config.py`), then run `sync.py`. If you change `app.py` itself, you must edit **both** copies.

> Known snag: `sync.py` hardcodes `DEV_DIR = "leximind_development"` (lowercase) but the real folder is `LexiMind_development`. Works on case-insensitive FSes (Windows/macOS); fails on Linux.

## Commands

```bash
# End-user run (Distribution) — creates venv, installs deps, prompts for API key, starts server, opens browser
cd Distribution && python run.py          # serves at http://127.0.0.1:5000

# Dev run with Docker (nginx :80 -> backend :5000)
cd LexiMind_development && docker compose up --build

# Dev backend only (no frontend serving — use only behind nginx or for API testing)
cd LexiMind_development/backend && python app.py

# Install backend deps into an existing venv
pip install -r LexiMind_development/backend/requirements.txt

# Propagate shared backend/frontend code from dev tree -> Distribution
python sync.py

# Uninstall user data (venv/, *.db, backend/.env) from Distribution
cd Distribution && python uninstall.py
```

There is **no test suite, linter, or formatter configured**. The only runnable check is `command_parser.py`'s embedded `__main__` block: `python backend/command_parser.py` prints parse results for a list of sample inputs.

## Backend request flow

`app.py` → `command_parser.parse_command()` → `llm_client.query_llm()` → `database` logging → JSON response. Single endpoint `POST /api/query` takes `{"input": "..."}`; aux endpoints `GET /api/history`, `GET /api/stats/words`, `GET /health`.

- **`command_parser.py`** — pure string/prefix matching with `shlex.split` for `$cmp`. Order of prefix checks matters (`$$$` before `$$cn` before `$$` before `$cn` before `$cmp` before `$`). Returns `{'type': ..., 'payload': ...}` (or `'words'` for CMP), or `None` for invalid.
- **`llm_client.py`** — one hardcoded prompt template per command type, all routed through `_call_deepseek()`. Model/url/key come from `config` (env). `DAILY_READING` returns early (skips the shared "no follow-up" suffix).
- **`config.py`** — `Config` reads env (with `.env` via `python-dotenv`). Validates `DEEPSEEK_API_KEY` at import time but only *prints* on failure (doesn't raise), so the app starts without a key and 503s on first LLM call.
- **`database.py`** — SQLite with three tables (`words`, `history`, `daily_articles`), created via `init_db()` on import. ⚠️ `insert_history()` is inconsistent with the rest of the module (see known issues).

## Configuration

Env vars (see `.env.example` and `backend/.env`): `DEEPSEEK_API_KEY`, `DEEPSEEK_API_URL`, `DEEPSEEK_MODEL`, `GEMINI_API_KEY`, `FLASK_HOST` (default `127.0.0.1`; set `0.0.0.0` only behind nginx/Docker), `FLASK_PORT`, `FLASK_ENV` (default `production`), `DATABASE_PATH`, `MAX_HISTORY_RECORDS`, `RATE_LIMIT_PER_IP`, `MAX_INPUT_LENGTH`, `LOG_LEVEL`. `.env` is gitignored; only `.env.example` is tracked.

## Architecture notes & gotchas

- **`config.validate()` is called explicitly in `app.py` at import** (not at `config.py` import time), so importing `config`/`database` for unit tests does not crash when no key is set. The app will refuse to start without `DEEPSEEK_API_KEY`.
- **`database.py`** is the single owner of the SQLite connection (`get_db_connection()`). All table functions go through it and honor `config.DATABASE_PATH`. `insert_history()` writes to the `created_at` column (matches the schema) and prunes to `MAX_HISTORY_RECORDS`.
- **`daily-reading` dedups per local day**: `get_today_article()` compares against *local* today, and `insert_daily_article()` stores an explicit local timestamp — do NOT switch the `generated_at` column back to `DEFAULT CURRENT_TIMESTAMP`/`CURRENT_DATE`, those are UTC and will cause the dedup to miss near midnight / in UTC+ zones.
- **`command_parser` uses word boundaries** (`_word_boundary`) for `$`/`$$`/`$cn`/`$$cn`/`$cmp`. If you add a new `$`-prefixed command, it must also use a boundary check or it will shadow/be shadowed.
- **Rate limiting** counts only requests that actually reach the LLM (post-parse). Invalid/over-length inputs do not consume the per-IP quota.
- **`app.py` is excluded from `sync.py`** and diverges between trees (dev = API-only; Distribution = also serves static frontend + ships `run.py`/`uninstall.py`). Edit both copies by hand for changes to `app.py`; run `python sync.py` for shared modules.
- **No test suite.** Verification is via `command_parser.py`'s `__main__` block (`python backend/command_parser.py`) and ad-hoc Flask test-client scripts.
