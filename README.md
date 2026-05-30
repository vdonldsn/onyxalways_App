# OnyxAlways — Order Workshop

A lightweight, mobile-friendly order management app for the OnyxAlways custom print and design business. Tracks orders through a four-stage workflow (`New Order → Designing/Approval → Production → Complete`) with per-order cost, price, profit, and a small accounting dashboard.

**Stack:** FastAPI (Python) · SQLAlchemy · Supabase Postgres (or SQLite for local) · Vanilla JS frontend served from the same process.

---

## What you can do with it

- Add a new order (client name, description, item type, quantity, costs, sale price, due date, notes)
- See all orders on a four-column board
- Move orders forward (→) or back (←) through the workflow with one tap
- Edit or delete any order
- See live totals: active orders, outstanding revenue, this-month profit, lifetime profit
- Use it on your phone — the board collapses to swipeable tabs on small screens

---

## Architecture (the why)

| Concern | Choice | Why |
|---|---|---|
| Backend | **FastAPI** | Async, type-hinted, auto-generates Swagger docs at `/docs` (great for QA-testing the API directly) |
| ORM | **SQLAlchemy 2.0** | Database-agnostic — swap SQLite ↔ Postgres with one env var, no code change |
| DB (local) | **SQLite** | Zero setup, single file |
| DB (prod) | **Supabase Postgres** | Free tier, automatic backups, web UI to fix data on the fly |
| Frontend | **Single HTML + vanilla JS** | No build step, loads instantly, easy to read and modify |
| Hosting | **Railway** (recommended) or **Fly.io** | Runs the Dockerfile unchanged |
| Money fields | **Decimal** (Numeric in DB) | Never floats. Floats lose pennies and break accounting silently |
| Order lifecycle | **Enum with ordered values** | The enum order itself defines forward/back movement — single source of truth |

---

## Local development

### 1. Clone and install

```bash
git clone <your-repo>
cd onyxalways
python -m venv .venv
source .venv/bin/activate     # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
```

The default `.env` uses SQLite, which needs zero setup. The DB file is created automatically on first run.

### 3. Run it

```bash
uvicorn main:app --reload --port 8000
```

Then open:
- **App:** http://localhost:8000
- **API docs (Swagger UI):** http://localhost:8000/docs ← QA-friendly, you can hit every endpoint from here
- **Alternative API docs (ReDoc):** http://localhost:8000/redoc

---

## Production deployment: Railway + Supabase

This is the recommended path. Total cost: $0 to start (Supabase free + Railway trial credit), ~$5/mo once you need more.

### Step 1 — Create the Supabase database

