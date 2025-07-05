#!/usr/bin/env python
"""
Script para finalizar la integración de las optimizaciones en el sistema.
"""

import os
import sys
import logging
import importlib
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finalizar_optimizaciones')

def check_imports():
    """Verifica la disponibilidad de las dependencias necesarias"""
    logger.info("Verificando dependencias...")
    
    dependencies = [
        'dask', 'numba', 'aiohttp', 'requests', 'pandas', 'numpy',
        'flask', 'matplotlib', 'joblib', 'psutil'
    ]
    
    missing = []
    optional = []
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            logger.info(f"OK: {dep}")
        except ImportError:
            if dep in ['dask', 'numba', 'aiohttp', 'joblib']:
                optional.append(dep)
            else:
                missing.append(dep)
    
    if missing:
        logger.error(f"Faltan dependencias requeridas: {', '.join(missing)}")
        logger.error("Por favor, ejecuta: pip install -r requirements.txt")
        return False
        
    if optional:
        logger.warning(f"Algunas dependencias opcionales no están instaladas: {', '.join(optional)}")
        logger.warning("Algunas optimizaciones avanzadas no estarán disponibles")
    
    logger.info("Todas las dependencias requeridas están instaladas correctamente")
    return True

def create_config_dir():
    """Crea el directorio de configuración si no existe"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    logger.info(f"Directorio de configuración: {config_dir}")

def create_start_script():
    """Crea un script de inicio optimizado"""
    start_py = Path("start_optimized.py")
    with open(start_py, "w") as f:
        f.write("""#!/usr/bin/env python
'''
Script para iniciar la aplicación con todas las optimizaciones activadas.
'''
import os
import sys
import logging

# Configurar variables de entorno
os.environ['OPTIMIZE_CACHE'] = 'true'
os.environ['OPTIMIZE_HTTP'] = 'true'
os.environ['OPTIMIZE_DB'] = 'true'
os.environ['OPTIMIZE_LOGGING'] = 'true'
os.environ['OPTIMIZE_ANALYTICS'] = 'true'

from utils.config_manager import ConfigManager
from utils.log_manager import LogManager

# Cargar configuraciones
config_manager = ConfigManager(config_dir="config")
log_manager = LogManager(config=config_manager)

logger = logging.getLogger('startup')
logger.info("Iniciando aplicación con optimizaciones")

# Importar y ejecutar app
try:
    from app import app
    
    # Configurar modo de ejecución
    debug = config_manager.get("app.debug", default=False)
    port = config_manager.get("app.port", default=5000)
    
    logger.info(f"Iniciando servidor en http://127.0.0.1:{port} (Debug: {debug})")
    app.run(debug=debug, port=port, threaded=True)
    
except Exception as e:
    logger.error(f"Error al iniciar la aplicación: {e}")
    sys.exit(1)
""")
    logger.info(f"Script de inicio optimizado creado: {start_py}")

def create_diagnostic_script():
    """Crea un script de diagnóstico simplificado"""
    diag_py = Path("diagnostico_sistema.py")
    with open(diag_py, "w") as f:
        f.write("""#!/usr/bin/env python
'''
Script para diagnosticar el estado del sistema optimizado.
'''
import os
import sys
import logging
import importlib
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('diagnostico')

def verificar_modulos_optimizacion():
    '''Verifica que todos los módulos de optimización estén presentes'''
    modulos = [
        'utils/cache_manager.py',
        'utils/http_optimizer.py',
        'utils/db_optimizer.py',
        'utils/log_manager.py',
        'utils/config_manager.py',
        'utils/analytics_optimizer.py'
    ]
    
    for modulo in modulos:
        if Path(modulo).exists():
            logger.info(f"OK: {modulo}")
        else:
            logger.error(f"ERROR: {modulo} no existe")
    
    # Verificar scripts
    scripts = ['start_optimized.py']
    for script in scripts:
        if Path(script).exists():
            logger.info(f"OK: {script}")
        else:
            logger.error(f"ERROR: {script} no existe")

def verificar_integracion():
    '''Verifica la integración de los optimizadores en los archivos clave'''
    archivos = {
        'app.py': ['CacheManager', 'HTTPOptimizer', 'DBOptimizer', 'ConfigManager'],
        'utils/unified_data_adapter.py': ['CacheManager', 'HTTPOptimizer', 'DBOptimizer']
    }
    
    for archivo, componentes in archivos.items():
        if not Path(archivo).exists():
            logger.error(f"✗ {archivo} no existe")
            continue
            
        with open(archivo, 'r') as f:
            contenido = f.read()
            
        for componente in componentes:
            if componente in contenido:
                logger.info(f"OK: {archivo}: {componente} integrado")
            else:
                logger.warning(f"ERROR: {archivo}: {componente} no integrado")

def main():
    '''Función principal'''
    logger.info("Iniciando diagnóstico del sistema...")
    verificar_modulos_optimizacion()
    verificar_integracion()
    logger.info("Diagnóstico completado")

if __name__ == "__main__":
    main()
""")
    logger.info(f"Script de diagnóstico creado: {diag_py}")

def main():
    """Función principal"""
    logger.info("Iniciando finalización de optimizaciones...")
    
    # Verificar dependencias
    if not check_imports():
        return
    
    # Crear directorio de configuración
    create_config_dir()
    
    # Crear script de inicio optimizado
    create_start_script()
    
    # Crear script de diagnóstico
    create_diagnostic_script()
    
    # Verificar directorios importantes
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directorio de caché: {cache_dir}")
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"Directorio de logs: {logs_dir}")
    
    logger.info("Optimizaciones finalizadas correctamente.")
    logger.info("Para iniciar la aplicación optimizada, ejecute:")
    logger.info("  python start_optimized.py")
    logger.info("Para ejecutar un diagnóstico, ejecute:")
    logger.info("  python diagnostico_sistema.py")

if __name__ == "__main__":
    main()
