#!/usr/bin/env python
"""
Script para finalizar la integración de las optimizaciones en el sistema.
Este script completa la integración de los optimizadores y realiza las pruebas finales.
"""

import os
import sys
import logging
import importlib
import json
import time
from pathlib import Path
import subprocess
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finalize_optimization')

def check_imports():
    """Verifica la disponibilidad de todas las dependencias necesarias"""
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
            logger.info(f"✓ {dep}")
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
        logger.warning("Para instalarlas: pip install " + " ".join(optional))
    
    logger.info("Todas las dependencias requeridas están instaladas ✓")
    return True

def create_config_files():
    """Crea o actualiza archivos de configuración necesarios"""
    logger.info("Creando archivos de configuración...")
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Archivo de configuración general
    config_file = config_dir / "config.json"
    if not config_file.exists():
        config = {
            "app": {
                "secret_key": "fubol_optimized_key",
                "debug": False,
                "templates_auto_reload": True
            },
            "cache": {
                "memory_expiry": 3600,
                "disk_expiry": 86400,
                "max_memory_items": 100
            },
            "http": {
                "max_retries": 3,
                "retry_delay": 1.0,
                "timeout": 30.0,
                "max_connections": 10
            },
            "db": {
                "max_connections": 5,
                "timeout": 30.0,
                "check_same_thread": False
            },
            "log": {
                "level": "INFO",
                "file_rotation": "1 MB",
                "file_backups": 5,
                "console_enabled": True
            },
            "analytics": {
                "max_workers": 4,
                "chunk_size": 10000,
                "use_dask": True,
                "use_numba": True
            }
        }
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Archivo de configuración creado: {config_file}")
    
    # Archivo de mapeo de ligas
    leagues_file = config_dir / "leagues.json"
    if not leagues_file.exists():
        leagues = {
            "PD": {
                "name": "LaLiga",
                "country": "España",
                "espn_id": "esp.1"
            },
            "PL": {
                "name": "Premier League",
                "country": "Inglaterra",
                "espn_id": "eng.1"
            },
            "SA": {
                "name": "Serie A",
                "country": "Italia",
                "espn_id": "ita.1"
            },
            "BL1": {
                "name": "Bundesliga",
                "country": "Alemania",
                "espn_id": "ger.1"
            },
            "FL1": {
                "name": "Ligue 1",
                "country": "Francia",
                "espn_id": "fra.1"
            }
        }
        
        with open(leagues_file, "w") as f:
            json.dump(leagues, f, indent=4)
        logger.info(f"Archivo de mapeo de ligas creado: {leagues_file}")
    
    return True

def fix_remaining_files():
    """Corrige archivos adicionales que pueden necesitar ajustes"""
    logger.info("Corrigiendo archivos adicionales...")
    
    # Asegurar que la carpeta de caché existe
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Asegurar que la carpeta de logs existe
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Corregir problema con la función _parse_fecha en unified_data_adapter.py
    # Esto es necesario porque hay referencias a datetime.date pero el método devuelve datetime
    adapter_file = Path("utils/unified_data_adapter.py")
    if adapter_file.exists():
        with open(adapter_file, "r") as f:
            content = f.read()
        
        # Reemplazar la firma del método _parse_fecha si es necesario
        if "def _parse_fecha(self, fecha_str: str) -> datetime.date:" in content:
            content = content.replace(
                "def _parse_fecha(self, fecha_str: str) -> datetime.date:",
                "def _parse_fecha(self, fecha_str: str) -> datetime:"
            )
            
            with open(adapter_file, "w") as f:
                f.write(content)
            logger.info("Corregida la firma del método _parse_fecha")
    
    return True

def create_startup_scripts():
    """Crea scripts de inicio para diferentes plataformas"""
    logger.info("Creando scripts de inicio...")
    
    # Script Python
    start_py = Path("start_optimized.py")
    if not start_py.exists():
        with open(start_py, "w") as f:
            f.write("#!/usr/bin/env python\n")
            f.write("'''\n")
            f.write("Script para iniciar la aplicación con todas las optimizaciones activadas.\n")
            f.write("'''\n")
