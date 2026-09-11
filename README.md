# CityVision AI

SIH 2026 prototype for Problem Statement 26127: a city-wide AI engine for multi-camera ANPR trajectory tracking and urban traffic analytics. The existing command-center UI remains intact. The GIS page now uses Leaflet with OpenStreetMap tiles and backend-generated overlays.

## Inspection-driven implementation map

| Existing screen | Existing UI elements preserved | API and PostGIS data |
|---|---|---|
| Dashboard | KPI cards, volume chart, activity feed, camera status | `GET /api/v1/dashboard`; camera, detection, traffic measurement, alert aggregates; WebSocket `/ws/operations` |
| Live Camera Feed | camera grid, selected-camera detail, live toggle | `GET/POST /api/v1/cameras`; stream metadata, latest detections, heartbeats |
| Vehicle Search & Tracking | plate search, profile, timeline, export/create-alert actions | `GET /api/v1/vehicles/{plate}/trajectory`; vehicle and time-ordered detection records |
| GIS Traffic Map | existing controls and side panel | `GET /api/v1/map/layers?layer=traffic|cameras|heatmap|hotspots`; PostGIS GeoJSON for roads, cameras, trajectories and hotspots |
| Traffic Analytics | existing charts, date/export controls | traffic measurements grouped by time, corridor and vehicle type |
| Alerts | severity filters, status table | `GET /api/v1/alerts`, `PATCH /api/v1/alerts/{id}` |
| Camera Management | register action, status table, health panel | camera CRUD, health telemetry and configuration |
| Reports | report cards and export button | asynchronous report generation over detections, alerts and measurements |
| Settings | existing preference cards | authenticated user, notification, map, alert and camera settings |

## Backend

`backend/app/main.py` provides FastAPI REST endpoints, `/health`, Swagger at `/docs`, OpenAPI at `/openapi.json`, CORS allow-listing, a WebSocket operations heartbeat and explicit simulation mode. SQLAlchemy models and the initial Alembic migration define users, cameras, vehicles, vehicle detections, traffic measurements and alerts with foreign keys, timestamps and spatial GiST indexes. Extend the same migration pattern for report jobs, signal inventories and configuration records as those screens become editable.

Run locally:

```bash
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
npm install
npm run dev
```

Copy `.env.example` to `.env` and replace `JWT_SECRET`, database credentials and the deployed API host before production. Do not expose camera stream URLs to unauthenticated clients. Add role-based JWT dependencies to write endpoints before handing the system to operators.

## AI and demo boundary

The default system is simulation mode. Seeded values and visual camera tiles are demonstrations, not live CCTV or accuracy evidence. `backend/app/pipeline.py` defines the integration point for OpenCV frames, YOLO vehicle/plate detection, PaddleOCR and ByteTrack/DeepSORT. `track_id` remains video-local. Cross-camera journeys require plate observations plus time, camera position, direction, road distance and optionally validated visual re-identification. The project makes no accuracy claim. Validate measured precision/recall, OCR accuracy and false-match rates on the chosen local dataset before reporting them.

For an inference host, install `backend/requirements-ai.txt`. Use a public, permissioned traffic dataset such as [UA-DETRAC](https://detrac-db.rit.albany.edu/) for vehicle tracking research and [UFPR-ALPR](https://web.inf.ufpr.br/vri/databases/ufpr-alpr/) for plate recognition research, subject to each dataset's licence. Store downloaded data outside git. For custom YOLO training: use `images/train`, `images/val`, `images/test` with matching `labels/` folders; document the licence, split by source video to avoid leakage, train with the model's current official CLI, then report validation metrics and failure cases. PaddleOCR needs labelled plate crops and character-ground-truth for meaningful evaluation.

## Deployment

Deploy the frontend to Netlify using `netlify.toml`. Deploy the API container to a persistent host such as Render, Fly.io, Railway or a managed Kubernetes service; run `alembic upgrade head` as its release step. Use a managed PostgreSQL provider that supports the PostGIS extension, set `DATABASE_URL` to its TLS connection string, set `CORS_ORIGINS` to the Netlify domain, and set `VITE_API_BASE_URL`/`VITE_WS_URL` during the Netlify build. Replace the placeholder API host in `netlify.toml`.
