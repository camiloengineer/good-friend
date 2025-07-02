"""
Paquete de marcaje automático modularizado con procesamiento paralelo.
"""
from config import Config, EmailConfig, CHILE_HOLIDAYS_2025
from services.email_service import EmailService
from services.holiday_service import HolidayService
from services.marcaje_service import MarcajeService
from services.enhanced_marcaje_service import EnhancedMarcajeService
from utils.rut_validator import RutValidator
from utils.delay_manager import DelayManager
from utils.advanced_config import AdvancedConfig, CircuitBreaker, ExecutionConfig
from utils.logger import StructuredLogger, MetricsCollector
from concurrent.futures import ThreadPoolExecutor, as_completed

__version__ = "3.0.0"
__author__ = "Sistema de Marcaje Automático"
__description__ = "Sistema modularizado de marcaje automático con procesamiento paralelo"

__all__ = [
    "Config",
    "EmailConfig", 
    "CHILE_HOLIDAYS_2025",
    "EmailService",
    "HolidayService", 
    "MarcajeService",
    "EnhancedMarcajeService",
    "RutValidator",
    "DelayManager",
    "AdvancedConfig",
    "CircuitBreaker",
    "ExecutionConfig",
    "StructuredLogger",
    "MetricsCollector",
    "ThreadPoolExecutor",
    "as_completed"
]
