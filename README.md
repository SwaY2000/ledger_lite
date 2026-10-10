# LedgerLite

Two services that keep internal USD accounts:

- **wallet-service** — balances in USD and credits, deposits through an external payment provider,
  idempotent transfers, credit purchases and operation history. PostgreSQL.
- **provider-mock** — minimal in-memory payment provider that creates invoices and sends signed
  webhooks (optionally twice, or not at all).

## Quick start

```bash
docker compose up --build        # postgres + provider-mock (:8081) + wallet-service (:8080)
```

`docker compose` reads `.env.example` and then an optional `.env`, so the stack starts from a clean
clone. Copy `.env.example` to `.env` to override values; the repository contains no real secrets.
Host ports can be changed with `WALLET_HOST_PORT`, `PROVIDER_HOST_PORT` and `POSTGRES_HOST_PORT`.

Create accounts (the API key is printed once; only its SHA-256 hash is stored):

```bash
docker compose exec wallet-service python -m src.cli create-account --name alice
docker compose exec wallet-service python -m src.cli create-account --name bob
```

Walk through the main flow (API docs: http://localhost:8080/v1/docs, http://localhost:8081/docs):

```bash
W=http://localhost:8080; P=http://localhost:8081; PK=change-me-provider-api-key
ALICE=<alice api_key>; BOB_ID=<bob account_id>

# 1. Deposit: creates an invoice at the provider, returns pay_url
curl -X POST $W/v1/deposits -H "X-API-Key: $ALICE" -H 'Content-Type: application/json' -d '{"amount": "10.00"}'

# 2. "Pay" it at the provider; the webhook is delivered twice with the same event_id
curl -X POST $P/invoices/<invoice_id>/simulate -H "Authorization: Bearer $PK" -H 'Content-Type: application/json' \
  -d '{"status": "paid", "paid_amount": "10.00", "deliver_webhook": true, "duplicate": true}'

curl $W/v1/accounts/me -H "X-API-Key: $ALICE"          # balance_usd: "9.85" (credited once)

# 3. Idempotent transfer: repeat it, the money moves once
curl -X POST $W/v1/transfers -H "X-API-Key: $ALICE" -H 'Idempotency-Key: t-1' -H 'Content-Type: application/json' \
  -d "{\"to_account_id\": \"$BOB_ID\", \"amount\": \"5.00\"}"

# 4. Buy credits, read the history
curl -X POST $W/v1/purchases -H "X-API-Key: $ALICE" -H 'Content-Type: application/json' -d '{"credits": 30}'
curl "$W/v1/transactions?limit=20" -H "X-API-Key: $ALICE"

# 5. Lost webhook: simulate with "deliver_webhook": false, then reconcile
docker compose exec wallet-service python -m src.cli reconcile --older-than-minutes 0
```

## Tests and linters

Requires Python 3.12, Poetry 2.x and a running PostgreSQL (the one from compose is fine; tests use a
separate `ledgerlite_test` database that is created automatically).

```bash
docker compose up -d postgres

cd wallet_service
poetry install
poetry run ruff check . && poetry run ruff format --check . && poetry run mypy
poetry run pytest                  # TEST_DATABASE_URL overrides the default test database URL

cd ../provider_mock
poetry install
poetry run pytest
```

CI (`.github/workflows/ci.yaml`) runs ruff, mypy, `alembic upgrade head` + `alembic check` and pytest
against a PostgreSQL service container for both services, and builds the Docker images.

What is covered: money tables from the task (fee and credit price, plus tier boundaries), amount
parsing (number or more than two decimals → 422), webhook signature (valid, wrong, tampered, expired,
future, missing), duplicate and concurrent duplicate webhooks, late webhook after the deposit is closed,
`Idempotency-Key` replay and conflict, insufficient funds, concurrent transfers (never negative, no
deadlocks in opposite directions), provider timeout / unreachable → 502, pagination, rate limit and
reconciliation.

## Architecture

```
            X-API-Key                        Authorization: Bearer
  client ─────────────► wallet-service ──────────────────────────► provider-mock
                          │      ▲    POST /invoices, GET /invoices/{id}  │
                          │      │                                       │
                          │      └──── POST /v1/webhooks/provider ◄──────┘
                          ▼             X-Signature + X-Timestamp
                      PostgreSQL
```

Both services follow the same Clean Architecture layout and use `dependency-injector`
(the structure mirrors our team's reference service):

```
src/
  entities/        domain models and rules (money rounding, fee, credit tiers, balance invariants)
  use_cases/       one class per business operation, IUseCase[Input, Output]
  services/        provider client, webhook signature verifier, deposit settlement, API keys
  repositories/    protocols + PostgreSQL (SQLAlchemy) implementations, unit of work, mappers
  infrastructure/  database engine, HTTP client, rate limiter
  presentation/    FastAPI routes, request/response schemas, auth and rate-limit dependencies
  containers/      DI containers; routes receive use cases via Provide[...]
  cli/             create-account, reconcile
```

**Framework choice.** FastAPI + Pydantic v2: async I/O for the provider calls, strict request
validation (amounts are parsed by one custom type that rejects numbers and extra decimals) and
OpenAPI docs for free. SQLAlchemy 2 (async, asyncpg) gives explicit control over transactions and row
locks; Alembic manages the schema. `dependency-injector` keeps use cases free of framework code and
makes it trivial to swap the provider client for a fake in tests.

## Key decisions and trade-offs

1. **Money is `Decimal` end to end.** JSON amounts are strings, the DB uses `NUMERIC(18,2)`, all
   rounding (`ROUND_HALF_UP` to cents) lives in `entities/money`. Balances also have
   `CHECK (balance_usd >= 0)` as a last line of defense behind the application check.
2. **Exactly-once webhook crediting.** The signature is checked over the raw body bytes before parsing.
   Inside one transaction: insert `event_id` (unique, `ON CONFLICT DO NOTHING` → duplicate is a no-op),
   lock the deposit row, apply the status only if the deposit is still `pending`. A webhook for an
   unknown invoice returns 404 and is *not* recorded, so a redelivery can still succeed.
3. **Idempotent transfers in the same transaction as the money movement.** The idempotency record is
   inserted first; a concurrent request with the same key blocks on the unique index until the first
   one commits, then replays the stored response (or gets 409 for a different body). Business errors
   roll back the record too, so a transfer rejected for insufficient funds can be retried with the
   same key later.
4. **Row locks without deadlocks.** Accounts are locked in ascending id order with
   `FOR NO KEY UPDATE`. Plain `FOR UPDATE` deadlocked under load because foreign keys from ledger and
   idempotency rows take `KEY SHARE` locks on the account first (found by the concurrency tests).
5. **No network I/O inside DB transactions.** A deposit is committed as `pending`, then the provider is
   called with a 5 s timeout. Timeout, connection error or 5xx → `502 provider_unavailable`
   (4xx/malformed response → `502 provider_error`) and the deposit is marked `failed`.
6. **Cursor (keyset) pagination** for history: pages stay stable while new operations arrive.
7. **API keys are hashed with SHA-256**, not bcrypt/argon2: they are 256-bit random tokens, not
   passwords, so a fast hash is safe and allows an indexed lookup on every request.

## Simplifications and what is not done

- **Deposit whose invoice creation timed out.** It is marked `failed`, but the provider may have created
  the invoice anyway; a later payment for it would be ignored. A production version would keep such
  deposits in an `unknown` state and reconcile them by `external_id`.
- **Webhook racing invoice creation** (arrives before `invoice_id` is saved) gets 404 and relies on the
  provider retrying; the mock does not retry deliveries.
- **Rate limiter is in-memory** (per process, reset on restart). Behind `IRateLimiter`, so a Redis
  implementation is a drop-in replacement for multiple replicas.
- **Reconciliation is a CLI command**, not a scheduled job (cron / a sidecar would call it).
- **Purchases are not idempotent** (the task requires `Idempotency-Key` only for transfers); a retry after
  a network error may buy twice.
- Accounts are created through the CLI only; there is no admin API. The provider mock keeps state in
  memory and `pay_url` points to a page that does not exist.
