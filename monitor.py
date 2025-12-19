#!/usr/bin/env python3
"""
Sistema de monitoreo y healthcheck para el marcaje automático.
Enterprise-grade monitoring con métricas y alertas.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv

from utils.advanced_config import AdvancedConfig
from services.email_service import EmailService
from utils.logger import MetricsCollector


class HealthChecker:
    """Sistema de healthcheck para el marcaje automático."""
    
    def __init__(self, config: AdvancedConfig):
        self.config = config
        self.email_service = EmailService(
            config.get_email_address(), 
            config.get_email_pass(), 
            config, 
            config.DEBUG_MODE
        )
    
    def run_health_check(self) -> Dict[str, Any]:
        """Ejecutar un health check completo del sistema."""
        print("🏥 INICIANDO HEALTH CHECK DEL SISTEMA")
        print("=" * 50)
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {}
        }
        
        # Check 1: Configuración
        config_status = self._check_configuration()
        health_status['checks']['configuration'] = config_status
        
        # Check 2: Conectividad de email
        email_status = self._check_email_connectivity()
        health_status['checks']['email'] = email_status
        
        # Check 3: Selenium dependencies
        selenium_status = self._check_selenium_setup()
        health_status['checks']['selenium'] = selenium_status
        
        # Check 4: Logs y permisos
        logs_status = self._check_logs_setup()
        health_status['checks']['logs'] = logs_status
        
        # Determinar estado general
        failed_checks = [name for name, check in health_status['checks'].items() 
                        if check['status'] != 'PASS']
        
        if failed_checks:
            health_status['overall_status'] = 'UNHEALTHY'
            health_status['failed_checks'] = failed_checks
        
        self._print_health_report(health_status)
        return health_status
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Verificar configuración del sistema."""
        print("🔧 Verificando configuración...")
        
        try:
            # Verificar variables críticas
            critical_vars = ['EMAIL_ADDRESS_B64', 'EMAIL_PASS_B64', 'ACTIVE_RUTS_B64']
            missing_vars = []
            
            for var in critical_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return {
                    'status': 'FAIL',
                    'message': f'Variables faltantes: {missing_vars}',
                    'details': {'missing_variables': missing_vars}
                }
            
            # Verificar RUTs válidos
            if not self.config.ACTIVE_RUTS:
                return {
                    'status': 'FAIL',
                    'message': 'No se encontraron RUTs activos',
                    'details': {'active_ruts_count': 0}
                }
            
            return {
                'status': 'PASS',
                'message': f'Configuración válida: {len(self.config.ACTIVE_RUTS)} RUTs',
                'details': {
                    'ruts_count': len(self.config.ACTIVE_RUTS),
                    'debug_mode': self.config.DEBUG_MODE,
                    'parallel_execution': self.config.execution_config.parallel_execution
                }
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Error en configuración: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def _check_email_connectivity(self) -> Dict[str, Any]:
        """Verificar conectividad del servicio de email."""
        print("📧 Verificando conectividad de email...")
        
        try:
            # Intentar enviar email de prueba
            test_subject = "🧪 Health Check - Test de Conectividad"
            test_content = f"""Test de conectividad del sistema de marcaje automático.
            
Timestamp: {datetime.now().isoformat()}
Modo DEBUG: {self.config.DEBUG_MODE}
Estado: Sistema funcionando correctamente

Este es un email automático de health check."""
            
            success = self.email_service.send_email(
                test_subject, 
                test_content, 
                email_to=self.config.get_email_address()
            )
            
            if success:
                return {
                    'status': 'PASS',
                    'message': 'Email enviado exitosamente',
                    'details': {'email_address': self.config.get_email_address()}
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'Falló envío de email de prueba',
                    'details': {}
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Error en conectividad de email: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def _check_selenium_setup(self) -> Dict[str, Any]:
        """Verificar setup de Selenium."""
        print("🌐 Verificando setup de Selenium...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            # Verificar que Chrome está disponible
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Test rápido de inicialización
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get("about:blank")
            driver.quit()
            
            return {
                'status': 'PASS',
                'message': 'Selenium configurado correctamente',
                'details': {'webdriver': 'Chrome'}
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Error en setup de Selenium: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def _check_logs_setup(self) -> Dict[str, Any]:
        """Verificar setup de logs y permisos."""
        print("📁 Verificando setup de logs...")
        
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            
            # Crear directorio si no existe
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # Test de escritura
            test_file = os.path.join(logs_dir, f"health_check_{int(time.time())}.test")
            with open(test_file, 'w') as f:
                f.write("Health check test")
            
            # Limpiar archivo de prueba
            os.remove(test_file)
            
            return {
                'status': 'PASS',
                'message': 'Directorio de logs accesible',
                'details': {'logs_directory': logs_dir}
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Error en setup de logs: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def _print_health_report(self, health_status: Dict[str, Any]):
        """Imprimir reporte de health check."""
        print("\n" + "=" * 50)
        print("📊 REPORTE DE HEALTH CHECK")
        print("=" * 50)
        
        status_emoji = "✅" if health_status['overall_status'] == 'HEALTHY' else "❌"
        print(f"{status_emoji} Estado General: {health_status['overall_status']}")
        print()
        
        for check_name, check_result in health_status['checks'].items():
            status_emoji = "✅" if check_result['status'] == 'PASS' else "❌"
            print(f"{status_emoji} {check_name.title()}: {check_result['status']}")
            print(f"   └─ {check_result['message']}")
        
        if health_status['overall_status'] == 'UNHEALTHY':
            print(f"\n⚠️  Checks fallidos: {', '.join(health_status.get('failed_checks', []))}")
        
        print("=" * 50)


class SystemMonitor:
    """Monitor del sistema para métricas y alertas."""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Recopilar métricas del sistema."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_usage': self._get_cpu_usage(),
                'memory_usage': self._get_memory_usage(),
                'disk_usage': self._get_disk_usage()
            },
            'application': {
                'uptime': self._get_uptime(),
                'log_files_count': self._count_log_files(),
                'last_execution': self._get_last_execution_time()
            }
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def _get_cpu_usage(self) -> float:
        """Obtener uso de CPU."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Obtener uso de memoria."""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """Obtener uso de disco."""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except ImportError:
            return 0.0
    
    def _get_uptime(self) -> str:
        """Obtener uptime del sistema."""
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime)
        except ImportError:
            return "Unknown"
    
    def _count_log_files(self) -> int:
        """Contar archivos de log."""
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            if os.path.exists(logs_dir):
                return len([f for f in os.listdir(logs_dir) if f.endswith('.log')])
            return 0
        except Exception:
            return 0
    
    def _get_last_execution_time(self) -> str:
        """Obtener tiempo de última ejecución."""
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            if os.path.exists(logs_dir):
                log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
                if log_files:
                    latest_log = max(log_files, key=lambda f: os.path.getctime(os.path.join(logs_dir, f)))
                    mtime = os.path.getmtime(os.path.join(logs_dir, latest_log))
                    return datetime.fromtimestamp(mtime).isoformat()
            return "Never"
        except Exception:
            return "Unknown"


def main():
    """Función principal del monitor."""
    load_dotenv()
    
    print("🚀 SISTEMA DE MONITOREO ENTERPRISE")
    print("=" * 60)
    
    try:
        # Cargar configuración
        config = AdvancedConfig()
        
        # Ejecutar health check
        health_checker = HealthChecker(config)
        health_status = health_checker.run_health_check()
        
        # Recopilar métricas
        monitor = SystemMonitor()
        metrics = monitor.collect_system_metrics()
        
        print("\n📊 MÉTRICAS DEL SISTEMA:")
        print(f"   CPU: {metrics['system']['cpu_usage']:.1f}%")
        print(f"   Memoria: {metrics['system']['memory_usage']:.1f}%")
        print(f"   Disco: {metrics['system']['disk_usage']:.1f}%")
        print(f"   Uptime: {metrics['system']['uptime']}")
        print(f"   Archivos de log: {metrics['application']['log_files_count']}")
        print(f"   Última ejecución: {metrics['application']['last_execution']}")
        
        # Generar reporte en JSON
        report = {
            'health_check': health_status,
            'system_metrics': metrics,
            'report_generated_at': datetime.now().isoformat()
        }
        
        # Guardar reporte
        report_file = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado en: {report_file}")
        
        # Resultado final
        if health_status['overall_status'] == 'HEALTHY':
            print("\n✅ SISTEMA SALUDABLE - Todo funcionando correctamente")
            return 0
        else:
            print("\n❌ SISTEMA CON PROBLEMAS - Revisar checks fallidos")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR EN MONITOREO: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