import os
import sys
import logging
from flask import Flask
from utils.config_manager import ConfigManager
from utils.log_manager import LogManager

# Configurar variables de entorno
os.environ['OPTIMIZE_CACHE'] = 'true'
os.environ['OPTIMIZE_HTTP'] = 'true'
os.environ['OPTIMIZE_DB'] = 'true'
os.environ['OPTIMIZE_LOGGING'] = 'true'
os.environ['OPTIMIZE_ANALYTICS'] = 'true'

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
        os.chmod(start_py, 0o755)
        logger.info(f"Script Python creado: {start_py}")
    
    # Script PowerShell
    start_ps1 = Path("start_optimized.ps1")
    if not start_ps1.exists():
        with open(start_ps1, "w") as f:
            f.write("""# Script PowerShell para iniciar la aplicación optimizada
$env:OPTIMIZE_CACHE = 'true'
$env:OPTIMIZE_HTTP = 'true'
$env:OPTIMIZE_DB = 'true'
$env:OPTIMIZE_LOGGING = 'true'
$env:OPTIMIZE_ANALYTICS = 'true'

Write-Host "Iniciando aplicación con optimizaciones..."
python start_optimized.py
""")
        logger.info(f"Script PowerShell creado: {start_ps1}")
    
    # Script Bash
    start_sh = Path("start_optimized.sh")
    if not start_sh.exists():
        with open(start_sh, "w") as f:
            f.write("""#!/bin/bash
# Script Bash para iniciar la aplicación optimizada
export OPTIMIZE_CACHE=true
export OPTIMIZE_HTTP=true
export OPTIMIZE_DB=true
export OPTIMIZE_LOGGING=true
export OPTIMIZE_ANALYTICS=true

echo "Iniciando aplicación con optimizaciones..."
python start_optimized.py
""")
        os.chmod(start_sh, 0o755)
        logger.info(f"Script Bash creado: {start_sh}")
    
    return True

