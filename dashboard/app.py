#!/usr/bin/env streamlit
"""Persona dashboard: REGIONAL OPERATIONS MANAGER of the marketplace.

Design choices (documented in the README):
- Persona-first: the operator picks THEIR destination state; every panel is
  filtered to what that person would act on.
- Wireframe (top to bottom): KPI strip -> monthly revenue trend -> delivery-risk
  league across states (context) -> category mix. Decision-relevant first.
- One color, one meaning: accent for "our data"; risk is communicated by
  ordering + the AT RISK column, not by a rainbow of hues.
"""

import sqlite3
from datetime import date
from pathlib import Path

import altair as alt
import streamlit as st
from pandas import read_sql

DB = str(Path(__file__).resolve().parents[1] / "data" / "olist.sqlite")
ACCENT = "#c2410c"

st.set_page_config(page_title="Olist regional ops dashboard", layout="wide")
st.title("Olist — regional operations dashboard")
st.caption(f"Persona: regional operations manager · Olist public data, Sep 2016 – Sep 2018 · opened {date.today()}")

con = sqlite3.connect(DB)
states = [r[0] for r in con.execute("SELECT DISTINCT customer_state FROM customers ORDER BY customer_state")]
months = [r[0] for r in con.execute(
    "SELECT DISTINCT substr(order_purchase_timestamp,1,7) FROM orders WHERE order_delivered_customer_date != '' ORDER BY 1")]

with st.sidebar:
    st.header("Filters")
    state = st.selectbox("Destination state", states, index=(states.index("DF") if "DF" in states else 0))
    start = st.selectbox("From month", months, index=0)
    end = st.selectbox("To month", months[-1])
month_in = ",".join(f"'{m}'" for m in months if start <= m <= end)

# one WHERE fragment reused by every panel: delivered orders to the persona's state
BASE_JOIN = """
    JOIN orders AS o ON o.order_id = p.order_id
    JOIN customers AS c ON c.customer_id = o.customer_id
"""
BASE_WHERE = f"""
    WHERE c.customer_state = '{state}'
      AND o.order_delivered_customer_date != ''
      AND substr(o.order_purchase_timestamp,1,7) IN ({month_in})
"""

# --- KPI strip ---
kpi = read_sql(
    f"""SELECT COUNT() AS orders, ROUND(SUM(p.price + p.freight_value), 2) AS revenue
        FROM order_items AS p {BASE_JOIN}{BASE_WHERE}""",
    con,
)
# exact p90 for the persona's state, computed like q3 (window percentile):
p90_exact = read_sql(
    f"""SELECT days AS p90
        FROM (SELECT ROW_NUMBER() OVER (PARTITION BY 1 ORDER BY d) AS pos,
                      COUNT() OVER (PARTITION BY 1) AS n, d AS days
                FROM (SELECT CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS INT) AS d
                      FROM orders AS o WHERE o.order_delivered_customer_date != ''
                        AND EXISTS (SELECT 1 FROM customers AS c
                                    WHERE c.customer_id = o.customer_id AND c.customer_state = '{state}'
                                    AND substr(o.order_purchase_timestamp,1,7) IN ({month_in}))))
        WHERE pos = CAST(CEIL(0.9 * n) AS INT)""",
    con,
)
k = kpi.iloc[0]
st.subheader("Your market this window")
c1, c2, c3 = st.columns(3)
c1.metric("Delivered orders", f"{int(k.orders):,}")
c2.metric("Revenue (BRL)", f"$ {int(k.revenue):,}")
c3.metric("p90 delivery (days)", f"{int(p90_exact.iloc[0].p90)}" if len(p90_exact) else "n/a")

# --- monthly revenue trend (persona's state, all months then filtered) ---
trend = read_sql(
    f"""SELECT substr(o.order_purchase_timestamp,1,7) AS month,
           SUM(p.price + p.freight_value) AS revenue
        FROM order_items AS p {BASE_JOIN}{BASE_WHERE}
        GROUP BY substr(o.order_purchase_timestamp,1,7) ORDER BY 1""",
    con,
)
st.subheader("Revenue by month")
st.altair_chart(
    alt.Chart(trend)
    .mark_area(color=ACCENT + "33", line={"color": ACCENT, "width": 2})
    .encode(x="month:T", y="revenue:Q"),
    width="stretch",
)

# --- delivery-risk league across ALL states (context for the persona) ---
st.subheader("Delivery risk league (all states, full period)")
risk = read_sql(
    """SELECT c.customer_state AS state,
           COUNT() AS delivered_orders,
           ROUND(AVG(CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS REAL)), 1) AS avg_days
        FROM orders AS o JOIN customers AS c ON c.customer_id = o.customer_id
        WHERE o.order_delivered_customer_date != ''
        GROUP BY c.customer_state ORDER BY AVG(CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS REAL)) DESC""",
    con,
)
risk["verdict"] = risk["avg_days"].map(lambda d: "AT RISK" if d > 15 else "")
st.dataframe(risk, height=340)

# --- category mix for the persona's state ---
cats = read_sql(
    f"""SELECT t.product_category_name_english AS category,
           SUM(p.price + p.freight_value) AS revenue
        FROM order_items AS p {BASE_JOIN}
        LEFT JOIN products AS pr ON pr.product_id = p.product_id
        LEFT JOIN category_translation AS t ON t.product_category_name = pr.product_category_name
        {BASE_WHERE}
        GROUP BY t.product_category_name_english ORDER BY SUM(p.price + p.freight_value) DESC LIMIT 10""",
    con,
)
st.subheader("Top categories by revenue")
st.altair_chart(
    alt.Chart(cats).mark_bar(color=ACCENT).encode(x="revenue:Q", y="category:N")
    + alt.Chart(cats).mark_text(align="left", baseline="middle", dx=4)
    .encode(text="revenue:N", x="revenue:Q", y="category:N"),
    width="stretch",
)
