# Power BI Desktop Data Model, DAX & 3-Page Report Guide (Prompts P12 & P13)

---

## Part 1: Star Schema Data Model & Date Table (P12)

### A. Click-by-Click Import Steps
1. Open **Power BI Desktop** -> click **Home → Get data → Text/CSV** (or **Excel workbook**).
2. Load all 5 cleaned tables from `HCL_Project/data/clean/`:
   - `dim_teams.csv`
   - `dim_seasons.csv`
   - `dim_players.csv`
   - `dim_matches.csv`
   - `fact_player_match_stats.csv`
3. In **Transform Data (Power Query)**:
   - Verify **Use First Row as Headers** is active for every table.
   - Verify data types: `match_date` = **Date**, `runs_scored`/`balls_faced`/`wickets_taken`/`balls_bowled`/`not_out` = **Whole Number**, `overs_bowled` = **Decimal Number**.
   - Click **Close & Apply**.

### B. Star Schema Relationships (Model View)
Go to **Model view** (`Ctrl + 3`) and set the following **1-to-Many (`1:*`) Single-Direction** relationships (from Dimension -> Fact):
1. `dim_players[player_id]` (**1**) → `fact_player_match_stats[player_id]` (*****) — Cross-filter: **Single**
2. `dim_matches[match_id]` (**1**) → `fact_player_match_stats[match_id]` (*****) — Cross-filter: **Single**
3. `dim_teams[team_id]` (**1**) → `fact_player_match_stats[team_id]` (*****) — Cross-filter: **Single**
4. `dim_seasons[season_id]` (**1**) → `dim_matches[season_id]` (*****) — Cross-filter: **Single** *(snowflake link to filter matches & facts by season)*
5. *(Optional inactive relationships)* `dim_teams[team_id]` → `dim_players[team_id]` (Inactive if `dim_teams` already filters `fact_player_match_stats` directly, avoiding ambiguous filter paths).

### C. Create & Mark `dim_date` Table
1. Go to **Modeling → New table** and paste:
   ```dax
   dim_date =
   ADDCOLUMNS (
       CALENDAR ( DATE ( 2021, 1, 1 ), DATE ( 2024, 12, 31 ) ),
       "Year", YEAR ( [Date] ),
       "Month Number", MONTH ( [Date] ),
       "Month Name", FORMAT ( [Date], "MMM" ),
       "Year-Month", FORMAT ( [Date], "YYYY-MM" )
   )
   ```
2. Right-click `dim_date` → **Mark as date table → Mark as date table** → select `[Date]`.
3. In **Model view**, connect `dim_date[Date]` (**1**) → `dim_matches[match_date]` (*****) (**Single** cross-filter).

---

## Part 2: Core DAX Measures (With 1-Line Explanations)

Create a dedicated `_Measures` table (**Home → Enter Data**) and add these measures:

```dax
Total Runs = SUM ( fact_player_match_stats[runs_scored] )
// Sums all runs scored across the active filter context.

Innings Batted = SUM ( fact_player_match_stats[innings_batted] )
// Counts batting appearances where the player actually batted (innings_batted = 1).

Not Outs =
CALCULATE (
    SUM ( fact_player_match_stats[not_out] ),
    fact_player_match_stats[innings_batted] = 1
)
// Counts unbeaten batting innings while excluding did-not-bat (DNB) rows.

Batting Average =
VAR Dismissals = [Innings Batted] - [Not Outs]
RETURN
IF ( Dismissals > 0, DIVIDE ( [Total Runs], Dismissals ), [Total Runs] )
// Divides total runs by dismissals (Innings - Not Outs), falling back to Total Runs if unbeaten.

Batting Strike Rate =
DIVIDE ( [Total Runs] * 100, SUM ( fact_player_match_stats[balls_faced] ), 0 )
// Computes runs scored per 100 balls faced, safely returning 0 if balls faced is zero.

Total Wickets = SUM ( fact_player_match_stats[wickets_taken] )
// Sums all wickets taken across the active filter context.

Overs Bowled =
VAR TotalBalls = SUM ( fact_player_match_stats[balls_bowled] )
RETURN
QUOTIENT ( TotalBalls, 6 ) + DIVIDE ( MOD ( TotalBalls, 6 ), 10 )
// Aggregates exact balls_bowled back into cricket notation (e.g., 14 balls -> 2.2 overs).

Bowling Economy =
DIVIDE (
    SUM ( fact_player_match_stats[runs_conceded] ),
    DIVIDE ( SUM ( fact_player_match_stats[balls_bowled] ), 6 ),
    0
)
// Computes average runs conceded per 6-ball over from exact balls_bowled.

Season Runs Rank =
RANKX (
    ALLSELECTED ( dim_players[player_name] ),
    [Total Runs],
    ,
    DESC,
    DENSE
)
// Ranks players within the selected season using DENSE ranking so ties (e.g., 739 runs) share the same rank.

Prev Season Runs =
VAR CurrYear = MAX ( dim_seasons[season_year] )
RETURN
CALCULATE (
    [Total Runs],
    REMOVEFILTERS ( dim_seasons ),
    dim_seasons[season_year] = CurrYear - 1
)
// Retrieves the player's or team's total runs from the immediately preceding IPL season for YoY comparison.
```

