#!/usr/bin/env python
"""
Script para aplicar optimizaciones al sistema y actualizar dependencias.
Ejecuta este script para mejorar el rendimiento del sistema.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('optimize')

def run_command(command, desc=None):
    """
    Ejecuta un comando de shell y muestra su salida.
    
    Args:
        command: Comando a ejecutar
        desc: Descripción opcional del comando
    
    Returns:
        Código de retorno del comando
    """
    if desc:
        logger.info(f"{desc}...")
        
    logger.debug(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            capture_output=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error (código {result.returncode}): {result.stderr}")
            return result.returncode
            
        logger.debug(f"Salida: {result.stdout}")
        return 0
        
    except Exception as e:
        logger.error(f"Error al ejecutar comando: {e}")
        return 1

def main():
    """Función principal de optimización."""
    start_time = time.time()
    logger.info("Iniciando proceso de optimización del sistema...")
    
    # Obtener directorio raíz del proyecto
    project_root = Path(__file__).parent
    
    # Instalar dependencias actualizadas
    logger.info("Actualizando dependencias...")
    if run_command("pip install -r requirements.txt --upgrade", "Instalando dependencias") != 0:
        logger.error("Error al instalar dependencias. Abortando.")
        return 1
    
    # Verificar instalaciones opcionales
    try:
        import numba
        logger.info("Numba instalado correctamente.")
    except ImportError:
        logger.warning("Numba no se ha instalado. Algunas optimizaciones no estarán disponibles.")
        
    try:
        import dask
        logger.info("Dask instalado correctamente.")
    except ImportError:
        logger.warning("Dask no se ha instalado. Algunas optimizaciones para datos grandes no estarán disponibles.")
    
    # Crear directorios de caché si no existen
    cache_dirs = [
        "data/cache",
        "data/cache/analytics",
        "data/cache/http",
        "data/cache/api",
        "logs"
    ]
    
    for cache_dir in cache_dirs:
        os.makedirs(os.path.join(project_root, cache_dir), exist_ok=True)
        logger.debug(f"Directorio asegurado: {cache_dir}")
    
    # Generar archivo de configuración optimizado si no existe
    config_file = os.path.join(project_root, "config", "config.json")
    if not os.path.exists(config_file):
        config_dir = os.path.join(project_root, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        config_content = """{
    "app": {
        "name": "Fubol - Sistema de Análisis de Fútbol",
        "version": "1.1.0",
        "debug": false,
        "env": "production"
    },
    "logging": {
        "level": "INFO",
        "file": "logs/sistema.log",
        "max_size": 10485760,
        "backup_count": 5
    },
    "database": {
        "type": "sqlite",
        "path": "data/database/fubol.db",
        "pool_size": 5
    },
    "api": {
        "enabled": true,
        "port": 5000,
        "host": "0.0.0.0",
        "cors": true,
        "rate_limit": 100,
        "timeout": 30
    },
    "cache": {
        "enabled": true,
        "expiry": 3600,
        "max_items": 1000
    },
    "optimization": {
        "parallel_workers": 4,
        "use_dask": true,
        "use_numba": true,
        "batch_size": 1000
    },
    "data_sources": {
        "football_data": {
            "enabled": true,
            "api_key": ""
        },
        "espn_api": {
            "enabled": true,
            "base_url": "https://site.api.espn.com"
        },
        "open_football": {
            "enabled": true,
            "base_url": "https://github.com/openfootball/football.json"
        },
        "espn_data": {
            "enabled": true,
            "base_url": "https://www.espn.com/soccer"
        },
        "world_football": {
            "enabled": true,
            "base_url": "https://www.football-data.co.uk/data.php"
        }
    },
    "rate_limits": {
        "football-data.org": [60, 60],
        "api.football-data.org": [10, 60],
        "site.api.espn.com": [20, 60],
        "sports.core.api.espn.com": [20, 60]
    }
}"""
        
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)
            
        logger.info(f"Archivo de configuración generado: {config_file}")
    
    # Crear script de inicialización optimizado
    init_script = os.path.join(project_root, "start_optimized.py")
    init_content = """#!/usr/bin/env python
\"\"\"
Script de inicialización optimizado para la aplicación Fubol.
Este script configura todas las optimizaciones antes de iniciar la app.
\"\"\"

import os
import sys
import logging
from pathlib import Path

# Añadir directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar componentes de optimización
from utils.log_manager import log_manager, configure_exception_hooks
from utils.config_manager import config_manager
from utils.cache_manager import cache_manager
from utils.http_optimizer import http_optimizer
from utils.db_optimizer import db_optimizer
from utils.analytics_optimizer import analytics_optimizer

