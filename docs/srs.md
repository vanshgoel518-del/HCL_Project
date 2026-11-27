# Software Requirements Specification (SRS)
## IPL / Cricket Player Performance Dashboard (Project #21)

---

## 1. Purpose & Scope
This document specifies the functional, non-functional, and acceptance requirements for the **IPL Player Performance Dashboard**, an end-to-end sports analytics pipeline transforming raw synthetic match-level cricket data (`2021`–`2024`) into verified SQL tables, analytical reports, and an interactive BI dashboard.

---

## 2. Functional Requirements

| ID | Requirement | Description |
| :--- | :--- | :--- |
| **FR-1** | **Raw Data Ingestion & Audit Cleaning** | The Python cleaning script (`src/clean_data.py`) shall ingest all 5 raw CSV/Excel tables (`dim_teams`, `dim_seasons`, `dim_players`, `dim_matches`, `fact_player_match_stats`), resolve duplicates, casing/whitespace, mixed dates, `not_out` encodings, missing balls data, and negative placeholders, and output cleaned files to `data/clean/`. |
| **FR-2** | **Data Quality Audit Logging** | Every cleaning transformation shall count the exact rows modified and record `(issue, rule_applied, rows_affected)` in `reports/data_quality_log.csv`. No rows may be silently dropped. |
| **FR-3** | **Star-Schema Database Creation** | SQL DDL scripts (`sql/schema_sqlite.sql` and `sql/schema_oracle.sql`) shall define 4 dimension tables and 1 fact table with Primary Keys, Foreign Keys, and `CHECK` constraints enforcing valid ranges (`runs_scored >= 0`, `balls_bowled BETWEEN 0 AND 24`, `not_out IN (0, 1)`). |
| **FR-4** | **Analytical SQL Queries & Views** | SQL scripts (`sql/queries_sqlite.sql`, `sql/queries_oracle.sql`) shall answer 7 business questions using `JOIN`, `GROUP BY`, `CASE`, `RANK()`, `DENSE_RANK()`, and `LAG()`, and provide Oracle `CREATE OR REPLACE VIEW` leaderboards. |
| **FR-5** | **Not-Out & Missing Balls Handling** | Batting average shall divide `runs_scored` by `dismissals = innings_batted - not_out`; missing `balls_bowled` shall be reconstructed from `overs_bowled`; missing `balls_faced` shall be imputed via a documented rule and flagged. |
| **FR-6** | **Tie-Aware Season Ranking** | Season batting and bowling leaderboards shall preserve rank ties (`RANK()` / `DENSE_RANK()`) rather than breaking ties arbitrarily. |
| **FR-7** | **5-Player Benchmark Verification** | System outputs in Python, SQL, and Power BI/Excel shall match the expected totals (Runs, Batting Average, Strike Rate, Wickets, Economy) for 5 benchmark players (`P001`–`P005`). |
| **FR-8** | **Interactive Dashboard & Comparison** | The Power BI report (`.pbix`) and Excel/Streamlit views shall provide KPI player cards, Season/Team/Role slicers, a Player Comparison page, and drill-through to match-level stats. |

---

## 3. Non-Functional Requirements

| ID | Category | Requirement |
| :--- | :--- | :--- |
| **NFR-1** | **Data Integrity** | Zero silent row drops: `raw_rows - exact_duplicates == clean_rows` for every table (`34 - 2 = 32` players; `1,290 - 10 = 1,280` fact rows). |
| **NFR-2** | **Cross-Tool Parity** | Aggregate `SUM(runs_scored)` and `SUM(wickets_taken)` computed in Python `pandas` must equal SQLite/Oracle SQL totals to the exact integer. |
| **NFR-3** | **Reproducibility** | All scripts (`clean_data.py`, `load_and_query.py`, `analyze_and_plot.py`, `test_pipeline.py`) must execute deterministically from the project root without manual edits. |
| **NFR-4** | **Readability & Accessibility** | Charts and Power BI pages must use colorblind-safe high-contrast palettes, clear titles, axis labels, and source captions. |
| **NFR-5** | **Submission Portability** | All deliverables must be exportable to portal-accepted formats (`.xlsx`, `.csv`, `.pdf`, `.docx`) within the 20-file / 100 MB limit alongside the GitHub repository. |

---

## 4. Acceptance Criteria & Verification Matrix

| Test / Check | Expected Outcome | Verification Method |
| :--- | :--- | :--- |
| **AC-1: Primary Key Uniqueness** | `0` duplicate keys in all 5 cleaned tables (`32` players, `160` matches, `1,280` facts). | Automated check in `tests/test_pipeline.py` |
| **AC-2: Referential Integrity** | `100%` of `fact_player_match_stats` rows match valid `match_id`, `player_id`, and `team_id` dimension rows. | Foreign key enforcement + `test_pipeline.py` |
| **AC-3: Range & Null Validation** | `0` nulls in required keys/metrics; `runs_scored >= 0`, `balls_bowled` in `0..24`, `not_out` in `{0, 1}`. | SQL `CHECK` constraints + `test_pipeline.py` |
| **AC-4: 5-Player Accuracy** | `P001`–`P005` Runs, Average, Strike Rate, Wickets, Economy match `sample_5_players_benchmark`. | Automated comparison in `test_pipeline.py` & `q1` SQL |
| **AC-5: Tie Handling** | `S2023` batting query shows `P001` & `P005` tied at Rank `1` (`739` runs); `S2024` bowling query shows `P003` & `P004` tied at Rank `1` (`21` wickets). | Inspect `q2_season_batting_ranks.csv` & `q3_season_bowling_ranks.csv` |
| **AC-6: Python = SQL Parity** | Python `kpis.json` totals match SQLite query totals with `0` discrepancy. | Automated assertion in `test_pipeline.py` -> `reports/test_results.csv` |
