#!/usr/bin/env python
"""
Script de configuración para el sistema optimizado de análisis de fútbol.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import json
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup")

def run_command(cmd, desc=None, check=True):
    """Ejecuta un comando y devuelve su resultado"""
    if desc:
        logger.info(desc)
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            text=True, 
            capture_output=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando comando: {e}")
        logger.error(f"Salida: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    logger.info("Verificando versión de Python...")
    
    if sys.version_info < (3, 7):
        logger.error("Se requiere Python 3.7 o superior")
        sys.exit(1)
    
    logger.info(f"Usando Python {sys.version}")

def create_directories():
    """Crea los directorios necesarios para el proyecto"""
    logger.info("Creando estructura de directorios...")
    
    dirs = [
        "config",
        "data/cache",
        "logs",
        "backups"
    ]
    
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio creado: {path}")

def install_dependencies():
    """Instala las dependencias requeridas"""
    logger.info("Instalando dependencias...")
    
    # Verificar si requirements.txt existe
    if not Path("requirements.txt").exists():
        logger.error("No se encontró el archivo requirements.txt")
        sys.exit(1)
    
    result = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Instalando paquetes desde requirements.txt"
    )
    
    if result.returncode != 0:
        logger.warning("Algunos paquetes no pudieron instalarse. Intentando instalar esenciales...")
        
        # Instalar dependencias esenciales para las optimizaciones
        essential_pkgs = [
            "flask",
            "pandas",
            "numpy",
            "requests",
            "matplotlib",
            "seaborn",
            "psutil",
            "python-dotenv",
            "pyyaml"
        ]
        
        for pkg in essential_pkgs:
            run_command(
                f"{sys.executable} -m pip install {pkg}",
                f"Instalando {pkg}",
                check=False
            )

def create_config():
    """Crea o actualiza el archivo de configuración"""
    logger.info("Configurando el sistema...")
    
    config_path = Path("config/config.json")
    
    # Configuración por defecto
    default_config = {
        "app": {
            "debug": False,
            "secret_key": "fubol_secret_key_default",
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
    
    # Si ya existe, lo actualizamos sin sobrescribir
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
            
            # Combinar configuraciones manteniendo valores existentes
            merged_config = default_config.copy()
            for key, section in existing_config.items():
                if key in merged_config and isinstance(section, dict):
                    merged_config[key].update(section)
                else:
                    merged_config[key] = section
                    
            config = merged_config
            logger.info("Configuración existente actualizada")
        except Exception as e:
            logger.warning(f"Error leyendo configuración existente: {e}")
            logger.warning("Usando configuración predeterminada")
            config = default_config
    else:
        config = default_config
        logger.info("Creando nueva configuración")
    
    # Guardar configuración
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    
    logger.info(f"Configuración guardada en: {config_path}")

def apply_optimizations():
    """Aplica todas las optimizaciones disponibles"""
    logger.info("Aplicando optimizaciones...")
    
    # Ejecutar integración de optimizaciones
    if Path("integrar_optimizaciones.py").exists():
        run_command(
            f"{sys.executable} integrar_optimizaciones.py",
            "Integrando optimizaciones en el código principal"
        )
    else:
        logger.warning("No se encontró el script integrar_optimizaciones.py")
    
    # Optimizar plantillas
    if Path("optimizar_templates.py").exists():
        run_command(
            f"{sys.executable} optimizar_templates.py",
            "Optimizando plantillas HTML"
        )
    else:
        logger.warning("No se encontró el script optimizar_templates.py")

def create_startup_script():
    """Crea scripts para iniciar el sistema"""
    logger.info("Creando scripts de inicio...")
    
    # Script para Windows (PowerShell)
    win_script = Path("start_optimized.ps1")
    with open(win_script, "w", encoding="utf-8") as f:
        f.write("""# Script para iniciar el sistema optimizado (Windows)
$env:FUBOL_OPTIMIZE = "1"
$env:FUBOL_CONFIG_PATH = "config/config.json"

Write-Host "Iniciando sistema optimizado..."
python start_optimized.py
""")
    
    # Script para Linux/Mac
    unix_script = Path("start_optimized.sh")
    with open(unix_script, "w", encoding="utf-8") as f:
        f.write("""#!/bin/bash
# Script para iniciar el sistema optimizado (Unix)
export FUBOL_OPTIMIZE=1
export FUBOL_CONFIG_PATH="config/config.json"

echo "Iniciando sistema optimizado..."
python start_optimized.py
""")
    
    # Hacer ejecutable en sistemas Unix
    try:
        os.chmod(unix_script, 0o755)
    except:
        pass
    
    logger.info(f"Scripts de inicio creados: {win_script}, {unix_script}")

def main():
    """Función principal"""
    logger.info("Iniciando configuración del sistema optimizado...")
    
    check_python_version()
    create_directories()
    install_dependencies()
    create_config()
    apply_optimizations()
    create_startup_script()
    
    logger.info("Configuración completada")
    print("\nSistema listo para usar!")
    print("Para iniciar:")
    print(" - Windows: .\\start_optimized.ps1 o python start_optimized.py")
    print(" - Linux/Mac: ./start_optimized.sh o python start_optimized.py")
    print("\nPara un diagnóstico completo:")
    print(" python diagnostico_sistema.py")

if __name__ == "__main__":
    main()
