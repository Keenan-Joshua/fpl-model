## Project Overview
AI prediction model for Fantasy Premier League (FPL). Goal: predict player
performance. Currently transitioning from manual formula exploration (2026/27
season points modeling) toward training an AI model.

- Baseline added at `src/baseline.py`: expected points xP =
  form × minutes_probability × fixture_multiplier. Verified working
  (compiles + smoke-tested); wired end-to-end via cached FPL API data in Phase 6, Task 9.
- Latest pivot: target is the next gameweek's point-producing metrics
  (goals, assists, defcon, etc.), not points directly.

## Repository Layout
- `src/` — Python source. `fetch_data.py`: FPL API client with JSON caching.
  `baseline.py`: baseline xP model.
- `data/` — Cached FPL API JSON (`bootstrap_static_latest.json`, `fixtures_latest.json`, `event_live_GW*.json`) plus historical season CSVs.
- `notebooks/` — Exploration notebooks (e.g., `25-26_exploration.ipynb`).
- `requirements.txt` — Deps: requests, pandas, matplotlib, notebook.

## Commands
- Bootstrap (once per project): `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Activate existing env (per session): `source .venv/bin/activate`
- Fetch data: `python src/fetch_data.py`
- Explore: `jupyter lab notebooks`

## Conventions
- API code in `src/`; raw responses cached in `data/` (timestamped + `_latest`).
- Notebooks for exploration; modeling work should move into `src/`.

## Agent Notes / TODO
- No ML deps installed yet (add scikit-learn/torch when training starts).
- Baseline `calculate_xp` wired end-to-end via cached FPL API data; next step is feature engineering → train.
- Validation: leaning toward walk-forward backtesting; metrics — recommend reporting both
  RMSE and MAE; check outlier predictions.
- Features: candidate list agreed; deeper deliberation later.
- Deliverables: step-by-step phases (data → baseline → features/train → backtest → predict).
- Historical seasons: ~10 max; pre-25/26 data lacks defcon (defensive_contribution) fields.