1. Go to [supabase.com](https://supabase.com) → sign up → New project
2. Pick a region near you (US East for Nashville)
3. Save the database password somewhere safe — you can't recover it
4. Once the project is provisioned, go to **Project Settings → Database → Connection string → URI**
5. Pick the **"Transaction pooler"** option (this is important — direct connections don't scale well from cloud platforms)
6. Copy the URI. It looks like:
   ```
   postgresql://postgres.abcdefghijklmn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
7. Replace `[YOUR-PASSWORD]` with the actual password you saved

### Step 2 — Deploy to Railway

1. Push your code to GitHub (don't commit `.env` — `.gitignore` already covers this)
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Railway will detect the Dockerfile and build it
4. Once deployed, open the project → **Variables** tab → add:
   ```
   DATABASE_URL = postgresql://postgres.abcdefghijklmn:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
5. Railway will redeploy automatically with the new variable
6. Under **Settings → Networking**, click **Generate Domain** to get a public URL like `onyxalways.up.railway.app`

That's it. Visit the domain on your phone and add it to your home screen.

### Step 3 — Add to your phone's home screen (PWA-style)

**iOS:** Safari → share button → "Add to Home Screen"
**Android:** Chrome → menu → "Add to Home Screen"

The app will open full-screen, no browser chrome, like a native app.

---

## Backend API reference

All endpoints live under `/api`. You can test them all from `/docs`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness check |
| GET | `/api/orders` | List all orders (optionally filter by `?status_filter=NEW_ORDER`) |
| GET | `/api/orders/{id}` | Get one order |
| POST | `/api/orders` | Create a new order (starts in `NEW_ORDER` status) |
| PATCH | `/api/orders/{id}` | Partial update — only fields in the body are changed |
| DELETE | `/api/orders/{id}` | Hard delete (prefer setting status to `COMPLETE` instead) |
| POST | `/api/orders/{id}/advance` | Move to next status |
| POST | `/api/orders/{id}/regress` | Move to previous status |
| GET | `/api/summary` | Dashboard totals (active count, outstanding revenue, profits) |

### Example: create an order from the command line

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Marcus T.",
    "description": "25 black tees, gold chest logo, sizes M-XXL",
    "item_type": "T-Shirt",
    "quantity": 25,
    "material_cost": 87.50,
    "labor_cost": 75.00,
    "sale_price": 375.00,
    "due_date": "2026-06-15"
  }'
```

---

## How to use it (workflow)

A typical OnyxAlways order goes:

1. **New Order** — Customer calls or DMs. Hit `+ New Order`, fill in client name, description, item type, quantity, and your best guess at material cost + sale price. Sale price can be edited later.
2. **Designing / Approval** — You're sketching mockups or waiting on the client to approve. Hit `→` to move it here.
3. **Production** — Client approved, you're now printing/pressing/cutting. Hit `→` again.
4. **Complete** — Delivered and paid. Hit `→` one more time. The system stamps the completion date automatically, and the order rolls into your monthly + lifetime profit totals.

If something goes wrong (client wants changes after design, or production needs rework), hit `←` to walk it back a stage. Nothing is lost — completion dates clear automatically and re-stamp on the next forward move.

The **money summary at the top** updates live:
- **Active Orders** — anything not in Complete
- **Outstanding Revenue** — money owed to you (sum of sale prices for non-complete orders)
- **This Month Profit** — profit on orders completed this calendar month
- **Lifetime Profit** — total profit since day one

---

## Backing up

### SQLite (local)
Copy the `onyxalways.db` file somewhere safe. That's it.

### Supabase
Supabase automatically takes daily backups on the free tier. To download manually:
**Dashboard → Database → Backups → Download.** You can also use the SQL editor to dump specific tables.

---

## Where to extend it later

- **Auth** — Supabase has built-in auth. If you ever want to log in, or share the app with a partner, add `@app.middleware` to validate Supabase JWTs.
- **Photo attachments** — Supabase Storage gives you 1 GB free. Add an `image_url` column to `Order`, upload from the frontend modal, store the URL.
- **Client notifications** — Use the Resend or SendGrid API in the `update_order` handler to email the client when status changes to `Production` or `Complete`.
- **Recurring orders** — Add a `template` table; create new orders from a template with one click.
- **Multi-tenant** — Add a `user_id` column to orders, filter every query by it. Then anyone can use this for their own business.

---

## Tests (for your QA-minded brain)

Quick sanity test you can run against a running server:

```bash
# Health check
curl http://localhost:8000/api/health

# Create
curl -X POST http://localhost:8000/api/orders -H "Content-Type: application/json" \
  -d '{"client_name":"Test","description":"Test order","sale_price":100,"material_cost":30,"labor_cost":20}'

# List
curl http://localhost:8000/api/orders

# Advance through all 4 stages
curl -X POST http://localhost:8000/api/orders/1/advance   # → DESIGNING_APPROVAL
curl -X POST http://localhost:8000/api/orders/1/advance   # → PRODUCTION
curl -X POST http://localhost:8000/api/orders/1/advance   # → COMPLETE
curl -X POST http://localhost:8000/api/orders/1/advance   # → 400 error (already complete)

# Summary should now show $50 lifetime profit
curl http://localhost:8000/api/summary
```

For automated tests, FastAPI ships with a `TestClient` that wraps requests — drop a `tests/test_orders.py` file and use `pytest`. Happy to scaffold this if you want.
