"""
build_master_xlsx.py
Builds reports/Project21_Complete_Dataset_And_Reports.xlsx with 22 sheets
using openpyxl — produces a valid, openable Excel file.
"""

import csv
import json
import os
import sys

try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("ERROR: openpyxl not found. Run: pip install openpyxl")
    sys.exit(1)

ROOT   = r"c:\Users\user\OneDrive\Desktop\HCL_Project"
OUT    = os.path.join(ROOT, "reports", "Project21_Complete_Dataset_And_Reports.xlsx")

# ── Styles ────────────────────────────────────────────────────────────────────
HDR_FILL   = PatternFill("solid", fgColor="1F4E79")   # dark blue
HDR_FONT   = Font(color="FFFFFF", bold=True, size=10)
TITLE_FONT = Font(bold=True, size=14, color="1F4E79")
ALT_FILL   = PatternFill("solid", fgColor="DDEEFF")
THIN       = Side(style="thin", color="AAAAAA")
BORDER     = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

def style_header(ws, row_num, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row_num, column=c)
        cell.fill   = HDR_FILL
        cell.font   = HDR_FONT
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def style_data_row(ws, row_num, ncols, alt=False):
    fill = ALT_FILL if alt else PatternFill("solid", fgColor="FFFFFF")
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row_num, column=c)
        cell.fill   = fill
        cell.border = BORDER
        cell.alignment = Alignment(vertical="center", wrap_text=False)

def auto_col_width(ws, min_w=8, max_w=40):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                val = str(cell.value) if cell.value is not None else ""
                max_len = max(max_len, len(val))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, min_w), max_w)

def coerce(val):
    """Return int/float if numeric string, else string."""
    if val is None or val == "":
        return ""
    try:
        f = float(val)
        if f == int(f) and "." not in str(val):
            return int(f)
        return round(f, 4)
    except (ValueError, TypeError):
        return str(val)

# ── CSV reader ────────────────────────────────────────────────────────────────
def read_csv(filepath):
    if not os.path.exists(filepath):
        return [["FILE NOT FOUND: " + filepath]]
    rows = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows if rows else [["(empty)"]]

# ── Write a sheet from list-of-lists ─────────────────────────────────────────
def write_sheet(ws, rows, freeze_header=True):
    if not rows:
        ws.append(["(empty)"])
        return
    ncols = max(len(r) for r in rows)
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row, start=1):
            ws.cell(row=ri, column=ci, value=coerce(val))
        # pad missing cols
        for ci in range(len(row) + 1, ncols + 1):
            ws.cell(row=ri, column=ci, value="")
        if ri == 1:
            style_header(ws, ri, ncols)
        else:
            style_data_row(ws, ri, ncols, alt=(ri % 2 == 0))
    if freeze_header:
        ws.freeze_panes = "A2"
    auto_col_width(ws)

# ── Cover sheet ───────────────────────────────────────────────────────────────
def write_cover(ws):
    ws.freeze_panes = None
    info = [
        ("Project",          "IPL / Cricket Player Performance Dashboard"),
        ("Project Number",   "#21"),
        ("Domain",           "Sports & Entertainment"),
        ("GitHub Repo",      "https://github.com/vanshgoel518-del/HCL_Project"),
        ("Student",          "vanshgoel518-del"),
        ("Dataset",          "Agent-generated synthetic IPL-style (seed=20261127)"),
        ("Seasons",          "S2021, S2022, S2023, S2024  (4 seasons)"),
        ("Matches",          "160 total"),
        ("Players",          "32 unique (34 raw incl. 2 intentional duplicates)"),
        ("Fact Rows (Clean)","1,280 (raw 1,290 incl. 10 duplicates)"),
        ("Total Runs",       "35,978"),
        ("Total Wickets",    "1,143"),
        ("Batting Avg",      "51.62"),
        ("Batting SR",       "147.05"),
        ("Bowling Economy",  "8.21"),
    ]

    # Title
    ws.merge_cells("A1:C1")
    title_cell = ws["A1"]
    title_cell.value     = "Project #21 — IPL Player Performance Dashboard"
    title_cell.font      = TITLE_FONT
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Metadata table header
    ws["A3"] = "Field";   ws["A3"].font = HDR_FONT; ws["A3"].fill = HDR_FILL; ws["A3"].border = BORDER
    ws["B3"] = "Value";   ws["B3"].font = HDR_FONT; ws["B3"].fill = HDR_FILL; ws["B3"].border = BORDER

    for ri, (k, v) in enumerate(info, start=4):
        kc = ws.cell(row=ri, column=1, value=k)
        vc = ws.cell(row=ri, column=2, value=v)
        kc.font = Font(bold=True)
        for cell in (kc, vc):
            cell.border = BORDER
            cell.fill   = ALT_FILL if ri % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")

    # Sheet index
    sheet_index = [
        ("Sheet Name",          "Contents"),
        ("Cover & Guide",       "Project metadata + KPI summary"),
        ("kpis_summary",        "Flattened KPIs from kpis.json"),
        ("RAW_dim_teams",       "Raw teams dimension (8 rows)"),
        ("RAW_dim_seasons",     "Raw seasons (4 rows)"),
        ("RAW_dim_players",     "Raw players (34 rows, 2 intentional dups)"),
        ("RAW_dim_matches",     "Raw matches (160 rows, mixed date formats)"),
        ("RAW_fact_stats",      "Raw fact table (1,290 rows, 10 dups)"),
        ("CLEAN_dim_teams",     "Cleaned teams"),
        ("CLEAN_dim_seasons",   "Cleaned seasons"),
        ("CLEAN_dim_players",   "Cleaned players (32 rows)"),
        ("CLEAN_dim_matches",   "Cleaned matches (ISO dates, normalised fields)"),
        ("CLEAN_fact_stats",    "Cleaned fact table (1,280 rows)"),
        ("data_quality_log",    "9 cleaning rules + rows_affected per rule"),
        ("data_dictionary",     "52-column data dictionary"),
        ("Q1_5player_verify",   "SQL Q1 — 5 benchmark player career totals"),
        ("Q2_batting_ranks",    "SQL Q2 — Season batting RANK / DENSE_RANK"),
        ("Q3_bowling_ranks",    "SQL Q3 — Season bowling RANK / DENSE_RANK"),
        ("Q4_yoy_runs_lag",     "SQL Q4 — LAG() year-over-year run diff"),
        ("Q5_team_summary",     "SQL Q5 — Team batting & bowling by season"),
        ("Q6_perf_tiers",       "SQL Q6 — Elite / Consistent / Supporting tiers"),
        ("Q7_toss_impact",      "SQL Q7 — Toss decision & venue win-rate"),
        ("test_results",        "Pipeline tests — 6/6 PASS"),
    ]

    start_row = 4 + len(info) + 2
    ws.cell(row=start_row - 1, column=1, value="Sheet Index").font = Font(bold=True, size=12)

    for ri, (name, desc) in enumerate(sheet_index, start=start_row):
        nc = ws.cell(row=ri, column=1, value=name)
        dc = ws.cell(row=ri, column=2, value=desc)
        if ri == start_row:
            nc.font = HDR_FONT; nc.fill = HDR_FILL; nc.border = BORDER
            dc.font = HDR_FONT; dc.fill = HDR_FILL; dc.border = BORDER
        else:
            for cell in (nc, dc):
                cell.border = BORDER
                cell.fill   = ALT_FILL if ri % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 52
    ws.column_dimensions["C"].width = 10

