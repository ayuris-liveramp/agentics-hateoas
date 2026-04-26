-- Insert sample products
INSERT INTO products (name, description, price, cost, stock_quantity, status, created_at, updated_at) VALUES
  ('Laptop', 'High-performance laptop for professionals', 999.99, 600.00, 50, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Mouse', 'Wireless ergonomic mouse', 29.99, 15.00, 200, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Keyboard', 'Mechanical keyboard with RGB lighting', 79.99, 40.00, 150, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Monitor', '4K display monitor', 299.99, 180.00, 75, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
