# Dataset Documentation — Synthetic IPL Player Performance Dataset

## 1. Source, Generation & License
- **Dataset Name:** IPL Player Performance Synthetic Benchmark Dataset (`2021`–`2024`)
- **Source:** Agent-generated synthetic cricket dataset (`data/raw/ipl_player_performance_raw.xlsx` and `data/raw/*.csv`) — created deterministically (`seed = 20261127`) specifically for Project #21 without external Kaggle downloads.
- **License:** Educational / Synthetic Open Use (`CC0-equivalent` — free to modify, analyze, and publish in academic portfolios).
- **Disclaimer:** Player and franchise names are used solely as realistic domain identifiers for synthetic match simulations; match scores and player totals do not represent official BCCI/IPL records.

---

## 2. Table Architecture & Grain

| Table Name | Role | Grain (1 Row Represents) | Raw Rows | Clean Rows |
| :--- | :--- | :--- | :---: | :---: |
| `dim_teams` | Dimension | One IPL franchise | 8 | 8 |
| `dim_seasons` | Dimension | One IPL tournament season (`2021`–`2024`) | 4 | 4 |
| `dim_players` | Dimension | One player profile | 34 | 32 |
| `dim_matches` | Dimension | One scheduled/played match | 160 | 160 |
| `fact_player_match_stats` | Fact | One player's batting, bowling, and fielding line in one match | 1,290 | 1,280 |

---

## 3. Intentional Raw Data Quality Issues (For Pipeline Verification)

| # | Table | Issue Category | Rows Affected | Cleaning Rule to Apply |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `dim_players` | Exact duplicate player rows (`P004`, `P014`) | 2 | Deduplicate keeping first occurrence on `player_id`. |
| 2 | `dim_players` | Leading/trailing whitespace & inconsistent casing (`" batsman "`, `"BATSMAN"`, `"  Ravindra Jadeja "`) | 4 | Apply `.str.strip()` and standardize Title/Proper case. |
| 3 | `dim_matches` | Mixed date formats (`DD/MM/YYYY` and `DD-MMM-YYYY` instead of ISO `YYYY-MM-DD`) | 18 | Parse multiple date formats and format uniformly as `YYYY-MM-DD`. |
| 4 | `dim_matches` | Whitespace & casing in `venue` and `toss_decision` (`"FIELD "`, `"Bat"`) | 3 | Trim whitespace and lowercase `toss_decision` (`bat`/`field`). |
| 5 | `fact_player_match_stats` | Exact duplicate fact rows | 10 | Deduplicate keeping first occurrence on `stat_id`. |
| 6 | `fact_player_match_stats` | Non-binary / blank `not_out` values (`Yes`, `yes`, `Y`, `No`, `no`, `N`, or blank when `innings_batted = 0`) | 168 | Map `{Yes,yes,Y,1} -> 1`, `{No,no,N,0} -> 0`, blank DNB -> `0`. |
| 7 | `fact_player_match_stats` | Missing/`NA` `balls_bowled` where `overs_bowled > 0` | 25 | Derive exact balls via `floor(overs)*6 + round((overs%1)*10)`. |
| 8 | `fact_player_match_stats` | Missing/`NA` `balls_faced` on active batting innings (`runs_scored > 0`) | 15 | Impute from `runs_scored` using player-role median strike rate & flag. |
| 9 | `fact_player_match_stats` | Negative out-of-range placeholders (`runs_scored = -1`, `catches = -99`) on `innings_batted = 0` rows | 6 | Clamp negative did-not-bat placeholders to `0` and log. |

---

## 4. Built-In Rank Ties & 5 Benchmark Players
- **Engineered Ties in Rank:**
  - **Season 2023 Batting Tie:** `P001 Virat Kohli` and `P005 Suryakumar Yadav` both finish `S2023` with **`739` runs**.
  - **Season 2024 Bowling Tie:** `P003 Jasprit Bumrah` and `P004 Rashid Khan` both finish `S2024` with **`21` wickets**.
- **5 Benchmark Players (`sample_5_players_benchmark` sheet):**
  - `P001 Virat Kohli` (`T01`): 56 matches, 56 innings, 11 NO, **2,986 runs**, Avg **66.36**, SR **146.44**
  - `P002 Rohit Sharma` (`T02`): 52 matches, 52 innings, 10 NO, **2,731 runs**, Avg **65.02**, SR **147.14**
  - `P003 Jasprit Bumrah` (`T02`): 52 matches, 18 innings, 6 NO, **179 runs** (Avg **14.92**, SR **92.75**), **93 wickets**, Econ **7.94**
  - `P004 Rashid Khan` (`T07`): 36 matches, 11 innings, 6 NO, **89 runs** (Avg **17.80**, SR **95.70**), **79 wickets**, Econ **8.17**
  - `P005 Suryakumar Yadav` (`T02`): 52 matches, 52 innings, 11 NO, **2,673 runs**, Avg **65.20**, SR **149.83**
