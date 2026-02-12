# Second-Hand Clothes Auction API

A real-time auction platform for second-hand clothing, built with FastAPI and PostgreSQL. Features JWT authentication, soft-close (popcorn) bidding to prevent auction sniping, and push notifications via Firebase.

## Tech Stack

- **Python 3.12**, FastAPI, Uvicorn
- **PostgreSQL** via async SQLAlchemy 2.0 + asyncpg
- **Alembic** for database migrations
- **JWT** authentication (python-jose + bcrypt)
- **Firebase Realtime Database** for push notifications (optional)
- **Pydantic v2** for validation

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional)

### With Docker

```bash
cp .env.example .env
docker compose up -d
```

The API will be available at `http://localhost:8000`.

### Without Docker

```bash
# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL and create the database
createdb auctions

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### API Docs

Once running, interactive documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Auth (`/api/v1/auth`)

| Method | Path        | Auth | Description          |
|--------|-------------|------|----------------------|
| POST   | `/register` | No   | Create user          |
| POST   | `/login`    | No   | Returns JWT token    |
| GET    | `/me`       | Yes  | Current user profile |

### Items (`/api/v1/items`)

| Method | Path          | Auth | Description                              |
|--------|---------------|------|------------------------------------------|
| POST   | `/`           | Yes  | Create item listing                      |
| GET    | `/`           | No   | List items (filter: category, size, condition) |
| GET    | `/{item_id}`  | No   | Get item details                         |
| PUT    | `/{item_id}`  | Yes  | Update item (owner only)                 |
| DELETE | `/{item_id}`  | Yes  | Delete item (owner only, no active auction) |

### Auctions (`/api/v1/auctions`)

| Method | Path                      | Auth | Description                     |
|--------|---------------------------|------|---------------------------------|
| POST   | `/`                       | Yes  | Create auction for owned item   |
| GET    | `/`                       | No   | List auctions (filter: status)  |
| GET    | `/{auction_id}`           | No   | Get auction details             |
| POST   | `/{auction_id}/cancel`    | Yes  | Cancel auction (seller, no bids)|
| POST   | `/{auction_id}/bids`      | Yes  | Place a bid                     |
| GET    | `/{auction_id}/bids`      | No   | Bid history for auction         |

## Soft-Close (Popcorn Bidding)

To prevent last-second sniping, auctions use a soft-close mechanism:

- If a bid is placed within the last **5 minutes** of an auction, the end time is extended by **5 minutes**.
- Extensions are cumulative -- each late bid extends from the current end time.
- The original end time is preserved for reference; only the effective end time changes.
- The bid response includes a `was_extended` flag and the new `auction_end_time`.

Both the window and extension duration are configurable via `SOFT_CLOSE_WINDOW_MINUTES` and `SOFT_CLOSE_EXTENSION_MINUTES`.

## Auction Lifecycle

Auctions transition through statuses: `pending` -> `active` -> `ended` (or `cancelled`).

A background task runs every 30 seconds to:
- Activate `pending` auctions whose `start_time` has passed.
- Resolve `active` auctions whose `end_time` has passed (determines winner from highest bid).

Stale auctions are also resolved on-demand when fetched via GET.

## Event Notifications

An abstract `EventPublisher` interface supports push notifications:

- **`FirebaseEventPublisher`** -- pushes events to Firebase Realtime Database (enabled when `FIREBASE_CREDENTIALS_PATH` is set).
- **`NoOpEventPublisher`** -- no-op fallback for development and testing.

Events published: `bid_placed`, `auction_ended`.

## Configuration

All settings are loaded from environment variables (or `.env` file):

| Variable                       | Default                          | Description                    |
|--------------------------------|----------------------------------|--------------------------------|
| `DATABASE_URL`                 | `postgresql+asyncpg://...`       | PostgreSQL connection string   |
| `JWT_SECRET_KEY`               | `change-me-in-production`        | Secret for signing JWTs        |
| `JWT_ALGORITHM`                | `HS256`                          | JWT signing algorithm          |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                          | Token expiry in minutes        |
| `FIREBASE_CREDENTIALS_PATH`   | *(unset)*                        | Path to Firebase service account JSON |
| `FIREBASE_PROJECT_ID`         | *(unset)*                        | Firebase project ID            |
| `SOFT_CLOSE_WINDOW_MINUTES`   | `5`                              | Soft-close trigger window      |
| `SOFT_CLOSE_EXTENSION_MINUTES`| `5`                              | Extension per late bid         |

## Project Structure

```
app/
├── main.py              # FastAPI app, lifespan, router mounting
├── config.py             # Pydantic Settings
├── database.py           # Async engine, session factory, Base
├── dependencies.py       # get_db, get_current_user
├── exceptions.py         # HTTP exception helpers
├── models/               # SQLAlchemy models (User, Item, Auction, Bid)
├── schemas/              # Pydantic request/response schemas
├── routers/              # API route handlers
├── services/             # Business logic
└── events/               # EventPublisher interface + implementations
```

## Running Tests

Tests use an in-memory SQLite database and require no external services.

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
