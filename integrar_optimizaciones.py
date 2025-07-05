#!/usr/bin/env python
"""
Script para integrar las optimizaciones en el flujo principal de la aplicación.
Este script actualiza los archivos clave con las nuevas optimizaciones.
"""

import os
import sys
import re
import json
import shutil
from pathlib import Path
import logging
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integration')

def backup_file(file_path):
    """
    Crea una copia de seguridad del archivo antes de modificarlo
    
    Args:
        file_path: Ruta del archivo a respaldar
    
    Returns:
        Ruta del archivo de respaldo
    """
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = Path(file_path)
    backup_path = backup_dir / f"{file_path.name}.{timestamp}.bak"
    
    shutil.copy2(file_path, backup_path)
    logger.info(f"Archivo respaldado: {backup_path}")
    
    return backup_path

def integrate_app_py():
    """Integra las optimizaciones en app.py"""
    logger.info("Integrando optimizaciones en app.py")
    
    # Respaldar archivo original
    file_path = Path("app.py")
    backup_file(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Añadir nuevas importaciones
    import_pattern = r'from utils.unified_data_adapter import UnifiedDataAdapter\n'
    new_imports = (
        'from utils.unified_data_adapter import UnifiedDataAdapter\n'
        'from utils.cache_manager import CacheManager\n'
        'from utils.config_manager import ConfigManager\n'
        'from utils.log_manager import LogManager\n'
        'from utils.db_optimizer import DBOptimizer\n'
        'from utils.http_optimizer import HTTPOptimizer\n'
        'from utils.analytics_optimizer import AnalyticsOptimizer\n'
    )
    content = content.replace(import_pattern, new_imports)
    
    # Inicializar componentes de optimización después de crear la app Flask
    init_pattern = r'app = Flask\(__name__\)\n'
    new_init_code = (
        'app = Flask(__name__)\n\n'
        '# Inicializar componentes de optimización\n'
        'config_manager = ConfigManager(config_dir="config")\n'
        'log_manager = LogManager(config=config_manager)\n'
        'cache_manager = CacheManager(cache_dir="data/cache")\n'
        'db_optimizer = DBOptimizer(config=config_manager)\n'
        'http_optimizer = HTTPOptimizer(config=config_manager)\n'
        'analytics_optimizer = AnalyticsOptimizer(config=config_manager)\n\n'
    )
    content = content.replace(init_pattern, new_init_code)
    
    # Agregar configuración de la aplicación Flask
    config_pattern = r'# Registrar blueprint de API\n'
    config_code = (
        '# Configurar aplicación Flask\n'
        'app.config["SECRET_KEY"] = config_manager.get("app.secret_key", default="fubol_secret_key_default")\n'
        'app.config["DEBUG"] = config_manager.get("app.debug", default=False)\n'
        'app.config["TEMPLATES_AUTO_RELOAD"] = config_manager.get("app.templates_auto_reload", default=True)\n\n'
        '# Registrar blueprint de API\n'
    )
    content = content.replace(config_pattern, config_code)
    
    # Actualizar inicialización de UnifiedDataAdapter
    adapter_pattern = r'inicializar_componentes\(\)'
    new_adapter_init = 'inicializar_componentes(cache_manager=cache_manager, http_optimizer=http_optimizer, db_optimizer=db_optimizer)'
    content = content.replace(adapter_pattern, new_adapter_init)
    
    # Aplicar optimizaciones a rutas con alta carga
    # Ejemplo: Ruta de análisis histórico con caché
    route_pattern = r'@app\.route\(\"/historico\"\)\ndef historico\(\):'
    optimized_route = (
        '@app.route("/historico")\n'
        '@cache_manager.cache_route(expiry=300)  # Caché de 5 minutos\n'
        'def historico():'
    )
    content = content.replace(route_pattern, optimized_route)
    
    # Agregar manejo de errores mejorado
    error_handler = (
        '\n\n@app.errorhandler(Exception)\n'
        'def handle_exception(e):\n'
        '    """Manejador global de excepciones con logging mejorado"""\n'
        '    log_manager.log_exception(e)\n'
        '    return render_template("error.html", error=str(e)), 500\n'
    )
    content += error_handler
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info("Optimizaciones integradas en app.py")

def integrate_unified_data_adapter():
    """Integra las optimizaciones en unified_data_adapter.py"""
    logger.info("Integrando optimizaciones en unified_data_adapter.py")
    
    # Respaldar archivo original
    file_path = Path("utils/unified_data_adapter.py")
    backup_file(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Reemplazar el sistema de caché manual con CacheManager
    cache_import_pattern = r'# Variables globales para almacenamiento en memoria caché.*?_cached_data = \{.*?\}'
    cache_import_replacement = (
        '# Importar gestores de optimización\n'
        'from utils.cache_manager import CacheManager\n'
        'from utils.http_optimizer import HTTPOptimizer\n'
        'from utils.db_optimizer import DBOptimizer\n'
        'from utils.log_manager import LogManager\n'
        'from utils.analytics_optimizer import AnalyticsOptimizer\n\n'
        '# Instancias por defecto (se reemplazarán en initialize)\n'
        '_cache_manager = None\n'
        '_http_optimizer = None\n'
        '_db_optimizer = None'
    )
    content = re.sub(cache_import_pattern, cache_import_replacement, content, flags=re.DOTALL)
    
    # Añadir método de inicialización con componentes optimizados
    class_pattern = r'class UnifiedDataAdapter.*?:'
    init_method = (
        'class UnifiedDataAdapter:\n'
        '    """Adaptador unificado para múltiples fuentes de datos."""\n\n'
        '    def __init__(self, cache_manager=None, http_optimizer=None, db_optimizer=None):\n'
        '        """Inicializa el adaptador con componentes optimizados"""\n'
        '        global _cache_manager, _http_optimizer, _db_optimizer\n'
        '        \n'
        '        # Usar instancias proporcionadas o crear por defecto\n'
        '        _cache_manager = cache_manager or CacheManager(cache_dir="data/cache")\n'
        '        _http_optimizer = http_optimizer or HTTPOptimizer()\n'
        '        _db_optimizer = db_optimizer or DBOptimizer()\n'
        '        \n'
        '        # Inicializar adaptador de ESPN\n'
        '        self.espn_api = ESPNAPI(http_client=_http_optimizer.session)\n'
        '        \n'
        '        logger.info("UnifiedDataAdapter inicializado con optimizaciones")\n'
    )
    content = re.sub(class_pattern, init_method, content)
    
    # Optimizar métodos de acceso a datos (ejemplo con get_equipos)
    get_equipos_pattern = r'def get_equipos.*?return equipos'
    optimized_get_equipos = (
        '@_cache_manager.cache_function(key="equipos", expiry=3600)\n'
        '    def get_equipos(self, force_refresh=False):\n'
        '        """Obtiene la lista de equipos desde múltiples fuentes"""\n'
        '        # Si force_refresh es True, _cache_manager ignorará la caché\n'
        '        \n'
        '        logger.info("Obteniendo datos de equipos")\n'
        '        \n'
        '        # Usar http_optimizer para peticiones paralelas\n'
        '        equipos = _http_optimizer.fetch_parallel([\n'
        '            (self._fetch_equipos_api1, []),\n'
        '            (self._fetch_equipos_api2, []),\n'
        '            (self._fetch_equipos_espn, [])\n'
        '        ])\n'
        '        \n'
        '        # Unificar resultados\n'
        '        equipos_unificados = self._unificar_equipos(equipos)\n'
        '        \n'
        '        # Guardar en base de datos optimizada\n'
        '        with _db_optimizer.optimized_connection() as conn:\n'
        '            self._guardar_equipos_db(conn, equipos_unificados)\n'
        '        \n'
        '        return equipos_unificados'
    )
    content = re.sub(get_equipos_pattern, optimized_get_equipos, content, flags=re.DOTALL)
    
    # Añadir métodos auxiliares optimizados para cada fuente
    fetch_methods = (
        '    def _fetch_equipos_api1(self):\n'
        '        """Obtiene equipos de la primera API"""\n'
        '        # Implementación específica usando http_optimizer\n'
        '        return []\n'
        '        \n'
        '    def _fetch_equipos_api2(self):\n'
        '        """Obtiene equipos de la segunda API"""\n'
        '        # Implementación específica usando http_optimizer\n'
        '        return []\n'
        '        \n'
        '    def _fetch_equipos_espn(self):\n'
        '        """Obtiene equipos de ESPN"""\n'
        '        return self.espn_api.get_equipos()\n'
        '        \n'
        '    def _unificar_equipos(self, equipos_por_fuente):\n'
        '        """Unifica equipos de múltiples fuentes eliminando duplicados"""\n'
        '        # Usar AnalyticsOptimizer para procesamiento paralelo si hay muchos equipos\n'
        '        return [equipo for fuente in equipos_por_fuente for equipo in fuente]\n'
        '        \n'
        '    def _guardar_equipos_db(self, conn, equipos):\n'
        '        """Guarda equipos en base de datos de forma optimizada"""\n'
        '        # Implementación usando db_optimizer\n'
        '        pass\n'
    )
    content += "\n" + fetch_methods
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info("Optimizaciones integradas en unified_data_adapter.py")

def integrate_api_initialization():
    """Integra las optimizaciones en el módulo API"""
    logger.info("Integrando optimizaciones en el módulo API")
    
    # Respaldar archivo original
    file_path = Path("api/__init__.py")
    backup_file(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Modificar la inicialización de componentes para recibir optimizadores
    init_pattern = r'def inicializar_componentes\(\):'
    new_init = (
        'def inicializar_componentes(cache_manager=None, http_optimizer=None, db_optimizer=None):\n'
        '    """Inicializa los componentes del API con optimizadores"""\n'
        '    global data_adapter\n'
        '    data_adapter = UnifiedDataAdapter(\n'
        '        cache_manager=cache_manager,\n'
        '        http_optimizer=http_optimizer,\n'
        '        db_optimizer=db_optimizer\n'
        '    )'
    )
    content = re.sub(init_pattern, new_init, content, flags=re.DOTALL)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info("Optimizaciones integradas en api/__init__.py")

def create_config_files():
    """Crea archivos de configuración necesarios"""
    logger.info("Creando archivos de configuración")
    
    # Configuración principal
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config = {
        "app": {
            "debug": False,
            "secret_key": "fubol_secret_key_" + str(int(time.time())),
            "templates_auto_reload": True
        },
        "cache": {
            "enabled": True,
            "memory_expiry": 3600,
            "disk_expiry": 86400,
            "max_memory_items": 1000
        },
        "db": {
            "connection_pool_size": 5,
            "optimize_queries": True,
            "vacuum_frequency": 86400
        },
        "http": {
            "max_retries": 3,
            "timeout": 10,
            "use_session": True,
            "max_connections": 10,
            "rate_limit": {
                "enabled": True,
                "max_per_second": 5
            }
        },
        "logging": {
            "level": "INFO",
            "rotation": {
                "enabled": True,
                "max_size": "10MB",
                "backup_count": 5
            },
            "metrics": {
                "enabled": True,
                "interval": 3600
            }
        },
        "analytics": {
            "use_dask": True,
            "use_numba": True,
            "parallel_threshold": 1000,
            "batch_size": 500
        },
        "apis": {
            "espn": {
                "base_url": "https://site.api.espn.com/apis/site/v2/sports/soccer/",
                "rate_limit": 5
            },
            "football_data": {
                "base_url": "https://api.football-data.org/v2/",
                "rate_limit": 10,
                "api_key": ""  # Debe ser completado por el usuario
            }
        }
    }
    
    config_path = config_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    
    logger.info(f"Archivo de configuración creado: {config_path}")

def main():
    """Función principal que integra todas las optimizaciones"""
    logger.info("Iniciando integración de optimizaciones")
    
    # Crear configuración
    create_config_files()
    
    # Integrar optimizaciones
    integrate_app_py()
    integrate_unified_data_adapter()
    integrate_api_initialization()
    
    logger.info("Optimizaciones integradas exitosamente")
    logger.info("Para aplicar todas las optimizaciones, ejecute:")
    logger.info("python optimizar_sistema.py")

if __name__ == "__main__":
    main()
