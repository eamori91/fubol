#!/usr/bin/env python
"""
Script para actualizar la base de datos con datos de API externas.

Este script sincroniza la información de equipos, jugadores y partidos
desde las APIs externas a la base de datos local.

Uso:
    python update_database.py [--source SOURCE] [--data TYPE]

Argumentos:
    --source SOURCE    Fuente de datos a utilizar (football-data, api-football, all)
    --data TYPE        Tipo de datos a actualizar (teams, players, matches, all)
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
import json
import time
from typing import Dict, Any, List, Optional, Union

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.football_data_api import FootballDataAPI
    from utils.api_football import APIFootball
    from utils.database import db_manager
    import config
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("¿Has instalado todas las dependencias? Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'database_update.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('update_database')

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Actualiza la base de datos con datos de API')
    parser.add_argument('--source', choices=['football-data', 'api-football', 'all'],
                        default='all', help='Fuente de datos a utilizar')
    parser.add_argument('--data', choices=['teams', 'players', 'matches', 'all'],
                        default='all', help='Tipo de datos a actualizar')
    return parser.parse_args()

def init_apis() -> Dict[str, Any]:
    """
    Inicializa las conexiones a las APIs.
    
    Returns:
        Dict con las instancias de API inicializadas
    """
    apis = {}
    
    # Football-Data.org
    api_key_fd = os.environ.get('FOOTBALL_DATA_API_KEY', '')
    if api_key_fd:
        try:
            apis['football-data'] = FootballDataAPI({'api_key': api_key_fd})
            logger.info("API Football-Data.org inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar Football-Data.org API: {e}")
    else:
        logger.warning("No se encontró API key para Football-Data.org")
    
    # API-Football
    api_key_af = os.environ.get('API_FOOTBALL_KEY', '')
    api_host_af = os.environ.get('API_FOOTBALL_HOST', '')
    if api_key_af and api_host_af:
        try:
            apis['api-football'] = APIFootball({'api_key': api_key_af, 'api_host': api_host_af})
            logger.info("API-Football inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar API-Football: {e}")
    else:
        logger.warning("No se encontraron credenciales para API-Football")
    
    return apis

def update_leagues(api_name: str, api: Union[FootballDataAPI, APIFootball]):
    """
    Actualiza la información de ligas/competiciones en la base de datos.
    
    Args:
        api_name: Nombre de la API ('football-data' o 'api-football')
        api: Instancia de la API
    """
    logger.info(f"Actualizando ligas desde {api_name}...")
    
    try:
        # Obtener ligas/competiciones
        if api_name == 'football-data':
            competitions = api.fetch_competitions()
        else:  # api-football
            current_year = datetime.now().year
            competitions = api.fetch_leagues(current=True)
        
        if not competitions:
            logger.warning(f"No se obtuvieron ligas desde {api_name}")
            return
            
        logger.info(f"Se obtuvieron {len(competitions)} ligas/competiciones")
        
        # Procesar e insertar en la base de datos
        for comp in competitions:
            try:
                # Adaptar formato según la API
                if api_name == 'football-data':
                    liga_data = {
                        'codigo': comp.get('code', ''),
                        'nombre': comp.get('name', ''),
                        'pais': comp.get('area', {}).get('name', ''),
                        'temporada_actual': comp.get('currentSeason', {}).get('startDate', '')[:4] + '-' + 
                                          comp.get('currentSeason', {}).get('endDate', '')[-2:],
                        'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:  # api-football
                    liga_data = {
                        'codigo': comp.get('league', {}).get('id', ''),
                        'nombre': comp.get('league', {}).get('name', ''),
                        'pais': comp.get('country', {}).get('name', ''),
                        'temporada_actual': str(comp.get('seasons', [{}])[-1].get('year', '')),
                        'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                
                # Verificar si ya existe
                existing = db_manager.get_single_result(
                    "SELECT id FROM ligas WHERE codigo = :codigo", 
                    {'codigo': liga_data['codigo']}
                )
                
                if existing:
                    # Actualizar
                    liga_id = existing['id']
                    cols = ", ".join([f"{col} = :{col}" for col in liga_data.keys()])
                    update_query = f"UPDATE ligas SET {cols} WHERE id = :id"
                    params = liga_data.copy()
                    params['id'] = liga_id
                    
                    db_manager.execute_query(update_query, params)
                    logger.info(f"Actualizada liga: {liga_data['nombre']} ({liga_data['codigo']})")
                else:
                    # Insertar nueva
                    liga_id = db_manager.insert('ligas', liga_data)
                    logger.info(f"Insertada nueva liga: {liga_data['nombre']} ({liga_data['codigo']}) con ID {liga_id}")
                    
            except Exception as e:
                logger.error(f"Error al procesar liga {comp.get('name', 'desconocida')}: {e}")
                
        logger.info(f"Actualización de ligas desde {api_name} completada")
        
    except Exception as e:
        logger.error(f"Error al actualizar ligas desde {api_name}: {e}")

def update_teams(api_name: str, api: Union[FootballDataAPI, APIFootball]):
    """
    Actualiza la información de equipos en la base de datos.
    
    Args:
        api_name: Nombre de la API ('football-data' o 'api-football')
        api: Instancia de la API
    """
    logger.info(f"Actualizando equipos desde {api_name}...")
    
    try:
        # Obtener ligas disponibles
        ligas = db_manager.execute_query("SELECT id, codigo, nombre, temporada_actual FROM ligas")
        
        if not ligas:
            logger.warning("No hay ligas en la base de datos. Ejecuta primero la actualización de ligas.")
            return
        
        for liga in ligas:
            try:
                # Obtener equipos según la API
                if api_name == 'football-data':
                    teams = api.fetch_teams(competition_code=liga['codigo'])
                else:  # api-football
                    current_year = int(liga['temporada_actual'].split('-')[0])
                    teams = api.fetch_teams(league=liga['codigo'], season=current_year)
                
                if not teams:
                    logger.warning(f"No se obtuvieron equipos para {liga['nombre']} desde {api_name}")
                    continue
                    
                logger.info(f"Se obtuvieron {len(teams)} equipos para {liga['nombre']}")
                
                # Procesar e insertar en la base de datos
                for team in teams:
                    try:
                        # Adaptar formato según la API
                        if api_name == 'football-data':
                            equipo_data = {
                                'id_externo': str(team.get('id', '')),
                                'nombre': team.get('name', ''),
                                'nombre_corto': team.get('shortName', team.get('tla', '')),
                                'liga_id': liga['id'],
                                'pais': team.get('area', {}).get('name', ''),
                                'fundacion': team.get('founded', None),
                                'estadio': team.get('venue', ''),
                                'escudo_url': team.get('crest', ''),
                                'fuente': api_name,
                                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        else:  # api-football
                            equipo_data = {
                                'id_externo': str(team.get('team', {}).get('id', '')),
                                'nombre': team.get('team', {}).get('name', ''),
                                'nombre_corto': team.get('team', {}).get('code', ''),
                                'liga_id': liga['id'],
                                'pais': team.get('team', {}).get('country', ''),
                                'fundacion': team.get('team', {}).get('founded', None),
                                'estadio': team.get('venue', {}).get('name', ''),
                                'escudo_url': team.get('team', {}).get('logo', ''),
                                'fuente': api_name,
                                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        
                        # Verificar si ya existe por ID externo
                        existing = db_manager.get_single_result(
                            "SELECT id FROM equipos WHERE id_externo = :id_externo", 
                            {'id_externo': equipo_data['id_externo']}
                        )
                        
                        if existing:
                            # Actualizar
                            equipo_id = existing['id']
                            cols = ", ".join([f"{col} = :{col}" for col in equipo_data.keys()])
                            update_query = f"UPDATE equipos SET {cols} WHERE id = :id"
                            params = equipo_data.copy()
                            params['id'] = equipo_id
                            
                            db_manager.execute_query(update_query, params)
                            logger.info(f"Actualizado equipo: {equipo_data['nombre']} (ID: {equipo_id})")
                        else:
                            # Insertar nuevo
                            equipo_data['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            equipo_id = db_manager.insert('equipos', equipo_data)
                            logger.info(f"Insertado nuevo equipo: {equipo_data['nombre']} con ID {equipo_id}")
                            
                    except Exception as e:
                        logger.error(f"Error al procesar equipo {team.get('name', 'desconocido')}: {e}")
                
                logger.info(f"Actualización de equipos para {liga['nombre']} completada")
                
                # Pausa para evitar límites de API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error al actualizar equipos para {liga['nombre']}: {e}")
                
        logger.info(f"Actualización de equipos desde {api_name} completada")
        
    except Exception as e:
        logger.error(f"Error al actualizar equipos desde {api_name}: {e}")

def update_players(api_name: str, api: Union[FootballDataAPI, APIFootball]):
    """
    Actualiza la información de jugadores en la base de datos.
    
    Args:
        api_name: Nombre de la API ('football-data' o 'api-football')
        api: Instancia de la API
    """
    logger.info(f"Actualizando jugadores desde {api_name}...")
    
    try:
        # Obtener equipos
        equipos = db_manager.execute_query("SELECT id, id_externo, nombre FROM equipos")
        
        if not equipos:
            logger.warning("No hay equipos en la base de datos. Ejecuta primero la actualización de equipos.")
            return
            
        # Limitar la cantidad de equipos para no exceder límites de API
        max_equipos = 5  # Ajustar según necesidad
        equipos_muestra = equipos[:max_equipos]
        
        logger.info(f"Actualizando jugadores para {len(equipos_muestra)} equipos (de {len(equipos)} totales)")
        
        for equipo in equipos_muestra:
            try:
                # Obtener jugadores según la API
                if api_name == 'football-data':
                    players = api.fetch_players(team_id=equipo['id_externo'])
                else:  # api-football
                    # Obtener liga y temporada del equipo
                    equipo_info = db_manager.get_single_result(
                        """
                        SELECT e.id, l.codigo as liga_codigo, l.temporada_actual 
                        FROM equipos e
                        JOIN ligas l ON e.liga_id = l.id
                        WHERE e.id = :equipo_id
                        """, 
                        {'equipo_id': equipo['id']}
                    )
                    
                    if not equipo_info:
                        logger.warning(f"No se encontró información completa para el equipo {equipo['nombre']}")
                        continue
                        
                    liga_codigo = equipo_info['liga_codigo']
                    temporada = equipo_info['temporada_actual']
                    current_year = int(temporada.split('-')[0])
                    
                    players = api.fetch_players(
                        team=equipo['id_externo'],
                        league=liga_codigo,
                        season=current_year
                    )
                
                if not players:
                    logger.warning(f"No se obtuvieron jugadores para {equipo['nombre']} desde {api_name}")
                    continue
                    
                logger.info(f"Se obtuvieron {len(players)} jugadores para {equipo['nombre']}")
                
                # Procesar e insertar en la base de datos
                for player in players:
                    try:
                        # Adaptar formato según la API
                        if api_name == 'football-data':
                            jugador_data = {
                                'id_externo': str(player.get('id', '')),
                                'nombre': player.get('name', '').split(' ')[0],
                                'apellido': ' '.join(player.get('name', '').split(' ')[1:]),
                                'equipo_id': equipo['id'],
                                'posicion': player.get('position', ''),
                                'nacionalidad': player.get('nationality', ''),
                                'fecha_nacimiento': player.get('dateOfBirth', None),
                                'dorsal': player.get('shirtNumber', None),
                                'foto_url': '',
                                'fuente': api_name,
                                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        else:  # api-football
                            jugador_data = {
                                'id_externo': str(player.get('player', {}).get('id', '')),
                                'nombre': player.get('player', {}).get('firstname', ''),
                                'apellido': player.get('player', {}).get('lastname', ''),
                                'equipo_id': equipo['id'],
                                'posicion': player.get('statistics', [{}])[0].get('games', {}).get('position', ''),
                                'nacionalidad': player.get('player', {}).get('nationality', ''),
                                'fecha_nacimiento': player.get('player', {}).get('birth', {}).get('date', None),
                                'altura': player.get('player', {}).get('height', '').replace('cm', '').strip() or None,
                                'peso': player.get('player', {}).get('weight', '').replace('kg', '').strip() or None,
                                'dorsal': player.get('statistics', [{}])[0].get('games', {}).get('number', None),
                                'foto_url': player.get('player', {}).get('photo', ''),
                                'fuente': api_name,
                                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        
                        # Verificar si ya existe por ID externo
                        existing = db_manager.get_single_result(
                            "SELECT id FROM jugadores WHERE id_externo = :id_externo", 
                            {'id_externo': jugador_data['id_externo']}
                        )
                        
                        if existing:
                            # Actualizar
                            jugador_id = existing['id']
                            cols = ", ".join([f"{col} = :{col}" for col in jugador_data.keys()])
                            update_query = f"UPDATE jugadores SET {cols} WHERE id = :id"
                            params = jugador_data.copy()
                            params['id'] = jugador_id
                            
                            db_manager.execute_query(update_query, params)
                            logger.debug(f"Actualizado jugador: {jugador_data['nombre']} {jugador_data['apellido']} (ID: {jugador_id})")
                        else:
                            # Insertar nuevo
                            jugador_data['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            jugador_id = db_manager.insert('jugadores', jugador_data)
                            logger.debug(f"Insertado nuevo jugador: {jugador_data['nombre']} {jugador_data['apellido']} con ID {jugador_id}")
                            
                    except Exception as e:
                        logger.error(f"Error al procesar jugador {player.get('name', 'desconocido')}: {e}")
                
                logger.info(f"Actualización de jugadores para {equipo['nombre']} completada")
                
                # Pausa para evitar límites de API
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error al actualizar jugadores para {equipo['nombre']}: {e}")
                
        logger.info(f"Actualización de jugadores desde {api_name} completada")
        
    except Exception as e:
        logger.error(f"Error al actualizar jugadores desde {api_name}: {e}")

def update_matches(api_name: str, api: Union[FootballDataAPI, APIFootball]):
    """
    Actualiza la información de partidos en la base de datos.
    
    Args:
        api_name: Nombre de la API ('football-data' o 'api-football')
        api: Instancia de la API
    """
    logger.info(f"Actualizando partidos desde {api_name}...")
    
    try:
        # Obtener ligas disponibles
        ligas = db_manager.execute_query("SELECT id, codigo, nombre, temporada_actual FROM ligas")
        
        if not ligas:
            logger.warning("No hay ligas en la base de datos. Ejecuta primero la actualización de ligas.")
            return
            
        # Rangos de fechas
        fecha_desde = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        fecha_hasta = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        for liga in ligas:
            try:
                # Obtener partidos según la API
                if api_name == 'football-data':
                    matches = api.fetch_matches(
                        competition_code=liga['codigo'],
                        date_from=fecha_desde,
                        date_to=fecha_hasta
                    )
                else:  # api-football
                    current_year = int(liga['temporada_actual'].split('-')[0])
                    matches = api.fetch_matches(
                        league=liga['codigo'],
                        from_=fecha_desde,
                        to=fecha_hasta,
                        season=current_year
                    )
                
                if not matches:
                    logger.warning(f"No se obtuvieron partidos para {liga['nombre']} desde {api_name}")
                    continue
                    
                logger.info(f"Se obtuvieron {len(matches)} partidos para {liga['nombre']}")
                
                # Procesar e insertar en la base de datos
                for match in matches:
                    try:
                        # Adaptar formato según la API
                        if api_name == 'football-data':
                            # Obtener IDs de equipos
                            equipo_local = db_manager.get_single_result(
                                "SELECT id FROM equipos WHERE id_externo = :id_externo",
                                {'id_externo': str(match.get('homeTeam', {}).get('id', ''))}
                            )
                            
                            equipo_visitante = db_manager.get_single_result(
                                "SELECT id FROM equipos WHERE id_externo = :id_externo",
                                {'id_externo': str(match.get('awayTeam', {}).get('id', ''))}
                            )
                            
                            if not equipo_local or not equipo_visitante:
                                logger.warning(f"No se encontró equipo local o visitante para el partido {match.get('id', '')}")
                                continue
                                
                            partido_data = {
                                'id_externo': str(match.get('id', '')),
                                'liga_id': liga['id'],
                                'equipo_local_id': equipo_local['id'],
                                'equipo_visitante_id': equipo_visitante['id'],
                                'fecha': match.get('utcDate', '')[:19].replace('T', ' '),
                                'estado': match.get('status', 'SCHEDULED'),
                                'jornada': match.get('matchday', None),
                                'temporada': liga['temporada_actual'],
                                'estadio': match.get('venue', ''),
                                'arbitro': '',  # No disponible en esta API
                                'goles_local': match.get('score', {}).get('fullTime', {}).get('home', None),
                                'goles_visitante': match.get('score', {}).get('fullTime', {}).get('away', None),
                                'resultado_primer_tiempo_local': match.get('score', {}).get('halfTime', {}).get('home', None),
                                'resultado_primer_tiempo_visitante': match.get('score', {}).get('halfTime', {}).get('away', None),
                                'fuente': api_name,
                                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        else:  # api-football
                            # Obtener IDs de equipos
                            equipo_local = db_manager.get_single_result(
                                "SELECT id FROM equipos WHERE id_externo = :id_externo",
                                {'id_externo': str(match.get('teams', {}).get('home', {}).get('id', ''))}
                            )
                            
                            equipo_visitante = db_manager.get_single_result(
                                "SELECT id FROM equipos WHERE id_externo = :id_externo",
                                {'id_externo': str(match.get('teams', {}).get('away', {}).get('id', ''))}
                            )
                            
                            if not equipo_local or not equipo_visitante:
                                logger.warning(f"No se encontró equipo local o visitante para el partido {match.get('fixture', {}).get('id', '')}")
                                continue
                                
                            # Mapear estado
                            estado_map = {
                                'Match Finished': 'FINISHED',
                                'Not Started': 'SCHEDULED',
                                'Time to be defined': 'SCHEDULED',
                                'Match Postponed': 'POSTPONED',
                                'Match Suspended': 'SUSPENDED',
                                'Match Cancelled': 'CANCELLED',
                                'Match Abandoned': 'ABANDONED',
                                'In Progress': 'IN_PLAY'
                            }
                            
                            estado = estado_map.get(match.get('fixture', {}).get('status', {}).get('long', ''), 'SCHEDULED')
                                
                            partido_data = {
                                'id_externo': str(match.get('fixture', {}).get('id', '')),
                                'liga_id': liga['id'],
                                'equipo_local_id': equipo_local['id'],
                                'equipo_visitante_id': equipo_visitante['id'],
                                'fecha': match.get('fixture', {}).get('date', '')[:19].replace('T', ' '),
                                'estado': estado,
                                'jornada': match.get('league', {}).get('round', '').split(' - ')[-1] if match.get('league', {}).get('round') else None,
                                'temporada': liga['temporada_actual'],
                                'estadio': match.get('fixture', {}).get('venue', {}).get('name', ''),
                                'arbitro': match.get('fixture', {}).get('referee', ''),
                                'goles_local': match.get('goals', {}).get('home', None),
                                'goles_visitante': match.get('goals', {}).get('away', None),
                                'resultado_primer_tiempo_local': match.get('score', {}).get('halftime', {}).get('home', None),
                                'resultado_primer_tiempo_visitante': match.get('score', {}).get('halftime', {}).get('away', None),
                                'fuente': api_name,
                                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        
                        # Verificar si ya existe por ID externo
                        existing = db_manager.get_single_result(
                            "SELECT id FROM partidos WHERE id_externo = :id_externo", 
                            {'id_externo': partido_data['id_externo']}
                        )
                        
                        if existing:
                            # Actualizar
                            partido_id = existing['id']
                            cols = ", ".join([f"{col} = :{col}" for col in partido_data.keys()])
                            update_query = f"UPDATE partidos SET {cols} WHERE id = :id"
                            params = partido_data.copy()
                            params['id'] = partido_id
                            
                            db_manager.execute_query(update_query, params)
                            logger.debug(f"Actualizado partido ID: {partido_id}")
                        else:
                            # Insertar nuevo
                            partido_data['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            partido_id = db_manager.insert('partidos', partido_data)
                            logger.debug(f"Insertado nuevo partido con ID {partido_id}")
                            
                    except Exception as e:
                        logger.error(f"Error al procesar partido {match.get('id', 'desconocido')}: {e}")
                
                logger.info(f"Actualización de partidos para {liga['nombre']} completada")
                
                # Pausa para evitar límites de API
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error al actualizar partidos para {liga['nombre']}: {e}")
                
        logger.info(f"Actualización de partidos desde {api_name} completada")
        
    except Exception as e:
        logger.error(f"Error al actualizar partidos desde {api_name}: {e}")

def main():
    """Función principal del script."""
    args = parse_args()
    
    logger.info("Iniciando actualización de base de datos")
    
    # Inicializar APIs
    apis = init_apis()
    
    if not apis:
        logger.error("No se pudo inicializar ninguna API. Verifica las credenciales.")
        return
    
    # Determinar APIs a utilizar
    api_sources = list(apis.keys()) if args.source == 'all' else [args.source]
    api_sources = [s for s in api_sources if s in apis]
    
    if not api_sources:
        logger.error(f"No hay APIs disponibles para la fuente: {args.source}")
        return
        
    logger.info(f"Actualizando datos desde: {', '.join(api_sources)}")
    
    # Actualizar datos según el tipo solicitado
    for api_name in api_sources:
        api = apis[api_name]
        
        # Ligas/competiciones
        if args.data in ['all', 'teams']:
            update_leagues(api_name, api)
            
            # Pequeña pausa
            time.sleep(1)
        
        # Equipos
        if args.data in ['all', 'teams']:
            update_teams(api_name, api)
            
            # Pequeña pausa
            time.sleep(1)
            
        # Jugadores
        if args.data in ['all', 'players']:
            update_players(api_name, api)
            
            # Pequeña pausa
            time.sleep(1)
            
        # Partidos
        if args.data in ['all', 'matches']:
            update_matches(api_name, api)
    
    logger.info("Actualización de base de datos completada")

if __name__ == '__main__':
    main()
