from pydantic_settings import BaseSettings
from typing import Dict, Any
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/call_assignment")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", 8000))
    
    # Assignment timing
    max_assignment_time_ms: int = 100
    
    # Call duration parameters (in seconds)
    call_duration_mean: float = 180.0  # 3 minutes
    call_duration_std: float = 180.0   # 3 minutes std dev
    
    # Conversion probability matrix
    conversion_matrix: Dict[str, Dict[str, float]] = {
        "agente_tipo_1": {
            "llamada_tipo_1": 0.30,
            "llamada_tipo_2": 0.20,
            "llamada_tipo_3": 0.10,
            "llamada_tipo_4": 0.05
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
    
    # Agent and call types
    agent_types: list[str] = ["agente_tipo_1", "agente_tipo_2", "agente_tipo_3", "agente_tipo_4"]
    call_types: list[str] = ["llamada_tipo_1", "llamada_tipo_2", "llamada_tipo_3", "llamada_tipo_4"]
    
    # Webhook configuration
    webhook_url: str = "http://localhost:8001/webhook"
    webhook_timeout: int = 5
    
    # Test configuration
    test_num_calls: int = 100
    test_num_agents: int = 20
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()