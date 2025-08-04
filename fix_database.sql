-- Script para convertir toda la base de datos de UUID a VARCHAR
-- Esto arreglará completamente el problema de compatibilidad

BEGIN;

-- Eliminar foreign keys temporalmente
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_call_id_fkey;
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_agent_id_fkey;
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_tenant_id_fkey;
ALTER TABLE calls DROP CONSTRAINT IF EXISTS calls_assigned_agent_id_fkey;
ALTER TABLE calls DROP CONSTRAINT IF EXISTS calls_tenant_id_fkey;
ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_tenant_id_fkey;

-- Convertir tabla agents
ALTER TABLE agents ALTER COLUMN id TYPE VARCHAR USING id::text;
ALTER TABLE agents ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;
ALTER TABLE agents ALTER COLUMN current_call_id TYPE VARCHAR USING current_call_id::text;

-- Convertir tabla calls
ALTER TABLE calls ALTER COLUMN id TYPE VARCHAR USING id::text;
ALTER TABLE calls ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;
ALTER TABLE calls ALTER COLUMN assigned_agent_id TYPE VARCHAR USING assigned_agent_id::text;

-- Convertir tabla assignments
ALTER TABLE assignments ALTER COLUMN id TYPE VARCHAR USING id::text;
ALTER TABLE assignments ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;
ALTER TABLE assignments ALTER COLUMN call_id TYPE VARCHAR USING call_id::text;
ALTER TABLE assignments ALTER COLUMN agent_id TYPE VARCHAR USING agent_id::text;

-- Convertir tabla tenants
ALTER TABLE tenants ALTER COLUMN id TYPE VARCHAR USING id::text;

-- Cambiar defaults para usar gen_random_uuid()::text
ALTER TABLE agents ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;
ALTER TABLE calls ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;
ALTER TABLE assignments ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;
ALTER TABLE tenants ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;

-- Recrear foreign keys
ALTER TABLE agents ADD CONSTRAINT agents_tenant_id_fkey 
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE calls ADD CONSTRAINT calls_tenant_id_fkey 
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE calls ADD CONSTRAINT calls_assigned_agent_id_fkey 
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id) ON DELETE SET NULL;

ALTER TABLE assignments ADD CONSTRAINT assignments_tenant_id_fkey 
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE assignments ADD CONSTRAINT assignments_call_id_fkey 
    FOREIGN KEY (call_id) REFERENCES calls(id) ON DELETE CASCADE;

ALTER TABLE assignments ADD CONSTRAINT assignments_agent_id_fkey 
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE;

COMMIT;

-- Verificar que todo funcionó
\echo 'Conversión completada. Verificando estructura:'
\d agents