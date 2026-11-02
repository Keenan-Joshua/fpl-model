"""
Pulls data from the official Fantasy Premier League API and caches it
locally as JSON so you're not hitting the API every time you test
something downstream (modeling, notebooks, etc.).

Usage: python fetch_data.py
"""

import json
import requests
from pathlib import Path

BASE_URL = "https://fantasy.premierleague.com/api"
DATA_DIR = Path(__file__).parents[1] / "data"


def fetch_bootstrap_static() -> dict:
    """
    The main FPL endpoint. Returns everything about the current state
    of the game: all players, all teams, gameweek info, and the
    scoring rules — in one response.
    """
    url = f"{BASE_URL}/bootstrap-static/"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    # Raises `HTTPError`, if one occurred.
    return response.json()


def fetch_fixtures() -> list:
    """
    Every fixture for the season, including each team's Fixture
    Difficulty Rating (FDR) for upcoming matches.
    """
    url = f"{BASE_URL}/fixtures/"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_player_history(player_id: int) -> dict:
    """
    Gameweek-by-gameweek history for a single player (points, minutes,
    goals, assists, etc. per match). Useful once you want per-player
    form rather than just season totals.
    """
    url = f"{BASE_URL}/element-summary/{player_id}/"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_event_live(gw: int) -> dict:
    """
    Live (real-time) data for a given gameweek, e.g. actuals for gameweeks
    that have been played.
    """
    url = f"{BASE_URL}/event/{gw}/live/"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def save_json(data, filename: str) -> Path:
    """Save data to data/filename, creating the folder if needed."""
    DATA_DIR.mkdir(exist_ok=True)
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        # Serialize/Converts 'data' as a JSON formatted stream to file 'f'
    return filepath


def main():
    print("Fetching bootstrap-static (players, teams, gameweeks)...")
    bootstrap = fetch_bootstrap_static()
    path = save_json(bootstrap, "bootstrap_static_latest.json")
    print(f"  Saved {len(bootstrap['elements'])} players -> {path}")

    print("Fetching fixtures...")
    fixtures = fetch_fixtures()
    path = save_json(fixtures, "fixtures_latest.json")
    print(f"  Saved {len(fixtures)} fixtures -> {path}")

    print("Fetching live event data for played gameweeks...")
    for gw in (4, 5, 6, 7, 8):
        event_live = fetch_event_live(gw)
        path = save_json(event_live, f"event_live_GW{gw}.json")
        print(f"  Saved live data for GW{gw} -> {path}")

    print("\nDone. Player history for individual players can be pulled "
          "on demand with fetch_player_history(player_id) once you know "
          "which players you care about — it's a separate call per player, "
          "so it's not fetched for everyone by default.")


if __name__ == "__main__":
    main()