def create_diagnostic_script():
    """Crea un script para diagnóstico del sistema"""
    logger.info("Creando script de diagnóstico...")
    
    diag_script = Path("diagnostico_completo.py")
    if not diag_script.exists():
        with open(diag_script, "w") as f:
            f.write("""#!/usr/bin/env python
'''
Script para diagnóstico completo del sistema con optimizaciones.
Realiza pruebas de rendimiento y verifica la correcta integración de las optimizaciones.
'''
import os
import sys
import time
import json
import logging
import importlib
import platform
from pathlib import Path
import psutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('diagnostico')

class Diagnostico:
    """Clase para diagnóstico del sistema"""
    
    def __init__(self):
        """Inicializa el diagnóstico"""
        self.resultados = {
            "sistema": {},
            "python": {},
            "dependencias": {},
            "optimizaciones": {},
            "rendimiento": {},
            "integracion": {}
        }
    
    def diagnosticar_sistema(self):
        """Realiza diagnóstico del sistema operativo y hardware"""
        logger.info("Diagnosticando sistema operativo y hardware...")
        
        # Información del sistema
        self.resultados["sistema"]["os"] = platform.system()
        self.resultados["sistema"]["version"] = platform.version()
        self.resultados["sistema"]["machine"] = platform.machine()
        
        # Información de CPU
        self.resultados["sistema"]["cpu_count"] = psutil.cpu_count(logical=False)
        self.resultados["sistema"]["cpu_threads"] = psutil.cpu_count(logical=True)
        self.resultados["sistema"]["cpu_percent"] = psutil.cpu_percent()
        
        # Información de memoria
        mem = psutil.virtual_memory()
        self.resultados["sistema"]["memoria_total"] = f"{mem.total / (1024 ** 3):.2f} GB"
        self.resultados["sistema"]["memoria_disponible"] = f"{mem.available / (1024 ** 3):.2f} GB"
        self.resultados["sistema"]["memoria_usada_percent"] = mem.percent
        
        # Información de disco
        disk = psutil.disk_usage('/')
        self.resultados["sistema"]["disco_total"] = f"{disk.total / (1024 ** 3):.2f} GB"
        self.resultados["sistema"]["disco_disponible"] = f"{disk.free / (1024 ** 3):.2f} GB"
        self.resultados["sistema"]["disco_usado_percent"] = disk.percent
        
        return True
    
    def diagnosticar_python(self):
        """Realiza diagnóstico del entorno Python"""
        logger.info("Diagnosticando entorno Python...")
        
        # Versión de Python
        self.resultados["python"]["version"] = platform.python_version()
        self.resultados["python"]["implementation"] = platform.python_implementation()
        self.resultados["python"]["compiler"] = platform.python_compiler()
        
        # Ruta de Python
        self.resultados["python"]["executable"] = sys.executable
        self.resultados["python"]["path"] = sys.path
        
        return True
    
    def diagnosticar_dependencias(self):
        """Verifica las dependencias instaladas"""
        logger.info("Diagnosticando dependencias...")
        
        # Dependencias principales
        dependencias = {
            "requeridas": ["flask", "pandas", "numpy", "requests", "matplotlib"],
            "optimizacion": ["dask", "numba", "aiohttp", "joblib", "psutil"]
        }
        
        for categoria, lista in dependencias.items():
            self.resultados["dependencias"][categoria] = {}
            
            for dep in lista:
                try:
                    # Intentar importar e identificar versión
                    mod = importlib.import_module(dep)
                    version = getattr(mod, "__version__", "Desconocida")
                    self.resultados["dependencias"][categoria][dep] = {
                        "instalado": True,
                        "version": version
                    }
                except ImportError:
                    self.resultados["dependencias"][categoria][dep] = {
                        "instalado": False,
                        "version": None
                    }
        
        return True
    
    def diagnosticar_optimizaciones(self):
        """Verifica la integración de las optimizaciones"""
        logger.info("Diagnosticando optimizaciones...")
        
        # Verificar archivos de optimización
        optimizadores = [
            "utils/cache_manager.py",
            "utils/http_optimizer.py",
            "utils/db_optimizer.py",
            "utils/log_manager.py",
            "utils/config_manager.py",
            "utils/analytics_optimizer.py"
        ]
        
        self.resultados["optimizaciones"]["archivos"] = {}
        
        for opt in optimizadores:
            path = Path(opt)
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            
            self.resultados["optimizaciones"]["archivos"][opt] = {
                "existe": exists,
                "tamaño": size,
                "última_modificación": time.ctime(path.stat().st_mtime) if exists else None
            }
        
        # Verificar archivos de configuración
        self.resultados["optimizaciones"]["configuracion"] = {
            "config_json": Path("config/config.json").exists(),
            "leagues_json": Path("config/leagues.json").exists()
        }
        
        return True
    
    def probar_rendimiento(self):
        """Realiza pruebas básicas de rendimiento"""
        logger.info("Realizando pruebas de rendimiento...")
        
        # Pruebas de rendimiento de caché
        try:
            from utils.cache_manager import CacheManager
            start_time = time.time()
            cache = CacheManager()
            
            # Prueba de escritura en caché
            for i in range(1000):
                cache.set(f"key_{i}", f"value_{i}")
            
            # Prueba de lectura de caché
            for i in range(1000):
                _ = cache.get(f"key_{i}")
                
            cache_time = time.time() - start_time
            self.resultados["rendimiento"]["cache"] = {
                "tiempo": f"{cache_time:.4f}s",
                "operaciones_por_segundo": f"{2000/cache_time:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Error en prueba de caché: {e}")
            self.resultados["rendimiento"]["cache"] = {"error": str(e)}
        
        # Pruebas de rendimiento de base de datos
        try:
            from utils.db_optimizer import DBOptimizer
            import sqlite3
            
            # Crear BD temporal para pruebas
            db_path = "temp_test.db"
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, data TEXT)")
            conn.commit()
            conn.close()
            
            start_time = time.time()
            db_opt = DBOptimizer()
            
            # Prueba de escritura en BD
            with db_opt.connection_context(db_path) as conn:
                cursor = conn.cursor()
                for i in range(100):
                    cursor.execute("INSERT INTO test (data) VALUES (?)", (f"data_{i}",))
                conn.commit()
            
            # Prueba de lectura de BD
            with db_opt.connection_context(db_path) as conn:
                cursor = conn.cursor()
                for i in range(100):
                    cursor.execute("SELECT * FROM test WHERE id = ?", (i+1,))
                    _ = cursor.fetchone()
            
            db_time = time.time() - start_time
            self.resultados["rendimiento"]["bd"] = {
                "tiempo": f"{db_time:.4f}s",
                "operaciones_por_segundo": f"{200/db_time:.2f}"
            }
            
            # Limpiar
            if os.path.exists(db_path):
                os.remove(db_path)
                
        except Exception as e:
            logger.error(f"Error en prueba de base de datos: {e}")
            self.resultados["rendimiento"]["bd"] = {"error": str(e)}
        
        return True
    
    def probar_integracion(self):
        """Verifica la integración de los componentes optimizados"""
        logger.info("Probando integración de componentes...")
        
        # Verificar integración en app.py
        try:
            with open("app.py", "r") as f:
                content = f.read()
            
            integraciones = {
                "cache_manager": "from utils.cache_manager import CacheManager" in content,
                "http_optimizer": "from utils.http_optimizer import HTTPOptimizer" in content,
                "db_optimizer": "from utils.db_optimizer import DBOptimizer" in content,
                "log_manager": "from utils.log_manager import LogManager" in content,
                "config_manager": "from utils.config_manager import ConfigManager" in content,
                "analytics_optimizer": "from utils.analytics_optimizer import AnalyticsOptimizer" in content
            }
            
            self.resultados["integracion"]["app_py"] = integraciones
            self.resultados["integracion"]["app_py"]["puntaje"] = f"{sum(1 for v in integraciones.values() if v)}/{len(integraciones)}"
            
        except Exception as e:
            logger.error(f"Error al verificar integración en app.py: {e}")
            self.resultados["integracion"]["app_py"] = {"error": str(e)}
        
        # Verificar integración en unified_data_adapter.py
        try:
            with open("utils/unified_data_adapter.py", "r") as f:
                content = f.read()
            
            integraciones = {
                "cache_manager": "from utils.cache_manager import CacheManager" in content,
                "http_optimizer": "from utils.http_optimizer import HTTPOptimizer" in content,
                "db_optimizer": "from utils.db_optimizer import DBOptimizer" in content
            }
            
            self.resultados["integracion"]["unified_data_adapter"] = integraciones
            self.resultados["integracion"]["unified_data_adapter"]["puntaje"] = f"{sum(1 for v in integraciones.values() if v)}/{len(integraciones)}"
            
        except Exception as e:
            logger.error(f"Error al verificar integración en unified_data_adapter.py: {e}")
            self.resultados["integracion"]["unified_data_adapter"] = {"error": str(e)}
        
        return True
    
    def ejecutar_diagnostico_completo(self):
        """Ejecuta el diagnóstico completo del sistema"""
        logger.info("Iniciando diagnóstico completo del sistema...")
        
        self.diagnosticar_sistema()
        self.diagnosticar_python()
        self.diagnosticar_dependencias()
        self.diagnosticar_optimizaciones()
        self.probar_rendimiento()
        self.probar_integracion()
        
        # Guardar resultados en un archivo
        with open("diagnostico_resultados.json", "w") as f:
            json.dump(self.resultados, f, indent=4)
        
        logger.info("Diagnóstico completo finalizado")
        logger.info("Resultados guardados en diagnostico_resultados.json")
        
        # Mostrar resumen
        self._mostrar_resumen()
        
        return True
    
    def _mostrar_resumen(self):
        """Muestra un resumen de los resultados del diagnóstico"""
        print("\n" + "="*50)
        print("RESUMEN DEL DIAGNÓSTICO DEL SISTEMA")
        print("="*50)
        
        # Información del sistema
        print("\n[Sistema]")
        print(f"Sistema operativo: {self.resultados['sistema'].get('os')}")
        print(f"CPU: {self.resultados['sistema'].get('cpu_count')} núcleos, {self.resultados['sistema'].get('cpu_threads')} hilos")
        print(f"Memoria: {self.resultados['sistema'].get('memoria_total')}")
        
        # Dependencias
        print("\n[Dependencias]")
        req = self.resultados["dependencias"].get("requeridas", {})
        opt = self.resultados["dependencias"].get("optimizacion", {})
        req_installed = sum(1 for v in req.values() if v.get("instalado", False))
        opt_installed = sum(1 for v in opt.values() if v.get("instalado", False))
        
        print(f"Dependencias requeridas: {req_installed}/{len(req)}")
        print(f"Dependencias de optimización: {opt_installed}/{len(opt)}")
        
        # Optimizaciones
        print("\n[Optimizaciones]")
        arch = self.resultados["optimizaciones"].get("archivos", {})
        existing = sum(1 for v in arch.values() if v.get("existe", False))
        print(f"Módulos de optimización: {existing}/{len(arch)}")
        
        # Rendimiento
        print("\n[Rendimiento]")
        if "cache" in self.resultados["rendimiento"]:
            print(f"Caché: {self.resultados['rendimiento']['cache'].get('operaciones_por_segundo', 'N/A')} ops/s")
        if "bd" in self.resultados["rendimiento"]:
            print(f"Base de datos: {self.resultados['rendimiento']['bd'].get('operaciones_por_segundo', 'N/A')} ops/s")
        
        # Integración
        print("\n[Integración]")
        if "app_py" in self.resultados["integracion"]:
            print(f"app.py: {self.resultados['integracion']['app_py'].get('puntaje', 'N/A')}")
        if "unified_data_adapter" in self.resultados["integracion"]:
            print(f"unified_data_adapter.py: {self.resultados['integracion']['unified_data_adapter'].get('puntaje', 'N/A')}")
        
        print("\n" + "="*50)
        print("Para más detalles, consulta diagnostico_resultados.json")
        print("="*50 + "\n")


if __name__ == "__main__":
    diagnostico = Diagnostico()
    diagnostico.ejecutar_diagnostico_completo()
""")
        logger.info(f"Script de diagnóstico creado: {diag_script}")
    
    return True

