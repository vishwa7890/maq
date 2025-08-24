-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'normal' CHECK (role IN ('normal', 'premium')),
    quotes_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    quote_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    quote_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'approved', 'rejected')),
    client_name VARCHAR(255),
    total_amount DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed')),
    transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash, phone, role, quotes_used) VALUES
('john_doe', 'john@gmail.com', '$2b$10$example_hash', '+1234567890', 'normal', 2),
('jane_premium', 'jane@yahoo.com', '$2b$10$example_hash', '+1234567891', 'premium', 15)
ON CONFLICT (username) DO NOTHING;

-- Insert sample chat sessions
INSERT INTO chat_sessions (user_id, session_name, file_name) VALUES
(1, 'Welcome Chat', NULL),
(1, 'Project Alpha Quote', 'project_alpha.pdf'),
(2, 'Enterprise Solution', 'enterprise_requirements.pdf')
ON CONFLICT DO NOTHING;

-- Insert sample quotes
INSERT INTO quotes (user_id, session_id, quote_data, status, client_name, total_amount) VALUES
(1, 2, '{"items": [{"description": "Web Development", "quantity": 1, "rate": 50000, "amount": 50000}], "subtotal": 50000, "tax": 9000, "total": 59000}', 'approved', 'Tech Corp', 59000.00),
(2, 3, '{"items": [{"description": "Enterprise Solution", "quantity": 1, "rate": 200000, "amount": 200000}], "subtotal": 200000, "tax": 36000, "total": 236000}', 'pending', 'Global Inc', 236000.00)
ON CONFLICT DO NOTHING;
