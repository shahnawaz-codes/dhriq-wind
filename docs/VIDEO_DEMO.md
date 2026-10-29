# VIDEO_DEMO.md — Demo Video Plan (max 10 min, unlisted YouTube)

> Evaluation **starts with the video**. Do not submit without it.
> Use only real numbers from the running app. Fill the `[ ]` slots after Phase 5.
> Related: [PRD](PRD.md) · [FORECAST_LOGIC](FORECAST_LOGIC.md) · [ARCHITECTURE](ARCHITECTURE.md) · [ANALYSIS_NOTES (Phase 5)](PHASES.md)

## Recording tips
Screen + voice, 1080p, close other tabs, zoom browser to 110%, rehearse once, record the live deployed URL. Do not show your name, email or GitHub profile (anonymity). Keep to the time boxes.

## Part 1 — Customer presentation (≤ 5:00)

| Time | Segment | Say / show |
|---|---|---|
| 0:00–0:40 | Business problem | "You buy day-ahead power for tomorrow. Wind output is uncertain. You decide using forecasts, so you need to know which forecast you had, and how reliable it is." |
| 0:40–1:30 | Dashboard tour | Header, assumptions banner, KPI cards, chart, table. Say what each answers |
| 1:30–2:30 | Forecast selection | "For each hourly point we use the latest forecast published before the decision cutoff — never later ones (accuracy is measured at hourly points because WINDFOR publishes hourly forecasts)." Open Method popover. Show one record: forecast publish time before cutoff. Demonstrate cutoff selector (P0). Say it is provisional and adjustable |
| 2:30–4:00 | Accuracy analysis | Read MAE, RMSE, bias in MW with plain meaning. Show best/worst day from the chart or daily view. Change the cutoff (P0 selector) and show the effect. Use real values `[MAE] [RMSE] [bias] [coverage]` |
| 4:00–5:00 | Value and limits | Value: size your safety margin, see forecast reliability by day. Limits: January only, national wind only, cutoff assumed, no prices or weather, no buy recommendations. Next steps: other months/fuels, per-horizon accuracy, confirm cutoff with you; next step: confirm whether the forecast is an hourly average |

## Part 2 — Technical review (≤ 5:00)

| Time | Segment | Say / show |
|---|---|---|
| 5:00–5:45 | Architecture | ARCHITECTURE diagram: React on Vercel → FastAPI on Heroku (Docker) → Elexon. No DB, why |
| 5:45–6:30 | Elexon integration | `elexon_client.py`: params, weekly chunks, retries, both response shapes, WIND filter; mention what was verified in API_FINDINGS |
| 6:30–7:15 | Data processing | `normalize.py` and `matching.py`: validation, dedupe, expected 744-period grid (hourly), missing statuses, :30 exclusion guard |
| 7:15–8:15 | Forecast-selection logic | `cutoff.py` + `selection.py` and FORECAST_LOGIC: cutoff rule, inclusive boundary, leakage prevention, config; show the three boundary tests |
| 8:15–8:50 | Metrics + testing | `metrics.py` definitions; test counts/coverage; run `pytest` live |
| 8:50–9:25 | Docker and deployment | Dockerfiles, compose, env vars, CORS, health check, public URLs |
| 9:25–10:00 | Trade-offs and practices | Recharts vs alternatives, no DB, stdlib maths, split hosting, docs-first and PROJECT_RULES, AI tool use (disclosed), remaining risks |

## Submission checklist
- [ ] Video ≤ 10:00 total, both parts present, **unlisted** on YouTube, opens in incognito
- [ ] Public GitHub repo with an **anonymous random name**; no personal identifiers anywhere (code, docs, commits, video)
- [ ] README: file/directory details, how to start, link to the deployed app, **AI tools disclosure**
- [ ] Deployed app URL works in incognito (frontend + backend)
- [ ] Every URL submitted was opened in incognito mode and verified
- [ ] Total time logged ≤ 16 h (PHASES hours log)
- [ ] Form submitted: https://forms.cloud.microsoft/r/FTX6K2bbnU
