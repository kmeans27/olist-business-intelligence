-- Q4. Month-over-month revenue growth with LAG (window function).
-- Ops question: is the marketplace growing, and in which months did revenue
-- fall? Feeds the dashboard trend panel and the decision memo's context.
-- Revenue is counted only for orders with an actual delivery date (see README).
WITH monthly AS (
  SELECT substr(o.order_purchase_timestamp, 1, 7) AS month,
         SUM(p.price + p.freight_value) AS revenue
  FROM order_items AS p JOIN orders AS o ON o.order_id = p.order_id
  WHERE o.order_delivered_customer_date != ''
  GROUP BY substr(o.order_purchase_timestamp, 1, 7)
)
SELECT month, ROUND(revenue, 2) AS revenue_brl,
       ROUND(lag(revenue) OVER (PARTITION BY 1 ORDER BY month), 2) AS prev_revenue,
       ROUND(100.0 * (revenue - lag(revenue) OVER (PARTITION BY 1 ORDER BY month))
             / lag(revenue) OVER (PARTITION BY 1 ORDER BY month), 2) AS mom_growth_pct,
       CASE WHEN revenue < lag(revenue) OVER (PARTITION BY 1 ORDER BY month) THEN 1 ELSE 0 END AS revenue_declined
FROM monthly
ORDER BY month
