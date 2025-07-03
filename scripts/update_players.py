#!/usr/bin/env python
"""
Script para actualizar información de jugadores desde diferentes fuentes de datos.

Este script utiliza los adaptadores implementados en utils/ para obtener datos actualizados
de jugadores de diferentes equipos y los guarda en el sistema.

Uso:
    python update_players.py [--source SOURCE] [--team TEAM_ID] [--league LEAGUE] [--season SEASON]

Argumentos:
    --source SOURCE    Fuente de datos a utilizar (football-data, api-football)
    --team TEAM_ID     ID del equipo a actualizar
    --league LEAGUE    Código de la liga a actualizar (para obtener jugadores de todos los equipos)
    --season SEASON    Temporada a actualizar (ej. 2022)
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
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
        logging.FileHandler(os.path.join('data', 'update_players.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('update_players')

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Actualiza información de jugadores desde APIs externas')
    parser.add_argument('--source', choices=['football-data', 'api-football', 'all'],
                        default='football-data', help='Fuente de datos a utilizar')
    parser.add_argument('--team', type=str, help='ID del equipo a actualizar')
    parser.add_argument('--league', type=str, help='Código de la liga a actualizar (ej. PD, PL)')
    parser.add_argument('--season', type=str, help='Temporada a actualizar (ej. 2022)')
    return parser.parse_args()

def save_players_to_database(players: List[Dict[str, Any]], team_id: str, source: str) -> None:
    """
    Guarda los jugadores en la base de datos o en archivos JSON estructurados.
    
    Args:
        players: Lista de jugadores a guardar
        team_id: ID del equipo al que pertenecen
        source: Fuente de datos de donde provienen los jugadores
    """
    if not players:
        logger.warning(f"No hay jugadores para guardar del equipo {team_id}")
        return
    
    # Crear directorio si no existe
    jugadores_dir = os.path.join('data', 'equipos', 'jugadores')
    os.makedirs(jugadores_dir, exist_ok=True)
    
    # Directorio específico para el equipo
    team_dir = os.path.join(jugadores_dir, team_id)
    os.makedirs(team_dir, exist_ok=True)
    
    # Crear índice de jugadores para este equipo
    index_path = os.path.join(team_dir, 'indice.json')
    index = {
        'equipo_id': team_id,
        'ultima_actualizacion': datetime.now().isoformat(),
        'fuente': source,
        'total_jugadores': len(players),
        'jugadores': {}
    }
    
    # Procesar cada jugador
    for player in players:
        player_id = str(player.get('id', ''))
        if not player_id:
            logger.warning(f"Jugador sin ID, ignorando: {player.get('nombre', 'Desconocido')}")
            continue
        
        # Añadir metadatos
        player['ultima_actualizacion'] = datetime.now().isoformat()
        player['fuente'] = source
        player['equipo_id'] = team_id
        
        # Guardar jugador en archivo individual
        player_path = os.path.join(team_dir, f"{player_id}.json")
        
        with open(player_path, 'w', encoding='utf-8') as f:
            json.dump(player, f, ensure_ascii=False, indent=2)
        
        # Actualizar índice
        index['jugadores'][player_id] = {
            'id': player_id,
            'nombre': player.get('nombre', 'Desconocido'),
            'posicion': player.get('posicion', 'Desconocida'),
            'file_path': f"{player_id}.json"
        }
    
    # Guardar índice actualizado
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Se han guardado {len(players)} jugadores del equipo {team_id}")

def get_team_ids_from_league(source: str, league_code: str, season: Optional[str] = None) -> List[str]:
    """
    Obtiene los IDs de los equipos de una liga desde una fuente específica.
    
    Args:
        source: Fuente de datos a consultar
        league_code: Código de la liga
        season: Temporada (opcional)
        
    Returns:
        Lista de IDs de equipos
    """
    team_ids = []
    
    # Intentar primero cargar desde el índice local
    index_path = os.path.join('data', 'equipos', 'indice_equipos.json')
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
                
            for team_id, team_info in index.items():
                if team_info.get('liga') == league_code:
                    team_ids.append(team_id)
                    
            if team_ids:
                logger.info(f"Se encontraron {len(team_ids)} equipos en el índice local para la liga {league_code}")
                return team_ids
        except Exception as e:
            logger.error(f"Error al cargar índice de equipos: {e}")
    
    # Si no hay datos locales o hay error, intentar obtener de la fuente
    if source == 'football-data':
        api_key = os.environ.get('FOOTBALL_DATA_API_KEY', '')
        if not api_key:
            conf = config.ConfiguracionEntorno.obtener_config()
            api_key = conf.FUENTES_DATOS.get('football-data', {}).get('api_key', '')
            
        if api_key:
            api = FootballDataAPI({'api_key': api_key})
            teams = api.fetch_teams(competition_code=league_code, season=season)
            team_ids = [str(team.get('id')) for team in teams if team.get('id')]
            
    elif source == 'api-football':
        api_key = os.environ.get('API_FOOTBALL_KEY', '')
        api_host = os.environ.get('API_FOOTBALL_HOST', '')
        
        if api_key and api_host:
            api = APIFootball({'api_key': api_key, 'api_host': api_host})
            
            # Mapeo de códigos a IDs para API-Football
            league_ids = {
                'PD': 140,  # LaLiga
                'PL': 39,   # Premier League
                'BL1': 78,  # Bundesliga
                'SA': 135,  # Serie A
                'FL1': 61   # Ligue 1
            }
            
            league_id = league_ids.get(league_code)
            if league_id:
                season_year = season or datetime.now().year
                teams = api.fetch_teams(league=league_id, season=season_year)
                team_ids = [str(team.get('id')) for team in teams if team.get('id')]
    
    logger.info(f"Se obtuvieron {len(team_ids)} equipos de la API para la liga {league_code}")
    return team_ids

def update_from_football_data(args) -> None:
    """
    Actualiza jugadores desde Football-Data.org
    
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
        
        # Determinar equipos a actualizar
        team_ids = []
        if args.team:
            team_ids = [args.team]
        elif args.league:
            team_ids = get_team_ids_from_league('football-data', args.league, args.season)
        
        if not team_ids:
            logger.error("No se han especificado equipos para actualizar")
            return
        
        # Actualizar cada equipo
        for team_id in team_ids:
            try:
                logger.info(f"Obteniendo jugadores del equipo {team_id}")
                players = api.fetch_players(team_id=team_id)
                save_players_to_database(players, team_id, 'football-data')
                
                # Respetar límites de tasa
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error al obtener jugadores del equipo {team_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error general en actualización desde Football-Data.org: {e}")

def update_from_api_football(args) -> None:
    """
    Actualiza jugadores desde API-Football
    
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
        
        # Determinar temporada
        season = args.season or datetime.now().year
        
        # Determinar equipos a actualizar
        team_ids = []
        if args.team:
            team_ids = [args.team]
        elif args.league:
            # Mapeo de códigos a IDs para API-Football
            league_ids = {
                'PD': 140,  # LaLiga
                'PL': 39,   # Premier League
                'BL1': 78,  # Bundesliga
                'SA': 135,  # Serie A
                'FL1': 61   # Ligue 1
            }
            
            league_id = league_ids.get(args.league)
            if league_id:
                # Primero obtener los equipos de la liga
                teams = api.fetch_teams(league=league_id, season=season)
                team_ids = [str(team.get('id')) for team in teams if team.get('id')]
            else:
                # Si se proporciona directamente el ID numérico
                try:
                    league_id = int(args.league)
                    teams = api.fetch_teams(league=league_id, season=season)
                    team_ids = [str(team.get('id')) for team in teams if team.get('id')]
                except ValueError:
                    logger.error(f"Código de liga no válido: {args.league}")
                
        if not team_ids:
            logger.error("No se han especificado equipos para actualizar")
            return
        
        # Actualizar cada equipo
        for team_id in team_ids:
            try:
                logger.info(f"Obteniendo jugadores del equipo {team_id}")
                
                # La API podría requerir paginación
                all_players = []
                page = 1
                max_pages = 5  # Límite por seguridad
                
                while page <= max_pages:
                    players = api.fetch_players(team=team_id, season=season, page=page)
                    all_players.extend(players)
                    
                    if len(players) < 20:  # Si devuelve menos de lo esperado, probablemente es la última página
                        break
                        
                    page += 1
                    time.sleep(1)  # Respetar límites de tasa
                
                save_players_to_database(all_players, team_id, 'api-football')
                
            except Exception as e:
                logger.error(f"Error al obtener jugadores del equipo {team_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error general en actualización desde API-Football: {e}")

def main():
    """Función principal del script."""
    args = parse_args()
    
    logger.info(f"Iniciando actualización de jugadores desde fuente: {args.source}")
    
    if not args.team and not args.league:
        logger.error("Se requiere especificar --team o --league")
        return
    
    try:
        if args.source == 'football-data':
            update_from_football_data(args)
        elif args.source == 'api-football':
            update_from_api_football(args)
        elif args.source == 'all':
            update_from_football_data(args)
            update_from_api_football(args)
    except Exception as e:
        logger.error(f"Error general en actualización de jugadores: {e}")
    
    logger.info("Proceso de actualización de jugadores completado")

if __name__ == '__main__':
    main()
