# Excel Power Query Cleaning, PivotTables & Cross-Check Guide (Prompt P14)

Use this guide to build the Excel companion dashboard directly from [ipl_player_performance_raw.xlsx](file:///c:/Users/user/OneDrive/Desktop/HCL_Project/data/raw/ipl_player_performance_raw.xlsx).

---

## 1. Power Query Cleaning Steps
Open Excel → **Data → Get Data → From File → From Excel Workbook** → select `data/raw/ipl_player_performance_raw.xlsx`:

1. **`dim_players` Query:**
   - **Remove Duplicates:** Select `player_id` → **Home → Remove Rows → Remove Duplicates** (removes `2` duplicate rows).
   - **Trim & Proper Case:** Select `player_name`, `player_role`, `batting_hand` → **Transform → Format → Trim** then **Capitalize Each Word** (`4` rows fixed; note set `All-Rounder` / `Right-hand` consistently if needed).
2. **`dim_matches` Query:**
   - **Parse Mixed Dates:** Select `match_date` → **Transform → Data Type → Date → Using Locale...** (or parse `DD/MM/YYYY`, `DD-MMM-YYYY`, `YYYY-MM-DD`) → format as ISO `YYYY-MM-DD` (`18` dates standardized).
   - **Trim & Lowercase:** Trim `venue` and `city`; set `toss_decision` to **lowercase** (`3` rows fixed).
3. **`fact_player_match_stats` Query:**
   - **Remove Duplicates:** Select `stat_id` → **Remove Duplicates** (`10` duplicate rows removed).
   - **Normalize `not_out`:** Replace `"Yes"`, `"yes"`, `"Y"` → `1`; replace `"No"`, `"no"`, `"N"`, `null` → `0`; convert to **Whole Number** (`166` rows normalized).
   - **Replace Negative Errors:** Replace `-1` in `runs_scored` and `-99` in `catches` with `0` (`6` rows fixed).
   - **Fix Missing `balls_bowled`:** Replace `"NA"` with `null`, then add Conditional/Custom Column:
     ```powerquery
     if [balls_bowled] = null and [overs_bowled] > 0
     then Number.IntegerDivide(Number.RoundDown([overs_bowled]) * 6 + Number.Round(([overs_bowled] - Number.RoundDown([overs_bowled])) * 10), 1)
     else if [balls_bowled] = null then 0 else [balls_bowled]
     ```
   - **Fix Missing `balls_faced`:** Replace `"NA"` with `null`; flag missing active batting innings (`innings_batted = 1`) and impute using role median strike rate.
4. Click **Home → Close & Load To... → Only Create Connection** + check **Add this data to the Data Model** (Power Pivot) for all 5 tables.

---

## 2. PivotTables & Slicers Dashboard Sheet
Create a new sheet named `Dashboard` and insert 3 PivotTables linked to the Data Model:
1. **Pivot 1 — Top Season Batsmen:**
   - Rows: `dim_players[player_name]` (Top 10 Value Filter by Sum of `runs_scored`)
   - Values: `Sum of runs_scored`, `Sum of balls_faced`
2. **Pivot 2 — Top Season Bowlers:**
   - Rows: `dim_players[player_name]` (Top 10 Value Filter by Sum of `wickets_taken`)
   - Values: `Sum of wickets_taken`, `Sum of balls_bowled`, `Sum of runs_conceded`
3. **Pivot 3 — 5-Player Benchmark Verification:**
   - Filter: `dim_players[player_id]` IN `{P001, P002, P003, P004, P005}`
   - Rows: `player_id`, `player_name`
   - Values: `Sum of innings_batted`, `Sum of not_out`, `Sum of runs_scored`, `Sum of balls_faced`, `Sum of wickets_taken`
4. **Add Slicers:** Click any PivotTable → **PivotTable Analyze → Insert Slicer** → select `season_year`, `team_code`, `player_role` → right-click each slicer → **Report Connections** → check all 3 PivotTables.

---

## 3. Excel Cross-Check Formulas (Verify Against Python & SQL)
Assuming clean `fact_player_match_stats` is loaded on sheet `fact_clean` (where `C` = `player_id`, `E` = `innings_batted`, `F` = `runs_scored`, `G` = `balls_faced`, `J` = `not_out`, `L` = `balls_bowled`, `M` = `runs_conceded`, `N` = `wickets_taken`):

| Metric | Excel Verification Formula | Expected Clean Value |
| :--- | :--- | :--- |
| **Grand Total Runs** | `=SUM(fact_clean!F:F)` | `35,978` |
| **Grand Total Wickets** | `=SUM(fact_clean!N:N)` | `1,143` |
| **Player Total Runs (`P001`)** | `=SUMIFS(fact_clean!F:F, fact_clean!C:C, "P001")` | `2,986` |
| **Player Innings (`P001`)** | `=SUMIFS(fact_clean!E:E, fact_clean!C:C, "P001")` | `56` |
| **Player Not Outs (`P001`)** | `=SUMIFS(fact_clean!J:J, fact_clean!C:C, "P001", fact_clean!E:E, 1)` | `11` |
| **Player Batting Avg (`P001`)** | `=ROUND(SUMIFS(fact_clean!F:F, fact_clean!C:C, "P001") / (SUMIFS(fact_clean!E:E, fact_clean!C:C, "P001") - SUMIFS(fact_clean!J:J, fact_clean!C:C, "P001", fact_clean!E:E, 1)), 2)` | `66.36` |
| **Player Strike Rate (`P001`)** | `=ROUND((SUMIFS(fact_clean!F:F, fact_clean!C:C, "P001") / SUMIFS(fact_clean!G:G, fact_clean!C:C, "P001")) * 100, 2)` | `146.44` |
| **Player Economy (`P003`)** | `=ROUND(SUMIFS(fact_clean!M:M, fact_clean!C:C, "P003") / (SUMIFS(fact_clean!L:L, fact_clean!C:C, "P003") / 6), 2)` | `7.94` |
| **Average Match Runs** | `=AVERAGE(fact_clean!F:F)` | `28.11` |
| **Active Batting Innings Count** | `=COUNTIFS(fact_clean!E:E, 1)` | `977` |
