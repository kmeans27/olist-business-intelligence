#!/usr/bin/env python3
"""Compute the marketing-funnel decision-memo tables (segment conversion,
uplift, Wilson CI, MDE sizing) and write them to reports/decision_memo_data/.
The memo prose is written by hand on top of these numbers."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import sqlite3

import pandas

from olist_bi.funnel import segment_table

OUT = ROOT / "reports" / "decision_memo_data"
OUT.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(ROOT / "data" / "olist.sqlite")
leads = pandas.read_sql("SELECT * FROM mql", con)
deals = pandas.read_sql("SELECT * FROM closed_deals", con)

for key in ("origin",):
    table = segment_table(leads, deals, key)
    table.to_csv(OUT / f"segments_{key}.csv", index=False)
    print(f"== {key}")
    print(table.to_string(index=False))
# descriptive: which business segments do the WON deals concentrate in?
seg_deals = deals.groupby("business_segment").size().sort_values(ascending=False)
seg_deals.to_csv(OUT / "won_deal_segments.csv")
print("== won-deal business segments")
print(seg_deals.to_string())
print(f"\ntotal leads: {len(leads)}, closed deals matched: {int((leads['mql_id'].isin(set(deals['mql_id']))).sum())}")
