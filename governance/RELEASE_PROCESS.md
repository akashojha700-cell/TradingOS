# Release Process

> **Status:** Canonical · **Owner:** Engineering Lead · **Last reviewed:** 2026-06-28
> Authoritative release policy. Engineer-facing playbook lives in [`docs/RELEASE_PROCESS.md`](../docs/RELEASE_PROCESS.md).

## Table of Contents

- [Branching strategy](#branching-strategy)
- [Commit convention](#commit-convention)
- [Versioning](#versioning)
- [Release cadence](#release-cadence)
- [Release workflow](#release-workflow)
- [Hotfix process](#hotfix-process)
- [Rollback strategy](#rollback-strategy)
- [Tagging and artifacts](#tagging-and-artifacts)
- [Communication](#communication)

---

## Branching strategy

Trunk-based with short-lived feature branches.

| Branch | Purpose | Lifespan |
|---|---|---|
| `main` | Always shippable | Permanent |
| `feat/<slug>` | New feature | < 5 days |
| `fix/<slug>` | Bug fix | < 2 days |
| `refactor/<slug>` | No behaviour change | < 5 days |
| `chore/<slug>` | Tooling, docs, deps | < 2 days |
| `hotfix/<slug>` | Production emergency | < 24 hours |
| `release/<vX.Y.Z>` | Optional release candidate stabilisation | Created only when needed |

Rules:

- `main` is protected. No direct pushes. PR + 1 approval + green CI.
- Long-lived branches are a smell. If a branch ages past its window, rebase to `main` and split.
- Squash-merge into `main`; preserve a clean linear history.

## Commit convention

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | Use |
|---|---|
| `feat` | New user-visible feature |
| `fix` | Bug fix |
| `refactor` | Internal change, no behaviour difference |
| `perf` | Performance improvement |
| `test` | Tests only |
| `docs` | Documentation only |
| `build` | Build system, Dockerfile, CI |
| `chore` | Tooling, deps, repo hygiene |
| `revert` | Revert a previous commit |

Breaking changes carry a `!` (e.g. `feat(api)!: rename /events to /v1/events`) and a `BREAKING CHANGE:` footer.

## Versioning

[Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`.

| Bump | When |
|---|---|
| MAJOR | Breaking API or schema change |
| MINOR | Backwards-compatible feature |
| PATCH | Bug fix, doc-only, internal cleanup |

Pre-MVP releases use the `0.x` track. Once the MVP loop closes end-to-end, we cut `1.0.0`.

The single source of truth for the version is `app/__init__.__version__`. It must match:

- `APP_VERSION` in `.env.example`
- The latest section in `docs/CHANGELOG.md`
- The git tag

## Release cadence

| Cadence | Trigger |
|---|---|
| **Per sprint** | Default. Cut a release at sprint close once DoD passes. |
| **Ad-hoc** | A high-value fix or feature that should not wait for sprint close. |
| **Hotfix** | Production incident. See [Hotfix process](#hotfix-process). |

Cadence is a target, not a deadline. Quality gates dominate calendar pressure.

## Release workflow

1. **Freeze window** — declare a freeze on `main` for non-release commits (Slack `#engineering`).
2. **Pre-flight**
   - CI green on `main`.
   - CHANGELOG promoted: `[Unreleased]` → `[X.Y.Z] — YYYY-MM-DD`.
   - `__version__`, `.env.example`, README all updated.
   - Sprint document closed under `docs/sprint/`.
3. **Tag**
   - `git tag -a vX.Y.Z -m "Release X.Y.Z"`
   - `git push origin vX.Y.Z`
4. **Build**
   - CI builds the Docker image and pushes to the registry (when configured).
   - Image tagged `tradingos:X.Y.Z` and `tradingos:latest`.
5. **Verify**
   - Deploy to staging (when available).
   - Smoke-test `/`, `/health`, `/version`, plus the sprint's headline feature.
6. **Promote**
   - Roll forward to production.
7. **Announce**
   - Short note in `#releases` linking the CHANGELOG entry and the demo.

## Hotfix process

Triggered by a production incident or a critical security issue.

1. Open `hotfix/<short-slug>` from the latest release tag.
2. Smallest possible fix. No drive-by refactors.
3. Bump PATCH version (`X.Y.Z+1`).
4. CHANGELOG entry under a new `[X.Y.Z+1]` section with an **Incident** note.
5. PR + 1 approval + CI green.
6. Tag, build, deploy as above.
7. Forward-merge `hotfix/...` into `main` to avoid regression.
8. File a follow-up to write a short incident note in [`docs/LESSONS_LEARNED.md`](../docs/LESSONS_LEARNED.md).

## Rollback strategy

Rollbacks are first-class — they are the *fastest* mitigation, not a defeat.

| Step | Action |
|---|---|
| 1 | Identify the last known-good image tag (`tradingos:X.Y.Z-1`). |
| 2 | Re-deploy that tag. SQLite migrations apply automatically and are designed to be backwards-compatible. |
| 3 | Mark the bad release in CHANGELOG with `**ROLLED BACK on YYYY-MM-DD**`. |
| 4 | Open a hotfix branch from the good tag. |
| 5 | Write an incident note (see Hotfix step 8). |

**Migrations must be backwards-compatible by default.** Any forward-only migration requires an ADR before merge.

## Tagging and artifacts

- Git tags are immutable and signed where possible.
- Docker images are pushed with both `X.Y.Z` and `latest` tags.
- `latest` is *advisory*; production always pins a specific version.

## Communication

| Audience | Channel | When |
|---|---|---|
| Engineering | `#engineering` | Freeze, tag, deploy |
| Stakeholders | `#releases` or weekly digest | Post-deploy |
| Users (future) | In-app changelog | Major / minor releases |
