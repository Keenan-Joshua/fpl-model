## Phase 1, Task 1 — updated source list:

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
### 2. Task: Refresh bootstrap-static + fixtures caches to current season state.
- Description: Run python root/src/fetch_data.py (or targeted fetches) to update bootstrap_static_latest.json / fixtures_latest.json and timestamped variants; confirm the current gameweek (late Oct 2026 → likely GW5/GW6).
- Affected files: root/src/fetch_data.py, root/data/bootstrap_static_latest.json, root/data/fixtures_latest.json.
- Dependencies: Task 1. Effort: S (15 mins). Verification: Bootstrap shows current GW; fixtures include upcoming FDR.
### 3. Task: Add and use the per-GW live endpoint for actuals.
- Description: Add fetch_event_live(gw) hitting /api/event/{GW}/live/, then fetch for played GWs of 2026/27 (GW1–GW3) to capture actuals (points, minutes, goals, assists, defensive contribution, etc.).
- Affected files: root/src/fetch_data.py (new fetcher + cache).
- Dependencies: Task 2. Effort: S (30 mins). Verification: Live response contains per-player stats for the GW.
### 4. Task: Add per-player element-summary fetching for target players.
- Description: Use /api/element-summary/{EID}/ (via existing fetch_player_history) for the shortlist of players of interest → prior-GW history, remaining fixtures; feeds form, minutes, avg_fdr_next5 for the baseline.
- Affected files: root/src/fetch_data.py, root/data/ (per-player cached JSON).
- Dependencies: Task 2. Effort: M (1 hr). Verification: Per-player summary returns history events + remaining fixtures.
## Phase 3 — Historical seasons acquisition (confirmed sound, unchanged)
### 5. Task: Acquire 2025/26 training set from GitHub repo.
- What: cleaned_players.csv, gws/gw1–38.csv (or merged_gw.csv), per-player history.csv.
- Affected files: data/2025-26/... (GitHub).
- Dependencies: Task 1. Effort: S (30 mins). Verification: GWs 1–38 present; target columns present.
### 6. Task: Acquire historical seasons via cleaned_merged_seasons.csv.
- What: Single long-format source for seasons ≤ ~2024/25.
- Affected files: data/cleaned_merged_seasons.csv.
- Dependencies: Task 5. Effort: M (1–2 hrs). Verification: Season coverage ≥ 10 historical seasons; defcon caveats flagged.
## Phase 4 — Supporting data
### 7. Task: Acquire fixtures/FDR.
- Description: Prefer FPL API fixtures/ for current season (already cached); use GitHub data/<season>/fixtures.csv for historical seasons.
- Affected files: root/data/fixtures_latest.json, data/<season>/fixtures.csv.
- Dependencies: Phase 2/3. Effort: S (15 mins). Verification: FDR columns present.
## Phase 5 — Ingestion code update
### 8. Task: Extend fetch_data.py with fetch_event_live(gw) and persistence for element summaries; keep bootstrap/fixtures flow.
- Affected files: root/src/fetch_data.py.
- Dependencies: Tasks 2, 3, 4. Effort: M (1 day). Verification: python root/src/fetch_data.py runs cleanly; new cached files appear in root/data/.
## Phase 6 — Downstream phases (next in AGENTS.md sequence)
### 9. Task: Wire baseline xP (form × minutes_prob × fixture_multiplier) using FPL API-derived bootstrap + fixtures + element-summary, with next-GW target metrics from event/{GW}/live/ or element-summary.