"""
Paquete de marcaje automático modularizado.
"""
from config import Config, EmailConfig, CHILE_HOLIDAYS_2025
from services.email_service import EmailService
from services.holiday_service import HolidayService
from services.marcaje_service import MarcajeService
from utils.rut_validator import RutValidator
from utils.delay_manager import DelayManager

__version__ = "2.0.0"
__author__ = "Sistema de Marcaje Automático"
__description__ = "Sistema modularizado de marcaje automático sin LaunchDarkly"

__all__ = [
    "Config",
    "EmailConfig", 
    "CHILE_HOLIDAYS_2025",
    "EmailService",
    "HolidayService", 
    "MarcajeService",
    "RutValidator",
    "DelayManager"
]
