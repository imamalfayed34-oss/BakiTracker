# বাকি ট্র্যাকার — Baki Tracker

Digital baki/udhar ledger for small shops in Bangladesh.

**Phase 0 — Foundation.** This is the skeleton: FastAPI backend + Supabase + PWA shell, deployed on Railway. Once live, you'll see three green dots on your phone confirming the whole pipeline works.

---

## Project structure

```
baki-tracker/
├── backend/
│   ├── main.py            FastAPI app — serves API + frontend
│   ├── config.py          env settings
│   ├── database.py        Supabase client
│   ├── requirements.txt
│   └── routers/
│       └── health.py      /api/health + /api/health/db
├── frontend/
│   ├── index.html         PWA shell
│   ├── manifest.json      Add-to-Home-Screen config
│   ├── service-worker.js  offline shell cache
│   ├── css/style.css
│   ├── js/app.js          pings backend, shows status
│   └── icons/             192 + 512 app icons
├── schema.sql             run this in Supabase
├── railway.json           Railway deploy config
├── nixpacks.toml          build config
├── .env.example
└── .gitignore
```

---

## Setup — do these in order

### 1. Create the Supabase project (5 min)
1. Go to https://supabase.com → New project
2. **Region: Singapore** (closest to Bangladesh = lowest latency)
3. Set a strong database password, save it somewhere safe
4. Wait ~2 min for it to provision

### 2. Run the schema (2 min)
1. In Supabase → **SQL Editor** → New query
2. Paste the entire contents of `schema.sql` → **Run**
3. Go to **Table Editor** — you should see 8 tables (users, customers, transactions, sms_log, subscriptions, payments, customer_tokens, promises)

### 3. Grab your API keys (1 min)
- Supabase → **Project Settings → API**
- Copy: `Project URL`, `anon public` key, and `service_role` key

### 4. Test locally (optional but recommended)
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# (mac/linux: source .venv/bin/activate)
pip install -r requirements.txt

# create backend/.env from the template and paste your keys
# then run:
uvicorn main:app --reload
```
Open http://localhost:8000 — you should see the app shell. Two of three dots green (PWA shows "registered" only over HTTPS, so localhost may show it differently — that's fine).

### 5. Push to GitHub (3 min)
```bash
cd baki-tracker
git init
git add .
git commit -m "Phase 0: foundation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/baki-tracker.git
git push -u origin main
```

### 6. Deploy on Railway (5 min)
1. Go to https://railway.app → New Project → Deploy from GitHub repo
2. Select your `baki-tracker` repo
3. Railway auto-detects Python via `nixpacks.toml`
4. Go to the service → **Variables** tab → add:
   - `SUPABASE_URL` = your project URL
   - `SUPABASE_ANON_KEY` = your anon key
   - `SUPABASE_SERVICE_KEY` = your service_role key
   - `APP_ENV` = `production`
5. Settings → Networking → **Generate Domain**
6. Open the generated URL on your phone

### 7. Confirm it works
On your phone you should see **three green dots**:
- 🟢 Backend server — live · production
- 🟢 Database (Supabase) — connected
- 🟢 PWA / offline shell — registered

Then tap Safari's share button → **Add to Home Screen**. The app installs like a native app.

---

## What's next

**Phase 1 — Phone + OTP login.** Every future feature builds on this skeleton: write code → `git push` → Railway redeploys in ~60 seconds → live.

---

*Phase 0 complete when all three dots are green on your phone.*
