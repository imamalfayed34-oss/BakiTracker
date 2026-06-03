# Baki Tracker — Complete Project Context

> Master reference for all strategic decisions, architecture, and build plans.
> Generated: June 3, 2026
> Save as `CLAUDE.md` in the baki-tracker project root.

---

## Product Vision

**Short-term:** A dead-simple mobile-first PWA where Bangladeshi shopkeepers track customer credit (baki). Customer gets SMS notification. Dashboard shows who owes what.

**Long-term:** Bangladesh's first informal credit bureau → credit infrastructure for 100M+ unbanked South Asians. The baki app is the wedge; the credit network is the platform.

---

## Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend | FastAPI (Python) | |
| Database | Supabase (PostgreSQL + built-in auth) | Singapore region |
| Frontend | HTML/CSS + Tailwind CSS | Mobile-first PWA |
| Hosting | Railway | Singapore region, auto-deploy from GitHub |
| SMS | SSL Wireless | Bangladesh, ৳0.30/SMS |
| Payments | bKash Checkout (primary) + SSLCommerz (fallback) | |
| Auth | Phone + OTP via Supabase Auth | |
| Analytics | Plausible Analytics | Privacy-friendly, lightweight |
| PDF/Reports | WeasyPrint (Python) | v2 feature |

---

## Database Schema

```sql
-- Users (shopkeepers)
users: id, phone, shop_name, created_at

-- Customers (people who owe baki)
customers: id, user_id, name, phone, created_at

-- Transactions (individual baki entries)
transactions: id, customer_id, type (baki/payment), amount, note, 
  source ('manual' | 'online'), payment_ref, fee_amount, created_at

-- SMS log
sms_log: id, customer_id, message, sent_at, delivery_status

-- Subscriptions
subscriptions: id, user_id, plan (free/standard), trial_start, trial_end, 
  paid_until, status (trial/active/expired/cancelled), 
  payment_method, last_payment_id, created_at

-- Payments (subscription + online baki payments)
payments: id, user_id, amount, method (bkash/sslcommerz), 
  transaction_id, status (pending/success/failed), created_at

-- Customer tokens (for customer-facing portal, v1.5+)
customer_tokens: id, phone, token (unique, unguessable), created_at

-- Promises (v2+)
promises: id, customer_id, promised_amount, promised_date, 
  status (pending/fulfilled/broken), created_at
```

### Key Design Decisions

**Running balance calculation:**
```sql
SELECT SUM(CASE WHEN type='baki' THEN amount ELSE -amount END) 
AS balance FROM transactions WHERE customer_id = ?
```
- No invoice matching needed — it's a running ledger, not invoice-based
- Partial payments are just transactions that reduce the total
- Shopkeepers don't care which specific purchase a payment is against
- They care about one number: কত বাকি আছে?

**Soft-delete only:** Never delete transaction data. Use correction transactions instead. This preserves the behavioral history needed for credit scoring later.

**Phone number as universal identifier:** Customers are identified by phone across shops. This enables the cross-shop credit network in v3.

---

## Architecture

```
Shopkeeper's phone (Chrome / PWA)
  → HTTPS request
  → FastAPI backend (Railway, Singapore)
  → PostgreSQL (Supabase, Singapore)
  → Response back to phone (100–300ms)

SMS flow:
  → Scheduled job on server (daily 8 AM)
  → Queries DB: overdue bakis > 7 days
  → Calls SSL Wireless SMS API
  → Customer gets: "আপনার [Shop Name]-এ ৳500 বাকি আছে। — BakiTracker.com"

Customer payment flow (v3):
  → Customer taps link in SMS (bakitracker.com/pay/{token})
  → Sees all baki across all shops (aggregated by phone)
  → Pays via bKash/Nagad/card
  → Backend receives webhook → transaction recorded
  → Shopkeeper gets notification

Deployment:
  Code on Windows PC → git push → GitHub → Railway auto-deploys → live
```

---

## Feature Tiers

### MVP (2.5 weeks, sessions 1–10)

