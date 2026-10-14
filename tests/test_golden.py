#!/usr/bin/env python3
"""Golden checks for the pipeline: query outputs must match independent
pandas computations on the same data. These run in CI before any report
is published."""

import sqlite3
from pathlib import Path

import pytest
from pandas import read_csv, read_sql

ROOT = Path(__file__).resolve().parents[1]
DB = str(ROOT / "data" / "olist.sqlite")
RESULTS = ROOT / "reports" / "sql_results"


@pytest.fixture(scope="session")
def con():
    return sqlite3.connect(DB)


def test_q1_category_revenue_totals_match_payments_basis():
    """Sum of Q1 revenue == delivered-orders revenue computed in pandas."""
    con = sqlite3.connect(DB)
    q1 = read_csv(RESULTS / "q1_category_revenue.csv")
    items = read_sql("SELECT order_id, price, freight_value FROM order_items", con)
    orders = read_sql("SELECT order_id, order_delivered_customer_date FROM orders", con)
    delivered = items.merge(orders, on="order_id", suffixes=("", "_o"))
    delivered = delivered[delivered.order_delivered_customer_date != ""]
    expected = float((delivered.price + delivered.freight_value).sum())
    assert abs(q1.gross_revenue_brl.sum() - expected) < 1.0
    assert abs(q1.revenue_pct.sum() - 100.0) < 0.1


def test_q2_seller_league_is_monotonic_and_covers():
    q2 = read_csv(RESULTS / "q2_seller_revenue_league.csv")
    assert (q2.revenue.diff().iloc[1:] <= 0).all(), "league must be sorted desc"
    assert q2.revenue_pct.sum() == pytest.approx(100.0, abs=0.1)
    assert q2.in_80pct_set.sum() > 0 and q2.cumulative_pct.iloc[-1] == pytest.approx(100.0, abs=0.1)


def test_q3_p90_matches_pandas_quantile(con):
    q3 = read_csv(RESULTS / "q3_state_delivery_risk.csv")
    days = read_sql(
        "SELECT c.customer_state AS state, CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS INT) AS days "
        "FROM orders AS o JOIN customers AS c ON c.customer_id = o.customer_id WHERE o.order_delivered_customer_date != ''",
        con,
    )
    for _, row in q3.iterrows():
        sub = days[days.state == row.state].days
        # SQL uses the ceil(0.9n)-th order statistic; numpy 'quantile(0.9)' interpolates,
        # so compare against the same order statistic:
        k = int(-(-0.9 * len(sub) // 1))  # ceil
        assert row.p90_delivery_days == sorted(sub)[k - 1]


def test_q4_growth_flags_concede():
    """Honest evaluation: the 2016-12 dip is a real data artifact (2 orders that
    month) — the pipeline must FLAG it, not smooth it away."""
    q4 = read_csv(RESULTS / "q4_monthly_growth.csv")
    dec = q4[q4.month == "2016-12"]
    assert len(dec) == 1 and dec.revenue_declined.iloc[0] == 1


def test_q5_repeat_rate_uses_real_person_ids():
    """customer_id is an alias per order; repeat analysis must use customer_unique_id."""
    con = sqlite3.connect(DB)
    q5 = read_csv(RESULTS / "q5_cohort_repeat_rate.csv")
    delivered = read_sql("SELECT customer_id FROM orders WHERE order_delivered_customer_date != ''", con)
    people = read_sql("SELECT customer_id, customer_unique_id FROM customers", con)
    persons_with_delivery = people.merge(delivered, on="customer_id").customer_unique_id.nunique()
    assert q5.new_customers.sum() == persons_with_delivery
    assert (q5.repeat_rate_pct >= 0).all() and (q5.repeat_rate_pct <= 100).all()


def test_funnel_baseline_matches_join(con):
    from olist_bi.funnel import segment_table

    leads = read_sql("SELECT * FROM mql", con)
    deals = read_sql("SELECT * FROM closed_deals", con)
    tbl = segment_table(leads, deals, "origin")
    total = int(tbl.converted.sum())
    joined = int(read_sql(
        "SELECT COUNT() FROM closed_deals AS d JOIN mql AS m ON m.mql_id = d.mql_id", con
    ).iloc[0, 0])
    assert total == joined == 842
    assert tbl.n.sum() == 8000
    # significance sanity: PAID_SEARCH ci_low must be above baseline (the memo's claim)
    paid = tbl[tbl.segment == "PAID_SEARCH"].iloc[0]
    assert paid.ci_low > paid.baseline