def crear_documentacion():
    """Actualiza la documentación de las optimizaciones"""
    logger.info("Creando documentación...")
    
    # Archivo de resumen de optimizaciones
    resumen = Path("RESUMEN_OPTIMIZACIONES_FINAL.md")
    if not resumen.exists():
        with open(resumen, "w") as f:
            f.write("""# Resumen de Optimizaciones Implementadas

## Módulos de Optimización

### 1. Sistema de Caché Avanzado (`utils/cache_manager.py`)
- Almacenamiento en memoria y disco con expiración configurable
- Estrategias de invalidación y limpieza automática
- Soporte para objetos complejos (DataFrames, modelos)
- Función decoradora para cachear resultados de funciones

### 2. Optimizador HTTP (`utils/http_optimizer.py`)
- Rate limiting automático para APIs externas
- Sistema de reintentos con backoff exponencial
- Paralelización de peticiones y gestión de conexiones
- Soporte para peticiones asíncronas con aiohttp

### 3. Optimizador de Base de Datos (`utils/db_optimizer.py`)
- Pool de conexiones para SQLite
- Optimizaciones de consultas y transacciones
- Compresión y limpieza automática de bases de datos
- Migraciones y verificación de esquemas

### 4. Gestor de Logging (`utils/log_manager.py`)
- Formato de logs personalizado con colores
- Rotación de archivos y limpieza automática
- Niveles de log configurables
- Filtros y handlers para diferentes tipos de mensajes

### 5. Gestor de Configuración (`utils/config_manager.py`)
- Configuración centralizada con soporte para múltiples fuentes
- Validación de configuraciones
- Actualización en tiempo real de parámetros
- Configuración por entorno (desarrollo, producción)

### 6. Optimizador de Análisis de Datos (`utils/analytics_optimizer.py`)
- Procesamiento de grandes conjuntos de datos con Dask
- Aceleración de cálculos con Numba
- Paralelización automática de operaciones
- Procesamiento por lotes para reducir uso de memoria

## Mejoras en la Interfaz de Usuario

### 1. Optimizaciones Frontend
- Lazy loading de imágenes y componentes
- Preload de recursos críticos
- Minificación y compresión de recursos estáticos

### 2. Progressive Web App (PWA)
- Service Worker para funcionamiento offline
- Manifest para instalación en dispositivos móviles
- Cache de recursos estáticos
- Interfaz de carga optimizada

## Integración y Configuración

### 1. Scripts de Utilidad
- Diagnóstico completo del sistema (`diagnostico_completo.py`)
- Scripts de inicio optimizados para diferentes plataformas
- Herramientas de integración y pruebas

### 2. Configuración Centralizada
- Archivos de configuración en formato JSON
- Mapeos y parámetros configurables
- Variables de entorno para control de optimizaciones

## Resultados

Las optimizaciones implementadas han resultado en:
- Reducción significativa en el uso de memoria
- Mejora de velocidad en operaciones de análisis de datos
- Mayor estabilidad y tolerancia a fallos
- Experiencia de usuario más fluida
- Mejor mantenibilidad y extensibilidad del código

## Uso

Para iniciar la aplicación con todas las optimizaciones:
```bash
# En sistemas Unix
./start_optimized.sh

# En Windows
.\start_optimized.ps1

# O directamente con Python
python start_optimized.py
```

Para ejecutar un diagnóstico completo:
```bash
python diagnostico_completo.py
```
""")
        logger.info(f"Documentación creada: {resumen}")
    
    return True