**Phase 0 — Foundation (Session 1, ~2hrs)**
- Supabase project creation (Singapore region)
- Database schema — all tables, RLS policies
- FastAPI project scaffolding with Supabase client
- Railway deployment pipeline (GitHub → auto-deploy)
- Health-check endpoint live
- PWA shell — blank home screen with Tailwind, manifest.json, service worker stub

**Phase 1 — Auth (Session 2, ~2hrs)**
- Supabase Auth with phone OTP
- Login screen UI (phone → OTP → dashboard)
- Auth middleware on FastAPI (JWT verification)
- Session persistence

**Phase 2 — Core Loop (Sessions 3–4, ~4hrs)**
- Customer CRUD (add, list, search)
- Customer list UI with Bangla initial avatars
- Transaction endpoints (add baki, record payment)
- Running balance calculation
- Customer profile with transaction history (the dispute resolution screen)

**Phase 3 — Dashboard + Polish (Session 5, ~2hrs)**
- Summary cards: মোট বাকি, আজ আদায়, কাস্টমার সংখ্যা
- Customer list sorted by highest baki
- Overdue badges (30+ days no payment → red)
- Search by name or phone
- FAB button for quick baki entry

**Phase 4 — SMS (Session 6, ~2hrs)**
- SSL Wireless API integration
- Send SMS on new baki entry (real-time)
- Manual "resend reminder" button per customer
- SMS log table (delivery status)
- Brand footer: "— BakiTracker.com"

**Phase 5 — Admin Dashboard (Session 7, ~1.5hrs)**
- `/admin` route (password-protected)
- User count, trial/paid/expired breakdown
- Revenue tracker, SMS usage, active vs dormant
- Churn list
- Plausible Analytics snippet

**Phase 6 — Payments + Subscription (Sessions 8–9, ~4hrs)**
- bKash Checkout integration (sandbox → production)
- Subscription table, trial logic, paid_until tracking
- 7-day free trial → trial countdown banner
- Read-only lockout for expired users:
  - ✅ Can VIEW existing customers and balances
  - ✅ Can SEARCH existing data
  - ❌ Cannot ADD new baki entries
  - ❌ Cannot SEND SMS reminders
  - ❌ Cannot ADD new customers beyond free 20-customer cap
- Payment confirmation flow
- Renewal SMS reminders (cron: 3 days before expiry)
- No auto-charge — manual renewal via bKash each month

**Phase 7 — Launch Prep (Session 10, ~2hrs)**
- PWA polish: icons, splash screen, meta tags
- End-to-end testing on real Android phone
- Custom domain SSL verified
- Shopkeeper demo script (3-minute pitch)

### v1.5 (Week 4, after 10 users)

- **Calendar view on customer profile** — red dots for baki dates, green for payment dates
- **Dashboard calendar** — tap date → see all transactions that day
- **Customer-facing receipt link** — SMS includes `baki.to/x7k9`, customer taps → sees read-only balance page, no login needed (token-based auth)
- PWA icons + splash screen + Add to Home Screen prompt
- SSLCommerz as payment fallback

### v2 (Month 2–3, after 50 users)

**Intelligence:**
- Payment promises tracker ("bhai 8 tarikh e 500 dibo")
- Promise fulfilled/broken auto-detection via cron
- Single-shop customer behavior tags: ভালো 🟢 / সতর্ক 🟡 / ঝুঁকিপূর্ণ 🔴
- Based on: payment reliability %, promise-keeping rate, baki trajectory
- Pure SQL thresholds, no ML needed yet

**Reliability:**
- Offline mode (IndexedDB + Workbox service workers)
- Background sync queue for writes
- Conflict resolution: last-write-wins with timestamp
- Offline banner: "অফলাইন মোড — ডাটা সেভ হচ্ছে"
- Practical v1 compromise: cache customer list for offline viewing, block new entries

