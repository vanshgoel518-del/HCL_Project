"""P15 Automated Pipeline & Verification Test Suite for Project #21.

Verifies primary key uniqueness, required non-null fields, valid value ranges,
Python vs. SQLite total parity, referential integrity, and exact 5-player
benchmark stats, saving results to reports/test_results.csv.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT_DIR / "data" / "clean"
DB_PATH = ROOT_DIR / "data" / "ipl_stats.db"
REPORTS_DIR = ROOT_DIR / "reports"

EXPECTED_5_BENCHMARK = {
    "P001": {"runs": 2986, "avg": 66.36, "sr": 146.44, "wickets": 0, "econ": 0.0},
    "P002": {"runs": 2731, "avg": 65.02, "sr": 147.14, "wickets": 0, "econ": 0.0},
    "P003": {"runs": 179, "avg": 14.92, "sr": 92.75, "wickets": 93, "econ": 7.94},
    "P004": {"runs": 89, "avg": 17.80, "sr": 95.70, "wickets": 79, "econ": 8.17},
    "P005": {"runs": 2673, "avg": 65.20, "sr": 149.83, "wickets": 0, "econ": 0.0},
}


def run_tests() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    def record(test_id: str, test_name: str, passed: bool, detail: str) -> None:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_id} - {test_name}: {detail}")
        results.append(
            {
                "test_id": test_id,
                "test_name": test_name,
                "status": status,
                "detail": detail,
            }
        )

    teams = pd.read_csv(CLEAN_DIR / "dim_teams.csv", na_values=[""], keep_default_na=False)
    seasons = pd.read_csv(CLEAN_DIR / "dim_seasons.csv", na_values=[""], keep_default_na=False)
    players = pd.read_csv(CLEAN_DIR / "dim_players.csv", na_values=[""], keep_default_na=False)
    matches = pd.read_csv(CLEAN_DIR / "dim_matches.csv", na_values=[""], keep_default_na=False)
    facts = pd.read_csv(CLEAN_DIR / "fact_player_match_stats.csv", na_values=[""], keep_default_na=False)

    # T01: No duplicate primary keys
    pk_checks = {
        "dim_teams.team_id": teams["team_id"].duplicated().sum(),
        "dim_seasons.season_id": seasons["season_id"].duplicated().sum(),
        "dim_players.player_id": players["player_id"].duplicated().sum(),
        "dim_matches.match_id": matches["match_id"].duplicated().sum(),
        "fact_player_match_stats.stat_id": facts["stat_id"].duplicated().sum(),
    }
    dup_total = int(sum(pk_checks.values()))
    record("T01", "No duplicate primary keys across all 5 clean tables", dup_total == 0, f"duplicates={dup_total}")

    # T02: No missing required fields
    req_nulls = (
        int(teams.isna().sum().sum())
        + int(seasons.isna().sum().sum())
        + int(players.isna().sum().sum())
        + int(matches.drop(columns=["win_margin_runs", "win_margin_wickets"]).isna().sum().sum())
        + int(facts.isna().sum().sum())
    )
    record("T02", "No missing required fields in cleaned tables", req_nulls == 0, f"missing_required_cells={req_nulls}")

    # T03: Valid value ranges
    bad_runs = int((facts["runs_scored"] < 0).sum())
    bad_balls_bowled = int((~facts["balls_bowled"].between(0, 24)).sum())
    bad_not_out = int((~facts["not_out"].isin([0, 1])).sum())
    bad_catches = int((facts["catches"] < 0).sum())
    range_err = bad_runs + bad_balls_bowled + bad_not_out + bad_catches
    record(
        "T03",
        "Valid value ranges (runs>=0, balls_bowled 0..24, not_out in {0,1})",
        range_err == 0,
        f"violations={range_err}",
    )

    # T04: Python totals equal SQLite database totals
    py_runs = int(facts["runs_scored"].sum())
    py_wkts = int(facts["wickets_taken"].sum())
    conn = sqlite3.connect(DB_PATH)
    try:
        sql_runs, sql_wkts = conn.execute(
            "SELECT SUM(runs_scored), SUM(wickets_taken) FROM fact_player_match_stats"
        ).fetchone()
    finally:
        conn.close()
    parity_ok = (py_runs == int(sql_runs)) and (py_wkts == int(sql_wkts))
    record(
        "T04",
        "Python totals equal SQLite database totals",
        parity_ok,
        f"py=({py_runs},{py_wkts}), sql=({sql_runs},{sql_wkts})",
    )

    # T05: Referential integrity (every fact row matches dim_players, dim_matches, dim_teams)
    orphan_players = int((~facts["player_id"].isin(players["player_id"])).sum())
    orphan_matches = int((~facts["match_id"].isin(matches["match_id"])).sum())
    orphan_teams = int((~facts["team_id"].isin(teams["team_id"])).sum())
    orphan_total = orphan_players + orphan_matches + orphan_teams
    record(
        "T05",
        "Referential integrity across fact and dimension tables",
        orphan_total == 0,
        f"orphan_keys={orphan_total}",
    )

    # T06: 5 Benchmark Players Verification
    mismatches = []
    for pid, exp in EXPECTED_5_BENCHMARK.items():
        sub = facts[facts["player_id"] == pid]
        inn = int(sub["innings_batted"].sum())
        no = int(sub.loc[sub["innings_batted"] == 1, "not_out"].sum())
        dis = inn - no
        runs = int(sub["runs_scored"].sum())
        bf = int(sub["balls_faced"].sum())
        wkts = int(sub["wickets_taken"].sum())
        bb = int(sub["balls_bowled"].sum())
        rc = int(sub["runs_conceded"].sum())
        avg = round(runs / dis, 2) if dis > 0 else float(runs)
        sr = round((runs / bf) * 100.0, 2) if bf > 0 else 0.0
        econ = round(rc / (bb / 6.0), 2) if bb > 0 else 0.0
        if (runs, avg, sr, wkts, econ) != (exp["runs"], exp["avg"], exp["sr"], exp["wickets"], exp["econ"]):
            mismatches.append(f"{pid}: got {(runs, avg, sr, wkts, econ)} vs exp {exp}")

    record(
        "T06",
        "5 sample benchmark players match expected stats",
        len(mismatches) == 0,
        "all 5 matched" if not mismatches else "; ".join(mismatches),
    )

    out_df = pd.DataFrame(results)
    out_df.to_csv(REPORTS_DIR / "test_results.csv", index=False)
    print(f"Saved test results to {REPORTS_DIR / 'test_results.csv'}")
    return results


if __name__ == "__main__":
    res = run_tests()
    if any(r["status"] != "PASS" for r in res):
        raise SystemExit(1)
