-- Q3. Delivery-risk by destination state: p90 of actual delivery days.
-- The regional ops manager's question: which states are at risk of missing
-- promises, i.e. p90 delivery time > 5 days? Percentile computed with window
-- functions (ROW_NUMBER + COUNT OVER PARTITION), no external percentile lib.
WITH delivered AS (
  SELECT o.customer_id,
         CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS INT) AS delivery_days
  FROM orders AS o
  WHERE o.order_delivered_customer_date != ''
),
state_of AS (
  SELECT c.customer_id, c.customer_state FROM customers AS c GROUP BY customer_id
),
per_state AS (
  SELECT s.customer_state AS state, d.delivery_days AS days
  FROM state_of AS s JOIN delivered AS d ON d.customer_id = s.customer_id
),
ranked AS (
  SELECT ROW_NUMBER() OVER (PARTITION BY state ORDER BY days) AS pos,
         COUNT() OVER (PARTITION BY state) AS n,
         ROUND(AVG(days) OVER (PARTITION BY state), 2) AS avg_delivery_days,
         state, days
    FROM per_state
)
SELECT state, n,
       days AS p90_delivery_days,
       avg_delivery_days,
       CASE WHEN days > 5 THEN 'AT RISK' ELSE 'ok' END AS risk_flag
FROM ranked
WHERE pos = CAST(CEIL(0.9 * n) AS INT)
ORDER BY p90_delivery_days DESC, state
