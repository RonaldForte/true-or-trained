# Developer Guide

How to set up and run True or Trained locally.

## Prerequisites

- **Python 3.12** (matches production on Render — see `backend/.python-version`)
- **Node.js 20+** (for PM2, and later the frontend)
- **PM2**: `npm install -g pm2`

## First-time setup

### Backend

From the repo root:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
cd ..
```

This creates an isolated Python environment in `backend/.venv` (gitignored) and installs the pinned dependencies into it.

## Running locally

All commands run from the **repo root**. No need to activate the venv — PM2 uses the venv's Python directly.

```powershell
pm2 start ecosystem.config.js
```

Then open:

- http://localhost:8000/docs — interactive API docs (Swagger UI)
- http://localhost:8000/health — health check

Saving any file in `backend/app/` restarts the server automatically.

### PM2 commands

| Command | What it does |
| --- | --- |
| `pm2 start ecosystem.config.js` | Start all services |
| `pm2 ls` | Status table (online / errored, restart count, memory) |
| `pm2 logs backend` | Live log tail (Ctrl+C stops tailing; server keeps running) |
| `pm2 logs backend --lines 30` | Show recent log history |
| `pm2 monit` | Live dashboard |
| `pm2 restart backend` | Manual restart |
| `pm2 stop backend` | Stop the server (also disables auto-reload) |
| `pm2 delete backend` | Remove from PM2 entirely |

> After `pm2 stop`, restart with `pm2 start ecosystem.config.js`, not `pm2 start backend` — starting by name leaves file watching off.

### Log files

Written to `logs/` (gitignored):

- `logs/backend.out.log` — request logs
- `logs/backend.err.log` — startup messages and errors (uvicorn writes its info logs to stderr, so not everything here is an error)

## Installing new Python packages

Activate the venv first so packages land in it, not your global Python:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install <package>
```

Then add the package with its exact version to `backend/requirements.txt` (check the version with `pip show <package>`).

> If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope Process RemoteSigned` first. It only applies to the current terminal session.

## Troubleshooting

**`pm2 ls` shows `errored`**
Check `pm2 logs backend --lines 30`. Most common cause: port 8000 already in use, often by a leftover server process. Find and stop it:

```powershell
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force
```

Then `pm2 delete backend` and `pm2 start ecosystem.config.js`.

## Why PM2 runs `pythonw.exe` (Windows notes)

The config in `ecosystem.config.js` has a few Windows-specific choices:

- **`pythonw.exe`** instead of `python.exe` — a venv's `python.exe` is a launcher that spawns the real interpreter, and that child opens a visible console window. `pythonw` never opens one.
- **PM2 `watch`** instead of `uvicorn --reload` — uvicorn's reload worker can't write to PM2's logs under `pythonw`.
- **`PYTHONDONTWRITEBYTECODE=1`** — stops Python writing `__pycache__` files, which PM2's watcher would otherwise treat as a change and restart twice per save.
- **`PYTHONUNBUFFERED=1`** — makes logs appear immediately instead of in delayed bursts.

## Production

PM2 is for local development only. In production, Render runs:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

and provides its own logs. See `docs/adr/0002-hosting-platform.md`.
