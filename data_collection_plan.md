## Phase 1, Task 1 — updated source list: (DONE)

base_url = https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/refs/heads/master/data


fpl_api = https://fantasy.premierleague.com/api

Current season (2026/27) sources:
- <fpl_api>/bootstrap-static
- <fpl_api>/fixtures
- <fpl_api>/event/{GW}/live
- <fpl_api>/element-summary/{EID}

Historical seasons sources:
- <base_url>/cleaned_merged_seasons.csv (≤23/24)
- <base_url>/<season>/merged_gw.csv (24/25, 25/26)
- <base_url>/<season>/fixtures.csv
## Phase 2 — Current season (2026/27) data acquisition via FPL API (revised)
### 2. Task: Refresh bootstrap-static + fixtures caches to current season state. (DONE — Phase 2 executed)
- Description: Run python root/src/fetch_data.py (or targeted fetches) to update bootstrap_static_latest.json / fixtures_latest.json and timestamped variants; confirm the current gameweek (late Oct 2026 → likely GW5/GW6).
- Note: Phase 2 execution completed successfully — `python root/src/fetch_data.py` ran clean and refreshed bootstrap_static_latest.json / fixtures_latest.json (now writes only the `_latest` variants, no dated variants). Current gameweek confirmation status: pending (late Oct 2026 → likely GW5/GW6).
- Current-season fixtures are handled via the FPL API `/fixtures` endpoint and cached through fetch_data.py (`fixtures_latest.json` / `fixtures_<date>.json`); historical-season fixtures come from the GitHub repo (`root/data/<season>/fixtures.csv`) and were acquired separately.
- Affected files: root/src/fetch_data.py, root/data/bootstrap_static_latest.json, root/data/fixtures_latest.json.
- Dependencies: Task 1. Effort: S (15 mins). Verification: Bootstrap shows current GW; fixtures include upcoming FDR.
### 3. Task: Add and use the per-GW live endpoint for actuals. (DONE — executed in Phase 2 run)
- Description: Add fetch_event_live(gw) hitting /api/event/{GW}/live/, then fetch for played GWs of 2026/27 (GW1–GW3) to capture actuals (points, minutes, goals, assists, defensive contribution, etc.). fetch_event_live + main() hook implemented and executed via the Phase 2 script run — event live persisted successfully (event_live_GW1.json, event_live_GW2.json, event_live_GW3.json).
- Affected files: root/src/fetch_data.py (new fetcher + cache).
- Dependencies: Task 2. Effort: S (30 mins). Verification: Live response contains per-player stats for the GW.
### 4. Task: Add per-player element-summary fetching for target players.
- Description: Use /api/element-summary/{EID}/ (via existing fetch_player_history) for the shortlist of players of interest → prior-GW history, remaining fixtures; feeds form, minutes, avg_fdr_next5 for the baseline.
- Affected files: root/src/fetch_data.py, root/data/ (per-player cached JSON).
- Dependencies: Task 2. Effort: M (1 hr). Verification: Per-player summary returns history events + remaining fixtures.
## Phase 3 — Historical seasons acquisition (DONE)
### 5. Task: Acquire 2025/26 training set from GitHub repo.
- What: Use merged_gw.csv (not gw1–38) — source: data/2025-26/gws/merged_gw.csv; acquired at root/data/2025-26/gws/merged_gw.csv. cleaned_players.csv / per-player history were superseded per the finalized source list.
- Affected files: data/2025-26/gws/merged_gw.csv (GitHub).
- Dependencies: Task 1. Effort: S (30 mins). Verification: GWs 1–38 present; target columns present.
### 6. Task: Acquire historical seasons via cleaned_merged_seasons.csv.
- What: Single long-format source for seasons ≤ ~2024/25; acquired at root/data/cleaned_merged_seasons.csv.
- Affected files: data/cleaned_merged_seasons.csv.
- Dependencies: Task 5. Effort: M (1–2 hrs). Verification: Season coverage ≥ 10 historical seasons; defcon caveats flagged.
## Phase 4 — Supporting data (DONE)
### 7. Task: Acquire fixtures/FDR.
- Description: Historical fixtures acquired from GitHub (saved under root/data/<season>/fixtures.csv): 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 (all valid, ~380 rows). 2016-17 and 2017-18 fixtures could NOT be acquired (source HTTP 404). Current-season fixtures deferred to Phase 2 (FPL API).
- Affected files: root/data/fixtures_latest.json, root/data/<season>/fixtures.csv.
- Dependencies: Phase 2/3. Effort: S (15 mins). Verification: FDR columns present.
## Phase 5 — Ingestion code update
### 8. Task: Extend fetch_data.py with fetch_event_live(gw) and persistence for element summaries; keep bootstrap/fixtures flow. (verification satisfied)
- Affected files: root/src/fetch_data.py.
- Dependencies: Tasks 2, 3, 4. Effort: M (1 day). Verification: `python root/src/fetch_data.py` ran cleanly and new cached files appeared in root/data/ (bootstrap_static_latest.json, fixtures_latest.json, event_live_GW*.json) → verification effectively satisfied.
## Phase 6 — Downstream phases (next in AGENTS.md sequence) — NEXT UP
- Status marker: Phase 2 executed successfully (bootstrap/fixtures + event live persisted); Phases 3/4 marked DONE; data-collection phases complete. Next phase: Phase 6 — Downstream phases (wire baseline xP, etc.).
### 9. Task: Wire baseline xP (form × minutes_prob × fixture_multiplier) using FPL API-derived bootstrap + fixtures + element-summary, with next-GW target metrics from event/{GW}/live/ or element-summary.