**Channels:**
- WhatsApp Business API chatbot
- User sends: "Karim, 01912345678, 1000"
- Haiku parses fuzzy Bangla/Banglish input (~$0.0001/message)
- Auto-creates baki entry, replies with confirmation
- Auto-SMS reminders (scheduled, configurable per customer)
- Bulk SMS to all overdue customers

**Operations:**
- Multi-user/staff role (owner vs staff permissions)
- Transaction correction audit trail (never edit, only add corrections)
- বাকি সীমা — credit limit per customer with warning alerts
- Daily/weekly/monthly collection reports
- Export to PDF/Excel

### v3 (Month 4–6, after 100+ shops)

**Customer payment portal:**
- Public page at `bakitracker.com/pay/{token}`
- Customer sees all baki across ALL shops (aggregated by phone)
- Pays via bKash / Nagad / card (partial payments OK)
- 1–1.5% convenience fee charged to customer (not shopkeeper)
- Shopkeeper receives exact amount owed
- Instant notification to shopkeeper on payment
- This is the move from tool → two-sided platform

**Cross-shop credit network (the moat):**
- When shopkeeper adds a customer, system checks phone across all shops
- Shows AGGREGATE reputation signal only (privacy-safe):
  - Number of shops where registered (count, no names)
  - Average payment speed across all shops
  - Overall behavior tag (ভালো / সতর্ক / ঝুঁকিপূর্ণ)
  - 60+ day overdue flag (boolean, no amounts)
- Individual shop data NEVER shared — aggregated signals only
- Opt-in for shopkeepers (contribute + receive)
- Premium tier: ৳299/month for network access
- Customer consent language in SMS footer from v1

**AI layer:**
- Haiku 4.5 debtor risk scoring (payment pattern analysis)
- Optimal reminder timing ML
- Smart transaction categorization from notes
- Estimated: <$1/month at 500 users

### v4 (Year 1+)

**B2B data products:**
- MFI credit score API (BRAC, Grameen, ASA partnerships)
- BNPL underwriting layer for digital commerce (ShopUp, Chaldal)
- Credit insurance actuarial data

**Expansion:**
- India (Hindi/regional) — OKhata proves massive demand
- Pakistan (Urdu)
- Myanmar, Nepal
- Sub-Saharan Africa

**Infrastructure:**
- Bangladesh's first informal credit bureau
- Behavioral credit profiles for unbanked population
- Capacitor.js native app wrapper for Play Store / App Store

---

## Revenue Model

### Pricing Tiers

| Tier | Price | Limits |
|------|-------|--------|
| Free | ৳0 | 20 customers, 5 SMS/month, basic dashboard |
| Standard | ৳149/month | Unlimited customers, unlimited SMS, full dashboard, reports |
| Network (v3) | ৳299/month | Standard + cross-shop credit signals |

### Revenue Streams

1. **Subscriptions** — ৳149–299/month per shop (entry point)
2. **Payment processing** — 1–1.5% of every baki payment made through the portal (the real business, v3+)
3. **B2B credit data API** — MFI/lender partnerships (v4+)

### Revenue Projections

| Timeline | Users | Monthly Revenue |
|----------|-------|----------------|
| Month 1 | 50 users (30 paid) | ৳4,470 |
| Month 3 | 150 users (100 paid) | ৳14,900 |
| Month 6 | 300 users (200 paid) | ৳29,800 |
| Month 12 | 800 users (500 paid) | ৳74,500 |

### Break-even: ~30 paying users

### Payment Collection (bKash Checkout flow):
1. User taps "আপগ্রেড করুন"
2. Backend creates bKash payment request (REST API)
3. bKash returns payment URL → user redirected
4. User enters PIN, confirms on bKash's page
5. bKash redirects back to callback URL with transaction ID
6. Backend verifies → updates subscription status
7. Monthly renewal: cron checks `paid_until`, sends SMS reminder 3 days before expiry, flips to read-only on expiry. No auto-debit.

---

## Cost Breakdown

