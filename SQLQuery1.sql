USE retail_pricing;
GO

CREATE TABLE sales_raw (
    product_id NVARCHAR(50),
    store_id NVARCHAR(50),
    date NVARCHAR(50),
    sales NVARCHAR(50),
    revenue NVARCHAR(50),
    stock NVARCHAR(50),
    price NVARCHAR(50),
    promo_type_1 NVARCHAR(50),
    promo_bin_1 NVARCHAR(50),
    promo_type_2 NVARCHAR(50),
    promo_bin_2 NVARCHAR(50),
    promo_discount_2 NVARCHAR(50),
    promo_discount_type_2 NVARCHAR(50)
);

USE retail_pricing;
GO

BULK INSERT sales_raw
FROM 'C:\ds journey\price optimization\sales.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '0x0a',
    CODEPAGE = '65001',
    TABLOCK
);
SELECT COUNT(*) AS total_rows
FROM sales_raw;
SELECT TOP 10 *
FROM sales_raw;
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT product_id) AS products,
    COUNT(DISTINCT store_id) AS stores,
    MIN(date) AS first_date,
    MAX(date) AS last_date
FROM sales_raw;

SELECT
    SUM(row_count) AS total_rows
FROM sys.dm_db_partition_stats
WHERE object_id = OBJECT_ID('dbo.sales_raw')
  AND index_id IN (0,1);
  
  SELECT TOP 10 *
FROM sales_raw;

SELECT
    store_id,
    SUM(TRY_CONVERT(float, sales)) AS total_sales
FROM sales_raw
GROUP BY store_id
ORDER BY total_sales DESC;

SELECT top 10 product_id,Sum(TRY_CONVERT(float, sales)) as total_sales
from sales_raw
group by product_id
order by total_sales Desc;

SELECT TOP 20
    product_id,
    store_id,
    date,
    TRY_CONVERT(float, price) AS price,
    TRY_CONVERT(float, sales) AS sales
FROM sales_raw
WHERE price <> ''
ORDER BY product_id, store_id, date;

SELECT
    TRY_CONVERT(float, price) AS price,
    COUNT(*) AS days,
    SUM(TRY_CONVERT(float, sales)) AS total_sales,
    AVG(TRY_CONVERT(float, stock)) AS avg_stock
FROM sales_raw
WHERE product_id = 'P0001'
  AND store_id = 'S0001'
  AND price <> ''
GROUP BY TRY_CONVERT(float, price)
ORDER BY price;

SELECT
    CASE
        WHEN NULLIF(LTRIM(RTRIM(promo_type_1)), '') IS NULL
         AND NULLIF(LTRIM(RTRIM(promo_type_2)), '') IS NULL
        THEN 'No Promotion'
        ELSE 'Promotion'
    END AS promotion_status,
    COUNT(*) AS days,
    AVG(TRY_CONVERT(float, sales)) AS avg_daily_sales
FROM sales_raw
GROUP BY
    CASE
        WHEN NULLIF(LTRIM(RTRIM(promo_type_1)), '') IS NULL
         AND NULLIF(LTRIM(RTRIM(promo_type_2)), '') IS NULL
        THEN 'No Promotion'
        ELSE 'Promotion'
    END;

    SELECT TOP 20
    promo_type_1,
    COUNT(*) AS rows_count
FROM sales_raw
GROUP BY promo_type_1
ORDER BY rows_count DESC;

SELECT
    promotion_status,
    COUNT(*) AS days,
    AVG(TRY_CONVERT(float, sales)) AS avg_daily_sales
FROM (
    SELECT
        CASE
            WHEN ISNULL(NULLIF(LTRIM(RTRIM(promo_type_1)), ''), '') = ''
             AND ISNULL(NULLIF(LTRIM(RTRIM(promo_type_2)), ''), '') = ''
            THEN 'No Promotion'
            ELSE 'Promotion'
        END AS promotion_status,
        sales
    FROM sales_raw
) AS x
GROUP BY promotion_status;


SELECT TOP 20
    promo_type_1,
    promo_type_2
FROM sales_raw
WHERE promo_type_1 IS NOT NULL
   OR promo_type_2 IS NOT NULL;

   SELECT
    ISNULL(NULLIF(LTRIM(RTRIM(promo_type_1)), ''), '[EMPTY]') AS promo_type_1,
    COUNT(*) AS rows_count
