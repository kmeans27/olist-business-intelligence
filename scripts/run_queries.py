#!/usr/bin/env python3
"""Run every sql/*.sql query against the SQLite db; save results to
reports/sql_results/<query>.csv and print a short preview."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "reports" / "sql_results"
DB = ROOT / "data" / "olist.sqlite"

import sqlite3

from pandas import DataFrame

OUT_DIR.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(DB)
for q in sorted(SQL_DIR.glob("*.sql")):
    sql = q.read_text()
    cur = con.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    df = DataFrame(rows, columns=cols)
    out = OUT_DIR / (q.stem + ".csv")
    df.to_csv(out, index=False)
    print(f"== {q.stem}: {len(df)} rows -> {out}")
    print(df.head(10).to_string(index=False))