| Scale | Hosting | Database | SMS | Claude Pro | Total |
|-------|---------|----------|-----|------------|-------|
| 0–100 users | ৳0 | ৳0 | ৳300 | ৳2,400 | ৳2,700 |
| 100–500 users | ৳600 | ৳3,000 | ৳1,500 | ৳2,400 | ৳7,500 |
| 500–2,000 users | ৳1,200 | ৳3,000 | ৳6,000 | ৳2,400 | ৳12,600 |

---

## PWA & Platform Notes

### iPhone/iOS
- PWA works on Safari — full-screen, home screen icon, offline caching all work
- Push notifications require iOS 16.4+ AND user must add to home screen first
- Safari storage can be evicted if app not opened for weeks (WebKit policy)
- 90%+ target users are Android — iOS is secondary for now
- When scaling: wrap with Capacitor.js (not React Native/Flutter) — wraps existing PWA code, zero rewrite

### Offline Strategy
- **v1:** Cache customer list via service worker for offline reading. Block new entries until online.
- **v2:** Full offline with IndexedDB + Workbox. Sync queue. Last-write-wins conflict resolution.

---

## Customer Acquisition Plan

### Phase 1: First 50 users (face-to-face, weeks 1–4)
- Walk into shops in Mirpur, Mohammadpur, Dhanmondi
- 5 shops per day for 10 days
- Open with the pain, not the product
- Demo on YOUR phone, then install on THEIRS
- 3-minute rule: if they can't add a customer and see SMS in 3 mins, onboarding is too complex
- Leave QR code sticker at counter

### Phase 2: Facebook groups (weeks 4–8)
- Join BD business groups, pharmacy/hardware owner groups
- Post value content, not ads
- Let people ask in comments

### Phase 3: Viral SMS loop (automatic)
- Every SMS carries "— BakiTracker.com"
- 50 shops × 30 customers × 2 SMS/month = 3,000 brand impressions/month

### Phase 4: YouTube + referrals (month 2+)
- One Bangla tutorial: "দোকানের বাকি হিসাব মোবাইলে রাখুন — ফ্রি"
- Built-in referral: invite a friend → both get 1 month free

### Phase 5: Customer-driven pull (v3+)
- Customers asking their other shops to use BakiTracker
- Demand-side pull — the most powerful growth mechanism

---

## UI Design System

- **Font:** Plus Jakarta Sans (or system font fallback)
- **Colors:**
  - Overdue/negative: `#E24B4A` (red) with `#E24B4A15` background
  - Healthy/paid: `#1D9E75` (green) with `#1D9E7515` background
  - Warning/partial: `#EF9F27` (amber) with `#EF9F2718` background
  - Avatars: random from `#534AB7`, `#1D9E75`, `#EF9F27`, `#85B7EB` at 20% opacity
- **Border radius:** 12px cards, 50% avatars, 20px FAB
- **Touch targets:** minimum 44px
- **FAB:** green `#1D9E75`, bottom-right, "+" to add new baki

### Customer Profile Screen
- Top: name, phone, total বাকি (big red text)
- Calendar with red/green date dots (v1.5)
- Transaction history (newest first): date, type (বাকি/পরিশোধ), amount, note
- This is the dispute resolution screen — the killer feature

### Customer Behavior Tags (v2)
- 🟢 **ভালো** — pays within 14 days avg, balance stable/declining
- 🟡 **সতর্ক** — pays within 30 days, balance slowly growing
- 🔴 **ঝুঁকিপূর্ণ** — 30+ day avg, balance climbing, broken promises

---

## SMS Templates

**When baki is added:**
```
[Customer Name], আপনার [Shop Name]-এ ৳[amount] বাকি যোগ হয়েছে। মোট বাকি: ৳[total]।
— BakiTracker.com
```

**Auto reminder (overdue 7+ days):**
```
[Customer Name], আপনার [Shop Name]-এ ৳[total] বাকি আছে। অনুগ্রহ করে পরিশোধ করুন।
— BakiTracker.com
```

**When payment is recorded:**
```
ধন্যবাদ [Customer Name]! ৳[amount] পরিশোধ পেয়েছি। অবশিষ্ট বাকি: ৳[remaining]।
— BakiTracker.com
```

