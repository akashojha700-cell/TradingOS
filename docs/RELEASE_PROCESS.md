# Release Process — Engineer Playbook

> Canonical policy: [`governance/RELEASE_PROCESS.md`](../governance/RELEASE_PROCESS.md). This document is the working playbook with copy-pasteable commands and a pre-flight checklist.

## Table of Contents

- [TL;DR](#tldr)
- [Pre-flight checklist](#pre-flight-checklist)
- [Release commands](#release-commands)
- [Tag conventions](#tag-conventions)
- [Hotfix playbook](#hotfix-playbook)
- [Rollback playbook](#rollback-playbook)
- [Post-release](#post-release)
- [Troubleshooting](#troubleshooting)

---

## TL;DR

1. Pass the [pre-flight checklist](#pre-flight-checklist).
2. Bump version + CHANGELOG + `.env.example`.
3. Tag `vX.Y.Z` and push.
4. CI builds + tags Docker image.
5. Deploy. Smoke-test. Announce.

## Pre-flight checklist

Before cutting a release from `main`:

- [ ] CI green on the head of `main`.
- [ ] No open P0/P1 issues against the scope being released.
- [ ] `pytest -ra` passes locally.
- [ ] `docker compose up --build` returns 200 from `/`, `/health`, `/version` end-to-end.
- [ ] Sprint document under `docs/sprint/` is closed (acceptance criteria checked, retrospective written).
- [ ] `app/__init__.__version__`, `APP_VERSION` in `.env.example`, and the new CHANGELOG header all match.
- [ ] Diff between previous tag and HEAD has been skimmed for surprises (`git log v<prev>..HEAD --oneline`).

## Release commands

```bash
# 1. Confirm head
git switch main
git pull --ff-only

# 2. Bump the version
#    Update app/__init__.py __version__ and .env.example APP_VERSION
#    Promote docs/CHANGELOG.md [Unreleased] → [X.Y.Z] - YYYY-MM-DD

# 3. Commit the bump
git add app/__init__.py .env.example docs/CHANGELOG.md
git commit -m "chore(release): vX.Y.Z"

# 4. Tag and push
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin main
git push origin vX.Y.Z

# 5. Build image locally if CI cannot (free-tier fallback)
docker build -t tradingos:X.Y.Z .
docker tag tradingos:X.Y.Z tradingos:latest
```

## Tag conventions

| Tag | Shape | Notes |
|---|---|---|
| Release | `vX.Y.Z` | Signed where possible. Immutable. |
| Release candidate | `vX.Y.Z-rcN` | Optional, when stabilisation is needed. |
| Hotfix | `vX.Y.Z+1` | Patch bump from the release being fixed. |

Never reuse a tag. Never delete a tag. If a release is bad, ship a new one and mark the bad tag in CHANGELOG.

## Hotfix playbook

A production-impacting issue cannot wait for the next sprint release.

```bash
# 1. Branch from the broken release tag
git switch -c hotfix/<slug> vX.Y.Z

# 2. Smallest possible fix
#    + test that reproduces the issue
#    + CHANGELOG entry under [X.Y.Z+1] with an "Incident" note

# 3. PR + review + CI

# 4. Cut the hotfix release
git tag -a vX.Y.Z+1 -m "Hotfix X.Y.Z+1 - <one-line summary>"
git push origin vX.Y.Z+1

# 5. Forward-merge to main so the fix is not lost
git switch main
git merge --no-ff hotfix/<slug>
git push origin main
```

Mandatory follow-up: add a short entry to [`LESSONS_LEARNED.md`](./LESSONS_LEARNED.md) within 48 hours describing what failed and what changes prevent recurrence.

## Rollback playbook

Roll back is the *fastest* mitigation. Use it.

1. Identify the last known-good tag.
2. Redeploy the image: `docker run tradingos:<prev>` or your orchestrator's equivalent.
3. Verify `/health` and the previously-working sprint feature.
4. Edit `docs/CHANGELOG.md` to add `**ROLLED BACK on YYYY-MM-DD — see incident note**` under the bad release.
5. Open `hotfix/<slug>` from the good tag.
6. File an incident note (see Hotfix step above).

> Migrations land backwards-compatible by default. If a release ships a forward-only migration, the rollback also requires a data-migration step; do not introduce forward-only migrations without an ADR.

## Post-release

- [ ] Smoke test in production: `/`, `/health`, `/version`, plus the sprint headline feature.
- [ ] Announce in `#releases` with CHANGELOG link.
- [ ] Open the next sprint document from `docs/sprint/TEMPLATE.md`.
- [ ] Reset `[Unreleased]` in CHANGELOG.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Image won't start | Missing env var | Compare runtime env against `.env.example`. |
| `/health` returns `degraded` | DB probe failing | Check storage volume mount + permissions. |
| CI build fails on tag push | Tag points to commit not on `main` | Ensure the tag is on the merged commit, not a local one. |
| Wrong version reported by `/version` | `__version__` not bumped or env override stale | Confirm `app/__init__.__version__`, redeploy. |
| Logs missing request-id | Background task created without context copy | Re-bind `contextvars` inside the task. |
