#!/usr/bin/env python
"""
Script principal para ejecutar todas las pruebas y actualizaciones de integración con datos reales.

Este script orquesta la ejecución de todos los componentes necesarios para la integración:
1. Configuración de la base de datos
2. Actualización de datos desde APIs externas
3. Pruebas de integración con el sistema
4. Demostración de funcionalidades

Uso:
    python run_integration.py [--reset] [--source SOURCE]

Argumentos:
    --reset           Reiniciar la base de datos antes de ejecutar
    --source SOURCE   Fuente de datos a utilizar (football-data, api-football, all)
"""

import os
import sys
import argparse
import logging
import subprocess
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/integration_run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('run_integration')

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Ejecuta la integración completa con datos reales')
    parser.add_argument('--reset', action='store_true', help='Reiniciar la base de datos')
    parser.add_argument('--source', choices=['football-data', 'api-football', 'all'],
                       default='all', help='Fuente de datos a utilizar')
    return parser.parse_args()

def run_script(script_path, args=None):
    """
    Ejecuta un script de Python con los argumentos proporcionados.
    
    Args:
        script_path: Ruta al script a ejecutar
        args: Lista de argumentos adicionales para el script
        
    Returns:
        True si el script se ejecutó correctamente, False en caso contrario
    """
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
        
    logger.info(f"Ejecutando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        logger.info(f"Script {script_path} ejecutado correctamente (código: {result.returncode})")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar {script_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Excepción al ejecutar {script_path}: {e}")
        return False

def main():
    """Función principal del script."""
    args = parse_args()
    
    logger.info("Iniciando ejecución de integración con datos reales")
    
    # Verificar disponibilidad de credenciales
    if not os.environ.get('FOOTBALL_DATA_API_KEY') and not os.environ.get('API_FOOTBALL_KEY'):
        logger.warning("⚠️ No se encontraron credenciales de API en variables de entorno.")
        logger.warning("Algunas funcionalidades pueden no estar disponibles.")
        logger.warning("Configura FOOTBALL_DATA_API_KEY y/o API_FOOTBALL_KEY.")
    
    # 1. Configurar/reiniciar base de datos
    db_args = ['--db_type', 'sqlite']
    if args.reset:
        db_args.append('--reset')
        
    if not run_script('scripts/setup_database.py', db_args):
        logger.error("❌ Error en la configuración de la base de datos. Abortando.")
        return
        
    logger.info("✅ Base de datos configurada correctamente")
    
    # 2. Actualizar datos desde APIs externas
    update_args = ['--source', args.source, '--data', 'all']
    if run_script('scripts/update_database.py', update_args):
        logger.info("✅ Actualización de datos desde APIs completada")
    else:
        logger.warning("⚠️ Hubo problemas al actualizar datos desde APIs")
        
    # Pequeña pausa
    time.sleep(2)
    
    # 3. Ejecutar pruebas de integración
    if run_script('scripts/test_data_integration.py'):
        logger.info("✅ Pruebas de integración con datos reales completadas")
    else:
        logger.warning("⚠️ Hubo problemas en las pruebas de integración")
        
    # 4. Ejecutar demostración
    demo_args = ['--source', args.source]
    if run_script('scripts/demo_integracion.py', demo_args):
        logger.info("✅ Demostración de integración completada")
    else:
        logger.warning("⚠️ Hubo problemas en la demostración de integración")
    
    logger.info("🎉 Proceso de integración con datos reales finalizado")
    
if __name__ == '__main__':
    main()