# Configurar sistema de logs
log_manager.configure(
    console_level='INFO',
    file_level='DEBUG',
    json_logs=True,
    enable_metrics=True
)

# Activar hooks para excepciones no capturadas
configure_exception_hooks()

# Obtener logger
logger = log_manager.get_logger('main')
logger.info("Iniciando sistema optimizado...")

# Inicializar configuración
config_manager.reload()
logger.info(f"Configuración cargada: {len(config_manager.as_dict())} secciones")

# Inicializar caché con parámetros de configuración
cache_expiry = config_manager.get('cache.expiry', 3600)
cache_max_items = config_manager.get('cache.max_items', 1000)
cache_manager.memory_expiry = cache_expiry
cache_manager.max_memory_items = cache_max_items
cache_manager.enabled = config_manager.get('cache.enabled', True)
logger.info(f"Sistema de caché configurado: expiry={cache_expiry}s, max_items={cache_max_items}")

# Configurar HTTP Optimizer
http_optimizer.max_retries = 3
http_optimizer.timeout = config_manager.get('api.timeout', 30)
http_optimizer.max_connections = 10

# Configurar rate limits desde config
rate_limits = config_manager.get('rate_limits', {})
if rate_limits:
    http_optimizer.rate_limit = rate_limits
    logger.info(f"Rate limits configurados para {len(rate_limits)} dominios")

# Configurar DB Optimizer
db_path = config_manager.get('database.path', 'data/database/fubol.db')
db_pool_size = config_manager.get('database.pool_size', 5)

# Configurar Analytics Optimizer
analytics_optimizer.max_workers = config_manager.get('optimization.parallel_workers', 4)
analytics_optimizer.use_dask = config_manager.get('optimization.use_dask', True)
analytics_optimizer.use_numba = config_manager.get('optimization.use_numba', True)

# Ejecutar la aplicación Flask
logger.info("Iniciando aplicación Flask...")
from app import app

if __name__ == '__main__':
    debug = config_manager.get('app.debug', False)
    port = config_manager.get('api.port', 5000)
    host = config_manager.get('api.host', '0.0.0.0')
    
    logger.info(f"Servidor iniciado en http://{host}:{port} (debug={debug})")
    app.run(debug=debug, host=host, port=port)
"""
    
    with open(init_script, "w", encoding="utf-8") as f:
        f.write(init_content)
        
    logger.info(f"Script de inicio optimizado generado: {init_script}")
    
    # Hacerlo ejecutable en entornos Unix
    if os.name != 'nt':
        os.chmod(init_script, 0o755)
    
    # Crear script de diagnóstico del sistema
    diag_script = os.path.join(project_root, "diagnostico_sistema.py")
    diag_content = """#!/usr/bin/env python
\"\"\"
Script para diagnóstico del sistema y optimizaciones.
Ejecuta este script para obtener información sobre el rendimiento del sistema.
\"\"\"

import os
import sys
import time
import platform
import psutil
import logging
from pathlib import Path

# Añadir directorio raíz al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger('diagnostico')

