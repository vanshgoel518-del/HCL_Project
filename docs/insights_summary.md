# Insights Summary & Recommendations — Project #21 (IPL Player Performance)

## 1. Executive Summary
Across **4 IPL seasons (`2021`–`2024`, `160` matches, `32` players, `1,280` clean player-match records)**, players scored **`35,978` total runs** (overall batting average **`51.62`**, strike rate **`147.05`**) and took **`1,143` wickets** (overall economy **`8.21`**). Automated pipeline checks (`tests/test_pipeline.py`) confirmed **6/6 PASS** with exact Python-to-SQL parity (`35,978` runs, `1,143` wickets) and `100%` match on all 5 benchmark players.

---

## 2. Key Analytical Insights

1. **Data Quality & Missing-Balls Sensitivity:**
   - Cleaning resolved **`249` field/row issues** across `9` rules without silently dropping non-duplicate rows (`2` duplicate players + `10` duplicate fact rows removed; `166` `not_out` flags normalized; `18` dates standardized; `25` missing `balls_bowled` values recovered from `overs_bowled`; `15` missing `balls_faced` values imputed).
   - Imputing the `15` missing `balls_faced` rows shifted aggregate strike rate minimally from **`146.98`** (observed balls only) to **`147.05`** (`+0.07`), proving imputation preserved macro batting trends while retaining all `977` active innings.

2. **Not-Out Impact on Batting Averages (5-Player Benchmark):**
   - Properly subtracting `not_out` innings from dismissals (`Innings - Not Outs`) raised benchmark averages materially (`P001 Virat Kohli`: `2,986` runs across `56` innings with `11` not outs -> Avg **`66.36`**, SR **`146.44`**; `P005 Suryakumar Yadav`: `2,673` runs, `11` not outs -> Avg **`65.20`**, SR **`149.83`**; `P002 Rohit Sharma`: `2,731` runs, `10` not outs -> Avg **`65.02`**, SR **`147.14`**).
   - Benchmark bowlers delivered strong containment: `P003 Jasprit Bumrah` took **`93` wickets** at Econ **`7.94`**, and `P004 Rashid Khan` took **`79` wickets** at Econ **`8.17`**.

3. **Ties in Season Rankings (`RANK()` vs. `DENSE_RANK()`):**
   - Using SQL window functions preserved exact ties: in **`2023`**, `Virat Kohli` and `Suryakumar Yadav` tied for **Rank 1** with **`739` runs** each; in **`2021`**, `Jasprit Bumrah` and `Mohammed Siraj` tied for **Rank 1** with **`27` wickets** each; and in **`2024`**, `Rashid Khan` (`Econ 8.06`) and `Jasprit Bumrah` (`Econ 8.07`) tied for **Rank 3** with **`21` wickets** each.

4. **Franchise & Role Concentration:**
   - **MI (`7,188` runs, `144` wickets)** and **RCB (`7,165` runs, `165` wickets)** generated the highest combined batting output, while **SRH (`195` wickets)** led all franchises in total wickets.
   - **Batsmen** contributed **`21,184` runs (`58.88%`)**, **All-Rounders** contributed **`8,229` runs + `265` wickets**, **Wicket-Keepers** scored **`5,046` runs**, and **Bowlers** claimed **`878` wickets (`76.82%`)**.

5. **Toss Decision Advantage:**
   - Captains elected to **field first** in `93` of `160` matches (`58.1%`) and won **`50` of `93` (`53.76%`)**, compared to only **`24` wins in `67` matches (`35.82%`)** when electing to **bat first**.

---

## 3. Actionable Recommendations
1. **Adopt `DENSE_RANK()` + Secondary Tiebreakers in Fantasy/Broadcast Leaderboards:** Display tied ranks explicitly (e.g., `T-1`) and sort visually by Strike Rate (batting) or Economy Rate (bowling).
2. **Enforce Schema `CHECK` Constraints & `balls_faced_imputed` Flags at Ingestion:** Prevent negative placeholders and missing ball counts before BI refresh; allow analysts to toggle imputed rows in Power BI slicers.
3. **Prioritize Chasing Strategy & All-Rounder Depth:** Given the **`+17.94` percentage-point win-rate edge** for teams chasing after winning the toss (`53.76%` vs. `35.82%`), teams should favor bowling first and investing in All-Rounders who supply **`22.87%` of runs (`8,229`)** alongside **`23.18%` of wickets (`265`)**.
