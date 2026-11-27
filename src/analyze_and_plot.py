"""P9 KPI Computation & Visualization Script for Project #21.

Computes batting, bowling, season, and 5-player verification KPIs on data/clean/,
saves reports/kpis.json, and generates 4 labeled PNG charts in reports/charts/.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
CLEAN_DIR = ROOT_DIR / "data" / "clean"
REPORTS_DIR = ROOT_DIR / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"

SAMPLE_5_IDS = ["P001", "P002", "P003", "P004", "P005"]


def compute_and_plot() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    teams = pd.read_csv(CLEAN_DIR / "dim_teams.csv", na_values=[""], keep_default_na=False)
    seasons = pd.read_csv(CLEAN_DIR / "dim_seasons.csv", na_values=[""], keep_default_na=False)
    players = pd.read_csv(CLEAN_DIR / "dim_players.csv", na_values=[""], keep_default_na=False)
    matches = pd.read_csv(CLEAN_DIR / "dim_matches.csv", na_values=[""], keep_default_na=False)
    facts = pd.read_csv(CLEAN_DIR / "fact_player_match_stats.csv", na_values=[""], keep_default_na=False)
    dq_log = pd.read_csv(REPORTS_DIR / "data_quality_log.csv")

    # Assumption 1: Batting Average = Total Runs / (Innings Batted - Not Outs); if 0 dismissals, fallback to Total Runs.
    # Assumption 2: Balls Bowled is always converted to overs via balls_bowled / 6.0 for Economy Rate.
    # Assumption 3: Imputed balls_faced rows (balls_faced_imputed == 1) are included in overall strike rate,
    #               and sensitivity vs. excluding imputed rows is shown explicitly in Chart 4.
    df = (
        facts.merge(matches[["match_id", "season_id", "match_date", "venue"]], on="match_id", how="left")
        .merge(seasons[["season_id", "season_year"]], on="season_id", how="left")
        .merge(players[["player_id", "player_name", "player_role", "nationality"]], on="player_id", how="left")
        .merge(teams[["team_id", "team_code", "team_name"]], on="team_id", how="left")
    )
    df["match_month"] = pd.to_datetime(df["match_date"]).dt.to_period("M").astype(str)

    total_runs = int(df["runs_scored"].sum())
    total_innings = int(df["innings_batted"].sum())
    total_not_outs = int(df.loc[df["innings_batted"] == 1, "not_out"].sum())
    total_dismissals = total_innings - total_not_outs
    total_balls_faced = int(df["balls_faced"].sum())
    total_wickets = int(df["wickets_taken"].sum())
    total_balls_bowled = int(df["balls_bowled"].sum())
    total_runs_conceded = int(df["runs_conceded"].sum())

    overall_bat_avg = round(total_runs / total_dismissals, 2) if total_dismissals > 0 else float(total_runs)
    overall_sr = round((total_runs / total_balls_faced) * 100.0, 2) if total_balls_faced > 0 else 0.0
    overall_econ = round(total_runs_conceded / (total_balls_bowled / 6.0), 2) if total_balls_bowled > 0 else 0.0

    # Top batsman and bowler per season (preserving ties cleanly)
    season_bat = (
        df.groupby(["season_year", "player_id", "player_name", "team_code"], as_index=False)
        .agg(total_runs=("runs_scored", "sum"), balls_faced=("balls_faced", "sum"))
    )
    season_bat["rank"] = season_bat.groupby("season_year")["total_runs"].rank(method="min", ascending=False).astype(int)
    top_season_batsmen = (
        season_bat[season_bat["rank"] == 1]
        .sort_values(["season_year", "player_id"])
        .to_dict(orient="records")
    )

    season_bowl = (
        df[df["balls_bowled"] > 0]
        .groupby(["season_year", "player_id", "player_name", "team_code"], as_index=False)
        .agg(total_wickets=("wickets_taken", "sum"), balls_bowled=("balls_bowled", "sum"), runs_conceded=("runs_conceded", "sum"))
    )
    season_bowl["economy_rate"] = (season_bowl["runs_conceded"] / (season_bowl["balls_bowled"] / 6.0)).round(2)
    season_bowl["rank"] = season_bowl.groupby("season_year")["total_wickets"].rank(method="min", ascending=False).astype(int)
    top_season_bowlers = (
        season_bowl[season_bowl["rank"] == 1]
        .sort_values(["season_year", "player_id"])
        .to_dict(orient="records")
    )

    # 5 benchmark players verification
    bench_rows = []
    for pid in SAMPLE_5_IDS:
        sub = df[df["player_id"] == pid]
        inn = int(sub["innings_batted"].sum())
        no = int(sub.loc[sub["innings_batted"] == 1, "not_out"].sum())
        dis = inn - no
        runs = int(sub["runs_scored"].sum())
        bf = int(sub["balls_faced"].sum())
        wkts = int(sub["wickets_taken"].sum())
        bb = int(sub["balls_bowled"].sum())
        rc = int(sub["runs_conceded"].sum())
        bench_rows.append(
            {
                "player_id": pid,
                "player_name": str(sub["player_name"].iloc[0]),
                "team_code": str(sub["team_code"].iloc[0]),
                "matches_played": int(sub["match_id"].nunique()),
                "innings_batted": inn,
                "not_outs": no,
                "total_runs": runs,
                "total_balls_faced": bf,
                "batting_average": round(runs / dis, 2) if dis > 0 else float(runs),
                "strike_rate": round((runs / bf) * 100.0, 2) if bf > 0 else 0.0,
                "total_wickets": wkts,
                "total_balls_bowled": bb,
                "total_runs_conceded": rc,
                "economy_rate": round(rc / (bb / 6.0), 2) if bb > 0 else 0.0,
            }
        )

    kpis = {
        "dataset": "Synthetic IPL Player Performance Dataset (2021-2024)",
        "total_matches": int(matches["match_id"].nunique()),
        "total_players": int(players["player_id"].nunique()),
        "total_fact_rows": int(len(facts)),
        "total_runs": total_runs,
        "total_wickets": total_wickets,
        "overall_batting_average": overall_bat_avg,
        "overall_strike_rate": overall_sr,
        "overall_economy_rate": overall_econ,
        "top_season_batsmen": top_season_batsmen,
        "top_season_bowlers": top_season_bowlers,
        "sample_5_players_verification": bench_rows,
    }
    (REPORTS_DIR / "kpis.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    print("Saved KPIs to", REPORTS_DIR / "kpis.json")

    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    # Chart 1: Monthly Runs & Strike Rate Trend
    monthly = (
        df.groupby("match_month", as_index=False)
        .agg(total_runs=("runs_scored", "sum"), balls_faced=("balls_faced", "sum"))
        .sort_values("match_month")
    )
    monthly["strike_rate"] = (monthly["total_runs"] / monthly["balls_faced"]) * 100.0

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(monthly["match_month"], monthly["total_runs"], color="#1F4E78", alpha=0.85, label="Total Runs")
    ax1.set_title("Monthly Runs Scored & Batting Strike Rate Trend (2021-2024)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Tournament Month (YYYY-MM)", fontsize=10)
    ax1.set_ylabel("Total Runs Scored", color="#1F4E78", fontsize=10)
    ax1.tick_params(axis="x", rotation=40)
    ax1.grid(axis="y", linestyle="--", alpha=0.35)

    ax2 = ax1.twinx()
    ax2.plot(monthly["match_month"], monthly["strike_rate"], color="#D97706", marker="o", linewidth=2.2, label="Strike Rate")
    ax2.set_ylabel("Batting Strike Rate", color="#D97706", fontsize=10)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "monthly_runs_trend.png", dpi=150)
    plt.close(fig)

    # Chart 2: Performance by IPL Franchise (Team Comparison)
    team_agg = (
        df.groupby("team_code", as_index=False)
        .agg(total_runs=("runs_scored", "sum"), total_wickets=("wickets_taken", "sum"))
        .sort_values("total_runs", ascending=False)
    )
    x = range(len(team_agg))
    fig, ax1 = plt.subplots(figsize=(10, 5))
    bars = ax1.bar([i - 0.18 for i in x], team_agg["total_runs"], width=0.36, color="#0F766E", label="Total Runs")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(team_agg["team_code"], fontsize=10)
    ax1.set_title("Franchise Comparison: Total Runs vs. Total Wickets (2021-2024)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("IPL Team Code", fontsize=10)
    ax1.set_ylabel("Total Runs Scored", color="#0F766E", fontsize=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.35)

    ax2 = ax1.twinx()
    ax2.bar([i + 0.18 for i in x], team_agg["total_wickets"], width=0.36, color="#1D4ED8", label="Total Wickets")
    ax2.set_ylabel("Total Wickets Taken", color="#1D4ED8", fontsize=10)
    for b in bars:
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 40, f"{int(b.get_height())}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "team_performance_comparison.png", dpi=150)
    plt.close(fig)

    # Chart 3: Contribution by Player Role Category
    role_agg = (
        df.groupby("player_role", as_index=False)
        .agg(total_runs=("runs_scored", "sum"), total_wickets=("wickets_taken", "sum"))
        .sort_values("total_runs", ascending=False)
    )
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].barh(role_agg["player_role"], role_agg["total_runs"], color="#2563EB")
    axes[0].invert_yaxis()
    axes[0].set_title("Total Runs by Player Role", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Total Runs Scored")
    axes[0].grid(axis="x", linestyle="--", alpha=0.35)

    axes[1].barh(role_agg["player_role"], role_agg["total_wickets"], color="#EA580C")
    axes[1].invert_yaxis()
    axes[1].set_title("Total Wickets by Player Role", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Total Wickets Taken")
    axes[1].grid(axis="x", linestyle="--", alpha=0.35)

    fig.suptitle("Player Role Contribution Breakdown (2021-2024)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "role_contribution_breakdown.png", dpi=150)
    plt.close(fig)

    # Chart 4: Problem Area — Data Quality Fixes & Missing Balls Impact
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    dq_plot = dq_log.sort_values("rows_affected", ascending=True)
    short_labels = [lbl.split(" (")[0] for lbl in dq_plot["issue"]]
    axes[0].barh(short_labels, dq_plot["rows_affected"], color="#DC2626")
    axes[0].set_title("Rows Fixed per Data Quality Issue", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Rows Affected")
    axes[0].grid(axis="x", linestyle="--", alpha=0.35)

    # Right subplot: Missing balls recovery & strike rate comparison
    no_imp = df[df["balls_faced_imputed"] == 0]
    sr_observed_only = (no_imp["runs_scored"].sum() / no_imp["balls_faced"].sum()) * 100.0
    sr_with_imputed = overall_sr
    econ_complete_only = (
        df.loc[df["balls_bowled"] > 0, "runs_conceded"].sum()
        / (df.loc[df["balls_bowled"] > 0, "balls_bowled"].sum() / 6.0)
    )
    metrics_lbl = ["SR (Observed Balls)", "SR (With Imputed Balls)", "Bowling Econ (Recovered)"]
    metrics_val = [sr_observed_only, sr_with_imputed, econ_complete_only]
    colors = ["#475569", "#1F4E78", "#0F766E"]
    bars4 = axes[1].bar(metrics_lbl, metrics_val, color=colors, width=0.5)
    axes[1].set_title("Missing Balls Recovery & Metric Sensitivity", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Rate (Strike Rate / Economy)")
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].grid(axis="y", linestyle="--", alpha=0.35)
    for b in bars4:
        axes[1].text(b.get_x() + b.get_width() / 2, b.get_height() + 2, f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("Data Quality Audit & Missing Balls Impact Analysis", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "data_quality_and_missing_balls.png", dpi=150)
    plt.close(fig)
    print("Generated 4 PNG charts in", CHARTS_DIR)


if __name__ == "__main__":
    compute_and_plot()
