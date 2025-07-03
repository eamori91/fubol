#!/usr/bin/env python
"""
Script para actualizar datos desde fuentes externas.
Utilizado para la integración con datos reales.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import pandas as pd
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'update_data.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('update_data')

# Asegurar que existan las carpetas necesarias
for folder in ['logs', 'data/backups']:
    if not os.path.exists(folder):
        os.makedirs(folder)

def parse_args():
    """Procesa los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Actualiza datos desde fuentes externas')
    
    parser.add_argument('--source', choices=['football_data_org', 'api_football', 'local_csv', 'all'], 
                        default='all', help='Fuente de datos a utilizar')
    
    parser.add_argument('--data', choices=['teams', 'players', 'matches', 'all'],
                        default='all', help='Tipo de datos a actualizar')
    
    parser.add_argument('--force', action='store_true',
                        help='Forzar actualización incluso si los datos son recientes')
    
    parser.add_argument('--backup', action='store_true',
                        help='Crear respaldo antes de actualizar')
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Ejecutar sin realizar cambios (simulación)')
    
    return parser.parse_args()

def create_backup():
    """Crea un respaldo de los datos actuales"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('data', 'backups', timestamp)
    
    logger.info(f"Creando respaldo en {backup_dir}")
    
    # Crear directorio de respaldo
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Respaldar archivos CSV
    csv_files = [
        os.path.join('cache', 'partidos_historicos.csv'),
        os.path.join('cache', 'partidos_generados.csv')
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            backup_file = os.path.join(backup_dir, os.path.basename(csv_file))
            logger.info(f"Respaldando {csv_file} -> {backup_file}")
            if os.path.exists(csv_file):
                with open(csv_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dest:
                        dest.write(src.read())
    
    # Respaldar archivos JSON de equipos
    equipos_dir = os.path.join('data', 'equipos', 'equipos')
    if os.path.exists(equipos_dir):
        backup_equipos_dir = os.path.join(backup_dir, 'equipos')
        if not os.path.exists(backup_equipos_dir):
            os.makedirs(backup_equipos_dir)
            
        for file in os.listdir(equipos_dir):
            if file.endswith('.json'):
                source_path = os.path.join(equipos_dir, file)
                dest_path = os.path.join(backup_equipos_dir, file)
                logger.info(f"Respaldando {source_path} -> {dest_path}")
                with open(source_path, 'r', encoding='utf-8') as src:
                    with open(dest_path, 'w', encoding='utf-8') as dest:
                        dest.write(src.read())
    
    logger.info(f"Respaldo completado en {backup_dir}")
    return backup_dir

def update_from_football_data_org(data_type):
    """Actualiza datos desde Football-Data.org API"""
    try:
        from utils.data_fetcher import FootballDataOrgFetcher
        logger.info(f"Actualizando {data_type} desde Football-Data.org")
        
        # En una implementación real, cargaríamos la clave API desde config.py
        api_key = "TU_API_KEY_AQUI"  # Reemplazar con clave real o cargarla de config
        
        fetcher = FootballDataOrgFetcher(api_key)
        
        if data_type in ['teams', 'all']:
            logger.info("Obteniendo datos de equipos...")
            teams = fetcher.fetch_teams(league_code='PL')  # Premier League
            logger.info(f"Obtenidos {len(teams)} equipos")
        
        if data_type in ['matches', 'all']:
            logger.info("Obteniendo datos de partidos...")
            matches = fetcher.fetch_matches(days=30)  # Últimos 30 días
            logger.info(f"Obtenidos {len(matches)} partidos")
            
            # Guardar partidos en formato CSV
            if matches:
                df = pd.DataFrame(matches)
                df.to_csv(os.path.join('cache', 'partidos_nuevos.csv'), index=False)
                logger.info("Partidos guardados en cache/partidos_nuevos.csv")
                
                # Integrar con partidos históricos si existe el archivo
                hist_file = os.path.join('cache', 'partidos_historicos.csv')
                if os.path.exists(hist_file):
                    hist_df = pd.read_csv(hist_file)
                    # Eliminar duplicados basados en ID de partido y concatenar
                    combined_df = pd.concat([hist_df, df]).drop_duplicates(subset=['id'])
                    combined_df.to_csv(hist_file, index=False)
                    logger.info(f"Integrados {len(df)} partidos con datos históricos")
                else:
                    df.to_csv(hist_file, index=False)
                    logger.info(f"Creado nuevo archivo histórico con {len(df)} partidos")
        
        if data_type in ['players', 'all']:
            logger.info("Obteniendo datos de jugadores...")
            players = fetcher.fetch_players(team_id='66')  # Por ejemplo, Manchester United
            logger.info(f"Obtenidos {len(players)} jugadores")
        
        logger.info(f"Actualización desde Football-Data.org completada para {data_type}")
        return True
        
    except ImportError:
        logger.error("No se encontró el módulo FootballDataOrgFetcher. Verifica utils/data_fetcher.py")
        return False
    except Exception as e:
        logger.error(f"Error al actualizar datos desde Football-Data.org: {str(e)}")
        return False

def update_from_api_football(data_type):
    """Actualiza datos desde API-Football"""
    try:
        logger.info(f"Actualizando {data_type} desde API-Football")
        
        # Simulación: en producción, se implementaría la conexión real a la API
        logger.info("Simulando actualización desde API-Football...")
        
        # Datos simulados para demostración
        if data_type in ['teams', 'all']:
            teams = [
                {"id": 1, "name": "Real Madrid", "country": "Spain", "league": "La Liga"},
                {"id": 2, "name": "FC Barcelona", "country": "Spain", "league": "La Liga"},
                {"id": 3, "name": "Manchester City", "country": "England", "league": "Premier League"}
            ]
            logger.info(f"Simulados {len(teams)} equipos")
            
        if data_type in ['matches', 'all']:
            matches = [
                {"id": 101, "date": "2023-11-15", "home_team": 1, "away_team": 2, "home_score": 2, "away_score": 1},
                {"id": 102, "date": "2023-11-16", "home_team": 3, "away_team": 1, "home_score": 1, "away_score": 1}
            ]
            logger.info(f"Simulados {len(matches)} partidos")
        
        logger.info(f"Simulación de actualización desde API-Football completada para {data_type}")
        return True
        
    except Exception as e:
        logger.error(f"Error al actualizar datos desde API-Football: {str(e)}")
        return False

def update_from_local_csv(data_type):
    """Actualiza desde archivos CSV locales"""
    try:
        logger.info(f"Actualizando {data_type} desde archivos CSV locales")
        
        if data_type not in ['matches', 'all']:
            logger.warning("Sólo se soporta actualización de partidos desde CSV")
            return False
            
        local_file = os.path.join('data', 'external', 'matches.csv')
        
        if not os.path.exists(local_file):
            logger.error(f"Archivo {local_file} no encontrado")
            return False
        
        logger.info(f"Leyendo datos desde {local_file}")
        df = pd.read_csv(local_file)
        logger.info(f"Leídos {len(df)} registros")
        
        # Guardar en cache
        output_file = os.path.join('cache', 'partidos_historicos.csv')
        df.to_csv(output_file, index=False)
        logger.info(f"Datos guardados en {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al actualizar datos desde CSV: {str(e)}")
        return False

def main():
    """Función principal"""
    args = parse_args()
    logger.info("Iniciando actualización de datos")
    logger.info(f"Parámetros: source={args.source}, data={args.data}, force={args.force}")
    
    if args.dry_run:
        logger.info("MODO SIMULACIÓN: No se realizarán cambios")
    
    if args.backup and not args.dry_run:
        backup_dir = create_backup()
        logger.info(f"Respaldo creado en {backup_dir}")
    
    success = True
    
    # Actualizar según la fuente especificada
    if args.source in ['football_data_org', 'all'] and not args.dry_run:
        if not update_from_football_data_org(args.data):
            success = False
    
    if args.source in ['api_football', 'all'] and not args.dry_run:
        if not update_from_api_football(args.data):
            success = False
    
    if args.source in ['local_csv', 'all'] and not args.dry_run:
        if not update_from_local_csv(args.data):
            success = False
    
    if args.dry_run:
        logger.info("Simulación completada sin errores")
    elif success:
        logger.info("Actualización completada exitosamente")
    else:
        logger.error("La actualización finalizó con errores")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
