-- Insert sample orders
-- Orders reference customers and products by their IDs
-- total_price = quantity * product.price
INSERT INTO orders (customer_id, product_id, quantity, total_price, cost, status, created_at, updated_at) VALUES
  (1, 1, 1, 999.99, 600.00, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (2, 2, 3, 89.97, 45.00, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (3, 3, 2, 159.98, 80.00, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (4, 4, 1, 299.99, 180.00, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (5, 2, 5, 149.95, 75.00, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  (1, 3, 1, 79.99, 40.00, 'cancelled', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
