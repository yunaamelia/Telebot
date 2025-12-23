-- Database initialization script for Cash Flow Bot
-- This script runs automatically when PostgreSQL container starts

-- Set timezone
SET timezone = 'Asia/Makassar';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE cashflow_db TO cashflow_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for Cash Flow Bot';
END $$;
