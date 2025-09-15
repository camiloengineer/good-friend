#!/usr/bin/env python3
"""
Test del RUT del colega en modo PRODUCCIÓN (Selenium real) - Enterprise Edition.
"""

import os
import sys
from dotenv import load_dotenv
from utils.advanced_config import AdvancedConfig, ExecutionConfig
from services.email_service import EmailService
from services.enhanced_marcaje_service import EnhancedMarcajeService
from utils.delay_manager import DelayManager
from utils.logger import MetricsCollector

def test_rut_colega_produccion():
    """Probar el RUT del colega en modo PRODUCCIÓN con Selenium real y enterprise features."""
    load_dotenv()
    
    print("🚀 PRUEBA DEL RUT DEL COLEGA - MODO PRODUCCIÓN ENTERPRISE")
    print("=" * 70)
    print("⚠️  ATENCIÓN: Esta prueba ejecutará Selenium REAL")
    print("⚠️  Se realizará un marcaje REAL en el sistema")
    print("⚠️  Con retry logic y circuit breaker habilitados")
    print("=" * 70)
    
    # Cargar configuración avanzada
    config = AdvancedConfig()
    
    # FORZAR modo PRODUCCIÓN (DEBUG=False)
    config.DEBUG_MODE = False
    
    # Configurar execution config para testing (sin delay, con retry)
    config.execution_config = ExecutionConfig(
        parallel_execution=False,
        max_workers=1,
        retry_attempts=2,
        retry_delay_seconds=10,
        circuit_breaker_threshold=3,
        enable_metrics=True
    )
    
    print(f"🔧 DEBUG_MODE forzado a: {config.DEBUG_MODE}")
    print(f"🔧 Retry attempts: {config.execution_config.retry_attempts}")
    print(f"� Circuit breaker threshold: {config.execution_config.circuit_breaker_threshold}")
    
    print(f"📋 RUTs activos: {config.ACTIVE_RUTS}")
    print()
    
    # Encontrar el RUT del colega (172667341)
    rut_colega = None
    for rut in config.ACTIVE_RUTS:
        if rut.startswith("1726"):
            rut_colega = rut
            break
    
    if not rut_colega:
        print("❌ No se encontró el RUT del colega")
        return
    
    print(f"🎯 RUT del colega: {rut_colega}")
    print()
    
    print("🚀 INICIANDO MARCAJE REAL CON ENTERPRISE FEATURES...")
    print("-" * 60)
    
    # Inicializar servicios con configuración enterprise
    email_service = EmailService(config.get_email_address(), config.get_email_pass(), config, False)
    metrics_collector = MetricsCollector()
    
    # DelayManager modificado para NO aplicar delay en testing
    class NoDelayManager:
        def get_random_delay(self, rut): return 0
        def get_statistics(self): return {'total_ruts': 0, 'coincidences': 0}
    
    delay_manager = NoDelayManager()
    marcaje_service = EnhancedMarcajeService(
        email_service, 
        delay_manager, 
        False,  # DEBUG=False
        config.execution_config,
        metrics_collector
    )
    
    try:
        print("⚡ Ejecutando marcaje con enterprise features...")
        print(f"🔄 Circuit breaker state: {marcaje_service.get_circuit_breaker_status()['state']}")
        
        # Procesar el RUT del colega con Selenium REAL
        success = marcaje_service.process_rut(rut_colega)
        
        if success:
            print("✅ Marcaje completado exitosamente")
        else:
            print("❌ Marcaje falló")
        
        # Mostrar métricas finales
        metrics = marcaje_service.get_metrics_summary()
        print("\n📊 MÉTRICAS FINALES:")
        print(f"   Éxitos: {metrics['successes']}")
        print(f"   Errores: {metrics['errors']}")
        print(f"   Tasa de éxito: {metrics['success_rate']*100:.1f}%")
        print(f"   Tiempo total: {metrics['total_execution_time_seconds']:.2f}s")
        
        cb_status = marcaje_service.get_circuit_breaker_status()
        print(f"   Circuit breaker: {cb_status['state']} (fallos: {cb_status['failure_count']})")
        
    except Exception as e:
        print(f"❌ ERROR durante el marcaje: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("-" * 60)
    print("🏁 PRUEBA ENTERPRISE COMPLETADA")

if __name__ == "__main__":
    test_rut_colega_produccion()
