#!/usr/bin/env python
"""
Script para ejecutar tareas de optimización programadas.
Este script puede configurarse como una tarea cron o programada.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import time
from datetime import datetime, timedelta
import json

# Añadir directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join(project_root, 'logs', 'optimizaciones.log')
)
logger = logging.getLogger('optimizaciones')

def optimizar_base_datos():
    """Optimiza la base de datos con VACUUM y análisis."""
    try:
        from utils.db_optimizer import db_optimizer
        
        db_path = os.path.join(project_root, "data/database/fubol.db")
        if os.path.exists(db_path):
            logger.info(f"Optimizando base de datos: {db_path}")
            db_optimizer.optimize_database(db_path)
            logger.info("Base de datos optimizada correctamente")
        else:
            logger.warning(f"Base de datos no encontrada: {db_path}")
            
    except Exception as e:
        logger.error(f"Error optimizando base de datos: {e}")
        return False
        
    return True

def limpiar_cache_antigua():
    """Elimina archivos de caché antiguos."""
    try:
        from utils.cache_manager import cache_manager
        
        # Limpiar cachés expiradas
        cache_dir = os.path.join(project_root, "data/cache")
        
        # Contar archivos antes
        archivos_antes = sum([len(files) for _, _, files in os.walk(cache_dir)])
        
        # Obtener estadísticas
        stats_antes = cache_manager.get_stats()
        
        # Recorrer directorios de caché
        archivos_eliminados = 0
        bytes_liberados = 0
        
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                if not file.endswith('.cache'):
                    continue
                    
                ruta_completa = os.path.join(root, file)
                
                # Verificar fecha de modificación
                mtime = os.path.getmtime(ruta_completa)
                edad_dias = (time.time() - mtime) / (24 * 3600)
                
                # Eliminar si tiene más de 7 días
                if edad_dias > 7:
                    try:
                        tamano = os.path.getsize(ruta_completa)
                        os.unlink(ruta_completa)
                        archivos_eliminados += 1
                        bytes_liberados += tamano
                    except Exception as e:
                        logger.warning(f"Error al eliminar caché {ruta_completa}: {e}")
        
        # Contar archivos después
        archivos_despues = sum([len(files) for _, _, files in os.walk(cache_dir)])
        
        logger.info(f"Limpieza de caché: {archivos_eliminados} archivos eliminados, "
                   f"{bytes_liberados / (1024*1024):.2f} MB liberados")
        logger.info(f"Archivos en caché: {archivos_antes} → {archivos_despues}")
        
        # Limpiar caché en memoria
        cache_manager.clear_all()
        logger.info("Caché en memoria limpiada")
        
    except Exception as e:
        logger.error(f"Error limpiando caché: {e}")
        return False
        
    return True

def generar_informe_rendimiento():
    """Genera un informe de rendimiento del sistema."""
    try:
        informe = {
            "fecha": datetime.now().isoformat(),
            "sistema": {}
        }
        
        # Información de uso de disco
        import shutil
        usage = shutil.disk_usage(project_root)
        
        informe["sistema"]["disco"] = {
            "total_gb": usage.total / (1024**3),
            "usado_gb": usage.used / (1024**3),
            "libre_gb": usage.free / (1024**3),
            "porcentaje_usado": usage.used * 100 / usage.total
        }
        
        # Información de base de datos
        db_path = os.path.join(project_root, "data/database/fubol.db")
        if os.path.exists(db_path):
            tamano_db = os.path.getsize(db_path) / (1024*1024)  # MB
            informe["sistema"]["base_datos"] = {
                "ruta": db_path,
                "tamano_mb": tamano_db
            }
            
            # Estadísticas de tablas
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener lista de tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tablas = [row[0] for row in cursor.fetchall()]
                
                tabla_stats = {}
                for tabla in tablas:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                        count = cursor.fetchone()[0]
                        tabla_stats[tabla] = {"registros": count}
                    except:
                        pass
                
                informe["sistema"]["base_datos"]["tablas"] = tabla_stats
                conn.close()
            except Exception as e:
                logger.warning(f"No se pudieron obtener estadísticas de tablas: {e}")
        
        # Información de caché
        cache_dir = os.path.join(project_root, "data/cache")
        if os.path.exists(cache_dir):
            tamano_total = sum(os.path.getsize(os.path.join(dirpath, filename))
                              for dirpath, _, filenames in os.walk(cache_dir)
                              for filename in filenames) / (1024*1024)  # MB
            
            num_archivos = sum(len(files) for _, _, files in os.walk(cache_dir))
            
            informe["sistema"]["cache"] = {
                "archivos": num_archivos,
                "tamano_mb": tamano_total
            }
        
        # Información de logs
        logs_dir = os.path.join(project_root, "logs")
        if os.path.exists(logs_dir):
            tamano_total = sum(os.path.getsize(os.path.join(dirpath, filename))
                              for dirpath, _, filenames in os.walk(logs_dir)
                              for filename in filenames) / (1024*1024)  # MB
            
            num_archivos = sum(len(files) for _, _, files in os.walk(logs_dir))
            
            informe["sistema"]["logs"] = {
                "archivos": num_archivos,
                "tamano_mb": tamano_total
            }
        
        # Guardar informe
        informe_path = os.path.join(project_root, "logs", "rendimiento.json")
        with open(informe_path, 'w', encoding='utf-8') as f:
            json.dump(informe, f, indent=2)
            
        logger.info(f"Informe de rendimiento generado: {informe_path}")
        
    except Exception as e:
        logger.error(f"Error generando informe de rendimiento: {e}")
        return False
        
    return True

def rotar_logs():
    """Rota los archivos de log para controlar su tamaño."""
    try:
        logs_dir = os.path.join(project_root, "logs")
        if not os.path.exists(logs_dir):
            return True
            
        for file in os.listdir(logs_dir):
            if not file.endswith('.log'):
                continue
                
            log_path = os.path.join(logs_dir, file)
            size_mb = os.path.getsize(log_path) / (1024*1024)
            
            # Si el archivo supera 10MB, rotarlo
            if size_mb > 10:
                # Crear nombre con timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{file}.{timestamp}"
                backup_path = os.path.join(logs_dir, backup_name)
                
                # Renombrar archivo actual
                os.rename(log_path, backup_path)
                
                logger.info(f"Log rotado: {file} → {backup_name} ({size_mb:.2f} MB)")
                
                # Eliminar logs antiguos (más de 5)
                all_backups = [f for f in os.listdir(logs_dir) if f.startswith(file + '.')]
                if len(all_backups) > 5:
                    # Ordenar por nombre (que incluye timestamp)
                    all_backups.sort()
                    # Eliminar los más antiguos
                    for old_backup in all_backups[:-5]:
                        os.unlink(os.path.join(logs_dir, old_backup))
                        logger.info(f"Log antiguo eliminado: {old_backup}")
        
    except Exception as e:
        logger.error(f"Error rotando logs: {e}")
        return False
        
    return True

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Ejecuta tareas de optimización programadas.')
    parser.add_argument('--all', action='store_true', help='Ejecutar todas las tareas')
    parser.add_argument('--db', action='store_true', help='Optimizar base de datos')
    parser.add_argument('--cache', action='store_true', help='Limpiar caché antigua')
    parser.add_argument('--report', action='store_true', help='Generar informe de rendimiento')
    parser.add_argument('--logs', action='store_true', help='Rotar archivos de log')
    
    args = parser.parse_args()
    
    # Si no se especifica ninguna tarea, ejecutar todas
    if not (args.all or args.db or args.cache or args.report or args.logs):
        args.all = True
    
    logger.info("Iniciando tareas de optimización programadas")
    start_time = time.time()
    
    resultados = {}
    
    # Optimizar base de datos
    if args.all or args.db:
        logger.info("Ejecutando optimización de base de datos...")
        resultados["base_datos"] = optimizar_base_datos()
    
    # Limpiar caché antigua
    if args.all or args.cache:
        logger.info("Ejecutando limpieza de caché...")
        resultados["cache"] = limpiar_cache_antigua()
    
    # Generar informe de rendimiento
    if args.all or args.report:
        logger.info("Generando informe de rendimiento...")
        resultados["informe"] = generar_informe_rendimiento()
    
    # Rotar logs
    if args.all or args.logs:
        logger.info("Rotando archivos de log...")
        resultados["logs"] = rotar_logs()
    
    # Resumen
    elapsed = time.time() - start_time
    exito = all(resultados.values())
    
    logger.info(f"Tareas completadas en {elapsed:.2f} segundos")
    for tarea, resultado in resultados.items():
        estado = "OK" if resultado else "ERROR"
        logger.info(f"- {tarea}: {estado}")
    
    return 0 if exito else 1

if __name__ == "__main__":
    sys.exit(main())
