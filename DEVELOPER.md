# Developer Guide

How to set up and run True or Trained locally.

## Prerequisites

- **Python 3.12** (matches production on Render — see `backend/.python-version`)
- **Node.js 24 LTS** (Vite 8 requires 20.19+ or 22.12+)
- **PM2**: `npm install -g pm2`

## First-time setup

### Backend

From the repo root:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
cd ..
```

This creates an isolated Python environment in `backend/.venv` (gitignored) and installs the pinned dependencies into it.

- `requirements.txt` — runtime dependencies (what Render installs in production)
- `requirements-dev.txt` — runtime + dev tools like pytest (includes `requirements.txt` via `-r`)

### Frontend

From the repo root:

```powershell
cd frontend
npm install
cd ..
```

## Running locally

All commands run from the **repo root**. No need to activate the venv — PM2 uses the venv's Python directly.

```powershell
pm2 start ecosystem.config.js
```

This starts both services:

| Service | URL | Reload on save |
| --- | --- | --- |
| `frontend` | http://localhost:5173 — the game | Vite hot-reloads in the browser |
| `backend` | http://localhost:8000/docs — interactive API docs | PM2 restarts on changes in `backend/app/` |
| `images` | http://localhost:8001 — serves `data/build/images` | — |

The backend needs the pairs manifest at `data/build/manifest.json` and the `images` service needs `data/build/images` — build them first (see [Building the image set](#building-the-image-set)). Locally, images come from the `images` service instead of R2.

The backend only accepts browser requests from origins listed in `ALLOWED_ORIGINS` (comma-separated; defaults to `http://localhost:5173`). This is CORS — browsers block a page on one origin from calling an API on another unless the API allows it.

### PM2 commands

| Command | What it does |
| --- | --- |
Replace `<name>` with `backend` or `frontend`, or use `all`.

| Command | What it does |
| --- | --- |
| `pm2 start ecosystem.config.js` | Start all services |
| `pm2 ls` | Status table (online / errored, restart count, memory) |
| `pm2 logs` | Live log tail of everything (Ctrl+C stops tailing; services keep running) |
| `pm2 logs <name> --lines 30` | Show recent log history for one service |
| `pm2 monit` | Live dashboard |
| `pm2 restart <name>` | Manual restart |
| `pm2 stop <name>` | Stop a service (also disables backend auto-reload) |
| `pm2 delete all` | Remove everything from PM2 |

> After `pm2 stop`, restart with `pm2 start ecosystem.config.js`, not `pm2 start backend` — starting by name leaves file watching off.

### Log files

Written to `logs/` (gitignored), one `.out.log` and `.err.log` per service:

- `logs/backend.out.log` — request logs
- `logs/backend.err.log` — startup messages and errors (uvicorn writes its info logs to stderr, so not everything here is an error)
- `logs/frontend.out.log` — Vite dev server output

## Running checks

### Frontend

From `frontend/`:

```powershell
npm run lint     # oxlint
npm run build    # TypeScript type-check + production build into dist/
```

### Backend tests

From `backend/`:

```powershell
.venv\Scripts\python -m pytest        # run all tests
.venv\Scripts\python -m pytest -v     # verbose: list each test
```

Tests live in `backend/tests/` and use FastAPI's `TestClient`, which calls the app in-memory — no server needed, so PM2 doesn't have to be running. Config is in `backend/pyproject.toml`.

### CI

GitHub Actions runs on every pull request and every push to `main` (`.github/workflows/tests.yml`):

- **Backend tests** — pytest
- **Frontend build** — lint, type-check, build

Both checks must pass before a PR can merge into `main`.

## Installing new Python packages

Activate the venv first so packages land in it, not your global Python:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install <package>
```

Then add the package with its exact version to `backend/requirements.txt` — or `requirements-dev.txt` if it's only needed for development/testing (check the version with `pip show <package>`).

> If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope Process RemoteSigned` first. It only applies to the current terminal session.

