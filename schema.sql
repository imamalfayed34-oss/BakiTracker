-- ============================================================
-- Baki Tracker — Database Schema
-- Run this in Supabase SQL Editor (SQL Editor → New query → paste → Run)
-- ============================================================

-- NOTE: Supabase Auth already manages the auth.users table.
-- Our `users` table below is the shopkeeper PROFILE, linked to auth.users.id.

-- ------------------------------------------------------------
-- USERS (shopkeepers) — profile linked to Supabase Auth
-- ------------------------------------------------------------
create table if not exists public.users (
  id          uuid primary key references auth.users(id) on delete cascade,
  phone       text not null,
  shop_name   text,
  created_at  timestamptz not null default now()
);

-- ------------------------------------------------------------
-- CUSTOMERS (people who owe baki)
-- ------------------------------------------------------------
create table if not exists public.customers (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.users(id) on delete cascade,
  name        text not null,
  phone       text,
  created_at  timestamptz not null default now()
);
create index if not exists idx_customers_user on public.customers(user_id);
create index if not exists idx_customers_phone on public.customers(phone);

-- ------------------------------------------------------------
-- TRANSACTIONS (individual baki / payment entries)
-- Running balance = SUM(baki) - SUM(payment) per customer
-- ------------------------------------------------------------
create table if not exists public.transactions (
  id           uuid primary key default gen_random_uuid(),
  customer_id  uuid not null references public.customers(id) on delete cascade,
  type         text not null check (type in ('baki','payment','correction')),
  amount       numeric(12,2) not null check (amount >= 0),
  note         text,
  source       text not null default 'manual' check (source in ('manual','online')),
  payment_ref  text,
  fee_amount   numeric(12,2) default 0,
  created_at   timestamptz not null default now()
);
create index if not exists idx_tx_customer on public.transactions(customer_id);
create index if not exists idx_tx_created on public.transactions(created_at);

-- ------------------------------------------------------------
-- SMS LOG
-- ------------------------------------------------------------
create table if not exists public.sms_log (
  id              uuid primary key default gen_random_uuid(),
  customer_id     uuid references public.customers(id) on delete set null,
  message         text not null,
  sent_at         timestamptz not null default now(),
  delivery_status text default 'pending'
);

-- ------------------------------------------------------------
-- SUBSCRIPTIONS (trial / paid lifecycle)
-- ------------------------------------------------------------
create table if not exists public.subscriptions (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.users(id) on delete cascade,
  plan            text not null default 'free' check (plan in ('free','standard','network')),
  trial_start     timestamptz,
  trial_end       timestamptz,
  paid_until      timestamptz,
  status          text not null default 'trial' check (status in ('trial','active','expired','cancelled')),
  payment_method  text,
  last_payment_id text,
  created_at      timestamptz not null default now()
);
create index if not exists idx_sub_user on public.subscriptions(user_id);

-- ------------------------------------------------------------
-- PAYMENTS (subscription + online baki payments)
-- ------------------------------------------------------------
create table if not exists public.payments (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references public.users(id) on delete set null,
  amount          numeric(12,2) not null,
  method          text check (method in ('bkash','sslcommerz','nagad','card')),
  transaction_id  text,
  status          text not null default 'pending' check (status in ('pending','success','failed')),
  created_at      timestamptz not null default now()
);

-- ------------------------------------------------------------
-- CUSTOMER TOKENS (for customer-facing payment portal, v1.5+)
-- ------------------------------------------------------------
create table if not exists public.customer_tokens (
  id          uuid primary key default gen_random_uuid(),
  phone       text not null,
  token       text not null unique,
  created_at  timestamptz not null default now()
);
create index if not exists idx_token on public.customer_tokens(token);

-- ------------------------------------------------------------
-- PROMISES (payment promise tracker, v2+)
-- ------------------------------------------------------------
create table if not exists public.promises (
  id              uuid primary key default gen_random_uuid(),
  customer_id     uuid not null references public.customers(id) on delete cascade,
  promised_amount numeric(12,2) not null,
  promised_date   date not null,
  status          text not null default 'pending' check (status in ('pending','fulfilled','broken')),
  created_at      timestamptz not null default now()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Each shopkeeper can only see/touch their own data.
-- ============================================================

alter table public.users          enable row level security;
alter table public.customers      enable row level security;
alter table public.transactions   enable row level security;
alter table public.sms_log        enable row level security;
alter table public.subscriptions  enable row level security;
alter table public.payments       enable row level security;
alter table public.promises       enable row level security;

-- USERS: a shopkeeper can read/update only their own profile row
create policy "own profile read"   on public.users for select using (auth.uid() = id);
create policy "own profile insert" on public.users for insert with check (auth.uid() = id);
create policy "own profile update" on public.users for update using (auth.uid() = id);

-- CUSTOMERS: scoped to the owning shopkeeper
create policy "own customers" on public.customers for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- TRANSACTIONS: scoped via the customer's owner
create policy "own transactions" on public.transactions for all
  using (exists (
    select 1 from public.customers c
    where c.id = transactions.customer_id and c.user_id = auth.uid()
  ))
  with check (exists (
    select 1 from public.customers c
    where c.id = transactions.customer_id and c.user_id = auth.uid()
  ));

-- SMS LOG: scoped via the customer's owner
create policy "own sms" on public.sms_log for all
  using (exists (
    select 1 from public.customers c
    where c.id = sms_log.customer_id and c.user_id = auth.uid()
  ))
  with check (true);

-- SUBSCRIPTIONS / PAYMENTS: scoped to the shopkeeper
create policy "own subscription" on public.subscriptions for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own payments" on public.payments for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- PROMISES: scoped via the customer's owner
create policy "own promises" on public.promises for all
  using (exists (
    select 1 from public.customers c
    where c.id = promises.customer_id and c.user_id = auth.uid()
  ))
  with check (exists (
    select 1 from public.customers c
    where c.id = promises.customer_id and c.user_id = auth.uid()
  ));

-- ============================================================
-- DONE. Verify tables exist:  Table Editor → you should see 8 tables.
-- ============================================================
