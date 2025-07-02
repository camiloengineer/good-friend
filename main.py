"""
Script principal de marcaje automático - Enterprise Edition.
Versión modularizada con procesamiento paralelo, retry logic y observabilidad.
"""
import os
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Config, EmailConfig
from utils.advanced_config import AdvancedConfig
from utils.logger import StructuredLogger, MetricsCollector
from services.email_service import EmailService
from services.holiday_service import HolidayService
from services.enhanced_marcaje_service import EnhancedMarcajeService
from utils.delay_manager import DelayManager


def setup_logging():
    """Configurar el sistema de logging estructurado."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Generate log filename with pattern
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = f"marcaje-logs-{os.getenv('GITHUB_RUN_NUMBER', '*')}-{current_date}.log"
    log_filepath = os.path.join(logs_dir, log_filename)

    # Inicializar el logger estructurado
    structured_logger = StructuredLogger(log_filepath)
    
    logging.info(f"Iniciando logging estructurado en archivo: {log_filepath}")
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
    
    # Cargar configuración avanzada
    config = AdvancedConfig()
    config.print_advanced_debug_info()
    
    # Verificar si el script está activo
    print("🔍 Verificando configuración inicial...")
    if not config.CLOCK_IN_ACTIVE:
        print("⏹️ Script desactivado por variable CLOCK_IN_ACTIVE")
        logging.info("Script desactivado por variable de entorno CLOCK_IN_ACTIVE")
        return
    
    print("✅ Script activo, continuando...")
    
    # Inicializar métricas si están habilitadas
    metrics_collector = MetricsCollector() if config.execution_config.enable_metrics else None
    
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
    marcaje_service = EnhancedMarcajeService(
        email_service, 
        delay_manager, 
        config.DEBUG_MODE,
        config.execution_config,
        metrics_collector
    )
    
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

    # Procesar RUTs (siempre en paralelo si hay más de uno)
    print("=" * 40)
    print(f"👥 INICIANDO PROCESAMIENTO DE {len(ruts)} RUTs")
    print(f"📧 Email principal: {config.get_email_address()}")
    print(f"📧 Email especial: {config.get_special_email() or 'No configurado'}")
    print("=" * 40)

    if len(ruts) > 1:
        print(f"🚀 Usando procesamiento PARALELO con {config.execution_config.max_workers} workers")
        success_count = process_ruts_parallel(marcaje_service, ruts, config.execution_config.max_workers)
    else:
        print("🔄 Usando procesamiento para un solo RUT")
        success_count = process_ruts_sequential(marcaje_service, ruts)
    
    # Mostrar estadísticas finales
    print_final_statistics(delay_manager, metrics_collector, success_count, len(ruts), marcaje_service)


def process_ruts_sequential(marcaje_service: EnhancedMarcajeService, ruts: list) -> int:
    """Procesar RUTs de forma secuencial."""
    success_count = 0
    for rut in ruts:
        if marcaje_service.process_rut(rut):
            success_count += 1
    return success_count


def process_ruts_parallel(marcaje_service: EnhancedMarcajeService, ruts: list, max_workers: int) -> int:
    """Procesar RUTs de forma paralela usando ThreadPoolExecutor."""
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todos los RUTs al pool de threads
        future_to_rut = {executor.submit(marcaje_service.process_rut, rut): rut for rut in ruts}
        
        # Procesar resultados conforme se completan
        for future in as_completed(future_to_rut):
            rut = future_to_rut[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                print(f"✅ RUT {rut[:4]}**** completado: {'éxito' if success else 'error'}")
            except Exception as exc:
                print(f"❌ RUT {rut[:4]}**** generó excepción: {exc}")
    
    return success_count


def print_final_statistics(delay_manager: DelayManager, metrics_collector: MetricsCollector, 
                          success_count: int, total_ruts: int, marcaje_service: EnhancedMarcajeService):
    """Imprimir estadísticas finales del procesamiento."""
    delay_stats = delay_manager.get_statistics()
    
    print("=" * 60)
    print("📊 ESTADÍSTICAS FINALES:")
    print(f"   RUTs procesados: {total_ruts}")
    print(f"   Éxitos: {success_count}")
    print(f"   Errores: {total_ruts - success_count}")
    print(f"   Tasa de éxito: {(success_count/total_ruts*100):.1f}%")
    print(f"   Coincidencias de delay: {delay_stats['coincidences']}")
    
    # Métricas avanzadas si están disponibles
    if metrics_collector:
        metrics = metrics_collector.get_summary()
        print(f"   Tiempo total de ejecución: {metrics['total_execution_time_seconds']:.2f}s")
        print(f"   Tiempo promedio por RUT: {metrics['average_duration_seconds']:.2f}s")
        print(f"   Delays aplicados: {metrics['delays_applied']}")
    
    # Estado del circuit breaker
    cb_status = marcaje_service.get_circuit_breaker_status()
    print(f"   Circuit Breaker: {cb_status['state']} (fallos: {cb_status['failure_count']})")
    
    print("🏁 PROCESAMIENTO COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
