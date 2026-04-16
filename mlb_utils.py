"""
mlb_utils.py — MLB Statistics Utility Functions

Provides drop-in replacements for pybaseball's FanGraphs-dependent functions
(batting_stats, pitching_stats, team_batting, team_pitching) using the
official MLB Stats API (statsapi.mlb.com), which is freely accessible and
requires no API key, no caching, and no third-party account.

Functions
---------
team_batting_mlb(year)
    Team batting totals for a season. One row per team.

team_pitching_mlb(year)
    Team pitching totals for a season. One row per team.

batting_stats_mlb(year, min_pa=1)
    Individual player batting stats for a season. One row per player-team.

pitching_stats_mlb(year, min_ip=1)
    Individual player pitching stats for a season. One row per player-team.

Notes
-----
- All functions accept a four-digit integer year (e.g. 2025).
- Column names match pybaseball / FanGraphs conventions (HR, BB, SO, 2B, 3B,
  AVG, OBP, SLG, OPS, etc.) so existing book code works without modification.
- Players who appeared for multiple teams in a season have one row per team.
- Historical data is available back to at least 1970.
"""

import requests
import pandas as pd

_MLB_API = "https://statsapi.mlb.com/api/v1"


def _team_abbrevs(year):
    """Return {team_id: abbreviation} for all MLB teams in a given year."""
    r = requests.get(
        f"{_MLB_API}/teams",
        params={"sportId": 1, "season": year},
        timeout=10,
    )
    r.raise_for_status()
    return {t["id"]: t["abbreviation"] for t in r.json()["teams"]}


def _parse_ip(ip_str):
    """
    Convert an MLB API innings-pitched string to a float.

    The API encodes innings as 'NNN.O' where NNN is full innings and O is
    the number of outs (0, 1, or 2). For example, '7.2' means 7 innings and
    2 outs, i.e. 7.667 innings.
    """
    parts = str(ip_str).split(".")
    if len(parts) == 2:
        return int(parts[0]) + int(parts[1]) / 3
    return float(ip_str)


# ---------------------------------------------------------------------------
# Team-level functions
# ---------------------------------------------------------------------------

def team_batting_mlb(year):
    """
    Team batting totals for a season via the MLB Stats API.

    Parameters
    ----------
    year : int
        The MLB season (e.g. 2025).

    Returns
    -------
    pd.DataFrame
        One row per team with columns:
        Season, yearID, Team, G, AB, H, 2B, 3B, HR, R, RBI, BB, SO, SB,
        HBP, AVG, OBP, SLG, OPS.
    """
    abbrevs = _team_abbrevs(year)
    r = requests.get(
        f"{_MLB_API}/teams/stats",
        params={"season": year, "sportId": 1, "stats": "season",
                "group": "hitting", "gameType": "R"},
        timeout=10,
    )
    r.raise_for_status()
    rows = []
    for s in r.json()["stats"][0]["splits"]:
        st = s["stat"]
        rows.append({
            "Season": year,
            "yearID": year,
            "Team":   abbrevs.get(s["team"]["id"], s["team"]["name"]),
            "G":      st.get("gamesPlayed", 0),
            "AB":     st["atBats"],
            "H":      st["hits"],
            "2B":     st["doubles"],
            "3B":     st["triples"],
            "HR":     st["homeRuns"],
            "R":      st["runs"],
            "RBI":    st["rbi"],
            "BB":     st["baseOnBalls"],
            "SO":     st["strikeOuts"],
            "SB":     st["stolenBases"],
            "HBP":    st.get("hitByPitch", 0),
            "AVG":    float(st.get("avg", 0) or 0),
            "OBP":    float(st.get("obp", 0) or 0),
            "SLG":    float(st.get("slg", 0) or 0),
            "OPS":    float(st.get("ops", 0) or 0),
        })
    return pd.DataFrame(rows)


