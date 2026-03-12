# Storage Box

Inventory tracking webapp for portable storage containers. Each StorageBox represents a physical plastic tote containing items, tracked with QR codes for quick access.

## Architecture

```
┌─────────────┐
│    Nginx     │  Port 80/443
│  (reverse    │  Serves frontend static files
│   proxy)     │  Proxies /api/* to backend
└──────┬──────┘
       │
  ┌────┴────────────────┐
  │                     │
  ▼                     ▼
┌──────────┐    ┌──────────────┐
│ FastAPI  │    │ React SPA    │
│ (Python) │    │ (TypeScript) │
│ Port 8000│    │ Vite + TW    │
└────┬─────┘    └──────────────┘
     │
     ▼
┌──────────┐
│PostgreSQL│
│+ PostGIS │
│ Port 5432│
└──────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Database** | PostgreSQL 16 + PostGIS 3.4 |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async), Alembic |
| **Frontend** | React 19, TypeScript, Tailwind CSS, Vite |
| **Web Server** | Nginx (reverse proxy + static serving) |
| **Maps** | React Leaflet + OpenStreetMap |
| **QR Codes** | qrcode.react |
| **PDF Export** | WeasyPrint |
| **Infrastructure** | Docker Compose, Terraform (DigitalOcean) |

### Project Structure

```
storage-box/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic request/response schemas
│   │   ├── routers/   # API route handlers
│   │   ├── services/  # Business logic
│   │   └── utils/     # Audit logging helpers
│   └── Dockerfile
├── frontend/          # React SPA
│   ├── src/
│   │   ├── api/       # Axios API client
│   │   ├── components/# UI components (layout, boxes, items, shared)
│   │   ├── pages/     # Route pages
│   │   ├── hooks/     # Custom React hooks
│   │   └── types/     # TypeScript interfaces
│   └── Dockerfile
├── nginx/             # Nginx config + Dockerfile
├── terraform/         # DigitalOcean infrastructure as code
├── docker-compose.yml # Development stack
└── .env.example       # Environment variables template
```

### Database Schema

- **storage_boxes** — ID, box_code (BOX-0001), name, GPS location (PostGIS), audit fields
- **items** — Global item registry (unique by name)
- **box_items** — Per-box item quantities (many-to-many between boxes and items)
- **tags** — Custom tags (seeded: PCB, VACATION, LONG_TERM)
- **box_item_tags** — Tags applied per box-item combination
- **audit_log** — Tracks all mutations (add, remove, transfer, create, delete)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET/POST | `/api/v1/boxes` | List / create boxes |
| GET/PUT/DELETE | `/api/v1/boxes/:id` | Get / update / delete box |
| GET | `/api/v1/boxes/code/:code` | Get box by code (QR landing) |
| GET/POST | `/api/v1/boxes/:id/items` | List / add items |
| PUT/DELETE | `/api/v1/boxes/:id/items/:item_id` | Update / remove item |
| POST | `/api/v1/transfers` | Transfer items between boxes |
| GET | `/api/v1/search?q=` | Search boxes and items |
| GET/POST | `/api/v1/tags` | List / create tags |
| POST | `/api/v1/reports` | Generate report (HTML/PDF/CSV) |
| GET | `/api/v1/boxes/:id/audit-log` | Box audit history |
| GET | `/api/v1/config` | App configuration |

## Running Locally

### Prerequisites

- Docker and Docker Compose
- Node.js 22+ (for frontend development)
- Python 3.12+ (for backend development)

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/grovecj/storage-box.git
cd storage-box

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up -d

# The app is now available at:
# - Frontend (dev server): http://localhost:5173
# - API: http://localhost:8000
# - Nginx (production proxy): http://localhost:80
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to the backend at `http://backend:8000`.

### Backend Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs are available at `http://localhost:8000/docs` (Swagger UI).

## Deployment

### DigitalOcean with Terraform

```bash
cd terraform

# Copy and fill in variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your DO token, SSH key name, etc.

# Deploy
terraform init
terraform plan
terraform apply
```

This provisions:
- 1x Droplet (Ubuntu 24.04) with Docker pre-installed
- 1x Managed PostgreSQL 16 cluster
- Firewall rules (SSH, HTTP, HTTPS)
- Optional DNS record for your domain

### Deploying to Any Linux Server

```bash
# On the server:
# 1. Install Docker and Docker Compose
# 2. Clone the repo
git clone https://github.com/grovecj/storage-box.git
cd storage-box

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, APP_BASE_URL, SECRET_KEY

# 4. Build and run
docker compose -f docker-compose.yml up -d --build
```

### SSL/HTTPS

For production, install Certbot on the host and configure Nginx with SSL:

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d boxes.cartergrove.me
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://storagebox:changeme@db:5432/storagebox` |
| `APP_BASE_URL` | Base URL for QR codes | `http://localhost` |
| `APP_ENV` | Environment (development/production) | `development` |
| `SECRET_KEY` | Application secret key | `dev-secret-key` |

## Features

- **Box Management** — Create, edit, delete storage boxes with auto-generated IDs (BOX-0001)
- **Item Tracking** — Add items with quantities and custom tags, tracked per-box
- **Transfers** — Move items (full or partial quantities) between boxes
- **GPS Location** — Device geolocation or manual coordinates, proximity sorting
- **QR Codes** — Printable QR codes linking directly to each box
- **Search** — Full-text search across box IDs, item names, and tags
- **Reports** — Generate inventory reports in HTML, PDF, or CSV format (LETTER paper)
- **Audit Log** — Complete history of all item and box mutations
- **Dark/Light Mode** — Toggle between themes
- **Mobile Responsive** — Optimized for phone scanning workflow
