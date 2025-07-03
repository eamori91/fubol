#!/usr/bin/env python
"""
Script para actualizar información de partidos desde diferentes fuentes de datos.

Este script utiliza los adaptadores implementados en utils/ para obtener datos actualizados
de partidos de diferentes ligas y los guarda en el sistema.

Uso:
    python update_matches.py [--source SOURCE] [--league LEAGUE] [--days DAYS] [--from DATE] [--to DATE]

Argumentos:
    --source SOURCE   Fuente de datos a utilizar (football-data, api-football)
    --league LEAGUE   Código de la liga a actualizar (ej. PD, PL, BL1, SA, FL1)
    --days DAYS       Número de días a consultar (hacia atrás desde hoy)
    --from DATE       Fecha de inicio (formato: YYYY-MM-DD)
    --to DATE         Fecha de fin (formato: YYYY-MM-DD)
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.football_data_api import FootballDataAPI
from utils.api_football import APIFootball
import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'update_matches.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('update_matches')

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Actualiza información de partidos desde APIs externas')
    parser.add_argument('--source', choices=['football-data', 'api-football', 'all'],
                        default='football-data', help='Fuente de datos a utilizar')
    parser.add_argument('--league', type=str, help='Código de la liga a actualizar (ej. PD, PL)')
    parser.add_argument('--days', type=int, default=7, 
                        help='Número de días a consultar (hacia atrás desde hoy)')
    parser.add_argument('--from', dest='date_from', type=str, 
                        help='Fecha de inicio (formato: YYYY-MM-DD)')
    parser.add_argument('--to', dest='date_to', type=str, 
                        help='Fecha de fin (formato: YYYY-MM-DD)')
    return parser.parse_args()

def save_matches_to_database(matches: List[Dict[str, Any]], league: str, date_from: str, date_to: str, source: str) -> None:
    """
    Guarda los partidos en la base de datos o en archivos JSON estructurados.
    
    Args:
        matches: Lista de partidos a guardar
        league: Código de la liga
        date_from: Fecha de inicio
        date_to: Fecha de fin
        source: Fuente de datos de donde provienen los partidos
    """
    if not matches:
        logger.warning(f"No hay partidos para guardar de la liga {league}")
        return
    
    # Crear directorio si no existe
    partidos_dir = os.path.join('data', 'partidos')
    os.makedirs(partidos_dir, exist_ok=True)
    
    # Ordenar por fecha
    matches = sorted(matches, key=lambda x: x.get('fecha', ''))
    
    # Guardar en un archivo JSON
    filename = f"{league or 'all'}_{date_from}_to_{date_to}.json"
    filepath = os.path.join(partidos_dir, filename)
    
    matches_data = {
        'liga': league,
        'fecha_inicio': date_from,
        'fecha_fin': date_to,
        'total_partidos': len(matches),
        'fuente': source,
        'fecha_actualizacion': datetime.now().isoformat(),
        'partidos': matches
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(matches_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Se han guardado {len(matches)} partidos en {filepath}")
    
    # Actualizar también en formato CSV para compatibilidad con sistema existente
    try:
        import pandas as pd
        df = pd.DataFrame(matches)
        csv_path = filepath.replace('.json', '.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Se ha guardado versión CSV en {csv_path}")
        
        # Actualizar caché de partidos históricos
        cache_dir = os.path.join('cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        if any(match.get('estado') == 'FINISHED' for match in matches):
            # Si hay partidos finalizados, actualizar históricos
            hist_path = os.path.join(cache_dir, 'partidos_historicos.csv')
            
            # Si ya existe, leer y combinar
            if os.path.exists(hist_path):
                hist_df = pd.read_csv(hist_path, encoding='utf-8')
                
                # Filtrar solo partidos finalizados
                finished_df = df[df['estado'] == 'FINISHED'].copy()
                
                if not finished_df.empty:
                    # Combinar y eliminar duplicados si hay columna 'id'
                    if 'id' in hist_df.columns and 'id' in finished_df.columns:
                        combined_df = pd.concat([hist_df, finished_df])
                        combined_df = combined_df.drop_duplicates(subset=['id'], keep='last')
                    else:
                        # Sin IDs, intentar combinar por equipos y fecha
                        combined_df = pd.concat([hist_df, finished_df])
                        if all(col in combined_df.columns for col in ['fecha', 'equipo_local', 'equipo_visitante']):
                            combined_df = combined_df.drop_duplicates(
                                subset=['fecha', 'equipo_local', 'equipo_visitante'], 
                                keep='last'
                            )
                    
                    combined_df.to_csv(hist_path, index=False, encoding='utf-8')
                    logger.info(f"Se ha actualizado caché de partidos históricos con {len(finished_df)} nuevos partidos")
            else:
                # Si no existe, crear con los partidos finalizados
                finished_df = df[df['estado'] == 'FINISHED'].copy()
                if not finished_df.empty:
                    finished_df.to_csv(hist_path, index=False, encoding='utf-8')
                    logger.info(f"Se ha creado caché de partidos históricos con {len(finished_df)} partidos")
                
    except Exception as e:
        logger.error(f"Error al crear versiones CSV: {e}")

def update_from_football_data(args) -> None:
    """
    Actualiza partidos desde Football-Data.org
    
    Args:
        args: Argumentos de línea de comandos
    """
    try:
        logger.info("Iniciando actualización desde Football-Data.org")
        
        # Cargar configuración
        api_key = os.environ.get('FOOTBALL_DATA_API_KEY', '')
        if not api_key:
            conf = config.ConfiguracionEntorno.obtener_config()
            api_key = conf.FUENTES_DATOS.get('football-data', {}).get('api_key', '')
        
        if not api_key:
            logger.error("No se ha configurado API key para Football-Data.org")
            return
        
        # Inicializar API
        api = FootballDataAPI({'api_key': api_key})
        
        # Determinar fechas
        if args.date_from and args.date_to:
            date_from = args.date_from
            date_to = args.date_to
        else:
            days = args.days or 7
            date_to = datetime.now().strftime('%Y-%m-%d')
            date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Determinar ligas
        if args.league:
            leagues = [args.league]
        else:
            leagues = ['PD', 'PL', 'BL1', 'SA', 'FL1']
        
        # Obtener partidos para cada liga
        for league in leagues:
            try:
                logger.info(f"Obteniendo partidos de {league} desde {date_from} hasta {date_to}")
                matches = api.fetch_matches(competition_code=league, date_from=date_from, date_to=date_to)
                save_matches_to_database(matches, league, date_from, date_to, 'football-data')
                
                # Respetar límites de tasa
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error al obtener partidos de la liga {league}: {e}")
                
    except Exception as e:
        logger.error(f"Error general en actualización desde Football-Data.org: {e}")

def update_from_api_football(args) -> None:
    """
    Actualiza partidos desde API-Football
    
    Args:
        args: Argumentos de línea de comandos
    """
    try:
        logger.info("Iniciando actualización desde API-Football")
        
        # Cargar configuración
        api_key = os.environ.get('API_FOOTBALL_KEY', '')
        api_host = os.environ.get('API_FOOTBALL_HOST', '')
        
        if not api_key or not api_host:
            logger.error("No se han configurado credenciales para API-Football")
            return
        
        # Inicializar API
        api = APIFootball({'api_key': api_key, 'api_host': api_host})
        
        # Mapeo de códigos de liga a IDs de API-Football
        league_ids = {
            'PD': 140,  # LaLiga
            'PL': 39,   # Premier League
            'BL1': 78,  # Bundesliga
            'SA': 135,  # Serie A
            'FL1': 61   # Ligue 1
        }
        
        # Determinar fechas
        if args.date_from and args.date_to:
            date_from = args.date_from
            date_to = args.date_to
        else:
            days = args.days or 7
            date_to = datetime.now().strftime('%Y-%m-%d')
            date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Determinar ligas
        if args.league:
            if args.league in league_ids:
                leagues = {args.league: league_ids[args.league]}
            elif args.league.isdigit():
                leagues = {args.league: int(args.league)}
            else:
                logger.error(f"Código de liga no reconocido: {args.league}")
                return
        else:
            leagues = league_ids
        
        # Obtener partidos para cada liga
        for code, league_id in leagues.items():
            try:
                logger.info(f"Obteniendo partidos de {code} (ID: {league_id}) desde {date_from} hasta {date_to}")
                
                # La API permite consultar por rango de fechas
                matches = api.fetch_matches(league=league_id, from_=date_from, to=date_to)
                save_matches_to_database(matches, code, date_from, date_to, 'api-football')
                
                # Respetar límites de tasa
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error al obtener partidos de la liga {code}: {e}")
                
    except Exception as e:
        logger.error(f"Error general en actualización desde API-Football: {e}")

def main():
    """Función principal del script."""
    args = parse_args()
    
    logger.info(f"Iniciando actualización de partidos desde fuente: {args.source}")
    
    try:
        if args.source == 'football-data':
            update_from_football_data(args)
        elif args.source == 'api-football':
            update_from_api_football(args)
        elif args.source == 'all':
            update_from_football_data(args)
            update_from_api_football(args)
    except Exception as e:
        logger.error(f"Error general en actualización de partidos: {e}")
    
    logger.info("Proceso de actualización de partidos completado")

if __name__ == '__main__':
    main()
