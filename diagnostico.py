#!/usr/bin/env python
"""
Diagnóstico simple del sistema optimizado
"""

import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('diagnostico')

def verificar_archivos():
    """Verifica que los archivos clave existan"""
    
    # Optimizadores
    optimizadores = [
        'utils/cache_manager.py',
        'utils/http_optimizer.py',
        'utils/db_optimizer.py',
        'utils/log_manager.py',
        'utils/config_manager.py',
        'utils/analytics_optimizer.py',
    ]
    
    for archivo in optimizadores:
        if Path(archivo).exists():
            logger.info(f"OK - {archivo}")
        else:
            logger.error(f"FALTA - {archivo}")
    
    # Scripts
    scripts = ['start_optimized.py']
    for script in scripts:
        if Path(script).exists():
            logger.info(f"OK - {script}")
        else:
            logger.error(f"FALTA - {script}")
    
    # Directorios
    dirs = ['config', 'data/cache', 'logs']
    for d in dirs:
        if Path(d).exists():
            logger.info(f"OK - {d}/")
        else:
            logger.error(f"FALTA - {d}/")

def verificar_integracion():
    """Verifica la integración de los componentes en los archivos clave"""
    archivos = {
        'app.py': ['cache_manager', 'http_optimizer', 'db_optimizer'],
        'utils/unified_data_adapter.py': ['cache_manager', 'http_optimizer', 'db_optimizer']
    }
    
    for archivo, componentes in archivos.items():
        if not Path(archivo).exists():
            logger.error(f"FALTA - {archivo}")
            continue
            
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read().lower()
                
            for componente in componentes:
                if componente.lower() in contenido:
                    logger.info(f"OK - {archivo} contiene {componente}")
                else:
                    logger.warning(f"REVISAR - {archivo} no contiene {componente}")
        except Exception as e:
            logger.error(f"ERROR - No se pudo leer {archivo}: {e}")

if __name__ == "__main__":
    print("-" * 50)
    print("DIAGNÓSTICO DEL SISTEMA OPTIMIZADO")
    print("-" * 50)
    verificar_archivos()
    print("-" * 50)
    verificar_integracion()
    print("-" * 50)
