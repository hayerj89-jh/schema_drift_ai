CREATE OR REPLACE TABLE `bigquery-sandbox-296903.dev.cars` (
    brand STRING,
    inventory INT64,
    total_revenue FLOAT64
);

INSERT INTO `bigquery-sandbox-296903.dev.cars` (brand, inventory, total_revenue)
VALUES 
    ('Toyota', 15, 450000.75),
    ('Ford', 8, 320500.00),
    ('Honda', 12, 385000.50),
    ('Tesla', 4, 240000.00),
    ('Chevrolet', 10, 310250.25);