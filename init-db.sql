-- Initialization script for Call Assignment System Database
-- This script sets up the initial database structure and indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE agent_status_enum AS ENUM ('AVAILABLE', 'BUSY', 'PAUSED', 'OFFLINE');
CREATE TYPE call_status_enum AS ENUM ('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'ABANDONED', 'FAILED');
CREATE TYPE qualification_result_enum AS ENUM ('OK', 'KO', 'PENDING');
CREATE TYPE assignment_status_enum AS ENUM ('PENDING', 'ACTIVE', 'COMPLETED', 'FAILED');

-- Tenants table (for multi-tenant support)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agents table with partitioning for multi-tenancy
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    status agent_status_enum NOT NULL DEFAULT 'OFFLINE',
    last_call_end_time TIMESTAMP WITH TIME ZONE,
    current_call_id UUID,
    capabilities JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calls table with partitioning by creation date
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    phone_number VARCHAR(50) NOT NULL,
    call_type VARCHAR(50) NOT NULL,
    status call_status_enum NOT NULL DEFAULT 'PENDING',
    assigned_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    qualification_result qualification_result_enum NOT NULL DEFAULT 'PENDING',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds REAL,
    metadata JSONB DEFAULT '{}'
);

-- Assignments table
CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    status assignment_status_enum NOT NULL DEFAULT 'PENDING',
    assignment_time_ms REAL,
    expected_duration_seconds REAL,
    actual_duration_seconds REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- System metrics table for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value REAL NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    agent_type VARCHAR(50),
    call_type VARCHAR(50),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Test runs table for tracking test executions
CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name VARCHAR(255) NOT NULL,
    num_calls INTEGER NOT NULL,
    num_agents INTEGER NOT NULL,
    call_duration_mean REAL NOT NULL,
    call_duration_std REAL NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'RUNNING',
    results_summary JSONB,
    metadata JSONB DEFAULT '{}'
);

-- Performance indexes for high-throughput queries
-- Agents indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_tenant_status 
    ON agents (tenant_id, status) 
    WHERE status = 'AVAILABLE';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_tenant_type 
    ON agents (tenant_id, agent_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_idle_time 
    ON agents (tenant_id, last_call_end_time ASC NULLS FIRST) 
    WHERE status = 'AVAILABLE';

-- Calls indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_calls_tenant_status 
    ON calls (tenant_id, status, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_calls_tenant_type 
    ON calls (tenant_id, call_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_calls_pending 
    ON calls (tenant_id, created_at) 
    WHERE status = 'PENDING';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_calls_completion 
    ON calls (tenant_id, completed_at) 
    WHERE completed_at IS NOT NULL;

-- Assignments indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_tenant_status 
    ON assignments (tenant_id, status, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_call 
    ON assignments (call_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_agent 
    ON assignments (agent_id, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_performance 
    ON assignments (assignment_time_ms) 
    WHERE assignment_time_ms IS NOT NULL;

-- System metrics indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_tenant_type 
    ON system_metrics (tenant_id, metric_type, recorded_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_name_time 
    ON system_metrics (metric_name, recorded_at);

-- Functions for common operations
-- Function to get agent idle time
CREATE OR REPLACE FUNCTION get_agent_idle_time(agent_uuid UUID)
RETURNS INTERVAL AS $$
DECLARE
    last_call_time TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT last_call_end_time INTO last_call_time 
    FROM agents WHERE id = agent_uuid;
    
    IF last_call_time IS NULL THEN
        -- Agent never had a call, return a very large interval
        RETURN INTERVAL '999999 hours';
    ELSE
        RETURN NOW() - last_call_time;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to update agent status with timestamp
CREATE OR REPLACE FUNCTION update_agent_status()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update agent updated_at
CREATE TRIGGER trigger_update_agent_timestamp
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_status();

-- Function to calculate call wait time
CREATE OR REPLACE FUNCTION get_call_wait_time(call_uuid UUID)
RETURNS INTERVAL AS $$
DECLARE
    call_created TIMESTAMP WITH TIME ZONE;
    call_assigned TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT created_at, assigned_at INTO call_created, call_assigned 
    FROM calls WHERE id = call_uuid;
    
    IF call_assigned IS NULL THEN
        RETURN NULL;
    ELSE
        RETURN call_assigned - call_created;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- View for agent performance statistics
CREATE OR REPLACE VIEW agent_performance_stats AS
SELECT 
    a.id,
    a.name,
    a.agent_type,
    a.tenant_id,
    COUNT(ass.id) as total_assignments,
    COUNT(CASE WHEN ass.status = 'COMPLETED' THEN 1 END) as completed_assignments,
    AVG(ass.assignment_time_ms) as avg_assignment_time_ms,
    AVG(ass.actual_duration_seconds) as avg_call_duration_seconds,
    COUNT(CASE WHEN ass.assignment_time_ms <= 100 THEN 1 END)::FLOAT / 
        NULLIF(COUNT(ass.assignment_time_ms), 0) as performance_compliance_rate
FROM agents a
LEFT JOIN assignments ass ON a.id = ass.agent_id
GROUP BY a.id, a.name, a.agent_type, a.tenant_id;

-- View for call type performance
CREATE OR REPLACE VIEW call_type_performance AS
SELECT 
    c.tenant_id,
    c.call_type,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN c.status = 'COMPLETED' THEN 1 END) as completed_calls,
    COUNT(CASE WHEN c.qualification_result = 'OK' THEN 1 END) as successful_calls,
    AVG(c.duration_seconds) as avg_duration_seconds,
    AVG(EXTRACT(EPOCH FROM (c.assigned_at - c.created_at))) as avg_wait_time_seconds
FROM calls c
WHERE c.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY c.tenant_id, c.call_type;

-- Insert default tenant for single-tenant demo
INSERT INTO tenants (id, name, configuration) 
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID, 
    'Default Tenant', 
    '{"description": "Default tenant for single-tenant operations"}'
) ON CONFLICT (name) DO NOTHING;

-- Create materialized view for real-time dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_metrics AS
SELECT 
    NOW() as snapshot_time,
    COUNT(CASE WHEN a.status = 'AVAILABLE' THEN 1 END) as available_agents,
    COUNT(CASE WHEN a.status = 'BUSY' THEN 1 END) as busy_agents,
    COUNT(CASE WHEN c.status = 'PENDING' THEN 1 END) as pending_calls,
    COUNT(CASE WHEN c.status = 'IN_PROGRESS' THEN 1 END) as active_calls,
    COUNT(CASE WHEN ass.status = 'ACTIVE' THEN 1 END) as active_assignments
FROM agents a
CROSS JOIN calls c
CROSS JOIN assignments ass
WHERE a.created_at >= NOW() - INTERVAL '1 hour'
  AND c.created_at >= NOW() - INTERVAL '1 hour'
  AND ass.created_at >= NOW() - INTERVAL '1 hour';

-- Function to refresh dashboard metrics
CREATE OR REPLACE FUNCTION refresh_dashboard_metrics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW dashboard_metrics;
END;
$$ LANGUAGE plpgsql;

-- Create indexes on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_metrics_time 
    ON dashboard_metrics (snapshot_time);

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO call_assignment_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO call_assignment_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO call_assignment_app;

-- Enable Row Level Security for multi-tenancy (example)
-- ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (uncomment and adjust for production)
-- CREATE POLICY tenant_isolation_agents ON agents
--     FOR ALL TO call_assignment_app
--     USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

COMMIT;