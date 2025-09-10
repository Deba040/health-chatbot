-- schema.sql
-- Basic schema for AI Health Chatbot prototype (Day 1)
-- Use psql or your DB tool to run this file.

-- Users of the system (villagers / CHWs)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(32) UNIQUE,
    name VARCHAR(200),
    language VARCHAR(32),
    role VARCHAR(32), -- 'user' or 'chw' or 'admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Incoming user queries (messages)
CREATE TABLE IF NOT EXISTS queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    channel VARCHAR(32), -- whatsapp / sms / ussd / ivr
    message_text TEXT,
    response_text TEXT,
    status VARCHAR(32) DEFAULT 'received', -- received, processed, escalated, answered
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Vaccination records & scheduled reminders
CREATE TABLE IF NOT EXISTS vaccination_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    vaccine_name VARCHAR(200),
    scheduled_date DATE,
    status VARCHAR(32) DEFAULT 'scheduled', -- scheduled, done, missed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- CHW structured reports for outbreaks
CREATE TABLE IF NOT EXISTS chw_reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    district VARCHAR(200),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    report_type VARCHAR(64),
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Alerts / ingested outbreak feed
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300),
    description TEXT,
    source VARCHAR(200),
    severity VARCHAR(32),
    geo_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- RAG provenance / audit snippets
CREATE TABLE IF NOT EXISTS rag_snippets (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES queries(id) ON DELETE CASCADE,
    source_url TEXT,
    snippet TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- HITL (Human-in-the-loop) queue entries
CREATE TABLE IF NOT EXISTS hitl_queue (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES queries(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES users(id) NULL,
    state VARCHAR(32) DEFAULT 'pending', -- pending, approved, sent
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Simple index on created timestamps for quick queries
CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
