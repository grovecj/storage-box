# Storage Boxes — Project Context

## What We're Building

Storage Boxes is a mobile-first web app that helps users track the location and contents of physical storage containers. Target users: frequent travelers, multi-residence owners, people who are moving. **Core value prop**: Quickly answer "where is my [thing]?" without opening every box.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy async + AsyncPG, Alembic (configured, no migrations yet), WeasyPrint + Jinja2 for PDF reports
- **Database**: PostgreSQL 16 + PostGIS 3.4, GeoAlchemy2
- **Frontend**: React 19, TypeScript 5.7, Vite 6, Tailwind CSS 3.4, React Router 7, Axios, Leaflet + react-leaflet, qrcode.react, lucide-react
- **Infrastructure**: Docker Compose (local), DigitalOcean App Platform (prod), Nginx reverse proxy, Terraform

## Project Structure

```
storage-box/
├── CLAUDE.md
├── Dockerfile                 ← prod multi-stage build (port 8080)
├── docker-compose.yml         ← local dev environment
├── backend/
│   ├── Dockerfile             ← dev image (uvicorn --reload)
│   ├── requirements.txt
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       ├── schemas/
│       ├── routers/
│       ├── services/
│       └── utils/
├── frontend/
│   ├── src/
│   │   ├── pages/             ← Dashboard, BoxDetail, SearchResults, Reports, QRPrint, QRBatchPrint
│   │   ├── components/        ← boxes/, items/, layout/, reports/, search/, shared/
│   │   ├── hooks/             ← useGeolocation, useTheme
│   │   ├── api/               ← Axios client
│   │   ├── types/
│   │   └── styles/
│   └── ...
├── nginx/
├── terraform/
├── .github/workflows/ci.yml
└── .claude/
    ├── agents/
    └── skills/
```

## Development

```bash
docker compose up -d --build   # starts all services
```

| Service  | Port | Notes                          |
|----------|------|--------------------------------|
| db       | 5432 | PostGIS 16-3.4                 |
| backend  | 8000 | FastAPI, auto-reload           |
| frontend | 5173 | Vite dev server, hot-reload    |
| nginx    | 80   | Reverse proxy, access via http://localhost |

Seed data auto-loads in dev. Frontend hot-reloads via Vite; backend via `uvicorn --reload`.

## Key Architecture Notes

**Backend pattern**: routers → services → SQLAlchemy models

**API base**: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/boxes` | Create box |
| GET    | `/boxes` | List boxes |
| GET    | `/boxes/{box_id}` | Get box |
| GET    | `/boxes/code/{box_code}` | Get box by QR code |
| PUT    | `/boxes/{box_id}` | Update box |
| DELETE | `/boxes/{box_id}` | Delete box |
| GET    | `/boxes/{box_id}/items` | List items in box |
| POST   | `/boxes/{box_id}/items` | Add item to box |
| PUT    | `/boxes/{box_id}/items/{item_id}` | Update item |
| DELETE | `/boxes/{box_id}/items/{item_id}` | Delete item |
| GET    | `/boxes/{box_id}/audit-log` | Box audit log |
| GET    | `/tags` | List tags |
| POST   | `/tags` | Create tag |
| POST   | `/transfers` | Transfer box to new location |
| GET    | `/search` | Search boxes/items |
| GET    | `/search/autocomplete/items` | Item autocomplete |
| POST   | `/reports` | Generate PDF report |
| GET    | `/config` | App config |

**Database**: Tables auto-created on startup (no Alembic migrations in use yet).

**Frontend**: Custom Tailwind theme (amber accent, navy dark mode). Pages/components/hooks structure.

**Production**: Single multi-stage Dockerfile, port 8080, deployed to DigitalOcean App Platform at `boxes.cartergrove.me`.

## Design Principles

- **Mobile-first, always**: Every feature must work comfortably on a phone screen, one-handed
- **Speed over features**: A fast, lightweight experience beats a feature-rich slow one
- **Simplicity of data entry**: If it takes more than 15 seconds to log a new item, the app has failed
- **Offline-capable**: Users may be in garages, storage units, or basements with poor signal

## Domain Vocabulary

- **Box**: A physical storage container. Has a label, location, and optional photo
- **Location**: Where a box lives (e.g. "Seattle apartment — hall closet", "Mom's garage", "Storage unit 4B")
- **Item**: Something stored inside a box. Has a name, optional tags, optional photo
- **Tag**: Freeform label for items (e.g. "kitchen", "winter", "cables", "sentimental")
- **Transfer**: A recorded move of a box from one location to another

## Git & CI

- **Branch naming**: `feat/<issue_number>/<short-name>` (e.g. `feat/6/grouped-item-search`)
- **Commits**: Conventional commits — `feat:`, `fix:`, `chore:`, `test:`, `docs:`
- **CI**: GitHub Actions — frontend build + backend pytest on PR/push to main
- **Deploy**: Auto-deploy to DigitalOcean on push to main
- **PRs**: Must include description, screenshots for UI changes, test results

## Ticket Format

**GitHub Issues in `grovecj/storage-box` is the source of truth for all tickets.**

```markdown
# TICKET-<id>: <Title>

## Type: feature | bugfix | chore | design | test
## Priority: P0 (blocking) | P1 (core) | P2 (nice-to-have)
## Complexity: S | M | L | XL
## Agent: product-designer | ui-designer | software-architect | software-engineer | quality-engineer

## Description
What this ticket accomplishes and why it matters.

## Acceptance Criteria
- [ ] Specific, testable condition
- [ ] Another condition

## Technical Notes
Implementation hints, constraints, relevant existing code.

## Dependencies
- TICKET-<id> must be completed first
```

## Agent Workflow

- `/plan` — spawns product-designer + software-architect in parallel, synthesizes into tickets
- `/design <ticket-id>` — spawns ui-designer for a specific feature ticket
- `/implement <ticket-id>` — spawns software-engineer to implement a ticket
- `/test <ticket-id>` — spawns quality-engineer to write and run tests for a ticket
- `/review` — spawns quality-engineer to review current branch before PR

Agent definitions live in `.claude/agents/`:
- `product-designer` — feature planning, user flows, acceptance criteria
- `software-architect` — technical design, API contracts, data models
- `ui-designer` — production React+Tailwind components
- `software-engineer` — implementation
- `quality-engineer` — tests and PR review

## Test Requirements

**All new code must include tests** — enforced starting now.

- **Frontend**: Vitest + React Testing Library
- **Backend**: pytest + pytest-asyncio
- **Coverage gate**: 80% minimum on new code
- Quality engineer agent handles test planning and review
