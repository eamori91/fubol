#!/usr/bin/env python
"""
Script para actualizar información de equipos desde diferentes fuentes de datos.

Este script utiliza los adaptadores implementados en utils/ para obtener datos actualizados
de equipos de diferentes ligas y los guarda en el sistema.

Uso:
    python update_teams.py [--source SOURCE] [--league LEAGUE] [--season SEASON]

Argumentos:
    --source SOURCE    Fuente de datos a utilizar (football-data, api-football, open-football)
    --league LEAGUE    Código de la liga a actualizar (ej. PD, PL, BL1, SA, FL1)
    --season SEASON    Temporada a actualizar (ej. 2022, 2022-23)
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.football_data_api import FootballDataAPI
from utils.api_football import APIFootball
from utils.data_fetcher import DataFetcher
import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'update_teams.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('update_teams')

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Actualiza información de equipos desde APIs externas')
    parser.add_argument('--source', choices=['football-data', 'api-football', 'open-football', 'all'],
                        default='football-data', help='Fuente de datos a utilizar')
    parser.add_argument('--league', type=str, help='Código de la liga a actualizar (ej. PD, PL)')
    parser.add_argument('--season', type=str, help='Temporada a actualizar (ej. 2022)')
    return parser.parse_args()

def save_teams_to_database(teams: List[Dict[str, Any]], source: str) -> None:
    """
    Guarda los equipos en la base de datos o en archivos JSON estructurados.
    
    Args:
        teams: Lista de equipos a guardar
        source: Fuente de datos de donde provienen los equipos
    """
    if not teams:
        logger.warning(f"No hay equipos para guardar de la fuente {source}")
        return
    
    # Crear directorio si no existe
    equipos_dir = os.path.join('data', 'equipos')
    os.makedirs(equipos_dir, exist_ok=True)
    
    # Actualizar índice de equipos
    index_path = os.path.join(equipos_dir, 'indice_equipos.json')
    index = {}
    
    # Cargar índice existente si existe
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error al cargar índice de equipos: formato inválido")
            index = {}
    
    # Procesar cada equipo
    for team in teams:
        team_id = str(team.get('id', ''))
        if not team_id:
            logger.warning(f"Equipo sin ID, ignorando: {team.get('nombre', 'Desconocido')}")
            continue
        
        # Añadir metadatos
        team['ultima_actualizacion'] = datetime.now().isoformat()
        team['fuente'] = source
        
        # Guardar equipo en archivo individual
        team_dir = os.path.join(equipos_dir, 'equipos')
        os.makedirs(team_dir, exist_ok=True)
        team_path = os.path.join(team_dir, f"{team_id}.json")
        
        with open(team_path, 'w', encoding='utf-8') as f:
            json.dump(team, f, ensure_ascii=False, indent=2)
        
        # Actualizar índice
        index[team_id] = {
            'id': team_id,
            'nombre': team.get('nombre', 'Desconocido'),
            'liga': team.get('liga', team.get('codigo_liga', 'Desconocido')),
            'pais': team.get('pais', 'Desconocido'),
            'ultima_actualizacion': team['ultima_actualizacion'],
            'fuente': source,
            'file_path': f"equipos/{team_id}.json"
        }
    
    # Guardar índice actualizado
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Se han guardado {len(teams)} equipos de la fuente {source}")
    logger.info(f"Índice de equipos actualizado: {index_path}")

def update_from_football_data(args) -> None:
    """
    Actualiza equipos desde Football-Data.org
    
    Args:
        args: Argumentos de línea de comandos
    """
    try:
        logger.info("Iniciando actualización desde Football-Data.org")
        
        # Cargar configuración
        api_key = os.environ.get('FOOTBALL_DATA_API_KEY', '')
        if not api_key:
            # Intentar obtener de config.py
            conf = config.ConfiguracionEntorno.obtener_config()
            api_key = conf.FUENTES_DATOS.get('football-data', {}).get('api_key', '')
        
        if not api_key:
            logger.error("No se ha configurado API key para Football-Data.org")
            return
        
        # Inicializar API
        api = FootballDataAPI({'api_key': api_key})
        
        # Ligas por defecto si no se especifica una
        leagues = [args.league] if args.league else ['PD', 'PL', 'BL1', 'SA', 'FL1']
        
        for league in leagues:
            try:
                logger.info(f"Obteniendo equipos de la liga {league}")
                teams = api.fetch_teams(competition_code=league, season=args.season)
                save_teams_to_database(teams, 'football-data')
            except Exception as e:
                logger.error(f"Error al obtener equipos de la liga {league}: {e}")
                
    except Exception as e:
        logger.error(f"Error general en actualización desde Football-Data.org: {e}")

def update_from_api_football(args) -> None:
    """
    Actualiza equipos desde API-Football
    
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
        
        # Determinar ligas a actualizar
        if args.league and args.league in league_ids:
            leagues = {args.league: league_ids[args.league]}
        elif args.league and args.league.isdigit():
            # Si se proporciona directamente el ID numérico
            leagues = {args.league: int(args.league)}
        else:
            leagues = league_ids
        
        # Determinar temporada
        season = args.season or datetime.now().year
        
        for code, league_id in leagues.items():
            try:
                logger.info(f"Obteniendo equipos de la liga {code} (ID: {league_id})")
                teams = api.fetch_teams(league=league_id, season=season)
                save_teams_to_database(teams, 'api-football')
            except Exception as e:
                logger.error(f"Error al obtener equipos de la liga {code}: {e}")
                
    except Exception as e:
        logger.error(f"Error general en actualización desde API-Football: {e}")

