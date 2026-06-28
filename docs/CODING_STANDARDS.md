# Coding Standards

## Language & versions

- Python **3.12** only.
- All public functions and methods carry full type hints.
- `from __future__ import annotations` at the top of every module that defines types.

## Style

- Format with `black` (line length 88).
- Lint with `ruff` (default ruleset + `I`, `B`, `UP`, `C4`).
- Type-check with `mypy --strict` for new code; legacy areas may opt out via per-file pragmas.

## Documentation

- Every module starts with a one-paragraph docstring.
- Every public function/class has a docstring describing **what** it does and **why** a caller would use it.
- Use Google-style sections (`Args:`, `Returns:`, `Raises:`) for non-trivial functions.

## Architecture rules

- API routers **must not** import from `app/repositories/` or talk to the DB directly.
- Services **must not** import FastAPI types (`Request`, `Response`, `Depends`).
- Repositories **must not** import from services.
- Cross-layer types live in `app/schemas/` (wire) or as plain dataclasses in services.

## Configuration

- No hardcoded URLs, paths, or secrets. Add to `Settings` and source from env.
- Never log secrets. Use `_redact_db_url` (or equivalent) before logging connection strings.

## Logging

- Use `app.core.logging.get_logger(__name__)`.
- Use structured fields, not f-strings: `logger.info("event.processed", event_id=eid)`.
- Log at INFO for state changes, DEBUG for diagnostic detail, WARNING/ERROR for problems.

## Testing

- `pytest` only.
- Unit tests are fast and isolated. Integration tests use the FastAPI `TestClient` against an in-memory SQLite.
- Every new endpoint ships with at least one happy-path test and one validation/error test.
- Tests must not depend on external services. Use fakes/stubs.

## Errors

- Raise domain exceptions inside services. Translate to HTTP at the API boundary.
- Never `except Exception: pass`. Either handle and log, or let it propagate.

## Dependencies

- Add a library only when it provides clear value over stdlib.
- Pin exact versions in `requirements.txt`.
- Prefer free, OSS, and locally-runnable libraries.

## Naming

- `snake_case` for functions, variables, files.
- `PascalCase` for classes.
- `SCREAMING_SNAKE_CASE` for module-level constants.
- Settings env vars are `UPPER_SNAKE_CASE`.

## Commits

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`.
- One logical change per commit.

## Definition of Done (per change)

- Type-checks pass.
- Tests pass locally and in CI.
- New behaviour has tests.
- Documentation touched if behaviour changed.
- Logging added for any new state change.
- DECISIONS.md updated if an architectural choice was made.