## Building the image set

The game shows pairs: a real photo and an AI image of the same subject. Pairs come from Defactify / MS COCOAI (AI images generated from MS COCO captions), with each real photo's license looked up in COCO's annotations. `scripts/build_image_set.py` builds them reproducibly and normalizes every image (432×432 WebP, no metadata, random filename) so file properties can't reveal the answer. See `docs/adr/0006-image-dataset.md`.

Source downloads and output live in `data/` (gitignored). From the repo root:

```powershell
# One-time: script environment
py -3.12 -m venv scripts\.venv
scripts\.venv\Scripts\python -m pip install -r scripts\requirements.txt

# One-time: source data (~930 MB)
mkdir data\raw\coco, data\raw\defactify
curl.exe -L -o data\raw\coco\annotations_trainval2017.zip http://images.cocodataset.org/annotations/annotations_trainval2017.zip
curl.exe -L -o data\raw\defactify\validation-00000-of-00002.parquet https://huggingface.co/datasets/Rajarshi-Roy-research/Defactify_Image_Dataset/resolve/main/data/validation-00000-of-00002.parquet
curl.exe -L -o data\raw\defactify\validation-00001-of-00002.parquet https://huggingface.co/datasets/Rajarshi-Roy-research/Defactify_Image_Dataset/resolve/main/data/validation-00001-of-00002.parquet

# Build (~1 min, no further downloads)
scripts\.venv\Scripts\python -I scripts\build_image_set.py --coco-annotations data\raw\coco\annotations_trainval2017.zip --defactify-dir data\raw\defactify --out data\build
```

Output in `data/build/`: `images/*.webp`, `manifest.json` (one entry per pair: caption, generator, real and AI image ids with credits), and `contact_sheet.html` to review every pair side by side in a browser. The same `--seed` always produces identical files.

> `manifest.json` is the answer key — it says which image in each pair is real. Never commit it or upload it to the public bucket.

### Uploading images to R2

Images are served from the `true-or-trained-images` R2 bucket at `https://images.trueortrained.com`. Create an R2 API token with **Object Read & Write** on that bucket only, then in your own terminal:

```powershell
$env:R2_ENDPOINT = "https://<account-id>.r2.cloudflarestorage.com"
$env:R2_ACCESS_KEY_ID = "<access key id>"
$env:R2_SECRET_ACCESS_KEY = "<secret access key>"
scripts\.venv\Scripts\python -I scripts\upload_images.py --images-dir data\build\images
```

Only `images/*.webp` are uploaded, with `Cache-Control: immutable` (filenames are random and never reused). Re-running skips images already in the bucket.

## Troubleshooting

**`pm2 ls` shows `errored`**
Check `pm2 logs <name> --lines 30`. Most common cause: the port (8000 backend, 5173 frontend) is already in use, often by a leftover process. Find and stop it:

```powershell
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force
```

Then `pm2 delete all` and `pm2 start ecosystem.config.js`.

**Frontend shows "Could not load an image"**
The backend isn't reachable or CORS is rejecting the request. Check `pm2 ls` shows `backend` online, and the browser devtools console for a CORS error.

## Why PM2 runs `pythonw.exe` (Windows notes)

The config in `ecosystem.config.js` has a few Windows-specific choices:

- **`pythonw.exe`** instead of `python.exe` — a venv's `python.exe` is a launcher that spawns the real interpreter, and that child opens a visible console window. `pythonw` never opens one.
- **PM2 `watch`** instead of `uvicorn --reload` — uvicorn's reload worker can't write to PM2's logs under `pythonw`.
- **`PYTHONDONTWRITEBYTECODE=1`** — stops Python writing `__pycache__` files, which PM2's watcher would otherwise treat as a change and restart twice per save.
- **`PYTHONUNBUFFERED=1`** — makes logs appear immediately instead of in delayed bursts.

