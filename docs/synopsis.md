# Project Synopsis — IPL Player Performance Dashboard (Project #21)

**Domain:** Sports and Entertainment  
**Tools & Stack:** Python (`pandas`, `matplotlib`, `pytest`), SQLite & Oracle SQL (DDL, DML, Window Functions, Views), Excel & Power BI (Star Schema, DAX, Slicers, Drill-Through)  
**Dataset:** Agent-Generated Synthetic IPL-Style Benchmark Dataset (2021–2024)

---

## 1. Background & Objectives
Evaluating cricket players across multiple T20 seasons requires combining match-level batting, bowling, and fielding events into reliable season and career metrics. Raw cricket logs commonly contain duplicate entries, mixed text/date conventions, missing ball counts, and ambiguous `not_out` flags that silently corrupt aggregates if loaded directly into BI tools.

The objectives of this project are to:
1. **Standardize & Audit Raw Data:** Clean raw multi-table IPL statistics in Python without silently dropping rows, recording every transformation in `data_quality_log.csv`.
2. **Model a Star Schema:** Organize teams, seasons, players, matches, and player-match statistics into a normalized star schema implemented in both SQLite (local execution) and Oracle SQL (enterprise DDL, load scripts, queries, and views).
3. **Solve Cricket-Specific Edge Cases:** Correctly compute `not_out`-adjusted batting averages, handle tied season rankings via `RANK()` / `DENSE_RANK()`, and recover/impute missing balls data transparently.
4. **Verify & Visualize:** Cross-check 5 benchmark players (`P001`–`P005`) across Python, SQL, and Excel/Power BI, and deliver an interactive dashboard featuring season leaderboards, player cards, and head-to-head comparison.

---

## 2. Dataset Summary
Instead of relying on an external Kaggle dump, a reproducible synthetic IPL-style dataset was generated in `data/raw/ipl_player_performance_raw.xlsx` (and matching CSVs):
- **Coverage:** 4 IPL seasons (`2021`–`2024`), `8` franchises (`dim_teams`), `32` unique players (`34` raw rows in `dim_players`), `160` matches (`dim_matches`), and `1,280` unique player-match records (`1,290` raw rows in `fact_player_match_stats`).
- **Intentional Quality Issues Embedded for Testing:** `12` total duplicate rows (`2` in players, `10` in facts), `18` non-ISO match dates, `7` whitespace/casing anomalies, `168` non-binary/blank `not_out` entries, `25` missing `balls_bowled` values, `15` missing `balls_faced` values, and `6` negative placeholder values.
- **Deliberate Rank Ties:** Engineered ties in `S2023` total runs (`739` runs each for Virat Kohli & Suryakumar Yadav) and `S2024` total wickets (`21` wickets each for Jasprit Bumrah & Rashid Khan).

---

## 3. Methodology
1. **Phase A (Planning & Design):** Define problem statement, KPI formulas, SRS, data dictionary, and star-schema ER diagram.
2. **Phase B (Python ETL & Quality Audit):** Run `clean_data.py` to deduplicate, normalize text/dates/`not_out`, derive/impute balls, output clean tables, and write `data_quality_log.csv`.
3. **Phase C (SQL Warehouse & Analytics):** Create star-schema tables with `PRIMARY KEY`, `FOREIGN KEY`, and `CHECK` constraints; load clean CSVs; run 7 analytical queries (`JOIN`, `GROUP BY`, `CASE`, `RANK()`, `DENSE_RANK()`, `LAG()`).
4. **Phase D (BI Visualization & Verification):** Build Power BI player cards, slicers, and drill-through pages; verify 5 sample players and Python-vs-SQL parity via `test_pipeline.py`.

---

## 4. Expected Outcomes
- Fully auditable ETL pipeline with `0` silent row drops and automated `PASS/FAIL` test verification.
- Verified career and season statistics for 5 benchmark players (`Virat Kohli`, `Rohit Sharma`, `Jasprit Bumrah`, `Rashid Khan`, `Suryakumar Yadav`).
- Production-ready SQLite and Oracle SQL scripts plus an interactive Power BI / Excel dashboard revealing top performers by season, role contributions, and head-to-head player comparisons.
