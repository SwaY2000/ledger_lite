# AI notes

## Tools

- **Claude Code (Claude Opus 5.5)** in the terminal: read the task, studied our reference service to copy
  its structure, generated most of the code, tests, Dockerfiles, CI and the first drafts of the docs,
  ran linters/tests/`docker compose` and fixed what failed.

## Decided by me, not by the AI

- Architecture: the code must follow our team's reference service exactly — Clean Architecture layers,
  `dependency-injector` containers, use cases behind `IUseCase`, repositories behind protocols, the same
  tooling (Poetry, ruff, mypy). The first AI plan ignored this; I stopped it and pointed it at the reference.
- Stack (FastAPI + SQLAlchemy 2 async + Alembic), doing both bonus items, committing step by step
  without squashing.

## Where the generated code was wrong

1. **Deadlock in concurrent transfers.** The AI locked accounts with `SELECT ... FOR UPDATE` in sorted
   order and claimed this prevents deadlocks. The concurrency test (25 parallel transfers) failed with
   `deadlock detected`: inserting the idempotency row and ledger rows takes `FOR KEY SHARE` locks on the
   account through foreign keys, and two transactions then both tried to upgrade to `FOR UPDATE`.
   Fixed with `FOR NO KEY UPDATE`, which does not conflict with `KEY SHARE` (commit `a0e8198`).
2. **Pagination broke on the second page.** The keyset condition compared the `uuid` id column with a
   cursor value bound as `varchar` (`operator does not exist: uuid < character varying`). The first page
   worked, so only the multi-page test caught it. Fixed by binding cursor values with explicit types.
3. **`reconcile --older-than-minutes 0` silently used the 15-minute default** because of
   `args.older_than_minutes or default` (0 is falsy). The unit of the use case was correct and tested;
   the bug only showed up when reproducing a lost webhook end to end in `docker compose`.
4. **Test isolation wiped the whole configuration.** The fixture called `container.reset_override()` to
   undo the fake provider, but `Configuration.from_dict` is itself an override, so every following test
   failed with `Undefined configuration option "config.debug"`. Now only the overridden providers are reset.
5. Smaller ones: `Field(None, ...)` with a positional default made mypy treat optional fields as required
   (switched to `default=` and enabled the pydantic mypy plugin); Poetry initially installed dependencies
   into an unrelated IDE virtualenv (Python 3.14) found via `VIRTUAL_ENV`, fixed with per-service 3.12 venvs.

## Time spent

About **2 hours** in total.
