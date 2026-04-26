-- Insert sample customers
INSERT INTO customers (name, email, phone, status, created_at, updated_at) VALUES
  ('John Doe', 'john@example.com', '555-1234', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Jane Smith', 'jane@example.com', '555-5678', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Bob Johnson', 'bob@example.com', '555-9012', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Alice Williams', 'alice@example.com', '555-3456', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('Charlie Brown', 'charlie@example.com', '555-7890', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