## Deployment

PM2 is for local development only. Both services deploy automatically when `main` changes. See `docs/adr/0002-hosting-platform.md` for why these hosts.

| Service | Host | URL | Config |
| --- | --- | --- | --- |
| Frontend | Cloudflare Workers (static assets) | https://trueortrained.com | `frontend/wrangler.jsonc` + dashboard build settings (below) |
| Backend | Render (free) | https://api.trueortrained.com | `render.yaml` (Render Blueprint) |

### Backend (Render)

Defined in `render.yaml`. Render installs `requirements.txt` (not the dev file), starts `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and uses `/health` as its health check. Python version comes from `backend/.python-version`.

Environment variables (set in `render.yaml`):

- `ALLOWED_ORIGINS` — frontend origins allowed by CORS
- `PAIRS_FILE` — path to the pairs manifest: `/etc/secrets/manifest.json`
- `IMAGE_BASE_URL` — where images are served: `https://images.trueortrained.com`

The pairs manifest is a **Render Secret File** (service → Environment → Secret Files → filename `manifest.json`, contents of `data/build/manifest.json`), because it's the answer key and the repo is public. The backend refuses to start without it. Update it whenever the image set is rebuilt.

The free tier sleeps after ~15 minutes idle; the first request afterwards takes ~30–60s while it wakes. Logs are in the Render dashboard.

### Frontend (Cloudflare Workers)

Served as static assets by a Worker — no server code. `frontend/wrangler.jsonc` points Wrangler at the `dist/` build output; `single-page-application` mode serves `index.html` for unknown paths so client-side routes work. Node version comes from `frontend/.node-version`.

Workers Builds settings (Cloudflare dashboard → the Worker → Settings → Build):

- Root directory: `frontend`
- Build command: `npm run build`
- Deploy command: `npx wrangler deploy`
- Build variable: `VITE_API_URL=https://api.trueortrained.com`

`VITE_API_URL` is baked in at build time, so changing it requires a rebuild. The Worker's name in the dashboard must match `name` in `wrangler.jsonc`. Only `https://trueortrained.com` is allowed by CORS, so the `*.workers.dev` URL loads the page but can't reach the API.

### Changing the API safely

The frontend and backend deploy **independently** from the same merge: Cloudflare usually finishes in about a minute, Render takes a few minutes, and if Render's deploy fails it keeps the old backend running. So for a while — or indefinitely, after a failed deploy — the new frontend talks to the old backend.

A merge that changes an API's request or response shape and the frontend that uses it together will break the live site in that gap. This happened when the game switched to pairs (#7): a missing secret file failed the backend deploy, and the new frontend couldn't read the old `/round` response.

**Additive changes are always safe** — new endpoints, new optional request fields, new response fields the old frontend ignores. Ship them in one PR.

**Breaking changes go in steps (expand → migrate → contract):**

1. **Expand** — the backend supports old *and* new: add a new endpoint (e.g. `/v2/round`) or new fields alongside the old ones. Merge, then wait until Render shows the deploy as **Live** and check it on `https://api.trueortrained.com/docs`.
2. **Migrate** — switch the frontend to the new API. Merge. Old backend paths are still there, so either deploy order works.
3. **Contract** — once the new frontend is live, remove the old endpoint or fields in a follow-up PR.

**Before merging anything that touches deployment:**

- New environment variables or secret files exist in Render **before** the merge (the backend refuses to start without required config, and Render won't wait for you).
- New external resources (R2 objects, DNS records) are in place and verified.
- After merging, watch both deploys finish, then play one round on the live site.

**If a deploy breaks the site, roll back first, debug second:**

- **Frontend**: Cloudflare → Workers & Pages → `true-or-trained` → Deployments → previous version → Rollback. Instant.
- **Backend**: Render → `true-or-trained-api` → Events → a previous successful deploy → Rollback.

The next merge to `main` deploys forward again as normal.
