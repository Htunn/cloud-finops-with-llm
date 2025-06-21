-- Create necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS finops;

-- Create tables
-- AWS Cost data table
CREATE TABLE IF NOT EXISTS finops.aws_cost_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    usage_type VARCHAR(200),
    resource_id VARCHAR(200),
    cost DECIMAL(12,6) NOT NULL,
    usage_quantity DECIMAL(20,6),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    date_range_type VARCHAR(20) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost forecasts table
CREATE TABLE IF NOT EXISTS finops.cost_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    forecast_date DATE NOT NULL,
    forecasted_cost DECIMAL(12,6) NOT NULL,
    confidence_level DECIMAL(5,2),
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost optimization recommendations table
CREATE TABLE IF NOT EXISTS finops.cost_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id VARCHAR(50) NOT NULL,
    resource_id VARCHAR(200),
    service_name VARCHAR(100) NOT NULL,
    recommendation_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    potential_savings DECIMAL(12,6),
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table for LLM interactions
CREATE TABLE IF NOT EXISTS finops.chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    user_query TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    llm_model VARCHAR(100),
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User settings table
CREATE TABLE IF NOT EXISTS finops.user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    preferred_llm VARCHAR(50) DEFAULT 'local',
    budget_alerts JSONB,
    custom_dashboards JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_aws_cost_data_account_id ON finops.aws_cost_data(account_id);
CREATE INDEX IF NOT EXISTS idx_aws_cost_data_service_name ON finops.aws_cost_data(service_name);
CREATE INDEX IF NOT EXISTS idx_aws_cost_data_date_range ON finops.aws_cost_data(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_cost_forecasts_account_id ON finops.cost_forecasts(account_id);
CREATE INDEX IF NOT EXISTS idx_cost_forecasts_service_name ON finops.cost_forecasts(service_name);
CREATE INDEX IF NOT EXISTS idx_cost_forecasts_date ON finops.cost_forecasts(forecast_date);

-- Create read-only role for LLM access
CREATE ROLE llm_reader WITH LOGIN PASSWORD 'llm_secure_password';
GRANT CONNECT ON DATABASE finops TO llm_reader;
GRANT USAGE ON SCHEMA finops TO llm_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA finops TO llm_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA finops GRANT SELECT ON TABLES TO llm_reader;
