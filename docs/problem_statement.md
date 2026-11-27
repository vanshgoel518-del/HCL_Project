# Project #21 — Problem Statement & KPI Definitions

**Project Title:** IPL / Cricket Player Performance Dashboard  
**Domain:** Sports and Entertainment  

---

## Problem Statement

Cricket franchises, analysts, and fans rely on accurate match-by-match batting and bowling aggregates to evaluate player consistency across seasons, yet raw cricket datasets frequently distort leaderboards when not-out innings, missing balls-faced or balls-bowled records, and tied season totals are handled inconsistently. Naive calculations that divide runs by total innings rather than dismissals artificially deflate batting averages, missing balls data breaks strike-rate and economy computations, and basic sorting obscures true player rankings when two performers finish a season level on runs or wickets. This project builds an end-to-end data cleaning, star-schema SQL ranking, and interactive dashboard pipeline on a 4-season synthetic IPL dataset (2021–2024) so batting, bowling, and player-comparison metrics remain transparent, auditable, and mathematically verified across Python, SQL, and Power BI.

---

## Core KPI Definitions & Formulas

| KPI Name | Category | Formula | Edge-Case Handling Rule |
| :--- | :--- | :--- | :--- |
| **Matches Played** | Participation | `COUNT(DISTINCT match_id)` | Deduplicate `fact_player_match_stats` on `stat_id` (or `(match_id, player_id)`) before counting. |
| **Innings Batted** | Batting | `SUM(innings_batted)` | Only rows where `innings_batted = 1` count as a batting innings. |
| **Not Outs** | Batting | `SUM(CASE WHEN innings_batted = 1 THEN not_out ELSE 0 END)` | Normalize mixed values (`Yes`, `Y`, `1` -> `1`; `No`, `N`, `0` -> `0`; did-not-bat blank -> `0`). |
| **Total Runs** | Batting | `SUM(runs_scored)` | Clamp invalid negative placeholders (`-1`) on did-not-bat rows to `0` and log the rule. |
| **Batting Average** | Batting | `Total Runs / (Innings Batted - Not Outs)` | If `Dismissals = 0` (`Innings Batted = Not Outs`), return `Total Runs` (or `NULL` in strict SQL `NULLIF` mode) to prevent division by zero. |
| **Batting Strike Rate** | Batting | `(Total Runs / SUM(balls_faced)) * 100` | Exclude or impute missing `balls_faced` explicitly via documented role median SR; guard against `balls_faced = 0`. |
| **Total Wickets** | Bowling | `SUM(wickets_taken)` | Aggregate across valid match rows after deduplication. |
| **Overs Bowled** | Bowling | `FLOOR(SUM(balls_bowled) / 6) + (SUM(balls_bowled) % 6) / 10` | Always aggregate from `balls_bowled` rather than summing cricket notation (`3.2 + 3.4` overs) directly. |
| **Bowling Economy Rate** | Bowling | `SUM(runs_conceded) / (SUM(balls_bowled) / 6.0)` | Derive missing `balls_bowled` from `overs_bowled` (`floor(overs)*6 + round((overs%1)*10)`); guard against `balls_bowled = 0`. |
| **Bowling Strike Rate** | Bowling | `SUM(balls_bowled) / NULLIF(SUM(wickets_taken), 0)` | Guard against `0` wickets to avoid division by zero (`NULL` / `N/A` if no wickets taken). |
| **Season Rank (Batting / Bowling)** | Ranking | `RANK()` and `DENSE_RANK() OVER (PARTITION BY season_year ORDER BY metric DESC)` | Explicitly retain ties (e.g., `S2023` runs tie at `739`, `S2024` wickets tie at `21`) and break display order deterministically by secondary metric (Strike Rate / Economy). |
