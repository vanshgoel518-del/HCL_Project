"""P8 Database Loader & SQL Query Exporter (SQLite).

Creates data/ipl_stats.db from sql/schema_sqlite.sql, loads cleaned CSVs from
data/clean/, executes all 7 queries in sql/queries_sqlite.sql, and exports each
query result to reports/sql_outputs/<query_name>.csv.
"""

from __future__ import annotations

from pathlib import Path
import re
import sqlite3

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT_DIR / "data" / "clean"
SQL_DIR = ROOT_DIR / "sql"
DB_PATH = ROOT_DIR / "data" / "ipl_stats.db"
OUT_DIR = ROOT_DIR / "reports" / "sql_outputs"

LOAD_ORDER = [
    "dim_teams",
    "dim_seasons",
    "dim_players",
    "dim_matches",
    "fact_player_match_stats",
]


def parse_named_queries(sql_text: str) -> list[tuple[str, str]]:
    """Split queries_sqlite.sql by '-- QUERY_NAME: <name>' headers."""
    pattern = re.compile(r"^--\s*QUERY_NAME:\s*(\S+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(sql_text))
    queries: list[tuple[str, str]] = []
    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(sql_text)
        stmt = sql_text[start:end].strip().rstrip(";")
        queries.append((name, stmt))
    return queries


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    schema_sql = (SQL_DIR / "schema_sqlite.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(schema_sql)
        conn.execute("PRAGMA foreign_keys = ON;")

        for table in LOAD_ORDER:
            df = pd.read_csv(CLEAN_DIR / f"{table}.csv", na_values=[""], keep_default_na=False)
            # Preserve NULLs properly for nullable margin columns
            df = df.where(pd.notnull(df), None)
            df.to_sql(table, conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into {table}")

        queries_sql = (SQL_DIR / "queries_sqlite.sql").read_text(encoding="utf-8")
        named_queries = parse_named_queries(queries_sql)
        for q_name, q_sql in named_queries:
            res_df = pd.read_sql_query(q_sql, conn)
            out_csv = OUT_DIR / f"{q_name}.csv"
            res_df.to_csv(out_csv, index=False)
            print(f"Executed {q_name} -> {len(res_df)} rows saved to {out_csv.name}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
