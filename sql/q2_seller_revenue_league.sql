-- Q2. Seller league table with window functions.
-- ROW_NUMBER ranks sellers by revenue; a running SUM gives each seller's
-- cumulative revenue share. The business question: what is the SMALLEST set of
-- sellers that covers 80% of marketplace revenue? (build-vs-rebuild decision for
-- seller support/quality programs.)
WITH delivered_items AS (
  SELECT i.order_id, i.seller_id, i.price, i.freight_value
  FROM order_items AS i
  JOIN orders AS o ON o.order_id = i.order_id
  WHERE o.order_delivered_customer_date != ''
),
seller_revenue AS (
  SELECT seller_id, SUM(price + freight_value) AS revenue
  FROM delivered_items
  GROUP BY seller_id
),
league AS (
  SELECT ROW_NUMBER() OVER (PARTITION BY 1 ORDER BY revenue DESC) AS rank,
         seller_id,
         ROUND(revenue, 2) AS revenue,
         ROUND(100.0 * revenue / (SELECT SUM(revenue) FROM seller_revenue), 4) AS revenue_pct
    FROM seller_revenue
),
cumulative AS (
  SELECT rank, seller_id, revenue, revenue_pct,
         ROUND(SUM(revenue_pct) OVER (PARTITION BY 1 ORDER BY rank), 4) AS cumulative_pct
    FROM league
)
SELECT
  rank, seller_id, revenue, revenue_pct, cumulative_pct,
  CASE WHEN cumulative_pct - revenue_pct < 80.0 THEN 1 ELSE 0 END AS in_80pct_set
FROM cumulative
ORDER BY rank