def team_pitching_mlb(year):
    """
    Team pitching totals for a season via the MLB Stats API.

    Parameters
    ----------
    year : int
        The MLB season (e.g. 2025).

    Returns
    -------
    pd.DataFrame
        One row per team with columns:
        Season, yearID, Team, HR, BB, SO, IP, ERA, ER.
    """
    abbrevs = _team_abbrevs(year)
    r = requests.get(
        f"{_MLB_API}/teams/stats",
        params={"season": year, "sportId": 1, "stats": "season",
                "group": "pitching", "gameType": "R"},
        timeout=10,
    )
    r.raise_for_status()
    rows = []
    for s in r.json()["stats"][0]["splits"]:
        st = s["stat"]
        rows.append({
            "Season": year,
            "yearID": year,
            "Team":   abbrevs.get(s["team"]["id"], s["team"]["name"]),
            "HR":     st["homeRuns"],
            "BB":     st["baseOnBalls"],
            "SO":     st["strikeOuts"],
            "IP":     _parse_ip(st["inningsPitched"]),
            "ERA":    float(st.get("era", 0) or 0),
            "ER":     st.get("earnedRuns", 0),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Player-level functions
# ---------------------------------------------------------------------------

def batting_stats_mlb(year, min_pa=1):
    """
    Individual player batting stats for a season via the MLB Stats API.

    Parameters
    ----------
    year : int
        The MLB season (e.g. 2025).
    min_pa : int, optional
        Minimum plate appearances to include a player (default 1).

    Returns
    -------
    pd.DataFrame
        One row per player-team with columns:
        Season, Name, Team, G, PA, AB, H, 2B, 3B, HR, R, RBI, BB, IBB, SO,
        SB, CS, HBP, SF, SH, GDP, AVG, OBP, SLG, OPS.
        Players who appeared for multiple teams have one row per team.
    """
    abbrevs = _team_abbrevs(year)
    r = requests.get(
        f"{_MLB_API}/stats",
        params={"stats": "season", "season": year, "sportId": 1,
                "group": "hitting", "gameType": "R",
                "playerPool": "ALL", "limit": 5000},
        timeout=30,
    )
    r.raise_for_status()
    rows = []
    for s in r.json()["stats"][0]["splits"]:
        st = s["stat"]
        if st.get("plateAppearances", 0) < min_pa:
            continue
        team_id = s.get("team", {}).get("id")
        rows.append({
            "Season": year,
            "Name":   s["player"]["fullName"],
            "Team":   abbrevs.get(team_id, s.get("team", {}).get("name", "")),
            "G":      st.get("gamesPlayed", 0),
            "PA":     st.get("plateAppearances", 0),
            "AB":     st["atBats"],
            "H":      st["hits"],
            "2B":     st["doubles"],
            "3B":     st["triples"],
            "HR":     st["homeRuns"],
            "R":      st["runs"],
            "RBI":    st["rbi"],
            "BB":     st["baseOnBalls"],
            "IBB":    st.get("intentionalWalks", 0),
            "SO":     st["strikeOuts"],
            "SB":     st["stolenBases"],
            "CS":     st.get("caughtStealing", 0),
            "HBP":    st.get("hitByPitch", 0),
            "SF":     st.get("sacFlies", 0),
            "SH":     st.get("sacBunts", 0),
            "GDP":    st.get("groundIntoDoublePlay", 0),
            "AVG":    float(st.get("avg", 0) or 0),
            "OBP":    float(st.get("obp", 0) or 0),
            "SLG":    float(st.get("slg", 0) or 0),
            "OPS":    float(st.get("ops", 0) or 0),
        })
    return pd.DataFrame(rows)


def pitching_stats_mlb(year, min_ip=1):
    """
    Individual player pitching stats for a season via the MLB Stats API.

    Parameters
    ----------
    year : int
        The MLB season (e.g. 2025).
    min_ip : int or float, optional
        Minimum innings pitched to include a player (default 1).

    Returns
    -------
    pd.DataFrame
        One row per player-team with columns:
        Season, Name, Team, G, GS, W, L, IP, H, HR, BB, SO, ERA.
        Players who appeared for multiple teams have one row per team.
    """
    abbrevs = _team_abbrevs(year)
    r = requests.get(
        f"{_MLB_API}/stats",
        params={"stats": "season", "season": year, "sportId": 1,
                "group": "pitching", "gameType": "R",
                "playerPool": "ALL", "limit": 5000},
        timeout=30,
    )
    r.raise_for_status()
    rows = []
    for s in r.json()["stats"][0]["splits"]:
        st = s["stat"]
        ip = _parse_ip(st.get("inningsPitched", "0.0"))
        if ip < min_ip:
            continue
        team_id = s.get("team", {}).get("id")
        rows.append({
            "Season": year,
            "Name":   s["player"]["fullName"],
            "Team":   abbrevs.get(team_id, s.get("team", {}).get("name", "")),
            "G":      st.get("gamesPlayed", 0),
            "GS":     st.get("gamesStarted", 0),
            "W":      st.get("wins", 0),
            "L":      st.get("losses", 0),
            "IP":     ip,
            "H":      st.get("hits", 0),
            "HR":     st.get("homeRuns", 0),
            "BB":     st.get("baseOnBalls", 0),
            "SO":     st.get("strikeOuts", 0),
            "ERA":    float(st.get("era", 0) or 0),
        })
    return pd.DataFrame(rows)
