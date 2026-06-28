# Contributing

## Workflow

1. Pick (or open) a backlog item in [`BACKLOG.md`](BACKLOG.md).
2. Create a branch: `feat/<short-description>` or `fix/<short-description>`.
3. Make small, reviewable commits — one logical change per commit.
4. Open a PR against `main` with the linked backlog ID in the title.
5. CI must be green. At least one reviewer approves.
6. Squash-merge.

## Branch naming

- `feat/...` — new feature
- `fix/...` — bug fix
- `refactor/...` — no behaviour change
- `docs/...` — documentation only
- `chore/...` — tooling, deps, CI
- `test/...` — tests only

## Pull request checklist

- [ ] Tests added/updated and passing
- [ ] Type checks pass
- [ ] Documentation updated where relevant (`docs/`, docstrings, README)
- [ ] No secrets, no committed `.env`
- [ ] No hardcoded config values introduced
- [ ] CHANGELOG entry under "Unreleased"

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
uvicorn app.main:app --reload
```

## Review priorities

Reviewers check, in order:

1. **Architecture** — does this respect the layered boundaries?
2. **Tests** — do they cover the new behaviour and edge cases?
3. **Configuration** — anything new behind a flag, in `Settings`, in `.env.example`?
4. **Logging & observability** — new state changes logged structurally?
5. **Style** — readability, naming, comments.

## When in doubt

If a requirement is ambiguous, **do not invent architecture**. Open a TODO comment, file a backlog item, or start a discussion in the PR. ChatGPT remains the system architect; the engineer's job is to implement clearly and surface ambiguity.

## Code of conduct

Be direct, be respectful, focus on the work. Critique code, not people.
