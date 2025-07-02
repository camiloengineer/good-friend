"""
Sistema de configuración avanzado con validación y paralelización.
"""
import os
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from config import Config


@dataclass
class ExecutionConfig:
    """Configuración para la ejecución del sistema."""
    parallel_execution: bool = False
    max_workers: int = 2
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    circuit_breaker_threshold: int = 3
    enable_metrics: bool = True


class AdvancedConfig(Config):
    """Configuración avanzada que extiende la configuración base."""
    
    def __init__(self):
        super().__init__()
        self.execution_config = self._load_execution_config()
        self._validate_advanced_config()
    
    def _load_execution_config(self) -> ExecutionConfig:
        """Cargar configuración de ejecución desde variables de entorno."""
        return ExecutionConfig(
            parallel_execution=os.getenv('PARALLEL_EXECUTION', 'false').lower() == 'true',
            max_workers=int(os.getenv('MAX_WORKERS', '2')),
            retry_attempts=int(os.getenv('RETRY_ATTEMPTS', '3')),
            retry_delay_seconds=int(os.getenv('RETRY_DELAY_SECONDS', '30')),
            circuit_breaker_threshold=int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '3')),
            enable_metrics=os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        )
    
    def _validate_advanced_config(self):
        """Validar configuración avanzada."""
        exec_config = self.execution_config
        
        if exec_config.max_workers < 1 or exec_config.max_workers > 10:
            raise ValueError("MAX_WORKERS debe estar entre 1 y 10")
        
        if exec_config.retry_attempts < 0 or exec_config.retry_attempts > 10:
            raise ValueError("RETRY_ATTEMPTS debe estar entre 0 y 10")
        
        if exec_config.retry_delay_seconds < 1 or exec_config.retry_delay_seconds > 300:
            raise ValueError("RETRY_DELAY_SECONDS debe estar entre 1 y 300")
        
        if len(self.ACTIVE_RUTS) > 10:
            raise ValueError("Máximo 10 RUTs permitidos para evitar abuse del sistema")
    
    def should_use_parallel_processing(self) -> bool:
        """Determinar si se debe usar procesamiento paralelo."""
        return (self.execution_config.parallel_execution and 
                len(self.ACTIVE_RUTS) > 1 and 
                not self.DEBUG_MODE)  # No paralelizar en modo debug
    
    def get_thread_pool_executor(self) -> Optional[ThreadPoolExecutor]:
        """Obtener executor para procesamiento paralelo."""
        if self.should_use_parallel_processing():
            return ThreadPoolExecutor(max_workers=self.execution_config.max_workers)
        return None
    
    def print_advanced_debug_info(self):
        """Imprimir información de debug avanzada."""
        self.print_debug_info()  # Llamar al método padre
        
        print("\n🔧 CONFIGURACIÓN AVANZADA:")
        exec_config = self.execution_config
        print(f"   Procesamiento paralelo: {'✅ Habilitado' if exec_config.parallel_execution else '❌ Deshabilitado'}")
        print(f"   Max workers: {exec_config.max_workers}")
        print(f"   Intentos de retry: {exec_config.retry_attempts}")
        print(f"   Delay entre retries: {exec_config.retry_delay_seconds}s")
        print(f"   Circuit breaker threshold: {exec_config.circuit_breaker_threshold}")
        print(f"   Métricas habilitadas: {'✅ Sí' if exec_config.enable_metrics else '❌ No'}")
        
        if self.should_use_parallel_processing():
            print(f"🚀 Se usará procesamiento PARALELO con {exec_config.max_workers} workers")
        else:
            reasons = []
            if not exec_config.parallel_execution:
                reasons.append("no habilitado")
            if len(self.ACTIVE_RUTS) <= 1:
                reasons.append("solo 1 RUT")
            if self.DEBUG_MODE:
                reasons.append("modo DEBUG")
            print(f"🔄 Se usará procesamiento SECUENCIAL ({', '.join(reasons)})")


class CircuitBreaker:
    """Circuit breaker para prevenir cascading failures."""
    
    def __init__(self, threshold: int = 3, reset_timeout: int = 60):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Determinar si se puede ejecutar una operación."""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            # Verificar si es tiempo de intentar de nuevo
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() > self.reset_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        elif self.state == 'HALF_OPEN':
            return True
        return False
    
    def record_success(self):
        """Registrar éxito en operación."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def record_failure(self):
        """Registrar falla en operación."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.threshold:
            self.state = 'OPEN'
    
    def get_state(self) -> Dict[str, Any]:
        """Obtener estado del circuit breaker."""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'threshold': self.threshold,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }
