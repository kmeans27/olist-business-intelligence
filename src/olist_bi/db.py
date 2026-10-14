#!/usr/bin/env python3
"""Build the SQLite analysis database from the cleaned CSVs.

Type decisions:
- money columns -> REAL, counts -> INTEGER, dates -> ISO TEXT (sortable), ids -> TEXT.
- delivery_date stays TEXT; queries compute day differences with julianday().
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data" / "raw_clean"
DB = ROOT / "data" / "olist.sqlite"

TABLES = {  # sqlite table -> (csv file, {column: sqlite type})
    "orders": ("olist_orders_dataset.csv", {
        "order_id": "TEXT", "customer_id": "TEXT", "order_status": "TEXT",
        "order_purchase_timestamp": "TEXT", "order_approved_at": "TEXT",
        "order_delivered_customer_date": "TEXT", "order_estimated_delivery_date": "TEXT",
    }),
    "customers": ("olist_customers_dataset.csv", {
        "customer_id": "TEXT", "customer_unique_id": "TEXT",
        "customer_zip_code_prefix": "INTEGER", "customer_city": "TEXT", "customer_state": "TEXT",
    }),
    "order_items": ("olist_order_items_dataset.csv", {
        "order_id": "TEXT", "order_item_id": "INTEGER", "product_id": "TEXT",
        "seller_id": "TEXT", "shipping_limit_date": "TEXT",
        "price": "REAL", "freight_value": "REAL",
    }),
    "payments": ("olist_order_payments_dataset.csv", {
        "order_id": "TEXT", "payment_sequential": "INTEGER", "payment_type": "TEXT",
        "payment_installments": "INTEGER", "payment_value": "REAL",
    }),
    "reviews": ("olist_order_reviews_dataset.csv", {
        "order_id": "TEXT", "review_score": "INTEGER",
    }),
    "products": ("olist_products_dataset.csv", {
        "product_id": "TEXT", "product_category_name": "TEXT",
        "product_length_cm": "INTEGER", "product_weight_g": "INTEGER",
    }),
    "sellers": ("olist_sellers_dataset.csv", {
        "seller_id": "TEXT", "seller_state": "TEXT",
    }),
    "category_translation": ("product_category_name_translation.csv", {
        "product_category_name": "TEXT", "product_category_name_english": "TEXT",
    }),
    "mql": ("olist_marketing_qualified_leads_dataset.csv", {
        "mql_id": "TEXT", "first_contact_date": "TEXT",
        "landing_page_id": "TEXT", "origin": "TEXT",
    }),
    "closed_deals": ("olist_closed_deals_dataset.csv", {
        "mql_id": "TEXT", "seller_id": "TEXT", "sdr_id": "TEXT", "sr_id": "TEXT",
        "won_date": "TEXT", "business_segment": "TEXT", "lead_type": "TEXT",
        "lead_behaviour_profile": "TEXT", "has_company": "INTEGER", "has_gtin": "INTEGER",
        "average_stock": "REAL", "business_type": "TEXT",
        "declared_product_catalog_size": "REAL", "declared_monthly_revenue": "REAL",
    }),
}


def build() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    for table, (csv, cols) in TABLES.items():
        df = pd.read_csv(CLEAN / csv, dtype=str, keep_default_na=False)
        missing = set(cols) - set(df.columns)
        if missing:
            raise SystemExit(f"{csv} is missing columns {missing}; check the mirror")
        df = df[[c for c in cols]]
        for col, typ in cols.items():
            if typ == "INTEGER":
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
            elif typ == "REAL":
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        df.to_sql(table, con, if_exists="replace", index=False)
        print(f"{table}: {len(df)} rows")
    con.close()


if __name__ == "__main__":
    build()