---

## Part 3: 3-Page Report Layout, Visuals & Formatting (P13)

### Recommended Accessible High-Contrast Color Palette
- **Primary Navy:** `#1F4E78` (headers, KPI accents, primary batting bars)
- **Secondary Teal:** `#0F766E` (bowling metrics, positive deltas)
- **Accent Amber:** `#D97706` (strike rate trend lines, highlights)
- **Alert Coral:** `#DC2626` (missing balls / data-quality audit flags)
- **Canvas Background:** `#F8FAFC` (soft cool gray) with `#FFFFFF` card backgrounds and `#E2E8F0` thin card borders (`8px` corner radius).
- **Text:** `#0F172A` primary dark slate, `#475569` secondary labels.

### Page 1: Season Overview & Leaderboards
- **Top Slicers (Horizontal):** `dim_seasons[season_year]`, `dim_teams[team_code]`, `dim_players[player_role]`
- **4 KPI Cards:** `Total Runs` (`35,978`), `Total Wickets` (`1,143`), `Batting Average` (`51.62`), `Batting Strike Rate` (`147.05`)
- **Visual 1 (Left):** **Clustered Bar Chart** — Top 10 Run Scorers (`dim_players[player_name]` vs `[Total Runs]`, tooltip `[Batting Strike Rate]`, `[Season Runs Rank]`)
- **Visual 2 (Right):** **Clustered Bar Chart** — Top 10 Wicket Takers (`dim_players[player_name]` vs `[Total Wickets]`, tooltip `[Bowling Economy]`)
- **Visual 3 (Bottom):** **Line & Clustered Column Chart** — Monthly Runs & Strike Rate Trend (`dim_date[Year-Month]` on X-axis)

### Page 2: Player Cards & Head-to-Head Comparison
- **Slicers:** `dim_players[player_name]` (multi-select for 2–5 players), `dim_players[nationality]`, `dim_seasons[season_year]`
- **Visual 1 (Top Row):** **Multi-Row Player Card** — Displays `player_name`, `team_code`, `Total Runs`, `Batting Average`, `Batting Strike Rate`, `Total Wickets`, `Bowling Economy`
- **Visual 2 (Left):** **Scatter Chart** — `Batting Strike Rate` (X) vs `Batting Average` (Y), Bubble Size = `Total Runs`, Legend = `player_role`
- **Visual 3 (Right):** **Matrix / Comparison Table** — Rows: `season_year`, Columns: selected `player_name`, Values: `Total Runs`, `Prev Season Runs`, `Total Wickets`

### Page 3: Team / Venue Deep Dive & Data Quality Audit
- **Visual 1 (Top Left):** **Clustered Column Chart** — Franchise Runs & Wickets (`dim_teams[team_code]`)
- **Visual 2 (Top Right):** **100% Stacked Bar Chart** — Toss Decision (`bat` vs `field`) Win Impact by Venue
- **Visual 3 (Bottom):** **Table** — Data Quality & Imputation Summary (`balls_faced_imputed` flag check + `data_quality_log`)
- **Drill-Through Page (`Player Match Log`):**
  1. Create a 4th hidden page named **Player Match Log**.
  2. Drag `dim_players[player_name]` into the **Drill-through** field well.
  3. Add a detailed **Table** visual showing `match_date`, `venue`, `runs_scored`, `balls_faced`, `not_out`, `overs_bowled`, `wickets_taken`, and `player_of_match`.
  4. Users can right-click any player on Pages 1 or 2 → **Drill through → Player Match Log**.
