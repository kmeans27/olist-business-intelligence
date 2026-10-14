#!/usr/bin/env python3
"""Fetch raw Olist CSVs and apply the documented cleaning rules.

Cleaning decisions (all justified in the README):
- orders: keep ALL rows (cancelled orders are kept as a status column, not dropped,
  so status-based analysis is possible); drop rows with NULL order_status.
- dates: normalised to ISO-8601 strings so SQLite string comparison works.
- geolocation table is intentionally NOT downloaded (unused by any query; 1M rows).
"""

import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"

SOURCES = {
    # filename -> url. Mirrors of the official Kaggle "Brazilian E-Commerce Public Dataset
    # by Olist" (https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and
    # "Marketing Funnel by Olist" (https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist).
    "olist_orders_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_orders_dataset.csv",
    "olist_customers_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_customers_dataset.csv",
    "olist_order_items_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_order_payments_dataset.csv",
    "olist_products_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_products_dataset.csv",
    "olist_sellers_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_sellers_dataset.csv",
    "product_category_name_translation.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/product_category_name_translation.csv",
    "olist_order_reviews_dataset.csv": "https://raw.githubusercontent.com/Kaushal00Vaid/OLIST-Brazilian-Ecommerce-Analysis/main/data/olist_order_reviews_dataset.csv",
    "olist_marketing_qualified_leads_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_marketing_qualified_leads_dataset.csv",
    "olist_closed_deals_dataset.csv": "https://raw.githubusercontent.com/MarthaMueni/Marketing-Funnel-Olist/main/olist_closed_deals_dataset.csv",
}


def fetch(force: bool = False) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        dest = RAW / name
        if dest.exists() and not force:
            print(f"skip {name} (already present)")
            continue
        print(f"fetching {name} <- {url}")
        with urllib.request.urlopen(url, timeout=120) as resp:
            dest.write_bytes(resp.read())


def clean() -> None:
    """Apply cleaning rules; write cleaned copies to data/raw_clean/."""
    clean_dir = RAW.parent / "raw_clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    for name in SOURCES:
        src = RAW / name
        df = pd.read_csv(src, dtype=str, keep_default_na=False)
        if name == "olist_orders_dataset.csv":
            before = len(df)
            df = df[df["order_status"] != ""]
            print(f"{name}: dropped {before - len(df)} rows with empty order_status")
        # normalise the two Olist date formats to sortable ISO strings
        for col in df.columns:
            if col.endswith(("_date", "_at")):
                parsed = pd.to_datetime(df[col], format="mixed", errors="coerce")
                bad = parsed.isna() & (df[col] != "")
                if bad.any():
                    raise ValueError(
                        f"unparseable date in {name}/{col}: {df.loc[bad, col].iloc[0]}"
                    )
                df[col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S").where(parsed.notna(), "")
        df.to_csv(clean_dir / name, index=False)
        print(f"wrote cleaned {name} ({len(df)} rows)")
