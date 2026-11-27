"""P6 Data Cleaning Pipeline for Project #21 (IPL Player Performance Dashboard).

Reads all 5 raw CSV tables from data/raw/, applies auditable cleaning rules
without silently dropping non-duplicate rows, exports cleaned CSVs and a
multi-sheet Excel workbook to data/clean/, and writes reports/data_quality_log.csv.
"""

from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
CLEAN_DIR = ROOT_DIR / "data" / "clean"
REPORTS_DIR = ROOT_DIR / "reports"


def _col_letter(idx: int) -> str:
    letters = ""
    n = idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def write_xlsx_multi_sheet(out_path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    """Write a clean multi-sheet XLSX workbook using openpyxl or built-in OOXML fallback."""
    try:
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        return
    except ImportError:
        pass

    # Pure-Python OOXML fallback when openpyxl is not installed
    sheet_items = [(name[:31], df) for name, df in sheets.items()]
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        overrides = "".join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, len(sheet_items) + 1)
        )
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f"{overrides}</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>',
        )
        sheet_tags = "".join(
            f'<sheet name="{_xml_escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
            for i, (name, _) in enumerate(sheet_items, start=1)
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{sheet_tags}</sheets></workbook>",
        )
        wb_rels = "".join(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(sheet_items) + 1)
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{wb_rels}"
            f'<Relationship Id="rId{len(sheet_items) + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/></Relationships>',
        )
        zf.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
            '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
            '<fills count="3"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/></patternFill></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'
            "</styleSheet>",
        )

        for idx, (_, df) in enumerate(sheet_items, start=1):
            cols = list(df.columns)
            row_xmls = []
            hdr_cells = "".join(
                f'<c r="{_col_letter(c)}1" t="inlineStr" s="1"><is><t>{_xml_escape(str(col))}</t></is></c>'
                for c, col in enumerate(cols)
            )
            row_xmls.append(f'<row r="1">{hdr_cells}</row>')
            for r_idx, row_vals in enumerate(df.itertuples(index=False, name=None), start=2):
                cells = []
                for c_idx, val in enumerate(row_vals):
                    if pd.isna(val):
                        continue
                    ref = f"{_col_letter(c_idx)}{r_idx}"
                    if isinstance(val, (int, np.integer)) and not isinstance(val, bool):
                        cells.append(f'<c r="{ref}"><v>{int(val)}</v></c>')
                    elif isinstance(val, (float, np.floating)):
                        if np.isfinite(val):
                            cells.append(f'<c r="{ref}"><v>{float(val)}</v></c>')
                    else:
                        cells.append(
                            f'<c r="{ref}" t="inlineStr"><is><t>{_xml_escape(str(val))}</t></is></c>'
                        )
                row_xmls.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
            zf.writestr(
                f"xl/worksheets/sheet{idx}.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(row_xmls)}</sheetData></worksheet>',
            )


def _standardize_role(val: str) -> str:
    cleaned = str(val).strip().lower()
    mapping = {
        "batsman": "Batsman",
        "bowler": "Bowler",
        "all-rounder": "All-Rounder",
        "wicket-keeper": "Wicket-Keeper",
    }
    return mapping.get(cleaned, str(val).strip().title())


def _standardize_hand(val: str) -> str:
    cleaned = str(val).strip().lower()
    if cleaned == "right-hand":
        return "Right-hand"
    if cleaned == "left-hand":
        return "Left-hand"
    return str(val).strip().capitalize()


def _parse_mixed_date(val: str) -> str:
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"):
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return pd.to_datetime(s).strftime("%Y-%m-%d")


def _normalize_not_out(val: object, innings_batted: int) -> int:
    if innings_batted == 0 or pd.isna(val):
        return 0
    s = str(val).strip().lower()
    if s in {"1", "yes", "y", "true"}:
        return 1
    return 0


def _overs_to_balls(overs: float) -> int:
    whole = int(overs)
    rem = round((overs - whole) * 10)
    return whole * 6 + rem


