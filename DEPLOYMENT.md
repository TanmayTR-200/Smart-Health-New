# Deployment Guide — Smart Health

This guide covers deploying the **frontend** to **Vercel**, the **backend** to **Render**, and running everything in **Docker**.

## Architecture

```
Vercel (Frontend - React/Vite)  →  Render (Backend - FastAPI)  →  PostgreSQL (Render)
```

---

## Prerequisites

- A GitHub repo with the `Smart-Health-New` code pushed
- Accounts on [vercel.com](https://vercel.com), [render.com](https://render.com)
- (Optional) [Docker](https://docker.com) installed locally
- Your Gemini API key

---

## 1. Render — Backend API + PostgreSQL

### Option A: Blueprint (recommended)

1. Push your code to GitHub (make sure `render.yaml` is in the repo root)
2. Go to [render.com](https://dashboard.render.com) → **New** → **Blueprint**
3. Select your GitHub repo
4. Render will detect `render.yaml` and create:
   - **PostgreSQL database** (`smart-health-new-db`)
   - **Web service** (`smart-health-new-api`)
5. In the env vars section, set your **GEMINI_API_KEY**
6. Click **Apply**
7. Wait for the build to finish — note the backend URL (e.g., `https://smart-health-new-api-xxxx.onrender.com`)

### Option B: Manual setup

1. **Create database:**
   - Dashboard → **New** → **PostgreSQL**
   - Name: `smart-health-new-db`, Database: `smart_health_new`, Plan: Free
   - Save the **Internal Database URL**

2. **Create web service:**
   - Dashboard → **New** → **Web Service**
   - Connect your GitHub repo
   - Runtime: **Python 3**
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `python setup_database.py && cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables:
     - `DATABASE_URL` → from the PostgreSQL database (internal connection string)
     - `GEMINI_API_KEY` → your Gemini API key
   - Deploy

> ⏎ **Note:** The free Render plan spins down after 15 min of inactivity. The first request after idle may take ~30s to cold-start.

---

## 2. Vercel — Frontend

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Vercel will auto-detect Vite. Verify:
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Add environment variable:
   - **Key:** `VITE_API_URL`
   - **Value:** `https://your-render-backend-url.onrender.com/api`
     (use the Render URL from step 1, append `/api`)
6. Click **Deploy**

> The `vercel.json` in the `frontend/` folder handles SPA routing for React Router.

---

## 3. Docker — Local / Container Deployment

### Quick start with docker-compose (PostgreSQL + backend)

```bash
# Set your Gemini API key
export GEMINI_API_KEY=your_api_key_here

# Build and run
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Build & push to Docker Hub manually

```bash
# Build the image
docker build -t smart-health-new-backend .

# Run locally (with PostgreSQL URL)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/smart_health_new \
  -e GEMINI_API_KEY=your_api_key_here \
  smart-health-new-backend

# Tag and push to Docker Hub
docker tag smart-health-new-backend YOUR_DOCKERHUB_USERNAME/smart-health-new-backend:latest
docker push YOUR_DOCKERHUB_USERNAME/smart-health-new-backend:latest
```

### Pull and run from Docker Hub

```bash
docker pull YOUR_DOCKERHUB_USERNAME/smart-health-new-backend:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/smart_health_new \
  -e GEMINI_API_KEY=your_api_key_here \
  YOUR_DOCKERHUB_USERNAME/smart-health-new-backend:latest
```

---

## Environment Variables Reference

| Variable | Where | Example |
|---|---|---|
| `DATABASE_URL` | Render / Docker | `postgresql://user:pass@host:5432/smart_health_new` |
| `GEMINI_API_KEY` | Render / Docker | your Gemini API key |
| `VITE_API_URL` | Vercel | `https://smart-health-new-api.onrender.com/api` |
| `PORT` | Docker (auto-set on Render) | `8000` |

---

## Verification

After deployment:

1. **Backend health check:** Visit `https://your-render-url.onrender.com/` → should return `{"message": "Smart Health API is running", "success": true}`
2. **Frontend:** Visit your Vercel URL → dashboard should load with data from the backend
3. **API connectivity:** The frontend dashboard should show PHC data, health scores, and alerts
