"""
baseline.py

Baseline expected points (xP) model.

xP = base_form x minutes_probability x fixture_multiplier

This is deliberately simple: three interpretable factors multiplied
together. The goal is to get something end-to-end and validated
before adding complexity (per-position weighting, opponent strength
by attack/defense split, home/away splits, etc.).
"""

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parents[1] / "data"


def minutes_probability(player_row: pd.Series) -> float:
    """
    Rough estimate of how likely a player is to play meaningful
    minutes in the next gameweek, based on recent minutes played.

    This is a crude heuristic, not a prediction of starting XI —
    it's meant to penalize rotation risks and injured/benched
    players without needing team-news scraping.
    """
    minutes = player_row["minutes"]

    # players.csv doesn't give "minutes over last N games" directly from
    # bootstrap-static (that's season-to-date total minutes), so as a
    # starting proxy: compare season minutes against the max possible
    # for the season so far. Refine this later with per-gameweek history
    # from fetch_player_history() once you want more precision.
    max_possible_minutes = player_row.get("max_possible_minutes", None)

    if not max_possible_minutes or max_possible_minutes == 0:
        return 0.0

    ratio = minutes / max_possible_minutes
    return min(ratio, 1.0)


def fixture_multiplier(avg_fdr: float) -> float:
    """
    Converts average fixture difficulty rating (1=easiest, 5=hardest)
    into a multiplier centered around 1.0.

    FDR 3 (average difficulty) -> multiplier of 1.0 (no adjustment)
    FDR 1 (easiest)            -> multiplier of ~1.3
    FDR 5 (hardest)            -> multiplier of ~0.7
    """
    if pd.isna(avg_fdr):
        return 1.0  # no fixture data yet, don't penalize

    # Linear scale: each point of FDR away from 3 shifts multiplier by 0.15
    return 1.0 + (3 - avg_fdr) * 0.15


def calculate_xp(players_df: pd.DataFrame, gameweeks_played: int) -> pd.DataFrame:
    """
    Adds an 'xP' column to players_df.

    Expects players_df to already have:
      - 'form' (FPL's own recent-form metric, float)
      - 'minutes'
      - 'avg_fdr_next5' (from the fixtures step)

    gameweeks_played: how many gameweeks have happened so far this
    season, used to estimate max_possible_minutes (90 min/game).
    """
    df = players_df.copy()

    df["max_possible_minutes"] = gameweeks_played * 90
    df["minutes_prob"] = df.apply(minutes_probability, axis=1)
    df["fixture_mult"] = df["avg_fdr_next5"].apply(fixture_multiplier)

    # form comes as a string from the API - cast to float
    df["form"] = df["form"].astype(float)

    df["xP"] = df["form"] * df["minutes_prob"] * df["fixture_mult"]

    return df


def get_current_gw(bootstrap: dict) -> int | None:
    """
    Current gameweek from the bootstrap events (the one flagged
    is_current), or None if the bootstrap has no current event.
    """
    current = [e for e in bootstrap.get("events") or [] if e.get("is_current")]
    if not current:
        return None
    return int(current[0]["id"])


def get_next_gw(bootstrap: dict) -> int:
    """
    Next gameweek to predict: the first upcoming (is_next) event, or
    current + 1 if no upcoming event is flagged.
    """
    upcoming = [e for e in bootstrap.get("events") or [] if e.get("is_next")]
    if upcoming:
        return int(upcoming[0]["id"])
    current_gw = get_current_gw(bootstrap)
    return int(current_gw) + 1 if current_gw is not None else 1


def get_gameweeks_played(fixtures: list) -> int:
    """
    How many gameweeks have been completed this season so far — i.e.
    the bootstrap event-level 'finished' flag lags once a gameweek kicks
    off, so fixture-level start signals are used here.
    """
    started_gws = {f.get("event") for f in fixtures or [] if f.get("started")}
    return len(started_gws)


def build_players_df(bootstrap: dict) -> pd.DataFrame:
    """
    Map the FPL bootstrap-static elements[] into a players_df that
    carries the columns the baseline expects:

      - id, web_name, form (float), minutes (float), ep_next (float)
      - element_type, team, status

    Form comes back as a string like "6.0" from the API; missing values
    are coerced to 0.0 so the numeric steps downstream stay clean.
    """
    rows = []
    for e in bootstrap.get("elements") or []:
        rows.append({
            "id": e.get("id"),
            "web_name": e.get("web_name") or "",
            "form": float(e.get("form") or 0.0),
            "minutes": float(e.get("minutes") or 0),
            "ep_next": float(e.get("ep_next") or 0.0),
            "element_type": e.get("element_type"),
            "team": e.get("team"),
            "status": e.get("status"),
        })
    columns = [
        "id", "web_name", "form", "minutes", "ep_next",
        "element_type", "team", "status",
    ]
    return pd.DataFrame(rows, columns=columns)


