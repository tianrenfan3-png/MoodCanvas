# MoodCanvas

Express emotions through drawing and receive AI-powered mood analysis. Draw on a canvas, submit for analysis, and track your mood history over time.

## Architecture

```
┌─────────────┐     Firebase Auth      ┌─────────────┐
│   React     │ ◄────────────────────► │  Firebase   │
│  Frontend   │                        │    Auth     │
└──────┬──────┘                        └─────────────┘
       │ Bearer token
       │ multipart image
       ▼
┌─────────────┐     Firestore /        ┌─────────────┐
│   FastAPI   │ ◄── in-memory fallback │  Firestore  │
│   Backend   │                        │  (history,  │
│  + CLIP ML  │                        │   rewards)  │
└─────────────┘                        └─────────────┘
```

| Layer    | Stack                                              |
|----------|----------------------------------------------------|
| Frontend | React 18, TypeScript, Vite, Tailwind, react-konva |
| Backend  | FastAPI, Pydantic v2, Firebase Admin               |
| Database | Firestore (in-memory fallback without credentials) |
| ML       | CLIP ViT-B/32 with temperature-scaled softmax      |
| Testing  | pytest, Vitest                                     |

## Quick start

### Prerequisites

- Node.js 20+
- Python 3.10+ (3.12 recommended)
- Firebase project with Google sign-in enabled
- Firebase service account JSON (for backend)

### 1. Clone and configure

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit both `.env` files with your Firebase credentials.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# For local dev without GPU, use mock analyzer:
# Set ANALYZER_TYPE=mock in backend/.env

# For real CLIP analysis:
pip install torch torchvision
pip install git+https://github.com/openai/CLIP.git
# Set ANALYZER_TYPE=clip in backend/.env

uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker Compose

```bash
docker compose up
```

Runs backend (mock analyzer) on `:8000` and frontend dev server on `:5173`.

## API

Interactive docs at `http://localhost:8000/docs` when the backend is running.

| Method | Path               | Auth | Description                    |
|--------|--------------------|------|--------------------------------|
| GET    | `/ping`            | No   | Liveness check                 |
| GET    | `/health`          | No   | Analyzer status                |
| POST   | `/warmup`          | No   | Pre-load ML model              |
| GET    | `/moods`           | No   | List mood categories           |
| POST   | `/predict`         | Yes  | Analyze drawing + save history |
| GET    | `/history`         | Yes  | Paginated history              |
| GET    | `/history/:id`     | Yes  | Single entry                   |
| DELETE | `/history/:id`     | Yes  | Delete entry                   |
| DELETE | `/history`         | Yes  | Clear all history              |
| GET    | `/rewards/status`  | Yes  | Coins and streak               |
| POST   | `/rewards/claim`   | Yes  | Claim daily reward             |

## Environment variables

### Backend (`backend/.env`)

| Variable                   | Description                              |
|----------------------------|------------------------------------------|
| `CORS_ORIGINS`             | Comma-separated allowed origins          |
| `FIREBASE_CREDENTIALS_PATH`| Path to service account JSON             |
| `FIRESTORE_PROJECT_ID`     | Firebase project ID                      |
| `ANALYZER_TYPE`            | `clip` or `mock`                         |
| `CLIP_MODEL`               | e.g. `ViT-B/32`                          |
| `MAX_UPLOAD_BYTES`         | Max upload size (default 5MB)            |

### Frontend (`frontend/.env`)

| Variable                 | Description                |
|--------------------------|----------------------------|
| `VITE_FIREBASE_*`        | Firebase client config     |
| `VITE_API_URL`           | Backend URL                |
| `VITE_BASE_PATH`         | Base path for GitHub Pages |

## Firebase setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable **Google** sign-in under Authentication → Sign-in method
3. Register a web app and copy config to `frontend/.env`
4. Generate a service account key (Project Settings → Service accounts) and save as `backend/firebase-service-account.json`
5. Enable **Cloud Firestore** in the Firebase console

## Deployment

### Backend (Railway / Render / Fly.io)

1. Build from the repo-root `Dockerfile` (or `backend/Dockerfile` if the service root is `backend/`)
2. Set environment variables:
   - `FIREBASE_CREDENTIALS_JSON_B64` — base64 of the service account JSON (`python backend/scripts/encode_firebase_credentials.py key.json`)
   - `FIRESTORE_PROJECT_ID` — Firebase project ID
   - `ANALYZER_TYPE=mock` on small instances; use `clip` only on GPU/large plans
   - `CORS_ORIGINS` — e.g. `https://your-user.github.io` (no trailing slash)
3. **Railway networking:** if deploy logs show `/ping` 200 but the public URL returns 502, open **Settings → Networking → Public Networking**, edit your domain, and set **Target port** to `8080` (must match the `PORT` Railway injects — see deploy logs).
4. Do **not** set a custom `PORT` variable in Railway unless you also update the domain target port to match.

### Frontend (Vercel or GitHub Pages)

**Vercel:** Import repo, set root to `frontend`, add env vars.

**GitHub Pages:**
```bash
cd frontend
VITE_BASE_PATH=/YourRepoName/ npm run build
# Deploy dist/ to gh-pages branch
```

## Testing

```bash
# Backend
cd backend && pytest -v

# Frontend
cd frontend && npm run test && npm run build
```

## Features

- Google OAuth sign-in
- Touch-friendly drawing canvas with pen, eraser, colors, undo/redo
- CLIP-based mood analysis with calibrated probability scores
- Mood breakdown chart after analysis
- Server-persisted history with trend charts and CSV export
- Daily streak and coin rewards (server-validated)
- Dark mode
- Rate limiting on analysis endpoint

## Privacy

Drawings are sent to the backend for AI analysis. Thumbnails and mood data are stored per user in Firestore until deleted. Analysis is not performed locally in the browser.
