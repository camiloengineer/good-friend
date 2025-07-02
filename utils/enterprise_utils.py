"""
Utilidades enterprise adicionales para el sistema de marcaje.
Funciones de backup, cleanup y optimización.
"""

import os
import json
import shutil
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class BackupManager:
    """Gestor de backups para logs y configuraciones."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_logs(self, retention_days: int = 30) -> str:
        """Crear backup de logs y comprimir archivos antiguos."""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return "No logs directory found"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"logs_backup_{timestamp}.tar.gz"
        
        # Crear backup comprimido
        import tarfile
        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(logs_dir, arcname="logs")
        
        # Limpiar logs antiguos
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_files = 0
        
        for log_file in logs_dir.glob("*.log"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                log_file.unlink()
                cleaned_files += 1
        
        return f"Backup created: {backup_file}, {cleaned_files} old files cleaned"
    
    def backup_config(self) -> str:
        """Crear backup de configuraciones."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_backup_dir = self.backup_dir / f"config_{timestamp}"
        config_backup_dir.mkdir(exist_ok=True)
        
        # Backup de archivos de configuración
        config_files = [".env", "requirements.txt", "pytest.ini"]
        backed_up = []
        
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, config_backup_dir)
                backed_up.append(config_file)
        
        return f"Config backup created: {config_backup_dir}, files: {', '.join(backed_up)}"


class PerformanceAnalyzer:
    """Analizador de performance para optimización."""
    
    def __init__(self):
        self.metrics_file = Path("performance_metrics.json")
    
    def analyze_logs(self, days_back: int = 7) -> Dict[str, Any]:
        """Analizar logs para métricas de performance."""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {"error": "No logs directory found"}
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        analysis = {
            "period": f"Last {days_back} days",
            "executions": 0,
            "successes": 0,
            "errors": 0,
            "average_duration": 0,
            "error_patterns": {},
            "peak_hours": {},
            "rut_performance": {}
        }
        
        # Procesar archivos de log
        for log_file in logs_dir.glob("*.log"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) >= cutoff_date:
                self._process_log_file(log_file, analysis)
        
        # Calcular métricas derivadas
        if analysis["executions"] > 0:
            analysis["success_rate"] = analysis["successes"] / analysis["executions"] * 100
            analysis["error_rate"] = analysis["errors"] / analysis["executions"] * 100
        
        # Guardar análisis
        with open(self.metrics_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        return analysis
    
    def _process_log_file(self, log_file: Path, analysis: Dict[str, Any]):
        """Procesar un archivo de log individual."""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "INICIANDO procesamiento RUT" in line:
                        analysis["executions"] += 1
                    elif "MARCAJE COMPLETADO" in line:
                        analysis["successes"] += 1
                    elif "ERROR en RUT" in line:
                        analysis["errors"] += 1
                        # Extraer patrón de error
                        if ":" in line:
                            error_part = line.split(":", 2)[-1].strip()
                            error_key = error_part[:50]  # Primeros 50 caracteres
                            analysis["error_patterns"][error_key] = analysis["error_patterns"].get(error_key, 0) + 1
        except Exception as e:
            print(f"Error processing {log_file}: {e}")
    
    def get_recommendations(self) -> List[str]:
        """Obtener recomendaciones de optimización."""
        if not self.metrics_file.exists():
            return ["Run analyze_logs() first to get recommendations"]
        
        with open(self.metrics_file, 'r') as f:
            analysis = json.load(f)
        
        recommendations = []
        
        # Recomendaciones basadas en tasa de error
        error_rate = analysis.get("error_rate", 0)
        if error_rate > 10:
            recommendations.append(f"⚠️ Alta tasa de error ({error_rate:.1f}%) - Revisar configuración de Selenium")
        elif error_rate > 5:
            recommendations.append(f"🔧 Tasa de error moderada ({error_rate:.1f}%) - Considerar aumentar retry attempts")
        
        # Recomendaciones basadas en patrones de error
        if analysis.get("error_patterns"):
            most_common_error = max(analysis["error_patterns"].items(), key=lambda x: x[1])
            recommendations.append(f"🔍 Error más común: {most_common_error[0]} ({most_common_error[1]} veces)")
        
        # Recomendaciones de performance
        if analysis["executions"] > 0:
            if analysis["executions"] > 50:
                recommendations.append("📊 Alto volumen de ejecuciones - Considerar procesamiento paralelo")
            if analysis.get("average_duration", 0) > 300:  # 5 minutos
                recommendations.append("⏱️ Duración promedio alta - Optimizar delays o timeouts")
        
        return recommendations


class SystemOptimizer:
    """Optimizador del sistema para mejor performance."""
    
    def __init__(self):
        self.config_file = Path(".env")
    
    def optimize_for_production(self) -> List[str]:
        """Aplicar optimizaciones para entorno de producción."""
        optimizations = []
        
        if self.config_file.exists():
            # Leer configuración actual
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            changes = []
            
            # Optimización 1: Reducir retry delay en producción
            if "RETRY_DELAY_SECONDS=30" in content:
                content = content.replace("RETRY_DELAY_SECONDS=30", "RETRY_DELAY_SECONDS=15")
                changes.append("Reduced retry delay to 15 seconds")
            
            # Optimización 2: Habilitar métricas en producción
            if "ENABLE_METRICS=false" in content or "ENABLE_METRICS" not in content:
                if "ENABLE_METRICS=" in content:
                    content = content.replace("ENABLE_METRICS=false", "ENABLE_METRICS=true")
                else:
                    content += "\nENABLE_METRICS=true"
                changes.append("Enabled metrics collection")
            
            # Optimización 3: Configurar circuit breaker más agresivo
            if "CIRCUIT_BREAKER_THRESHOLD=3" in content:
                content = content.replace("CIRCUIT_BREAKER_THRESHOLD=3", "CIRCUIT_BREAKER_THRESHOLD=2")
                changes.append("More aggressive circuit breaker (threshold=2)")
            
            # Guardar cambios
            if changes:
                # Backup primero
                backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.config_file, backup_file)
                
                with open(self.config_file, 'w') as f:
                    f.write(content)
                
                optimizations.extend(changes)
                optimizations.append(f"Configuration backed up to {backup_file}")
        
        return optimizations
    
    def optimize_chrome_options(self) -> Dict[str, Any]:
        """Sugerir optimizaciones para opciones de Chrome."""
        suggestions = {
            "current_optimizations": [
                "--headless",
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-images"
            ],
            "additional_suggestions": [
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--memory-pressure-off",
                "--max_old_space_size=4096"
            ],
            "note": "Additional options may improve performance but could affect compatibility"
        }
        return suggestions


