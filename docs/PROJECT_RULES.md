# PROJECT_RULES.md — Rules for AI-Assisted Development

> Every coding agent and human MUST read this file and [INDEX](INDEX.md) before coding.

## 1. Rules

| # | Rule |
|---|---|
| R01 | **Read first.** Read the docs relevant to the task (see INDEX "when to read") before writing code |
| R02 | **Follow the architecture** in ARCHITECTURE.md. Propose a change in writing before deviating |
| R03 | **Separate frontend and backend.** Frontend only calls `/api/*`; backend never serves presentation logic |
| R04 | **Types everywhere.** TypeScript `strict: true`, no `any` without a comment; Python type hints on all functions; `mypy`/`pyright` clean on `domain/` |
| R05 | **No business logic in React components.** Components render; formatting helpers live in `src/lib/` |
| R06 | **Isolate integrations.** Only `services/elexon_client.py` talks to Elexon |
| R07 | **Independently testable core.** `domain/` is pure (no I/O, no globals, no `datetime.now()`; pass time in) |
| R08 | **No duplicated logic.** One implementation of cutoff, selection, metrics. Frontend never re-implements them |
| R09 | **No unnecessary abstractions.** No plugin systems, repositories, DI containers, or base classes without 2+ real uses |
| R10 | **Never fabricate** API responses, sample numbers or metrics in the app, UI, README or video. Test fixtures must be labelled synthetic (`# SYNTHETIC`) and live under `tests/fixtures/` only |
| R11 | **Never silently change business rules.** BR-01..BR-10 change only via an edit to FORECAST_LOGIC in the same commit, plus test updates |
| R12 | **Dependencies need a reason.** Add to ARCHITECTURE §2 (or a note in the PR) with a one-line justification; pin versions |
| R13 | **No secrets in git.** Use env vars; commit `.env.example` only |
| R14 | **Config via env vars** listed in DEPLOYMENT.md. No hard-coded URLs or cutoff times outside `config.py` / `import.meta.env` |
| R15 | **Naming:** Python `snake_case` (modules, functions), `PascalCase` classes; TS `camelCase` vars, `PascalCase` components, files `PascalCase.tsx` for components; API JSON `snake_case`; units in names (`generation_mw`) |
| R16 | **Formatting:** `ruff format` + `ruff check`; `prettier` + `eslint`; run before commit |
| R17 | **Tests for critical logic:** selection, cutoff, matching, metrics, normalisation, error mapping |
| R18 | **Explicit failures.** No bare `except`, no swallowed errors. Missing data is represented, not hidden |
| R19 | **Docs stay true.** Update affected docs when behaviour changes |
| R20 | **Done means verified.** Never mark a feature complete until its acceptance criteria are checked (see §3) |
| R21 | **Anonymity.** Repo name, README, docs, commits metadata, code comments and the video must not reveal the author's name, email, GitHub handle, university or location (challenge asks for an anonymous repo). Configure `git config user.name/email` with anonymous values for this repo |
| R22 | **AI disclosure.** README must state which AI tools were used and for what |
| R23 | **Time box.** Log hours in PHASES.md; stop P1/P2 work if the budget is at risk |
| R24 | **Keep scope.** No auth, DB, microservices, extra datasets |

## 2. Definition of done (per feature)
A feature is **done** only if all are true:
1. Mapped to a requirement ID (FR/NFR) and its acceptance criteria are verified (write the evidence in the commit/PR text).
2. Types and lint pass; no new warnings.
3. Unit/integration/component tests added or updated and passing.
4. Error, empty and loading states handled (UI) / error responses per API_SPEC (backend).
5. Docs updated where behaviour or config changed.
6. Works against real Elexon data (not only fixtures) for data-facing features.
7. No fabricated data, no secrets, no stray debug code.

## 3. Pre-commit checklist
- [ ] I read the relevant docs and my change follows them
- [ ] Business rules unchanged (or FORECAST_LOGIC + tests updated)
- [ ] `ruff check`, `ruff format --check`, `pytest` pass (backend)
- [ ] `npm run lint`, `npm run typecheck`, `npm test` pass (frontend)
- [ ] No secrets, personal identifiers, or large files committed
- [ ] New env vars added to `.env.example` and DEPLOYMENT.md
- [ ] New dependency justified and pinned
- [ ] No duplicated logic; no logic leaked into React components
- [ ] Docs and README updated
- [ ] Commit message states what and why, references requirement IDs

## 4. Agent working agreement
- Make small, reviewable changes; one phase at a time.
- If a requirement is ambiguous, stop and ask; do not guess silently. Record the decision in PRD "Open questions".
- Prefer reading the real API response over assuming its shape.
