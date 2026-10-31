## Project Overview
AI prediction model for Fantasy Premier League (FPL). Goal: predict player
performance. Currently transitioning from manual formula exploration (2026/27
season points modeling) toward training an AI model.

- Baseline added at `root/src/baseline.py`: expected points xP =
  form × minutes_probability × fixture_multiplier. Verified working
  (compiles + smoke-tested).
- Latest pivot: target is the next gameweek's point-producing metrics
  (goals, assists, defcon, etc.), not points directly.

## Repository Layout
- `root/src/` — Python source. `fetch_data.py`: FPL API client with JSON caching.
  `baseline.py`: baseline xP model.
- `root/data/` — Cached FPL API JSON (`bootstrap_static_*`, `fixtures_*`, `*_latest.json`).
- `root/notebooks/` — Exploration notebooks (e.g., `25-26_exploration.ipynb`).
- `root/requirements.txt` — Deps: requests, pandas, matplotlib, notebook.

## Commands
- Bootstrap (once per project): `python -m venv .venv && source .venv/bin/activate && pip install -r root/requirements.txt`
- Activate existing env (per session): `source .venv/bin/activate`
- Fetch data: `python root/src/fetch_data.py`
- Explore: `jupyter lab root/notebooks`

## Conventions
- API code in `root/src/`; raw responses cached in `root/data/` (timestamped + `_latest`).
- Notebooks for exploration; modeling work should move into `root/src/`.

## Agent Notes / TODO
- No ML deps installed yet (add scikit-learn/torch when training starts).
- Baseline `calculate_xp` verified: compiles, smoke-tested; next step is wiring to real
  `players_df` (`form`, `minutes`, `avg_fdr_next5`) + fixtures data.
- Validation: leaning toward walk-forward backtesting; metrics — recommend reporting both
  RMSE and MAE; check outlier predictions.
- Features: candidate list agreed; deeper deliberation later.
- Deliverables: step-by-step phases (data → baseline → features/train → backtest → predict).
- Historical seasons: ~10 max; pre-25/26 data lacks defcon (defensive_contribution) fields.