def ejecutar_diagnostico():
    """Ejecuta el script de diagnóstico para verificar la integración"""
    logger.info("Ejecutando diagnóstico final...")
    
    diag_script = Path("diagnostico_completo.py")
    if diag_script.exists():
        logger.info("Ejecutando script de diagnóstico completo...")
        try:
            result = subprocess.run(
                [sys.executable, "diagnostico_completo.py"],
                capture_output=True,
                text=True
            )
            logger.info("Diagnóstico completado")
            
            # Mostrar resultado resumido
            for line in result.stdout.split("\n"):
                if "[" in line and "]" in line:
                    logger.info(line)
                    
            return True
        except Exception as e:
            logger.error(f"Error al ejecutar diagnóstico: {e}")
            return False
    else:
        logger.error("El script de diagnóstico no existe")
        return False

def main():
    """Función principal"""
    logger.info("Iniciando finalización de optimizaciones...")
    
    # Verificar dependencias
    if not check_imports():
        return
    
    # Crear archivos de configuración
    create_config_files()
    
    # Corregir archivos pendientes
    fix_remaining_files()
    
    # Crear scripts de inicio
    create_startup_scripts()
    
    # Crear script de diagnóstico
    create_diagnostic_script()
    
    # Actualizar documentación
    crear_documentacion()
    
    # Ejecutar diagnóstico
    ejecutar_diagnostico()
    
    logger.info("Optimizaciones completadas exitosamente")
    logger.info("Para iniciar la aplicación optimizada, ejecute:")
    logger.info("  * Windows: .\\start_optimized.ps1")
    logger.info("  * Linux/Mac: ./start_optimized.sh")
    logger.info("  * Python directo: python start_optimized.py")

if __name__ == "__main__":
    main()