def compute_avg_fdr_next5(fixtures: list, next_gw: int, n_gws: int = 5) -> pd.Series:
    """
    Average fixture difficulty rating (FDR) over the next n_gws upcoming
    gameweeks, keyed by team id.

    FDR is 1 (easiest) .. 5 (hardest); lower is easier. For each team, we
    average the difficulty of the opponents it faces across its next n_gws
    of upcoming fixtures (from fixtures_latest.json).

    Returns a Series indexed by team_id (NaN for teams with no upcoming
    fixtures within the window).
    """
    upcoming = sorted(
        (
            f
            for f in fixtures or []
            if f.get("event", 0) >= next_gw and not f.get("finished", False)
        ),
        key=lambda f: f.get("kickoff_time") or "",
    )
    difficulties: dict[int, list[float]] = {}
    for f in upcoming[:n_gws]:
        for team_id, diff in (
            (f.get("team_a"), f.get("team_a_difficulty")),
            (f.get("team_h"), f.get("team_h_difficulty")),
        ):
            if team_id is None or diff is None:
                continue
            difficulties.setdefault(team_id, []).append(float(diff))
    return pd.Series(
        {team_id: float(sum(d) / len(d)) for team_id, d in difficulties.items()},
        dtype=float,
    )


def load_gw_actuals(gw: int) -> pd.DataFrame | None:
    """
    Load cached event live actuals for a gameweek and reshape them into
    a per-player DataFrame of target stat lines (minutes, goals, assists,
    defensive contribution, etc.).

    Returns None when no cached live file exists for the gameweek.
    """
    filepath = DATA_DIR / f"event_live_GW{gw}.json"
    if not filepath.exists():
        return None
    data = json.loads(filepath.read_text(encoding="utf-8"))
    rows = []
    for element in data.get("elements") or []:
        stats = element.get("stats") or {}
        rows.append({
            "id": element.get("id"),
            "actual_minutes": stats.get("minutes") or 0,
            "goals_scored": stats.get("goals_scored") or 0,
            "assists": stats.get("assists") or 0,
            "clean_sheets": stats.get("clean_sheets") or 0,
            "saves": stats.get("saves") or 0,
            "defensive_contribution": stats.get("defensive_contribution") or 0,
            "yellow_cards": stats.get("yellow_cards") or 0,
            "red_cards": stats.get("red_cards") or 0,
            "bonus": stats.get("bonus") or 0,
            "bps": stats.get("bps") or 0,
            "total_points": stats.get("total_points") or 0,
            "starts": stats.get("starts") or 0,
            "played": stats.get("played") or False,
        })
    return pd.DataFrame(rows, columns=[
        "id", "actual_minutes", "goals_scored", "assists", "clean_sheets",
        "saves", "defensive_contribution", "yellow_cards", "red_cards",
        "bonus", "bps", "total_points", "starts", "played",
    ])


if __name__ == "__main__":
    bootstrap = json.loads(
        (DATA_DIR / "bootstrap_static_latest.json").read_text(encoding="utf-8")
    )
    fixtures = json.loads(
        (DATA_DIR / "fixtures_latest.json").read_text(encoding="utf-8")
    )

    current_gw = get_current_gw(bootstrap)
    next_gw = get_next_gw(bootstrap)
    gameweeks_played = get_gameweeks_played(fixtures)

    players_df = build_players_df(bootstrap)
    players_df["avg_fdr_next5"] = players_df["team"].map(
        compute_avg_fdr_next5(fixtures, next_gw)
    ).fillna(3.0)
    players_df = calculate_xp(players_df, gameweeks_played)

    xP = players_df["xP"].dropna()
    print("Baseline xP smoke test - current season (2026/27) from cached FPL API data")
    print(f"  Current GW: {current_gw} | Next GW: {next_gw} | GWs played: {gameweeks_played}")
    print(f"  Players: {len(players_df)} | xP > 0: {int((players_df['xP'] > 0).sum())}")
    print(f"  xP - mean: {xP.mean():.3f} | median: {xP.median():.3f} | max: {xP.max():.3f}")

    latest_played_gw = max(
        (e["id"] for e in bootstrap.get("events") or [] if e.get("finished")),
        default=None,
    )
    actuals = load_gw_actuals(latest_played_gw) if latest_played_gw is not None else None

    top_players = players_df.sort_values("xP", ascending=False).head(10)
    print(f"\nTop 10 players by xP for GW{next_gw}:")
    for _, row in top_players.iterrows():
        print(
            f"  {row['web_name']} (team {row['team']}): form {row['form']:.2f}, "
            f"minutes_prob {row['minutes_prob']:.2f}, avg_fdr {row['avg_fdr_next5']:.2f}, "
            f"fixture_mult {row['fixture_mult']:.2f}, xP {row['xP']:.2f}, "
            f"ep_next {row['ep_next']:.2f}"
        )

    if actuals is not None:
        actuals = actuals.rename(columns={"minutes": "actual_minutes"})
        joined = players_df.merge(actuals, on="id")
        with_xp = joined[joined["xP"] > 0]
        print(
            f"\nNext-GW target stats from event_live_GW{latest_played_gw} actuals "
            f"(GW{next_gw} is upcoming and has no live data yet):"
        )
        print(
            f"  Mean actual total_points: {with_xp['total_points'].mean():.2f} | "
            f"mean actual goals: {with_xp['goals_scored'].mean():.2f} | "
            f"mean actual assists: {with_xp['assists'].mean():.2f} | "
            f"mean actual defensive_contribution: {with_xp['defensive_contribution'].mean():.2f}"
        )
