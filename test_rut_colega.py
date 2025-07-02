#!/usr/bin/env python3
"""
Test específico para debuggear el RUT del colega (172667341).
"""

import os
import sys
from dotenv import load_dotenv
from config import Config
from services.email_service import EmailService
from services.marcaje_service import MarcajeService
from utils.delay_manager import DelayManager

def test_rut_colega():
    """Probar específicamente el RUT del colega."""
    load_dotenv()
    
    print("🔍 PRUEBA ESPECÍFICA DEL RUT DEL COLEGA")
    print("=" * 60)
    
    # Cargar configuración
    config = Config()
    
    print(f"📋 RUTs activos: {config.ACTIVE_RUTS}")
    print(f"📋 RUTs excepciones: {config.EXCEPTIONS_RUTS}")
    print(f"📋 DEBUG_MODE: {config.DEBUG_MODE}")
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
    
    print(f"🎯 RUT del colega encontrado: {rut_colega}")
    print()
    
    # Inicializar servicios
    email_service = EmailService(config.get_email_address(), config.get_email_pass(), config, config.DEBUG_MODE)
    delay_manager = DelayManager()
    marcaje_service = MarcajeService(email_service, delay_manager, config.DEBUG_MODE)
    
    print("🚀 INICIANDO PROCESAMIENTO DEL RUT DEL COLEGA...")
    print("-" * 50)
    
    try:
        # Procesar SOLO el RUT del colega
        marcaje_service.process_rut(rut_colega, config.EXCEPTIONS_RUTS)
        print("✅ Procesamiento completado exitosamente")
        
    except Exception as e:
        print(f"❌ ERROR durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("-" * 50)
    print("🏁 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_rut_colega()
