"""P11 Interactive Streamlit Dashboard for Project #21 (IPL Player Performance)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT_DIR / "data" / "clean"

st.set_page_config(page_title="IPL Player Performance Dashboard", layout="wide")


@st.cache_data
def load_clean_data() -> pd.DataFrame:
    teams = pd.read_csv(CLEAN_DIR / "dim_teams.csv", na_values=[""], keep_default_na=False)
    seasons = pd.read_csv(CLEAN_DIR / "dim_seasons.csv", na_values=[""], keep_default_na=False)
    players = pd.read_csv(CLEAN_DIR / "dim_players.csv", na_values=[""], keep_default_na=False)
    matches = pd.read_csv(CLEAN_DIR / "dim_matches.csv", na_values=[""], keep_default_na=False)
    facts = pd.read_csv(CLEAN_DIR / "fact_player_match_stats.csv", na_values=[""], keep_default_na=False)

    return (
        facts.merge(matches[["match_id", "season_id", "match_date", "venue"]], on="match_id", how="left")
        .merge(seasons[["season_id", "season_year"]], on="season_id", how="left")
        .merge(players[["player_id", "player_name", "player_role", "nationality"]], on="player_id", how="left")
        .merge(teams[["team_id", "team_code", "team_name"]], on="team_id", how="left")
    )


def main() -> None:
    st.title("IPL Player Performance Dashboard (2021–2024)")
    st.caption("Data Source: Agent-Generated Synthetic IPL Benchmark Dataset (`data/clean/fact_player_match_stats.csv`).")

    df = load_clean_data()

    # Sidebar filters
    st.sidebar.header("Dashboard Filters")
    season_opts = sorted(df["season_year"].unique().tolist())
    sel_seasons = st.sidebar.multiselect("Season Year", season_opts, default=season_opts)

    team_opts = sorted(df["team_code"].unique().tolist())
    sel_teams = st.sidebar.multiselect("Team", team_opts, default=team_opts)

    role_opts = sorted(df["player_role"].unique().tolist())
    sel_roles = st.sidebar.multiselect("Player Role", role_opts, default=role_opts)

    filtered = df[
        df["season_year"].isin(sel_seasons)
        & df["team_code"].isin(sel_teams)
        & df["player_role"].isin(sel_roles)
    ]

    player_opts = sorted(filtered["player_name"].unique().tolist())
    default_players = [p for p in ["Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "Rashid Khan", "Suryakumar Yadav"] if p in player_opts]
    sel_players = st.sidebar.multiselect("Compare Players", player_opts, default=default_players or player_opts[:5])

    if filtered.empty:
        st.warning("No records match the selected filters.")
        return

    # 4 KPI Tiles
    total_runs = int(filtered["runs_scored"].sum())
    innings = int(filtered["innings_batted"].sum())
    not_outs = int(filtered.loc[filtered["innings_batted"] == 1, "not_out"].sum())
    dismissals = max(1, innings - not_outs)
    balls_faced = int(filtered["balls_faced"].sum())
    total_wickets = int(filtered["wickets_taken"].sum())

    bat_avg = round(total_runs / dismissals, 2)
    strike_rate = round((total_runs / balls_faced) * 100.0, 2) if balls_faced > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Runs", f"{total_runs:,}")
    c2.metric("Batting Average", f"{bat_avg:.2f}")
    c3.metric("Batting Strike Rate", f"{strike_rate:.2f}")
    c4.metric("Total Wickets", f"{total_wickets:,}")

    st.divider()

    # 3 Dynamic Charts
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("1. Runs & Wickets by Season")
        ssn_df = filtered.groupby("season_year", as_index=False).agg(Runs=("runs_scored", "sum"), Wickets=("wickets_taken", "sum"))
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.plot(ssn_df["season_year"].astype(str), ssn_df["Runs"], marker="o", color="#1F4E78", linewidth=2, label="Runs")
        ax.set_xlabel("Season")
        ax.set_ylabel("Total Runs", color="#1F4E78")
        ax2 = ax.twinx()
        ax2.plot(ssn_df["season_year"].astype(str), ssn_df["Wickets"], marker="s", color="#EA580C", linewidth=2, label="Wickets")
        ax2.set_ylabel("Total Wickets", color="#EA580C")
        fig.tight_layout()
        st.pyplot(fig)

    with col_b:
        st.subheader("2. Top 10 Run Scorers")
        top_bat = (
            filtered.groupby("player_name", as_index=False)["runs_scored"]
            .sum()
            .sort_values("runs_scored", ascending=False)
            .head(10)
        )
        fig2, ax2p = plt.subplots(figsize=(6, 3.8))
        ax2p.barh(top_bat["player_name"], top_bat["runs_scored"], color="#0F766E")
        ax2p.invert_yaxis()
        ax2p.set_xlabel("Total Runs")
        fig2.tight_layout()
        st.pyplot(fig2)

    st.subheader("3. Head-to-Head Player Comparison")
    comp = filtered[filtered["player_name"].isin(sel_players)]
    if not comp.empty:
        comp_agg = comp.groupby(["player_name", "team_code", "player_role"], as_index=False).agg(
            Runs=("runs_scored", "sum"),
            Innings=("innings_batted", "sum"),
            Balls_Faced=("balls_faced", "sum"),
            Wickets=("wickets_taken", "sum"),
            Balls_Bowled=("balls_bowled", "sum"),
            Runs_Conceded=("runs_conceded", "sum"),
        )
        comp_agg["Strike Rate"] = ((comp_agg["Runs"] / comp_agg["Balls_Faced"].replace(0, pd.NA)) * 100).fillna(0).round(2)
        comp_agg["Economy"] = (comp_agg["Runs_Conceded"] / (comp_agg["Balls_Bowled"].replace(0, pd.NA) / 6.0)).fillna(0).round(2)
        st.bar_chart(comp_agg.set_index("player_name")[["Runs", "Strike Rate", "Wickets"]])
        st.dataframe(comp_agg, use_container_width=True)


if __name__ == "__main__":
    main()