FROM sales_raw
GROUP BY ISNULL(NULLIF(LTRIM(RTRIM(promo_type_1)), ''), '[EMPTY]')
ORDER BY rows_count DESC;



SELECT
    promo_bin_1,
    COUNT(*) AS rows_count
FROM sales_raw
GROUP BY promo_bin_1
ORDER BY rows_count DESC;



SELECT
    ISNULL(promo_bin_1, 'No Promotion') AS promotion_level,
    COUNT(*) AS rows_count,
    AVG(TRY_CONVERT(float, sales)) AS avg_daily_sales
FROM sales_raw
GROUP BY ISNULL(promo_bin_1, 'No Promotion')
ORDER BY avg_daily_sales DESC;
USE retail_pricing;
GO

SELECT COUNT(*) AS total_rows
FROM sales_raw;

SELECT
    product_id,
    COUNT(DISTINCT TRY_CONVERT(float, price)) AS different_prices
FROM sales_raw
WHERE NULLIF(LTRIM(RTRIM(price)), '') IS NOT NULL
GROUP BY product_id
ORDER BY different_prices DESC;

SELECT
    product_id,
    COUNT(DISTINCT TRY_CONVERT(float, price)) AS different_prices
FROM sales_raw
WHERE NULLIF(LTRIM(RTRIM(price)), '') IS NOT NULL
GROUP BY product_id
HAVING COUNT(DISTINCT TRY_CONVERT(float, price)) >= 10
ORDER BY different_prices DESC;



SELECT
    product_id,
    store_id,
    TRY_CONVERT(float, price) AS price,
    COUNT(*) AS days,
    AVG(TRY_CONVERT(float, sales)) AS avg_daily_sales
FROM sales_raw
WHERE NULLIF(LTRIM(RTRIM(price)), '') IS NOT NULL
GROUP BY
    product_id,
    store_id,
    TRY_CONVERT(float, price)
HAVING COUNT(*) >= 10
ORDER BY
    product_id,
    store_id,
    price ASC;


    SELECT
    product_id,
    store_id,
    TRY_CONVERT(float, price) AS price,
    COUNT(*) AS days,
    AVG(TRY_CONVERT(float, sales)) AS avg_daily_sales
FROM sales_raw
WHERE NULLIF(LTRIM(RTRIM(price)), '') IS NOT NULL
  AND promo_bin_1 IS NULL
  AND TRY_CONVERT(float, stock) > 0
GROUP BY
    product_id,
    store_id,
    TRY_CONVERT(float, price)
HAVING COUNT(*) >= 10
ORDER BY
    product_id,
    store_id,
    price ASC;



 WITH clean_data AS (
    SELECT
        product_id,
        store_id,
        TRY_CONVERT(float, price) AS price,
        TRY_CONVERT(float, sales) AS sales
    FROM sales_raw
    WHERE TRY_CONVERT(float, price) IS NOT NULL
      AND TRY_CONVERT(float, sales) IS NOT NULL
      AND TRY_CONVERT(float, stock) > 0
      AND promo_bin_1 IS NULL
),

group_avg AS (
    SELECT
        product_id,
        store_id,
        COUNT(*) AS n,
        AVG(price) AS avg_price,
        AVG(sales) AS avg_sales
    FROM clean_data
    GROUP BY product_id, store_id
    HAVING COUNT(*) >= 30
),

centered AS (
    SELECT
        d.product_id,
        d.store_id,
        g.n,
        (d.price - g.avg_price) AS price_dev,
        (d.sales - g.avg_sales) AS sales_dev
    FROM clean_data d
    JOIN group_avg g
        ON d.product_id = g.product_id
       AND d.store_id = g.store_id
),

corr_stats AS (
    SELECT
        product_id,
        store_id,
        n,
        SUM(price_dev * sales_dev) AS covariance_part,
        SUM(price_dev * price_dev) AS price_var_part,
        SUM(sales_dev * sales_dev) AS sales_var_part
    FROM centered
    GROUP BY product_id, store_id, n
)

SELECT
    product_id,
    store_id,
    n,
    covariance_part /
    NULLIF(
        SQRT(price_var_part * sales_var_part),
        0
    ) AS price_sales_corr
FROM corr_stats
ORDER BY price_sales_corr;