# ── KPIs from JSON ────────────────────────────────────────────────────────────
def kpi_rows():
    kpi_path = os.path.join(ROOT, "reports", "kpis.json")
    if not os.path.exists(kpi_path):
        return [["kpi", "value"], ["FILE NOT FOUND", ""]]
    with open(kpi_path, encoding="utf-8") as f:
        kpis = json.load(f)
    rows = [["KPI", "Value"]]
    def flatten(obj, prefix=""):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flatten(v, key)
            elif isinstance(v, list):
                rows.append([key, json.dumps(v)])
            else:
                rows.append([key, v])
    flatten(kpis)
    return rows

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    wb = Workbook()
    wb.remove(wb.active)   # remove default empty sheet

    R = lambda rel: os.path.join(ROOT, rel)

    sheets_def = [
        ("Cover & Guide",     None),   # special
        ("kpis_summary",      None),   # special
        ("RAW_dim_teams",     R("data/raw/dim_teams.csv")),
        ("RAW_dim_seasons",   R("data/raw/dim_seasons.csv")),
        ("RAW_dim_players",   R("data/raw/dim_players.csv")),
        ("RAW_dim_matches",   R("data/raw/dim_matches.csv")),
        ("RAW_fact_stats",    R("data/raw/fact_player_match_stats.csv")),
        ("CLEAN_dim_teams",   R("data/clean/dim_teams.csv")),
        ("CLEAN_dim_seasons", R("data/clean/dim_seasons.csv")),
        ("CLEAN_dim_players", R("data/clean/dim_players.csv")),
        ("CLEAN_dim_matches", R("data/clean/dim_matches.csv")),
        ("CLEAN_fact_stats",  R("data/clean/fact_player_match_stats.csv")),
        ("data_quality_log",  R("reports/data_quality_log.csv")),
        ("data_dictionary",   R("reports/data_dictionary.csv")),
        ("Q1_5player_verify", R("reports/sql_outputs/q1_5_player_verification.csv")),
        ("Q2_batting_ranks",  R("reports/sql_outputs/q2_season_batting_ranks.csv")),
        ("Q3_bowling_ranks",  R("reports/sql_outputs/q3_season_bowling_ranks.csv")),
        ("Q4_yoy_runs_lag",   R("reports/sql_outputs/q4_yoy_player_runs_lag.csv")),
        ("Q5_team_summary",   R("reports/sql_outputs/q5_team_season_summary.csv")),
        ("Q6_perf_tiers",     R("reports/sql_outputs/q6_player_performance_tiers.csv")),
        ("Q7_toss_impact",    R("reports/sql_outputs/q7_toss_and_venue_impact.csv")),
        ("test_results",      R("reports/test_results.csv")),
    ]

    for name, csvpath in sheets_def:
        ws = wb.create_sheet(title=name)
        print(f"  Writing sheet: {name:<24}", end="")
        if name == "Cover & Guide":
            write_cover(ws)
            print("  (cover)")
        elif name == "kpis_summary":
            rows = kpi_rows()
            write_sheet(ws, rows)
            print(f"  {len(rows)} rows")
        else:
            rows = read_csv(csvpath)
            write_sheet(ws, rows)
            print(f"  {len(rows)} rows")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    size_kb = os.path.getsize(OUT) / 1024
    print(f"\n✅ Saved: {OUT}")
    print(f"   Size:   {size_kb:.1f} KB")
    print(f"   Sheets: {len(wb.sheetnames)}")
    print("   Sheet list:", wb.sheetnames)

if __name__ == "__main__":
    main()
