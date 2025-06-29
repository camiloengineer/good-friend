"""
Script principal de marcaje automático.
Versión modularizada sin dependencias de LaunchDarkly.
"""
import os
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv

from config import Config, EmailConfig
from services.email_service import EmailService
from services.holiday_service import HolidayService
from services.marcaje_service import MarcajeService
from utils.delay_manager import DelayManager


def setup_logging():
    """Configurar el sistema de logging."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Generate log filename with pattern
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = f"marcaje-logs-{os.getenv('GITHUB_RUN_NUMBER', '*')}-{current_date}.log"
    log_filepath = os.path.join(logs_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_filepath,
        level=logging.INFO,
        format="%(asctime)s-%(levelname)s-%(message)s",
        force=True
    )
    
    logging.info(f"Iniciando logging en archivo: {log_filepath}")
    return log_filepath


def print_startup_info(config: Config):
    """Imprimir información de inicio del script."""
    print("=" * 60)
    print("🚀 INICIANDO SCRIPT DE MARCAJE AUTOMÁTICO - MÚLTIPLES RUTS")
    print("=" * 60)
    print(f"📧 Email principal: {config.get_email_address()}")
    special_email = config.get_special_email()
    if special_email:
        print(f"📧 Email especial: {special_email}")
    print(f"🆔 RUTs configurados: {len(config.ACTIVE_RUTS)} RUTs - {[rut[:4] + '****' for rut in config.ACTIVE_RUTS]}")
    print("=" * 60)

    # Get Chile time right at the start
    chile_tz = pytz.timezone('America/Santiago')
    chile_time = datetime.now(chile_tz)
    print(f"⏰ HORA DE INICIO: {chile_time.strftime('%Y-%m-%d %H:%M:%S')} (CLT)")
    logging.info(f"Script iniciado a las: {chile_time.strftime('%Y-%m-%d %H:%M:%S')} (CLT)")


def main():
    """Función principal del script."""
    # Configurar logging
    setup_logging()
    
    # Load environment variables
    load_dotenv()
    print(f"🔍 DEBUG - Archivo .env cargado desde: {os.getcwd()}")
    print(f"🔍 DEBUG - DEBUG_MODE raw: '{os.getenv('DEBUG_MODE')}'")
    print(f"🔍 DEBUG - CLOCK_IN_ACTIVE raw: '{os.getenv('CLOCK_IN_ACTIVE')}'")
    
    # Cargar configuración
    config = Config()
    config.print_debug_info()
    
    # Verificar si el script está activo
    print("🔍 Verificando configuración inicial...")
    if not config.CLOCK_IN_ACTIVE:
        print("⏹️ Script desactivado por variable CLOCK_IN_ACTIVE")
        logging.info("Script desactivado por variable de entorno CLOCK_IN_ACTIVE")
        return
    
    print("✅ Script activo, continuando...")
    
    # Inicializar servicios
    email_service = EmailService(config.get_email_address(), config.get_email_pass(), config, config.DEBUG_MODE)
    
    # Crear máscaras de RUTs para logs
    active_ruts_masked = [rut[:4] + '****' for rut in config.ACTIVE_RUTS]
    
    # Verificar feriados
    holiday_service = HolidayService(email_service, len(config.ACTIVE_RUTS), active_ruts_masked)
    if holiday_service.is_holiday():
        print("🎄 Terminando ejecución - hoy es feriado")
        return
    
    # Imprimir información de inicio
    print_startup_info(config)
    
    # Inicializar servicios de marcaje
    delay_manager = DelayManager()
    marcaje_service = MarcajeService(email_service, delay_manager, config.DEBUG_MODE)
    
    # Obtener RUTs para procesar
    print("🔍 Obteniendo RUTs para procesar...")
    ruts = config.ACTIVE_RUTS
    
    if not ruts:
        print("❌ No se encontraron RUTs válidos para procesar")
        print("🏁 Finalizando script")
        return
    
    # Procesar RUTs
    print("=" * 40)
    print(f"👥 INICIANDO PROCESAMIENTO DE {len(ruts)} RUTs")
    print(f"📧 Email principal: {config.get_email_address()}")
    print(f"📧 Email especial: {config.get_special_email() or 'No configurado'}")
    print("=" * 40)

    # Procesar todos los RUTs en la lista
    for rut in ruts:
        marcaje_service.process_rut(rut, config.EXCEPTIONS_RUTS)
    
    # Mostrar estadísticas finales
    stats = delay_manager.get_statistics()
    print("=" * 40)
    print("📊 ESTADÍSTICAS FINALES:")
    print(f"   RUTs procesados: {stats['total_ruts']}")
    print(f"   Coincidencias de delay: {stats['coincidences']}")
    print("🏁 PROCESAMIENTO COMPLETADO")
    print("=" * 40)


if __name__ == "__main__":
    main()
