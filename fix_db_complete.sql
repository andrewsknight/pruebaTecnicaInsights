BEGIN;

-- Eliminar vistas que dependen de las columnas
DROP VIEW IF EXISTS agent_performance_stats CASCADE;
DROP VIEW IF EXISTS call_type_performance CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dashboard_metrics CASCADE;

-- Eliminar constraints
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_call_id_fkey;
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_agent_id_fkey;
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_tenant_id_fkey;
ALTER TABLE calls DROP CONSTRAINT IF EXISTS calls_assigned_agent_id_fkey;
ALTER TABLE calls DROP CONSTRAINT IF EXISTS calls_tenant_id_fkey;
ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_tenant_id_fkey;

-- Convertir columnas a VARCHAR
ALTER TABLE agents ALTER COLUMN id TYPE VARCHAR USING id::text;
ALTER TABLE agents ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;
ALTER TABLE agents ALTER COLUMN current_call_id TYPE VARCHAR USING current_call_id::text;
ALTER TABLE calls ALTER COLUMN id TYPE VARCHAR USING id::text;
ALTER TABLE calls ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;
ALTER TABLE calls ALTER COLUMN assigned_agent_id TYPE VARCHAR USING assigned_agent_id::text;
ALTER TABLE assignments ALTER COLUMN id TYPE VARCHAR USING id::text;
ALTER TABLE assignments ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;
ALTER TABLE assignments ALTER COLUMN call_id TYPE VARCHAR USING call_id::text;
ALTER TABLE assignments ALTER COLUMN agent_id TYPE VARCHAR USING agent_id::text;
ALTER TABLE tenants ALTER COLUMN id TYPE VARCHAR USING id::text;

-- Recrear constraints básicos
ALTER TABLE calls ADD CONSTRAINT calls_assigned_agent_id_fkey 
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id) ON DELETE SET NULL;
ALTER TABLE assignments ADD CONSTRAINT assignments_call_id_fkey 
    FOREIGN KEY (call_id) REFERENCES calls(id) ON DELETE CASCADE;
ALTER TABLE assignments ADD CONSTRAINT assignments_agent_id_fkey 
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE;

COMMIT;
