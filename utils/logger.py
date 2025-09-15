"""
Sistema de logging estructurado para marcaje automático.
"""
import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any


class StructuredLogger:
    """Logger estructurado con contexto para mejor observabilidad."""
    
    def __init__(self, log_filepath: str):
        self.log_filepath = log_filepath
        self._setup_logging()
    
    def _setup_logging(self):
        """Configurar el sistema de logging estructurado."""
        # Custom formatter para logs estructurados
        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': record.levelname,
                    'thread': threading.current_thread().name,
                    'message': record.getMessage(),
                }
                
                # Añadir contexto extra si está disponible
                if hasattr(record, 'rut_masked'):
                    log_entry['rut_masked'] = record.rut_masked
                if hasattr(record, 'action_type'):
                    log_entry['action_type'] = record.action_type
                if hasattr(record, 'duration_seconds'):
                    log_entry['duration_seconds'] = record.duration_seconds
                
                return json.dumps(log_entry, ensure_ascii=False)
        
        # Configurar el handler
        handler = logging.FileHandler(self.log_filepath)
        handler.setFormatter(StructuredFormatter())
        
        # Configurar el logger raíz
        logging.basicConfig(
            level=logging.INFO,
            handlers=[handler],
            force=True
        )
    
    @staticmethod
    def log_rut_start(rut_masked: str):
        """Log inicio de procesamiento de RUT."""
        extra = {'rut_masked': rut_masked}
        logging.info(f"Iniciando procesamiento RUT {rut_masked}", extra=extra)
    
    @staticmethod
    def log_rut_complete(rut_masked: str, action_type: str, duration_seconds: float):
        """Log finalización de procesamiento de RUT."""
        extra = {
            'rut_masked': rut_masked,
            'action_type': action_type,
            'duration_seconds': duration_seconds
        }
        logging.info(f"Completado {action_type} para RUT {rut_masked} en {duration_seconds:.2f}s", extra=extra)
    
    @staticmethod
    def log_error(rut_masked: str, error: str, action_type: str = None):
        """Log error durante procesamiento."""
        extra = {'rut_masked': rut_masked}
        if action_type:
            extra['action_type'] = action_type
        logging.error(f"Error en RUT {rut_masked}: {error}", extra=extra)


class MetricsCollector:
    """Recolector de métricas para monitoreo."""
    
    def __init__(self):
        self.metrics = {
            'ruts_processed': 0,
            'successes': 0,
            'errors': 0,
            'total_duration': 0.0,
            'delays_applied': 0,
            'start_time': datetime.now(),
        }
        self._lock = threading.Lock()
    
    def record_rut_start(self):
        """Registrar inicio de procesamiento de RUT."""
        with self._lock:
            self.metrics['ruts_processed'] += 1
    
    def record_success(self, duration_seconds: float):
        """Registrar éxito en procesamiento."""
        with self._lock:
            self.metrics['successes'] += 1
            self.metrics['total_duration'] += duration_seconds
    
    def record_error(self):
        """Registrar error en procesamiento."""
        with self._lock:
            self.metrics['errors'] += 1
    
    def record_delay_applied(self):
        """Registrar aplicación de delay."""
        with self._lock:
            self.metrics['delays_applied'] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas."""
        with self._lock:
            total_time = (datetime.now() - self.metrics['start_time']).total_seconds()
            avg_duration = (self.metrics['total_duration'] / self.metrics['successes'] 
                          if self.metrics['successes'] > 0 else 0)
            
            return {
                'ruts_processed': self.metrics['ruts_processed'],
                'successes': self.metrics['successes'],
                'errors': self.metrics['errors'],
                'success_rate': (self.metrics['successes'] / self.metrics['ruts_processed'] 
                               if self.metrics['ruts_processed'] > 0 else 0),
                'average_duration_seconds': avg_duration,
                'total_execution_time_seconds': total_time,
                'delays_applied': self.metrics['delays_applied'],
            }