def main():
    """Función principal para utilidades enterprise."""
    print("🔧 UTILIDADES ENTERPRISE DEL SISTEMA DE MARCAJE")
    print("=" * 60)
    
    # Backup manager
    print("📦 Ejecutando backup de sistema...")
    backup_manager = BackupManager()
    logs_backup = backup_manager.backup_logs()
    config_backup = backup_manager.backup_config()
    print(f"✅ {logs_backup}")
    print(f"✅ {config_backup}")
    
    # Performance analyzer
    print("\n📊 Analizando performance...")
    analyzer = PerformanceAnalyzer()
    analysis = analyzer.analyze_logs(days_back=7)
    
    if "error" not in analysis:
        print(f"   Ejecuciones últimos 7 días: {analysis['executions']}")
        print(f"   Tasa de éxito: {analysis.get('success_rate', 0):.1f}%")
        print(f"   Tasa de error: {analysis.get('error_rate', 0):.1f}%")
        
        recommendations = analyzer.get_recommendations()
        if recommendations:
            print("\n💡 Recomendaciones:")
            for rec in recommendations:
                print(f"   {rec}")
    else:
        print(f"   ⚠️ {analysis['error']}")
    
    # System optimizer
    print("\n⚡ Optimizaciones disponibles...")
    optimizer = SystemOptimizer()
    optimizations = optimizer.optimize_for_production()
    
    if optimizations:
        print("   Optimizaciones aplicadas:")
        for opt in optimizations:
            print(f"   ✅ {opt}")
    else:
        print("   ℹ️ Sistema ya optimizado")
    
    # Chrome optimizations
    chrome_opts = optimizer.optimize_chrome_options()
    print(f"\n🌐 Optimizaciones de Chrome disponibles: {len(chrome_opts['additional_suggestions'])}")
    
    print("\n🎉 Utilidades enterprise completadas")
    print("=" * 60)


if __name__ == "__main__":
    main()
