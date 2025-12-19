#!/bin/bash
# Script de deployment Enterprise para el sistema de marcaje automático

set -e  # Exit on any error

echo "INICIANDO DEPLOYMENT ENTERPRISE DEL SISTEMA DE MARCAJE"
echo "========================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    error "No se encuentra main.py o requirements.txt. Ejecuta desde el directorio raíz del proyecto."
fi

log "Verificando sistema..."

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    error "Python 3 no está instalado"
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log "Python versión: $PYTHON_VERSION"

# Verificar Chrome/Chromium
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    warning "Chrome/Chromium no detectado. Selenium podría no funcionar."
fi

# Crear virtual environment si no existe
if [ ! -d "venv" ]; then
    log "Creando virtual environment..."
    python3 -m venv venv
    success "Virtual environment creado"
else
    log "Virtual environment ya existe"
fi

# Activar virtual environment
log "Activando virtual environment..."
source venv/bin/activate

# Actualizar pip
log "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
log "Instalando dependencias..."
pip install -r requirements.txt
success "Dependencias instaladas"

# Crear directorios necesarios
log "Creando estructura de directorios..."
mkdir -p logs
mkdir -p backups
mkdir -p reports
success "Directorios creados"

# Verificar archivo .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log "Copiando .env.example a .env..."
        cp .env.example .env
        warning "IMPORTANTE: Edita el archivo .env con tus configuraciones reales"
    else
        error "No se encuentra .env ni .env.example"
    fi
else
    log "Archivo .env encontrado"
fi

# Ejecutar health check
log "Ejecutando health check del sistema..."
if python3 monitor.py; then
    success "Health check completado exitosamente"
else
    error "Health check falló. Revisa la configuración."
fi

# Ejecutar tests
log "Ejecutando tests del sistema..."
if python3 -m pytest tests/ -v; then
    success "Tests completados exitosamente"
else
    warning "Algunos tests fallaron. Revisa la salida anterior."
fi

# Crear script de inicio
log "Creando script de inicio..."
cat > start.sh << 'EOF'
#!/bin/bash
# Script de inicio para el sistema de marcaje automático

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 Iniciando sistema de marcaje automático..."
echo "Timestamp: $(date)"
echo "========================================"

python3 main.py

echo "========================================"
echo "Ejecución completada: $(date)"
EOF

chmod +x start.sh
success "Script de inicio creado: start.sh"

# Crear script de monitoreo
log "Creando script de monitoreo..."
cat > check_health.sh << 'EOF'
#!/bin/bash
# Script de health check para el sistema de marcaje automático

cd "$(dirname "$0")"
source venv/bin/activate

echo "🏥 Ejecutando health check..."
python3 monitor.py
EOF

chmod +x check_health.sh
success "Script de monitoreo creado: check_health.sh"

# Crear script para test de producción
log "Creando script de test de producción..."
cat > test_production.sh << 'EOF'
#!/bin/bash
# Script para ejecutar test de producción del colega

cd "$(dirname "$0")"
source venv/bin/activate

echo "⚠️  ATENCIÓN: Este test ejecutará marcaje REAL en producción"
echo "Presiona ENTER para continuar o Ctrl+C para cancelar..."
read

python3 test_rut_colega_produccion.py
EOF

chmod +x test_production.sh
success "Script de test de producción creado: test_production.sh"

# Configurar cron job (opcional)
log "¿Deseas configurar un cron job para ejecución automática? (y/n)"
read -p "Respuesta: " configure_cron

if [ "$configure_cron" = "y" ] || [ "$configure_cron" = "Y" ]; then
    SCRIPT_DIR=$(pwd)
    CRON_COMMAND="0 9,18 * * 1-5 cd $SCRIPT_DIR && ./start.sh >> logs/cron.log 2>&1"
    
    echo "Comando de cron sugerido (9 AM y 6 PM, lunes a viernes):"
    echo "$CRON_COMMAND"
    echo ""
    echo "Para agregarlo ejecuta: crontab -e"
    echo "Y agrega la línea anterior"
    warning "Recuerda ajustar los horarios según tus necesidades"
fi

# Crear documentación de deployment
log "Creando documentación..."
cat > DEPLOYMENT_README.md << 'EOF'
# Sistema de Marcaje Automático - Enterprise Edition

## Deployment Completado ✅

### Scripts Disponibles

- `./start.sh` - Ejecutar el sistema de marcaje
- `./check_health.sh` - Health check del sistema
- `./test_production.sh` - Test de producción (¡CUIDADO! Hace marcaje real)

### Configuración

1. Edita el archivo `.env` con tus configuraciones reales
2. Asegúrate de que las variables en base64 estén correctamente codificadas
3. Revisa la configuración enterprise en `.env.example`

### Monitoreo

El sistema incluye:
- Logging estructurado en JSON
- Métricas de performance
- Circuit breaker para prevenir fallos en cascada
- Retry logic automático
- Health checks automatizados

### Ejecución

```bash
# Activar environment
source venv/bin/activate

# Ejecutar sistema
./start.sh

# Health check
./check_health.sh

# Test de producción (¡CUIDADO!)
./test_production.sh
```

### Configuración Avanzada

Variables de entorno enterprise:
- `PARALLEL_EXECUTION=true` - Procesamiento paralelo
- `MAX_WORKERS=2` - Número de workers
- `RETRY_ATTEMPTS=2` - Intentos de retry
- `CIRCUIT_BREAKER_THRESHOLD=3` - Umbral del circuit breaker

### Cron Job Sugerido

```cron
# Ejecutar a las 9 AM y 6 PM, lunes a viernes
0 9,18 * * 1-5 cd /ruta/a/tu/proyecto && ./start.sh >> logs/cron.log 2>&1
```

### Troubleshooting

1. Si Chrome no funciona, instala Chrome/Chromium
2. Si fallan los emails, verifica SMTP y credenciales
3. Usa `./check_health.sh` para diagnóstico
4. Revisa logs en el directorio `logs/`
EOF

success "Documentación creada: DEPLOYMENT_README.md"

# Resumen final
echo ""
echo "========================================================"
echo "DEPLOYMENT ENTERPRISE COMPLETADO"
echo "========================================================"
echo ""
success "Virtual environment configurado"
success "Dependencias instaladas"
success "Health check ejecutado"
success "Tests ejecutados"
success "Scripts de gestión creados"
success "Documentación generada"
echo ""
warning "SIGUIENTES PASOS:"
echo "1. Edita el archivo .env con tus configuraciones reales"
echo "2. Ejecuta ./check_health.sh para verificar todo está bien"
echo "3. Usa ./start.sh para ejecutar el sistema"
echo "4. Lee DEPLOYMENT_README.md para más información"
echo ""
echo "Sistema listo"
echo "========================================================"
