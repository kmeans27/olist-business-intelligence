-- Q1. Revenue by product category (English names), Sep 2016 – Sep 2018.
-- Four-table join (items -> products -> translation) plus a CTE to isolate
-- delivered, completed orders first. Business question: what is the marketplace
-- actually selling, and how concentrated is it?
WITH completed_items AS (
  SELECT i.order_id, i.product_id, i.price, i.freight_value
  FROM order_items AS i
  JOIN orders AS o ON o.order_id = i.order_id
  WHERE o.order_delivered_customer_date != ''
)
SELECT
  t.product_category_name_english AS category,
  COUNT(*) AS items_sold,
  ROUND(SUM(price + freight_value), 2) AS gross_revenue_brl,
  ROUND(100.0 * SUM(price + freight_value)
        / (SELECT SUM(price + freight_value) FROM completed_items), 2) AS revenue_pct
FROM completed_items AS ci
JOIN products AS p ON p.product_id = ci.product_id
LEFT JOIN category_translation AS t ON t.product_category_name = p.product_category_name
GROUP BY t.product_category_name_english
ORDER BY gross_revenue_brl DESC