def main():
    \"\"\"Función principal de diagnóstico.\"\"\"
    print("="*70)
    print("DIAGNÓSTICO DEL SISTEMA FUBOL")
    print("="*70)
    
    # Información del sistema
    print("\\nINFORMACIÓN DEL SISTEMA:")
    print(f"- Sistema operativo: {platform.system()} {platform.release()}")
    print(f"- Python: {platform.python_version()} ({platform.python_implementation()})")
    print(f"- CPU: {psutil.cpu_count(logical=True)} núcleos lógicos")
    print(f"- RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    # Información de optimizaciones
    print("\\nCOMPONENTES DE OPTIMIZACIÓN:")
    
    # Verificar componentes
    componentes = {
        'cache_manager': 'Sistema de caché',
        'config_manager': 'Gestor de configuración',
        'log_manager': 'Sistema de logs avanzado',
        'http_optimizer': 'Optimizador HTTP',
        'db_optimizer': 'Optimizador de base de datos',
        'analytics_optimizer': 'Optimizador de análisis'
    }
    
    for module_name, desc in componentes.items():
        try:
            __import__(f"utils.{module_name}")
            print(f"- ✓ {desc} [INSTALADO]")
        except ImportError:
            print(f"- ✗ {desc} [NO INSTALADO]")
    
    # Verificar dependencias opcionales
    print("\\nDEPENDENCIAS OPCIONALES:")
    dependencias = {
        'numba': 'Compilación JIT para cálculos',
        'dask': 'Procesamiento de datos distribuido',
        'aiohttp': 'HTTP asíncrono',
        'yaml': 'Soporte YAML para configuración',
        'orjson': 'Serialización JSON optimizada',
        'line_profiler': 'Profiling de código',
        'memory_profiler': 'Análisis de consumo de memoria'
    }
    
    for dep_name, desc in dependencias.items():
        try:
            __import__(dep_name)
            print(f"- ✓ {dep_name}: {desc} [INSTALADO]")
        except ImportError:
            print(f"- ✗ {dep_name}: {desc} [NO INSTALADO]")
    
    # Verificar configuración
    try:
        from utils.config_manager import config_manager
        config = config_manager.as_dict()
        
        print("\\nCONFIGURACIÓN ACTUAL:")
        print(f"- Caché: {'ACTIVADO' if config.get('cache', {}).get('enabled', False) else 'DESACTIVADO'}")
        print(f"- Modo debug: {'ACTIVADO' if config.get('app', {}).get('debug', False) else 'DESACTIVADO'}")
        print(f"- Trabajadores paralelos: {config.get('optimization', {}).get('parallel_workers', 4)}")
        print(f"- Fuentes de datos: {len(config.get('data_sources', {}))}")
        
        # Verificar fuentes de datos
        print("\\nFUENTES DE DATOS:")
        for source, config in config.get('data_sources', {}).items():
            status = "ACTIVADO" if config.get('enabled', False) else "DESACTIVADO"
            print(f"- {source}: {status}")
            
    except Exception as e:
        print(f"\\nError al leer configuración: {e}")
    
    # Verificar base de datos
    try:
        import sqlite3
        from utils.db_optimizer import db_optimizer
        
        db_path = os.path.join(project_root, "data/database/fubol.db")
        
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024*1024)
            
            print(f"\\nBASE DE DATOS:")
            print(f"- Ruta: {db_path}")
            print(f"- Tamaño: {size_mb:.2f} MB")
            
            # Estadísticas básicas
            try:
                with db_optimizer.connection(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Tablas
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"- Tablas: {len(tables)}")
                    
                    # Algunas estadísticas de tablas importantes
                    tables_to_check = ['equipos', 'jugadores', 'partidos']
                    for table in tables_to_check:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            print(f"  - {table}: {count} registros")
                        except:
                            pass
            except Exception as e:
                print(f"  Error al obtener estadísticas: {e}")
        else:
            print("\\nBASE DE DATOS: No encontrada")
            
    except Exception as e:
        print(f"\\nError al verificar base de datos: {e}")
    
    # Sugerencias
    print("\\nSUGERENCIAS DE OPTIMIZACIÓN:")
    
    try:
        import psutil
        cpu_count = psutil.cpu_count(logical=True)
        
        if cpu_count <= 2:
            print("- Reducir 'parallel_workers' a 2 en config.json para sistemas con pocos núcleos")
            
        ram = psutil.virtual_memory().total / (1024**3)
        if ram < 4:
            print("- Desactivar uso de Dask en config.json para sistemas con poca memoria")
            print("- Reducir 'max_items' de caché a 500 en config.json")
            
        # Verificar tamaño de directorios de caché
        cache_dir = os.path.join(project_root, "data/cache")
        if os.path.exists(cache_dir):
            cache_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                            for dirpath, _, filenames in os.walk(cache_dir)
                            for filename in filenames) / (1024*1024)
                            
            if cache_size > 100:
                print(f"- Directorio de caché ocupa {cache_size:.1f} MB. Considerar limpiarlo.")
    except:
        pass
        
    print("\\nPara iniciar el sistema con todas las optimizaciones, ejecutar:")
    print("python start_optimized.py")
    print("="*70)

if __name__ == "__main__":
    main()
"""
    
    with open(diag_script, "w", encoding="utf-8") as f:
        f.write(diag_content)
        
    logger.info(f"Script de diagnóstico generado: {diag_script}")
    
    # Hacer ejecutable en entornos Unix
    if os.name != 'nt':
        os.chmod(diag_script, 0o755)
    
    # Intenta instalar psutil para el script de diagnóstico
    run_command("pip install psutil", "Instalando dependencia para diagnóstico")
    
    # Mostrar tiempo total
    elapsed_time = time.time() - start_time
    logger.info(f"Proceso de optimización completado en {elapsed_time:.2f} segundos")
    logger.info("")
    logger.info("Para iniciar el sistema optimizado, ejecuta:")
    logger.info("python start_optimized.py")
    logger.info("")
    logger.info("Para ver diagnóstico del sistema, ejecuta:")
    logger.info("python diagnostico_sistema.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
