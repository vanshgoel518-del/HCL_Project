# Project #21: IPL / Cricket Player Performance Dashboard

**Domain:** Sports and Entertainment  
**GitHub Repository:** https://github.com/vanshgoel518-del/HCL_Project  
**Tech Stack:** Python (`pandas`, `matplotlib`, `streamlit`), SQLite & Oracle SQL (Star Schema DDL, Window Functions, Views), Excel Power Query, Power BI Desktop

---

## 1. Overview
This project implements an auditable, end-to-end sports analytics pipeline on a 4-season synthetic IPL-style dataset (`2021`–`2024`, `8` franchises, `32` players, `160` matches, `1,280` clean player-match records). It explicitly handles cricket-specific data challenges:
- **Not-out innings** normalization (`Yes/Y/1` vs `No/N/0` vs did-not-bat blanks) for accurate Batting Average (`Runs / (Innings - Not Outs)`).
- **Missing balls data** recovery (`balls_bowled` derived from `overs_bowled`; `balls_faced` imputed via player-role median strike rate).
- **Ties in rank** preserved in season leaderboards via `RANK()` and `DENSE_RANK()` (`S2023` batting tie at `739` runs; `S2024` bowling tie at `21` wickets).
- **Zero silent row drops** with full transformation counts logged in `reports/data_quality_log.csv`.

---

## 2. Folder Structure
```text
HCL_Project/
├── app/
│   └── streamlit_app.py             # Interactive Streamlit player dashboard
├── data/
│   ├── raw/                         # Raw CSVs + multi-sheet raw Excel workbook
│   └── clean/                       # Cleaned CSVs + ipl_player_performance_clean.xlsx
├── docs/                            # Problem statement, synopsis, SRS, ER, Power BI & Excel guides
├── notebooks/
│   └── ipl_player_analysis.ipynb    # Annotated Jupyter analysis & insights notebook
├── reports/
│   ├── charts/                      # 4 PNG analytical charts
│   ├── sql_outputs/                 # CSV exports from all 7 SQL queries
│   ├── data_dictionary.csv
│   ├── data_quality_log.csv
│   ├── kpis.json
│   └── test_results.csv
├── sql/
│   ├── schema_sqlite.sql            # SQLite Star Schema DDL with CHECK constraints
│   ├── schema_oracle.sql            # Oracle Star Schema DDL
│   ├── load_oracle.sql              # Oracle INSERT & SQL*Loader instructions
│   ├── queries_sqlite.sql           # 7 SQLite analytical queries
│   └── queries_oracle.sql           # 7 Oracle queries + CREATE OR REPLACE VIEWs
├── src/
│   ├── clean_data.py                # P6 Python cleaning + quality log
│   ├── load_and_query.py            # P8 SQLite build, load & CSV export
│   └── analyze_and_plot.py          # P9 KPI JSON & 4 PNG charts
└── tests/
    └── test_pipeline.py             # P15 automated verification suite
```

---

## 3. Core KPI Definitions
| KPI | Formula |
| :--- | :--- |
| **Batting Average** | `Total Runs / (Innings Batted - Not Outs)` |
| **Batting Strike Rate** | `(Total Runs / Balls Faced) * 100` |
| **Bowling Economy** | `Runs Conceded / (Balls Bowled / 6.0)` |
| **Bowling Strike Rate** | `Balls Bowled / Wickets Taken` |
| **Overs Bowled** | `FLOOR(SUM(balls_bowled)/6) + (SUM(balls_bowled)%6)/10` |

---

## 4. How to Run the Pipeline
```bash
# 1. Clean raw data & generate data_quality_log.csv
python src/clean_data.py

# 2. Build SQLite star schema, load clean CSVs & export 7 query CSVs
python src/load_and_query.py

# 3. Compute KPIs (kpis.json) & generate 4 PNG charts
python src/analyze_and_plot.py

# 4. Run automated verification & 5-player benchmark tests
python tests/test_pipeline.py

# 5. (Optional) Launch interactive Streamlit dashboard
streamlit run app/streamlit_app.py
```