def clean_pipeline() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_entries: list[dict[str, object]] = []

    def record(issue: str, rule_applied: str, rows_affected: int) -> None:
        log_entries.append(
            {
                "issue": issue,
                "rule_applied": rule_applied,
                "rows_affected": int(rows_affected),
            }
        )
        print(f"[{issue}] {rule_applied} -> {int(rows_affected)} rows affected")

    # 1. Load all 5 raw CSVs (preserving literal 'None' in bowling_style)
    teams = pd.read_csv(RAW_DIR / "dim_teams.csv", na_values=[""], keep_default_na=False)
    seasons = pd.read_csv(RAW_DIR / "dim_seasons.csv", na_values=[""], keep_default_na=False)
    players = pd.read_csv(RAW_DIR / "dim_players.csv", na_values=[""], keep_default_na=False)
    matches = pd.read_csv(RAW_DIR / "dim_matches.csv", na_values=[""], keep_default_na=False)
    facts = pd.read_csv(
        RAW_DIR / "fact_player_match_stats.csv",
        na_values=["NA", "null", ""],
        keep_default_na=False,
    )

    # 2. Clean dim_players
    before_p = len(players)
    players = players.drop_duplicates(subset=["player_id"], keep="first").copy()
    record(
        "Duplicate player records (dim_players)",
        "Drop exact duplicate rows keeping first occurrence on player_id",
        before_p - len(players),
    )

    name_changed = players["player_name"] != players["player_name"].astype(str).str.strip()
    role_fixed = players["player_role"].astype(str).apply(_standardize_role)
    hand_fixed = players["batting_hand"].astype(str).apply(_standardize_hand)
    text_changed = (
        name_changed
        | (players["player_role"] != role_fixed)
        | (players["batting_hand"] != hand_fixed)
    ).sum()
    players["player_name"] = players["player_name"].astype(str).str.strip()
    players["player_role"] = role_fixed
    players["batting_hand"] = hand_fixed
    record(
        "Whitespace & casing inconsistencies (dim_players)",
        "Trim whitespace and standardize Title/Proper case for player_name, player_role, batting_hand",
        int(text_changed),
    )

    # 3. Clean dim_matches
    iso_mask = matches["match_date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$")
    non_iso_count = int((~iso_mask).sum())
    matches["match_date"] = matches["match_date"].apply(_parse_mixed_date)
    record(
        "Mixed match_date formats (dim_matches)",
        "Parse YYYY-MM-DD, DD/MM/YYYY, and DD-MMM-YYYY uniformly to ISO YYYY-MM-DD",
        non_iso_count,
    )

    venue_clean = matches["venue"].astype(str).str.strip()
    toss_clean = matches["toss_decision"].astype(str).str.strip().str.lower()
    match_text_changed = int(
        ((matches["venue"] != venue_clean) | (matches["toss_decision"] != toss_clean)).sum()
    )
    matches["venue"] = venue_clean
    matches["city"] = matches["city"].astype(str).str.strip()
    matches["toss_decision"] = toss_clean
    matches["win_margin_runs"] = matches["win_margin_runs"].astype("Int64")
    matches["win_margin_wickets"] = matches["win_margin_wickets"].astype("Int64")
    record(
        "Whitespace & casing inconsistencies (dim_matches)",
        "Trim venue/city whitespace and lowercase toss_decision to bat/field",
        match_text_changed,
    )

    # 4. Clean fact_player_match_stats
    before_f = len(facts)
    facts = facts.drop_duplicates(subset=["stat_id"], keep="first").copy()
    record(
        "Duplicate player-match records (fact_player_match_stats)",
        "Drop exact duplicate rows keeping first occurrence on stat_id",
        before_f - len(facts),
    )

    # Normalize not_out
    raw_not_out_non_binary = int(
        (~facts["not_out"].astype(str).isin(["0", "1"])).sum()
    )
    facts["not_out"] = [
        _normalize_not_out(v, int(inn))
        for v, inn in zip(facts["not_out"], facts["innings_batted"])
    ]
    record(
        "Mixed or blank not_out flags (fact_player_match_stats)",
        "Normalize Yes/Y/1->1, No/N/0->0, and blank when innings_batted=0->0",
        raw_not_out_non_binary,
    )

    # Fix negative placeholder values on DNB rows
    neg_mask = (facts["runs_scored"] < 0) | (facts["catches"] < 0)
    neg_count = int(neg_mask.sum())
    facts.loc[facts["runs_scored"] < 0, "runs_scored"] = 0
    facts.loc[facts["catches"] < 0, "catches"] = 0
    record(
        "Negative out-of-range placeholders (fact_player_match_stats)",
        "Clamp negative placeholder runs_scored and catches values on DNB rows to 0",
        neg_count,
    )

    # Derive missing balls_bowled from overs_bowled
    missing_bowled_mask = (facts["overs_bowled"] > 0) & (facts["balls_bowled"].isna())
    missing_bowled_count = int(missing_bowled_mask.sum())
    facts.loc[missing_bowled_mask, "balls_bowled"] = (
        facts.loc[missing_bowled_mask, "overs_bowled"].apply(_overs_to_balls)
    )
    facts["balls_bowled"] = facts["balls_bowled"].fillna(0).astype(int)
    record(
        "Missing balls_bowled where overs_bowled > 0 (fact_player_match_stats)",
        "Derive exact balls_bowled from cricket overs notation via floor(overs)*6 + round((overs%1)*10)",
        missing_bowled_count,
    )

    # Impute missing balls_faced on active batting innings using role median strike rate
    merged_roles = facts.merge(players[["player_id", "player_role"]], on="player_id", how="left")
    valid_bat = merged_roles[
        (merged_roles["innings_batted"] == 1) & (merged_roles["balls_faced"].notna()) & (merged_roles["balls_faced"] > 0)
    ].copy()
    valid_bat["row_sr"] = (valid_bat["runs_scored"] / valid_bat["balls_faced"]) * 100.0
    role_median_sr = valid_bat.groupby("player_role")["row_sr"].median().to_dict()
    overall_median_sr = float(valid_bat["row_sr"].median())

    missing_faced_mask = (facts["innings_batted"] == 1) & (facts["balls_faced"].isna())
    missing_faced_count = int(missing_faced_mask.sum())
    facts["balls_faced_imputed"] = 0
    if missing_faced_count > 0:
        for idx in facts.index[missing_faced_mask]:
            role = merged_roles.loc[idx, "player_role"]
            sr = role_median_sr.get(role, overall_median_sr)
            runs = float(facts.loc[idx, "runs_scored"])
            facts.loc[idx, "balls_faced"] = max(1, int(round(runs / (sr / 100.0))))
            facts.loc[idx, "balls_faced_imputed"] = 1
    facts["balls_faced"] = facts["balls_faced"].fillna(0).astype(int)
    record(
        "Missing balls_faced on active batting innings (fact_player_match_stats)",
        "Impute missing balls_faced from runs_scored using player_role median strike rate and set balls_faced_imputed=1",
        missing_faced_count,
    )

    # Enforce integer types on numeric fact columns
    int_cols = [
        "innings_batted",
        "runs_scored",
        "balls_faced",
        "fours",
        "sixes",
        "not_out",
        "balls_bowled",
        "runs_conceded",
        "wickets_taken",
        "maidens",
        "catches",
        "stumpings",
        "player_of_match",
        "balls_faced_imputed",
    ]
    for c in int_cols:
        facts[c] = facts[c].astype(int)

    # 5. Export cleaned CSVs + clean Excel workbook + data_quality_log.csv
    clean_tables = {
        "dim_teams": teams,
        "dim_seasons": seasons,
        "dim_players": players,
        "dim_matches": matches,
        "fact_player_match_stats": facts,
    }
    for name, df in clean_tables.items():
        df.to_csv(CLEAN_DIR / f"{name}.csv", index=False)

    log_df = pd.DataFrame(log_entries)
    log_df.to_csv(REPORTS_DIR / "data_quality_log.csv", index=False)

    excel_sheets = {**clean_tables, "data_quality_log": log_df}
    write_xlsx_multi_sheet(CLEAN_DIR / "ipl_player_performance_clean.xlsx", excel_sheets)
    print(f"\nCleaned tables written to {CLEAN_DIR}")
    print(f"Quality log written to {REPORTS_DIR / 'data_quality_log.csv'}")


if __name__ == "__main__":
    clean_pipeline()
