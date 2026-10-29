# Documentation Index

Start here. Read the "When to consult" column before working on a task.

| Document | Contents | When to consult |
|---|---|---|
| [../README.md](../README.md) | Overview, setup, structure, AI disclosure | First contact; setup; submission |
| [PRD.md](PRD.md) | Requirements (FR/NFR IDs), priorities, user stories, open questions | Before any feature; when scope is unclear |
| [PHASES.md](PHASES.md) | 16-hour plan, tasks, acceptance, hours log | Planning; deciding what to build next; time tracking |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data flow, error handling, caching, decisions | Before creating modules or adding dependencies |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Elexon fields (with verification status), internal models | Writing the Elexon client, normaliser, models |
| [FORECAST_LOGIC.md](FORECAST_LOGIC.md) | **Cutoff, selection, matching, metrics, data quality rules** | Any work on `domain/`, metrics, tests, API semantics. Read first |
| [API_SPEC.md](API_SPEC.md) | Our `/api/*` endpoints, params, responses, errors | Backend routes; frontend API client |
| [UI_UX.md](UI_UX.md) | Design tokens, layout, components, states, accessibility | Any frontend work |
| [PROJECT_RULES.md](PROJECT_RULES.md) | Strict dev rules, definition of done, commit checklist | Before every coding session and commit |
| [TESTING.md](TESTING.md) | Test plan, boundary cases, commands | Writing tests; before declaring done |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Env vars, Docker, Heroku/Vercel, CORS, verification | Docker/deploy phase; environment problems |
| [VIDEO_DEMO.md](VIDEO_DEMO.md) | Video outline and submission checklist | Recording; final submission |
| `API_FINDINGS.md` *(created in Phase 1)* | Real API findings and samples | After Phase 1; settle all [VERIFY] items |
| `ANALYSIS_NOTES.md` *(created in Phase 5)* | Real results and talking points | Video preparation |

## Stable IDs
`FR-xx` / `NFR-xx` / `US-xx` requirements (PRD) · `BR-xx` business rules (FORECAST_LOGIC) · `Q-xx` open questions (PRD §12) · `AD-xx` architecture decisions (ARCHITECTURE §13) · `R-xx` risks, `R01..R24` rules (PROJECT_RULES).

## Conflict rule
If documents disagree, precedence is: **FORECAST_LOGIC > API_SPEC > DATA_DICTIONARY > ARCHITECTURE > PRD > others**. Fix the conflict in the same commit.
