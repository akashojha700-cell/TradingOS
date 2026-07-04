# ADR-009 — Single-File React SPA served by FastAPI

- **Status:** Accepted
- **Date:** 2026-07-04
- **Owner:** Engineering Lead
- **Reviewers:** Product Owner
- **Related:** [`ADR-001-Free-First`](./ADR-001-Free-First.md), [`ADR-004-Modular-Monolith`](./ADR-004-Modular-Monolith.md), [Engineering Principles §7 & §8](../../governance/ENGINEERING_PRINCIPLES.md)

## Context

Sprint 2 needed a user-facing product. Swagger was fine for the engineer but useless for the primary user, who is not a developer.

Three shapes were on the table for the frontend:

1. **Full React project** — Vite/Next.js, Node build toolchain, separate deploy, its own Docker image.
2. **Server-rendered templates** — Jinja from FastAPI, small islands of interactivity if needed.
3. **Single-file React SPA** — one HTML file, React UMD from CDN, Babel Standalone in the browser, Tailwind CDN, Chart.js CDN. Served as a static asset by FastAPI.

Forces:

- The team is one engineer.
- The architecture is a **modular monolith** (ADR-004). Splitting deploy shape now adds friction.
- **Free-first** (ADR-001). A Node build stack costs local disk, CI time, and cognitive overhead.
- The UI is a **read-heavy dashboard with a few forms**, not a document-editor. Client-side rendering fits.
- Zero users today. Every optimisation for scale is premature.

## Decision

Ship the frontend as **one self-contained HTML file** at `app/web/index.html`, served by FastAPI at `/`. React 18, ReactDOM, Babel Standalone, Tailwind, and Chart.js are all loaded from CDNs. There is **no build step, no npm, no Node** in the repository.

FastAPI serves the SPA via a small route (`app/api/v1/web.py`) that reads the HTML file and returns it as `HTMLResponse`. The SPA talks to the same origin at `/api/v1/*` — no CORS, no separate deploy.

## Alternatives Considered

1. **Full React project (Vite + npm).** Modern, familiar, well-documented.
   *Rejected for now.* Adds a Node toolchain, a build step, a second Dockerfile stage, more moving parts to maintain. The value it unlocks (code splitting, tree-shaking, TypeScript) does not yet earn the cost for a single-engineer MVP.
2. **Server-rendered Jinja templates.** Simple.
   *Rejected.* Poor fit for a live-updating dashboard with charts. Would push us to a lot of htmx or Alpine gluing later; net complexity larger than a single React file.
3. **Static site + separate frontend deploy.** Cleanest separation.
   *Rejected.* Same-origin API calls avoid CORS; single-container deploy stays simple; and until the frontend is meaningfully larger than the backend, splitting deploys is premature.

## Consequences

**Positive.**

- **Zero build step.** `docker compose up` gives a fully working UI. No Node, no pnpm, no build cache invalidation.
- **Single origin.** No CORS setup, no double-deploy, no separate reverse proxy config.
- **One container.** Deployments and rollbacks stay atomic.
- **Provider-neutral, free-first path preserved.** All external assets are widely mirrored CDNs.
- **Fastest path to product feedback.** The user sees a real terminal UI without a two-week frontend project.

**Negative / cost.**

- **In-browser Babel** is slower than a pre-compiled bundle. First paint takes ~1–2s on a slow connection. Acceptable for a single-user MVP; unacceptable at scale.
- **No code splitting** — one file, always loaded fully. Fine until the SPA exceeds ~150 KB; today ~75 KB.
- **No TypeScript** — plain JSX. Type discipline lives at the API boundary (Pydantic) and in the developer's head.
- **CDN dependency at page load** — unavailable if the user is offline. Mitigation: acceptable for a browser-only product; can pre-fetch and cache assets locally in a later sprint if needed.
- **Editor tooling weaker** — no IDE React-project features on the HTML file. Mitigated by keeping components small and idiomatic.

**Operational impact.**

- The SPA is a single file in `app/web/`. Version-controlled and reviewable like any other source file.
- No new runtime dependencies were added.
- The API surface is unchanged.

**Testing implications.**

- Backend tests are untouched.
- The SPA is not unit-tested in this sprint. When the file grows past a threshold (see Future Review), we lift it into a real build.

**Migration effort if revisited.**

- Moving to a Vite/React project is a well-known migration: copy the component tree, add Vite config, add TS if desired, wire the FastAPI static-file mount to the built output. No architectural change on the backend.

## Future Review

Move to a full frontend project when **any** of these fire:

- The SPA file exceeds ~1500 lines / ~150 KB.
- We need TypeScript, Storybook, or unit-tested components.
- Multiple engineers work on the UI concurrently.
- We need code splitting because first paint gets slow.
- We ship a public marketing site and want SSR/SSG.

Scheduled review: end of Sprint 5 (Dashboard maturity), or earlier if a trigger fires.