---

## Privacy Architecture (Critical for v3+)

**Cross-shop network rules:**
- NEVER show Shop A's data to Shop B
- Aggregate, anonymized signals ONLY:
  - Number of shops where phone is registered (count, no names)
  - Average payment speed (aggregate, no per-shop breakdown)
  - Overall behavior tag
  - 60+ day overdue flag (boolean, no amount)
- Shopkeepers must opt-in to both contribute and receive
- Customer consent language in SMS footer from v1
- Keep aggregation logic separate from individual shop data (clean API boundary)

---

## Competitive Landscape

| Competitor | Status | Why you win |
|-----------|--------|-------------|
| OKhata (India) | 10M+ users India | Not in BD. Hindi-first. Proves model works. |
| HisabNikash (BD) | Exists, weak UX | Poor mobile UX. No SMS. Low adoption. |
| Paper khata | Real competitor | Error-prone, no reminders, no proof. |
| WhatsApp | Current "tracking" | No structure, no totals, messages buried. |

---

## WhatsApp Chatbot Architecture (v2)

```
Shopkeeper sends WhatsApp message:
  "Karim, 01912345678, 1000"
  → WhatsApp Business API webhook
  → Haiku parses fuzzy input (Bangla/Banglish/mixed)
  → Extracts: name, phone, amount
  → POST /api/baki
  → Reply: "✅ করিম-এর বাকি ৳1,000 যোগ হয়েছে। মোট: ৳3,500"
  → SMS sent to করিম (existing flow)
```

**API options:** Meta Cloud API (free 1K convos/month) or BSPs (Infobip, Twilio)
**Start Meta Business verification process early** — takes 1-2 weeks

---

## Strategic Flywheel

1. Shopkeeper signs up → adds customers → customers get SMS
2. Customer receives SMS → taps link → sees baki → pays online (v3)
3. Shopkeeper sees online payment → tells other shopkeepers
4. Customer sees all baki in one view → asks OTHER shops to use BakiTracker
5. New shopkeepers sign up because customers are asking
6. More shops = more credit data = stronger network signals = more value = harder to leave

---

## Key Architectural Decisions (Do Not Change)

1. **Phone number is universal customer ID** — enables cross-shop network
2. **Every transaction has a timestamp** — enables behavioral analysis
3. **Never delete data, only soft-delete** — preserves credit history
4. **Customer consent language in SMS from v1** — legal foundation for network
5. **Aggregation logic separate from shop data** — clean API boundary for B2B
6. **Read-only lockout, not full lockout** — keeps users engaged, drives conversion
7. **No auto-debit for subscriptions** — BD shopkeepers don't trust it yet
8. **Convenience fee on customer, not shopkeeper** — shopkeeper promotes digital payment
9. **Correction transactions, not edits** — full audit trail, fraud prevention

---

## Build Plan Summary

| Phase | What | Sessions | Hours |
|-------|------|----------|-------|
| Phase 0 | Foundation (Supabase + FastAPI + Railway) | 1 | ~2 |
| Phase 1 | Auth (phone + OTP) | 1 | ~2 |
| Phase 2 | Core loop (customers + transactions + profile) | 2 | ~4 |
| Phase 3 | Dashboard + polish | 1 | ~2 |
| Phase 4 | SMS integration | 1 | ~2 |
| Phase 5 | Admin dashboard | 1 | ~1.5 |
| Phase 6 | Payments + subscription | 2 | ~4 |
| Phase 7 | Launch prep + first 5 shops | 1 | ~2 |
| **Total MVP** | | **10** | **~20** |

**Principle:** Vertical slices, not horizontal layers. Every session ends with something deployable. Build one complete feature end-to-end per session.

---

*Last updated: June 3, 2026*
*Status: Strategic planning complete. Ready to build Phase 0.*
*Next action: Start Phase 0 — Supabase project + FastAPI skeleton + Railway deploy.*