def update_from_open_football(args) -> None:
    """
    Actualiza equipos desde Open-Football (GitHub)
    
    Args:
        args: Argumentos de línea de comandos
    """
    try:
        logger.info("Iniciando actualización desde Open-Football")
        
        # Inicializar DataFetcher existente
        fetcher = DataFetcher()
        
        # Mapeo de códigos de liga
        league_map = {
            'PL': 'premier-league',
            'PD': 'la-liga',
            'BL1': 'bundesliga',
            'SA': 'serie-a',
            'FL1': 'ligue-1'
        }
        
        # Determinar liga a actualizar
        league = None
        if args.league and args.league in league_map:
            league = league_map[args.league]
        
        # Determinar temporada
        season = args.season or '2022-23'
        
        # Obtener datos
        results = fetcher.fetch_openfootball_data(league, season)
        
        # Procesar resultados y extraer equipos
        teams = []
        for league_name, data in results.items():
            try:
                json_path = data.get('json_path')
                if not json_path or not os.path.exists(json_path):
                    continue
                    
                with open(json_path, 'r', encoding='utf-8') as f:
                    league_data = json.load(f)
                
                # Extraer equipos únicos
                teams_dict = {}
                for match in league_data.get('matches', []):
                    for team_type in ['team1', 'team2']:
                        team = match.get(team_type, {})
                        team_name = team.get('name')
                        if team_name and team_name not in teams_dict:
                            # Generar ID sintético basado en nombre
                            team_id = f"of-{hash(team_name) % 100000}"
                            teams_dict[team_name] = {
                                'id': team_id,
                                'nombre': team_name,
                                'codigo_liga': league_name,
                                'liga': league_data.get('name', league_name),
                                'pais': league_data.get('country', {}).get('name', 'Desconocido'),
                                'temporada': league_data.get('season')
                            }
                
                teams.extend(teams_dict.values())
                            
            except Exception as e:
                logger.error(f"Error al procesar datos de {league_name}: {e}")
        
        save_teams_to_database(teams, 'open-football')
                
    except Exception as e:
        logger.error(f"Error general en actualización desde Open-Football: {e}")

def main():
    """Función principal del script."""
    args = parse_args()
    
    logger.info(f"Iniciando actualización de equipos desde fuente: {args.source}")
    
    try:
        if args.source == 'football-data':
            update_from_football_data(args)
        elif args.source == 'api-football':
            update_from_api_football(args)
        elif args.source == 'open-football':
            update_from_open_football(args)
        elif args.source == 'all':
            update_from_football_data(args)
            update_from_api_football(args)
            update_from_open_football(args)
    except Exception as e:
        logger.error(f"Error general en actualización de equipos: {e}")
    
    logger.info("Proceso de actualización de equipos completado")

if __name__ == '__main__':
    main()
