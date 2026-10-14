-- Q5. Customer cohort matrix: first-purchase month x state, repeat-customer rate.
-- ROW_NUMBER() OVER (PARTITION BY customer) = 1 identifies each customer's first
-- order (no MIN-date string hacks). Ops question: which states have enough
-- repeat customers to justify a local loyalty program?
WITH customer_orders AS (
  SELECT o.order_id, o.customer_id, o.order_purchase_timestamp AS ts
  FROM orders AS o WHERE o.order_delivered_customer_date != ''
),
-- customer_id is an ALIAS per order; customer_unique_id is the real person.
person_of AS (
  SELECT c.customer_id, c.customer_unique_id, c.customer_state
  FROM customers AS c GROUP BY customer_id
),
person_orders AS (
  SELECT co.ts, pu.customer_unique_id AS person, pu.customer_state AS state
  FROM customer_orders AS co JOIN person_of AS pu ON pu.customer_id = co.customer_id
),
first_order AS (
  SELECT person, ts, state,
         ROW_NUMBER() OVER (PARTITION BY person ORDER BY ts) AS seq,
         COUNT() OVER (PARTITION BY person) AS n_orders
  FROM person_orders
)
SELECT substr(f.ts, 1, 7) AS first_month, f.state AS state,
       COUNT() AS new_customers,
       SUM(CASE WHEN f.n_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * AVG(CASE WHEN f.n_orders > 1 THEN 1 ELSE 0 END), 2) AS repeat_rate_pct
FROM first_order AS f
WHERE f.seq = 1
GROUP BY substr(f.ts, 1, 7), f.state
ORDER BY first_month, state
