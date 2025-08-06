# 📞 Sistema de Asignación de Llamadas - Prueba Técnica

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-orange.svg)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io)
[![Grafana](https://img.shields.io/badge/Grafana-Latest-orange.svg)](https://grafana.com)

Un sistema de asignación de llamadas de alto rendimiento diseñado para simular y evaluar algoritmos de distribución en call centers. Implementa arquitectura hexagonal con Domain-Driven Design, garantizando asignaciones en menos de 100ms con análisis estadístico completo.

## 🎯 **Características Principales**

### 🚀 **Alto Rendimiento**
- **Asignación < 100ms**: Garantía de asignación de llamadas en menos de 100 milisegundos
- **Escalabilidad**: Soporta miles de llamadas concurrentes
- **Cache Inteligente**: Redis para operaciones en tiempo real
- **Algoritmo Optimizado**: Longest Idle Time para distribución equitativa

### 🧪 **Sistema de Simulación Avanzado**
- **Generador de Eventos**: Simula llegadas de llamadas realistas
- **Distribución Probabilística**: Duración de llamadas con distribución normal
- **Cualificación Inteligente**: Sistema binomial de conversión OK/KO
- **Matriz de Conversión**: Probabilidades específicas por tipo de agente/llamada

### 📊 **Monitoreo y Analytics**
- **Dashboards en Tiempo Real**: Grafana + Prometheus
- **Métricas Detalladas**: Rendimiento, conversión, utilización
- **Reportes Automáticos**: Análisis estadístico post-ejecución
- **Webhooks**: Notificaciones a sistemas externos

### 🏗️ **Arquitectura Empresarial**
- **Domain-Driven Design**: Separación clara de responsabilidades
- **Arquitectura Hexagonal**: Fácil testing y mantenimiento
- **API REST Completa**: Documentación automática con Swagger
- **Multi-tenant Ready**: Preparado para múltiples inquilinos

## 📋 **Tabla de Contenidos**

- [🎯 Características Principales](#-características-principales)
- [🏗️ Arquitectura del Sistema](#️-arquitectura-del-sistema)
- [🚀 Instalación y Configuración](#-instalación-y-configuración)
- [🎮 Uso del Sistema](#-uso-del-sistema)
- [📊 API REST](#-api-rest)
- [🧪 Sistema de Pruebas](#-sistema-de-pruebas)
- [📈 Monitoreo y Métricas](#-monitoreo-y-métricas)
- [🔧 Configuración Avanzada](#-configuración-avanzada)
- [🎭 Funcionamiento Interno](#-funcionamiento-interno)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [🤝 Contribución](#-contribución)

---

## 🏗️ **Arquitectura del Sistema**

### **Patrón de Arquitectura: Hexagonal + DDD**

```
┌─────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │   FastAPI       │ │   PostgreSQL    │ │     Redis     │  │
│  │   REST API      │ │   Database      │ │     Cache     │  │
│  │   + Swagger     │ │   + Metrics     │ │  + Real-time  │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │   Prometheus    │ │     Grafana     │ │   Webhooks    │  │
│  │   Metrics       │ │   Dashboards    │ │   External    │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  APPLICATION LAYER                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │CallOrchestrator │ │ EventGenerator  │ │  TestRunner   │  │
│  │ (Coordinador    │ │ (Simulador de   │ │ (Suite de     │  │
│  │  Principal)     │ │   Eventos)      │ │  Pruebas)     │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    DOMAIN LAYER                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │   Agent     │ │    Call     │ │    Assignment       │    │
│  │  (Agente)   │ │  (Llamada)  │ │   (Asignación)      │    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
│  ┌─────────────────────┐ ┌─────────────────────────────┐    │
│  │ AssignmentService   │ │ QualificationService        │    │
│  │ (Lógica asignación) │ │ (Lógica cualificación)      │    │
│  └─────────────────────┘ └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### **Componentes Principales**

#### **🎯 CallOrchestrator (Cerebro del Sistema)**
- Coordina todo el proceso de asignación
- Garantiza tiempos < 100ms
- Maneja concurrencia y race conditions
- Programa finalización automática de llamadas

#### **🎲 EventGenerator (Simulador)**
- Genera llamadas sintéticas realistas
- Simula comportamiento de agentes
- Controla tasas de llegada configurables
- Maneja distribuciones estadísticas

#### **🧪 TestRunner (Suite de Pruebas)**
- Ejecuta pruebas completas del sistema
- Valida rendimiento vs. requerimientos
- Genera reportes detallados
- Compara resultados vs. expectativas

---

## 🚀 **Instalación y Configuración**

### **🔧 Requisitos del Sistema**

```bash
# Requisitos obligatorios
Python 3.11+
Docker 20.10+
Docker Compose 2.0+
Git 2.30+

# Requisitos de hardware recomendados
RAM: 4GB mínimo (8GB recomendado)
CPU: 2 cores mínimo (4 cores recomendado)
Disk: 2GB libre
```

### **⚡ Instalación Rápida (5 minutos)**

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd call-assignment-system

# 2. Setup automático completo
make setup

# 3. Ejecutar sistema
make up

# 4. Verificar funcionamiento
make demo

# 5. Ejecutar prueba completa
make test
```

### **🔧 Instalación Manual Detallada**

#### **Paso 1: Configurar Entorno Python**

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Linux/Mac)
source .venv/bin/activate

# Activar entorno (Windows)
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

#### **Paso 2: Configurar Variables de Entorno**

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración (opcional)
nano .env
```

**Variables principales:**
```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/call_assignment

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Configuración de pruebas
TEST_NUM_CALLS=100
TEST_NUM_AGENTS=20
CALL_DURATION_MEAN=180.0
CALL_DURATION_STD=180.0
```

#### **Paso 3: Iniciar Servicios de Infraestructura**

```bash
# Iniciar PostgreSQL y Redis
docker-compose up -d postgres redis

# Verificar que estén funcionando
docker-compose ps
```

#### **Paso 4: Inicializar Base de Datos**

```bash
# Crear tablas y datos iniciales
python src/main.py --init-db
```

---

## 🎮 **Uso del Sistema**

### **🖥️ Interfaz de Línea de Comandos**

El sistema incluye una CLI completa para todas las operaciones:

```bash
# Ver ayuda completa
python src/main.py --help

# 🚀 OPERACIONES PRINCIPALES

# Iniciar servidor API
python src/main.py api

# Ejecutar suite de pruebas completa
python src/main.py test

# Ejecutar prueba rápida de validación (20 llamadas, 5 agentes)
python src/main.py test --quick

# Ejecutar prueba de estrés (5 minutos de carga continua)
python src/main.py test --stress 5

# Ejecutar prueba personalizada
python src/main.py test --calls 500 --agents 50

# 📊 MONITOREO Y ESTADO

# Ver estado del sistema en tiempo real
python src/main.py status

# Ejecutar demostración interactiva
python src/main.py demo

# Ver métricas del sistema
curl http://localhost:8000/system/metrics

# 🧹 MANTENIMIENTO

# Limpiar datos de prueba
python src/main.py cleanup

# Ejecutar prueba de carga personalizada
python src/main.py load --duration 300 --calls-per-minute 200
```

### **⚡ Comandos Make (Recomendado)**

```bash
# Setup completo desde cero
make setup

# Iniciar todo el sistema
make up

# Parar sistema
make down

# Ejecutar pruebas
make test              # Prueba completa
make test-quick        # Prueba rápida
make test-stress       # Prueba de estrés

# Monitoreo
make status            # Estado del sistema
make logs              # Ver logs en vivo
make metrics           # Métricas actuales

# Mantenimiento
make clean             # Limpiar todo
make reset             # Reset completo
```

---

## 📊 **API REST**

### **🌐 Documentación Interactiva**

Una vez iniciado el servidor, la API está disponible en:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### **📞 Endpoints de Llamadas**

#### **Crear y Asignar Llamada**
```http
POST /calls
Content-Type: application/json

{
  "phone_number": "+1555000123",
  "call_type": "llamada_tipo_1"
}

Response:
{
  "success": true,
  "assignment_id": "uuid-here",
  "agent_id": "uuid-here",
  "call_id": "uuid-here",
  "assignment_time_ms": 45.2,
  "message": "Assignment successful"
}
```

#### **Obtener Detalles de Llamada**
```http
GET /calls/{call_id}

Response:
{
  "id": "uuid-here",
  "phone_number": "+1555000123",
  "call_type": "llamada_tipo_1",
  "status": "COMPLETED",
  "assigned_agent_id": "uuid-here",
  "qualification_result": "OK",
  "created_at": "2025-08-06T12:00:00Z",
  "assigned_at": "2025-08-06T12:00:01Z",
  "completed_at": "2025-08-06T12:03:01Z",
  "duration_seconds": 180.5,
  "wait_time_seconds": 1.2
}
```

#### **Cancelar Llamada**
```http
DELETE /calls/{call_id}

Response:
{
  "message": "Call uuid-here cancelled successfully"
}
```

### **👥 Endpoints de Agentes**

#### **Crear Agente**
```http
POST /agents
Content-Type: application/json

{
  "name": "Agent Smith",
  "agent_type": "agente_tipo_1"
}

Response:
{
  "id": "uuid-here",
  "name": "Agent Smith",
  "agent_type": "agente_tipo_1",
  "status": "OFFLINE",
  "created_at": "2025-08-06T12:00:00Z",
  "updated_at": "2025-08-06T12:00:00Z"
}
```

#### **Listar Agentes**
```http
GET /agents

Response:
[
  {
    "id": "uuid-here",
    "name": "Agent Smith",
    "agent_type": "agente_tipo_1",
    "status": "AVAILABLE",
    "idle_time_seconds": 120.5,
    ...
  }
]
```

#### **Actualizar Estado de Agente**
```http
PUT /agents/{agent_id}/status
Content-Type: application/json

{
  "status": "AVAILABLE"
}
```

#### **Ver Agentes Disponibles**
```http
GET /agents/available

# Retorna agentes ordenados por tiempo de inactividad (longest idle first)
```

### **🔧 Endpoints del Sistema**

#### **Estado del Sistema**
```http
GET /system/status

Response:
{
  "timestamp": "2025-08-06T12:00:00Z",
  "agents": {
    "total": 20,
    "available": 15,
    "busy": 3,
    "paused": 1,
    "offline": 1
  },
  "active_assignments": 3,
  "metrics": {
    "calls_assigned": 1250,
    "calls_completed": 1240,
    "calls_ok": 350,
    "calls_ko": 890,
    "last_assignment_time_ms": 67.3,
    "last_call_duration": 195.7
  },
  "system_health": {
    "redis_connected": true,
    "performance_target_met": true
  }
}
```

#### **Métricas del Sistema**
```http
GET /system/metrics

Response:
{
  "timestamp": "2025-08-06T12:00:00Z",
  "metrics": {
    "calls_assigned": 1250.0,
    "calls_completed": 1240.0,
    "calls_ok": 350.0,
    "calls_ko": 890.0,
    "calls_saturated": 5.0,
    "assignment_errors": 2.0,
    "last_assignment_time_ms": 67.3,
    "last_call_duration": 195.7
  }
}
```

#### **Métricas para Prometheus**
```http
GET /metrics

Response:
# HELP calls_total Total calls processed
# TYPE calls_total counter
calls_total{call_type="llamada_tipo_1",status="completed"} 350.0
calls_total{call_type="llamada_tipo_2",status="completed"} 340.0

# HELP assignment_time_seconds Call assignment time
# TYPE assignment_time_seconds histogram
assignment_time_seconds_bucket{le="0.01"} 0.0
assignment_time_seconds_bucket{le="0.05"} 1200.0
assignment_time_seconds_bucket{le="0.1"} 1250.0
assignment_time_seconds_bucket{le="+Inf"} 1250.0

# HELP active_agents Active agents by status
# TYPE active_agents gauge
active_agents{status="available"} 15.0
active_agents{status="busy"} 3.0
active_agents{status="paused"} 1.0
```

#### **Health Check**
```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-08-06T12:00:00Z",
  "redis_connected": true
}
```

---

## 🧪 **Sistema de Pruebas**

### **🔬 Tipos de Pruebas Disponibles**

#### **1. Prueba Completa (Recomendada)**
```bash
python src/main.py test

# Parámetros:
# - 100 llamadas (configurable)
# - 20 agentes (configurable)  
# - Distribución equitativa de tipos
# - Análisis estadístico completo
# - Duración: ~10-15 minutos
```

#### **2. Prueba Rápida (Para Desarrollo)**
```bash
python src/main.py test --quick

# Parámetros:
# - 20 llamadas
# - 5 agentes
# - Duración: ~2-3 minutos
```

#### **3. Prueba de Estrés (Performance)**
```bash
python src/main.py test --stress 10

# Parámetros:
# - 10 minutos de duración
# - Carga continua
# - 200 llamadas/minuto
# - Monitoreo de saturación
```

#### **4. Prueba Personalizada**
```bash
python src/main.py test --calls 500 --agents 30

# Parámetros completamente personalizables
```

### **📊 Estructura del Reporte**

Cada prueba genera un reporte JSON completo:

```json
{
  "test_metadata": {
    "test_name": "Call Assignment Test - 2025-08-06T12:00:00Z",
    "num_calls": 100,
    "num_agents": 20,
    "call_duration_mean": 180.0,
    "call_duration_std": 180.0,
    "started_at": "2025-08-06T12:00:00Z",
    "completed_at": "2025-08-06T12:15:23Z",
    "total_duration_seconds": 923.4
  },
  "final_report": {
    "executive_summary": {
      "test_outcome": "PASSED",
      "total_calls_processed": 100,
      "assignment_success_rate": 0.98,
      "performance_compliance": true,
      "key_findings": [
        "✅ Assignment time requirement met (< 100ms)",
        "✅ System stability requirement met",
        "✅ Qualification rates match expected conversion matrix"
      ]
    },
    "detailed_metrics": {
      "assignment_performance": {
        "calls_assigned": 98,
        "calls_saturated": 2,
        "avg_assignment_time_ms": 67.3,
        "max_assignment_time_ms": 95.7,
        "assignments_under_100ms": 98,
        "performance_compliance_rate": 1.0
      },
      "qualification_accuracy": {
        "by_combination": {
          "agente_tipo_1_llamada_tipo_1": {
            "total_calls": 25,
            "ok_calls": 8,
            "actual_conversion_rate": 0.32,
            "expected_conversion_rate": 0.30,
            "rate_difference_percentage": 6.67
          }
        },
        "overall_stats": {
          "total_completed_calls": 96,
          "total_ok_calls": 28,
          "overall_conversion_rate": 0.292
        }
      }
    },
    "recommendations": [
      "✅ System shows excellent performance compliance",
      "💡 Consider testing with higher load for scalability validation"
    ]
  }
}
```

### **🎯 Validaciones Automáticas**

El sistema valida automáticamente:

#### **✅ Rendimiento**
- Tiempo de asignación < 100ms (SLA crítico)
- Tasa de éxito > 95%
- Tasa de error < 5%
- Tiempo de respuesta del sistema

#### **✅ Funcionalidad**
- Distribución correcta de tipos de llamada
- Algoritmo "Longest Idle Time" funcionando
- Estados de agentes consistentes
- Integridad de datos en Redis + PostgreSQL

#### **✅ Estadísticas**
- Duración de llamadas siguiendo distribución normal
- Tasas de conversión OK/KO según matriz probabilística
- Diferencias estadísticas dentro de márgenes esperados
- Varianza aceptable en muestras grandes

---

## 📈 **Monitoreo y Métricas**

### **🎛️ Stack de Monitoreo**

```bash
# Iniciar stack completo
make up

# URLs de acceso:
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - API: http://localhost:8000/docs
```

### **📊 Dashboards de Grafana**

#### **🎯 Dashboard Principal**
- **Llamadas por Segundo**: Gráfico en tiempo real
- **Estados de Agentes**: Gauge con distribución
- **Tiempos de Asignación**: Histograma de performance
- **Tasa de Conversión**: OK/KO por tipo
- **Saturación del Sistema**: Alertas automáticas

#### **📞 Dashboard de Llamadas**
- **Volumen por Tipo**: Distribución de llamada_tipo_X
- **Duración Promedio**: Por tipo de agente/llamada
- **Cola de Espera**: Llamadas pendientes
- **Abandono**: Tasa de llamadas canceladas

#### **👥 Dashboard de Agentes**
- **Utilización**: % tiempo ocupado vs disponible  
- **Tiempo Promedio Inactivo**: Por agente individual
- **Performance Individual**: Conversiones por agente
- **Distribución de Carga**: Equity en asignaciones

### **🎨 Consultas PromQL Útiles**

```promql
# Llamadas por segundo
rate(calls_total[5m])

# Percentil 95 de tiempo de asignación  
histogram_quantile(0.95, assignment_time_seconds_bucket)

# Tasa de conversión por tipo
sum by(call_type) (calls_total{status="ok"}) / 
sum by(call_type) (calls_total)

# Agentes disponibles vs total
active_agents{status="available"} / 
sum(active_agents)

# Saturación del sistema
rate(calls_total{status="saturated"}[5m])

# Latencia promedio de asignación
rate(assignment_time_seconds_sum[5m]) / 
rate(assignment_time_seconds_count[5m])
```

### **🚨 Alertas Configuradas**

```yaml
# Tiempo de asignación > 90ms
- alert: HighAssignmentTime
  expr: histogram_quantile(0.95, assignment_time_seconds_bucket) > 0.09
  for: 1m

# Tasa de saturación > 5%
- alert: SystemSaturated  
  expr: rate(calls_total{status="saturated"}[5m]) > 0.05
  for: 30s

# Sin agentes disponibles
- alert: NoAgentsAvailable
  expr: active_agents{status="available"} == 0
  for: 10s
```

---

## 🔧 **Configuración Avanzada**

### **⚙️ Matriz de Conversión**

La matriz define las probabilidades de éxito (OK) para cada combinación agente/llamada:

```python
conversion_matrix = {
    "agente_tipo_1": {
        "llamada_tipo_1": 0.30,  # 30% probabilidad OK
        "llamada_tipo_2": 0.20,  # 20% probabilidad OK  
        "llamada_tipo_3": 0.10,  # 10% probabilidad OK
        "llamada_tipo_4": 0.05   # 5% probabilidad OK
    },
    "agente_tipo_2": {
        "llamada_tipo_1": 0.20,
        "llamada_tipo_2": 0.15,
        "llamada_tipo_3": 0.07,
        "llamada_tipo_4": 0.04
    },
    "agente_tipo_3": {
        "llamada_tipo_1": 0.15,
        "llamada_tipo_2": 0.12,
        "llamada_tipo_3": 0.06,
        "llamada_tipo_4": 0.03
    },
    "agente_tipo_4": {
        "llamada_tipo_1": 0.12,
        "llamada_tipo_2": 0.10,
        "llamada_tipo_3": 0.04,
        "llamada_tipo_4": 0.02
    }
}
```

**Interpretación**: Un `agente_tipo_1` handling a `llamada_tipo_1` tiene 30% probabilidad de generar resultado "OK".

### **⏱️ Configuración de Duración**

```python
# Distribución normal para duración de llamadas
CALL_DURATION_MEAN = 180.0  # 3 minutos promedio
CALL_DURATION_STD = 180.0   # 3 minutos desviación estándar

# Resultado: Mayoría 1-6 minutos, algunas muy cortas/largas
# Distribución realista de call center
```

### **🎯 Algoritmo de Asignación**

**Estrategia: Longest Idle Time**

1. **Filtrar**: Solo agentes con status `AVAILABLE`
2. **Calcular**: Tiempo inactivo desde última llamada
3. **Ordenar**: Por tiempo inactivo (descendente)
4. **Seleccionar**: Agente con mayor tiempo inactivo
5. **Asignar**: Cambiar estados atómicamente

**Ventajas**:
- ✅ Distribución equitativa de carga
- ✅ Evita sobrecarga de agentes específicos  
- ✅ Mantiene agentes activos/entrenados
- ✅ Algoritmo simple y predecible

### **🔄 Configuración de Redis**

```python
# Configuración optimizada para alta concurrencia
REDIS_CONFIG = {
    "maxmemory": "512mb",
    "maxmemory-policy": "allkeys-lru",
    "appendonly": "yes",
    "save": "900 1 300 10 60 10000",
    "tcp-keepalive": 60
}
```

### **🗄️ Configuración de PostgreSQL**

```sql
-- Índices optimizados para queries frecuentes
CREATE INDEX CONCURRENTLY idx_agents_status_type ON agents(status, agent_type);
CREATE INDEX CONCURRENTLY idx_calls_status_created ON calls(status, created_at);
CREATE INDEX CONCURRENTLY idx_assignments_status_created ON assignments(status, created_at);

-- Configuraciones de rendimiento
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

---

## 🎭 **Funcionamiento Interno**

### **🔄 Flujo Completo de una Llamada**

```
📞 LLEGADA LLAMADA
   POST /calls {"phone_number": "+1555000123", "call_type": "llamada_tipo_1"}
          ↓
🔍 BÚSQUEDA AGENTES DISPONIBLES  
   CallOrchestrator → Redis Cache → PostgreSQL
   Query: SELECT * FROM agents WHERE status = 'AVAILABLE' ORDER BY last_call_end_time ASC
          ↓
🎯 SELECCIÓN ALGORITMO LONGEST IDLE TIME
   AssignmentService → Calcular idle_time para cada agente
   Seleccionar: max(current_time - last_call_end_time)
          ↓
⚡ ASIGNACIÓN ATÓMICA (Objetivo < 100ms)
   BEGIN TRANSACTION
   - Agent: AVAILABLE → BUSY
   - Call: PENDING → ASSIGNED  
   - Crear Assignment record
   - Update Redis cache
   COMMIT TRANSACTION
          ↓
📊 GENERACIÓN DURACIÓN ESPERADA
   QualificationService → numpy.random.normal(μ=180s, σ=180s)
   Resultado: 157.3 segundos (ejemplo)
          ↓
⏰ PROGRAMACIÓN FINALIZACIÓN AUTOMÁTICA
   asyncio.create_task(complete_after_delay(157.3))
   Timer guardado en: call_timers[call_id]
          ↓
📡 NOTIFICACIÓN WEBHOOK
   WebhookClient → POST http://external-system/webhook
   Payload: {"event": "CALL_ASSIGNED", "call_id": "...", "agent_id": "...", "assignment_time_ms": 67.3}
          ↓
⏳ ESPERA PROGRAMADA (157.3 segundos)
   Sistema continúa procesando otras llamadas...
          ↓
🎲 CUALIFICACIÓN AUTOMÁTICA
   QualificationService → Binomial(n=1, p=conversion_matrix[agent_type][call_type])
   Ejemplo: agente_tipo_1 + llamada_tipo_1 → p=0.30 → resultado: KO (70% probabilidad)
          ↓
✅ FINALIZACIÓN Y LIBERACIÓN
   - Call: ASSIGNED → COMPLETED (qualification: KO, duration: 157.3s)
   - Agent: BUSY → AVAILABLE (last_call_end_time = now())  
   - Assignment: ACTIVE → COMPLETED
   - Update Redis + PostgreSQL
          ↓
📈 ACTUALIZACIÓN MÉTRICAS
   Redis Counters:
   - calls_completed++
   - calls_ko++  
   - last_call_duration = 157.3
   - last_assignment_time_ms = 67.3
          ↓
📡 NOTIFICACIÓN FINALIZACIÓN
   WebhookClient → POST http://external-system/webhook  
   Payload: {"event": "CALL_COMPLETED", "qualification": "KO", "duration": 157.3}
          ↓
🔄 AGENTE DISPONIBLE PARA NUEVA ASIGNACIÓN
   Agent idle_time = 0, ready for next call
```

### **🧮 Algoritmos Internos**

#### **⏱️ Cálculo de Idle Time**
```python
def get_idle_time_seconds(self) -> float:
    if self.last_call_end_time is None:
        return float('inf')  # Prioridad máxima para nuevos agentes
    return (datetime.utcnow() - self.last_call_end_time).total_seconds()
```

#### **🎲 Cualificación Probabilística**
```python
def qualify_call(self, agent_type: str, call_type: str) -> QualificationResult:
    probability = self.conversion_matrix[agent_type][call_type]
    result = numpy.random.binomial(n=1, p=probability)
    return QualificationResult.OK if result == 1 else QualificationResult.KO
```

#### **📏 Generación de Duración**
```python
def generate_duration(self, mean: float, std: float) -> float:
    duration = numpy.random.normal(mean, std)
    return max(1.0, duration)  # Mínimo 1 segundo
```

### **🔒 Manejo de Concurrencia**

#### **Lock Distribuido (Redis)**
```python
async def create_assignment_lock(self, call_id: str, ttl: int = 5) -> bool:
    key = f"assignment_lock:{call_id}"
    result = await redis.set(key, datetime.utcnow().isoformat(), nx=True, ex=ttl)
    return result is not None
```

#### **Transacciones Atómicas (PostgreSQL)**
```python
async def assign_call_atomic(self, call, agent):
    async with db_session.begin():
        # Verificar estados actuales
        current_agent = await refresh_agent_status(agent.id)
        if current_agent.status != AgentStatus.AVAILABLE:
            raise RaceConditionException()
        
        # Actualizar ambos estados
        agent.status = AgentStatus.BUSY
        call.status = CallStatus.ASSIGNED
        
        await save_agent(agent)  
        await save_call(call)
        # COMMIT automático si no hay excepciones
```

---

## 🛠️ **Troubleshooting**

### **⚠️ Problemas Comunes**

#### **❌ "Assignment time exceeds 100ms"**
```bash
# Síntomas
WARNING - Assignment time 156ms exceeds 100ms limit

# Causas posibles
1. Base de datos lenta
2. Redis saturado  
3. Demasiadas llamadas concurrentes
4. Consultas no optimizadas

# Soluciones
make status                    # Ver carga del sistema
make clean && make up         # Reiniciar servicios  
docker stats                  # Ver uso de recursos
```

#### **❌ "No agents available - system saturated"**
```bash
# Síntomas  
ERROR - No agents available - system saturated

# Causas posibles
1. Todos los agentes ocupados
2. Agentes en estado PAUSED/OFFLINE
3. Configuración incorrecta de agentes

# Soluciones
curl http://localhost:8000/agents/available  # Ver agentes disponibles
python src/main.py demo                     # Crear agentes de prueba
```

#### **❌ "Redis connection failed"**
```bash
# Síntomas
ConnectionError: Error -3 connecting to redis:6379

# Soluciones
docker-compose ps              # Ver estado de Redis
docker-compose restart redis  # Reiniciar Redis
docker-compose logs redis     # Ver logs de error
```

#### **❌ "Database connection error"**
```bash
# Síntomas
asyncpg.exceptions.InvalidCatalogNameError: database "call_assignment" does not exist

# Soluciones  
docker-compose down -v        # Limpiar volúmenes
docker-compose up postgres -d # Recrear base de datos
python src/main.py --init-db  # Inicializar esquema
```

#### **❌ "Docker permission denied"**
```bash
# Síntomas
permission denied while trying to connect to the Docker daemon socket

# Soluciones
sudo usermod -aG docker $USER  # Agregar usuario al grupo docker
newgrp docker                  # Aplicar cambios  
sudo systemctl restart docker # Reiniciar servicio
```

#### **❌ "Port 8000 already in use"**
```bash
# Síntomas
ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8000): address already in use

# Soluciones
sudo lsof -i :8000           # Ver qué usa el puerto
pkill -f "main.py api"       # Matar API local
docker-compose down          # Parar contenedores
```

### **🔧 Comandos de Diagnóstico**

```bash
# Estado completo del sistema
make status

# Logs en tiempo real
make logs

# Ver métricas actuales
curl http://localhost:8000/system/metrics | python -m json.tool

# Test de conectividad  
curl http://localhost:8000/health
curl http://localhost:3000/api/health    # Grafana
curl http://localhost:9090/-/healthy     # Prometheus

# Verificar base de datos
docker-compose exec postgres psql -U user call_assignment -c "SELECT COUNT(*) FROM agents;"

# Verificar Redis
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli info stats

# Ver procesos de Docker
docker-compose ps
docker stats

# Ver volúmenes y redes
docker volume ls
docker network ls
```

### **📊 Métricas de Salud del Sistema**

```bash
# Verificar performance
curl -s http://localhost:8000/system/metrics | grep "last_assignment_time_ms"

# Verificar saturación  
curl -s http://localhost:8000/system/metrics | grep "calls_saturated"

# Verificar errores
curl -s http://localhost:8000/system/metrics | grep "_errors"

# Estado de agentes
curl -s http://localhost:8000/system/status | jq '.agents'
```

---

## 🚀 **Despliegue en Producción**

### **🔧 Variables de Entorno de Producción**

```env
# Configuración de producción
ENVIRONMENT=production
DEBUG=false

# Base de datos con pool optimizado
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/call_assignment
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# Redis con configuración de cluster
REDIS_URL=redis://redis-cluster:6379/0
REDIS_MAX_CONNECTIONS=100

# API con múltiples workers
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=8

# Logging estructurado
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=https://your-sentry-dsn

# Monitoreo
METRICS_ENABLED=true
PROMETHEUS_PUSH_GATEWAY=http://pushgateway:9091

# Seguridad
SECRET_KEY=your-super-secret-production-key
CORS_ORIGINS=https://your-frontend-domain.com
```

### **🐳 Docker Compose para Producción**

```yaml
version: '3.8'

services:
  api:
    image: call-assignment-system:latest
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

### **🔍 Monitoring de Producción**

```yaml
# prometheus.yml para producción
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'call-assignment-cluster'
    static_configs:
      - targets: ['api-1:8000', 'api-2:8000', 'api-3:8000']
    scrape_interval: 10s

rule_files:
  - "/etc/prometheus/alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

---

## 🤝 **Contribución**

### **🔧 Setup de Desarrollo**

```bash
# Clonar repositorio
git clone <repository-url>
cd call-assignment-system

# Setup completo de desarrollo
make dev-setup

# Instalar hooks de pre-commit
pre-commit install

# Ejecutar tests
make test

# Ejecutar linting
make lint
```

### **📋 Guía de Contribución**

#### **🌿 Branching Strategy**
```bash
# Crear rama para nueva funcionalidad
git checkout -b feature/nueva-funcionalidad

# Crear rama para bugfix
git checkout -b bugfix/descripcion-del-bug

# Crear rama para hotfix
git checkout -b hotfix/fix-critico
```

#### **✅ Checklist antes de Pull Request**
- [ ] Tests pasan: `make test`
- [ ] Linting limpio: `make lint`  
- [ ] Documentación actualizada
- [ ] Changelog actualizado
- [ ] Pruebas de integración OK
- [ ] Performance tests OK

#### **🧪 Ejecutar Tests Locales**
```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración  
pytest tests/integration/

# Tests de performance
python src/main.py test --stress 1

# Coverage completo
pytest --cov=src tests/
```

### **📝 Estándares de Código**

#### **🐍 Python Style Guide**
```python
# Seguir PEP 8
# Usar type hints
def assign_call(self, call: Call, agents: List[Agent]) -> AssignmentResult:
    
# Documentar funciones complejas
async def complex_algorithm(self, data: ComplexData) -> Result:
    """
    Executes complex assignment algorithm.
    
    Args:
        data: Input data with validation rules
        
    Returns:
        Result object with success status and metrics
        
    Raises:
        ValidationError: If input data is invalid
        TimeoutError: If algorithm exceeds time limit
    """
```

#### **🏗️ Arquitectura**
- Mantener separación clara de capas (Domain/Application/Infrastructure)
- Nuevas funcionalidades en el dominio primero
- Usar dependency injection para testabilidad
- Evitar lógica de negocio en controllers

#### **📊 Testing**
- Cobertura mínima: 80%
- Tests unitarios para lógica de negocio
- Tests de integración para API endpoints
- Tests de performance para algoritmos críticos

---

## 📚 **Referencias y Documentación**

### **🔗 Enlaces Importantes**

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **PostgreSQL Performance**: https://www.postgresql.org/docs/current/performance-tips.html
- **Redis Best Practices**: https://redis.io/docs/manual/clients-guide/
- **Prometheus Monitoring**: https://prometheus.io/docs/practices/naming/
- **Grafana Dashboards**: https://grafana.com/docs/grafana/latest/dashboards/

### **📖 Arquitectura y Patrones**

- **Domain-Driven Design**: https://martinfowler.com/bliki/DomainDrivenDesign.html
- **Hexagonal Architecture**: https://alistair.cockburn.us/hexagonal-architecture/
- **Event-Driven Architecture**: https://microservices.io/patterns/data/event-driven-architecture.html

### **📊 Estadísticas y Probabilidades**

- **Distribución Normal**: https://docs.scipy.org/doc/numpy/reference/random/generated/numpy.random.normal.html
- **Distribución Binomial**: https://docs.scipy.org/doc/numpy/reference/random/generated/numpy.random.binomial.html
- **Statistical Analysis**: https://docs.scipy.org/doc/scipy/reference/stats.html

---

## 📄 **Licencia**

Este proyecto está licenciado bajo la **MIT License**.

```
MIT License

Copyright (c) 2025 Call Assignment System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🎉 **Agradecimientos**

- **FastAPI Team** - Por el excelente framework
- **PostgreSQL Community** - Por la robustez de la base de datos
- **Redis Team** - Por la velocidad del cache
- **Grafana Labs** - Por las herramientas de visualización
- **Prometheus** - Por el sistema de métricas

---

**¡Gracias por usar el Sistema de Asignación de Llamadas!** 🚀

Si tienes preguntas, sugerencias o encuentras algún problema, por favor:
- 🐛 Abre un **issue** en el repositorio
- 💡 Propón **mejoras** via pull request  
- 📧 Contacta al equipo de desarrollo
- ⭐ Dale **estrella** al repo si te resulta útil

**¡Happy Coding!** 🎯