"""
Adaptador para la API de API-Football (api-sports.io)
https://www.api-football.com/

Este módulo proporciona una clase que implementa la interfaz BaseDataFetcher
para obtener datos de API-Football
"""

import requests
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, TypedDict

from utils.data_fetcher import BaseDataFetcher

logger = logging.getLogger('APIFootball')

class APIFootball(BaseDataFetcher):
    """
    Adaptador para la API API-Football (api-sports.io)
    Implementa la interfaz BaseDataFetcher
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el adaptador de API-Football
        
        Args:
            config: Diccionario con configuración (api_key, etc.)
        """
        super().__init__(config if config is not None else {})
        self.base_url = 'https://v3.football.api-sports.io'
        
        # Intentar obtener API key y host de configuración o variables de entorno
        self.api_key = config.get('api_key', '') if config else os.environ.get('API_FOOTBALL_KEY', '')
        self.api_host = config.get('api_host', '') if config else os.environ.get('API_FOOTBALL_HOST', 'v3.football.api-sports.io')
        
        if not self.api_key:
            logger.warning("No se ha proporcionado API key para API-Football")
            
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.api_host
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una petición a la API
        
        Args:
            endpoint: Endpoint de la API (ej. /leagues)
            params: Parámetros de la petición
            
        Returns:
            Diccionario con la respuesta JSON
        """
        if not self.api_key:
            raise ValueError("Se requiere API key para API-Football")
        
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Control de errores y límites de tasa
            if response.status_code == 429:
                # Too many requests
                logger.warning(f"Límite de tasa alcanzado. Esperando antes de reintentar.")
                self.rate_limit_wait(60)  # Esperar 60 segundos
                return self._make_request(endpoint, params)
                
            # Verificar información de uso de API
            if 'x-ratelimit-remaining' in response.headers:
                remaining = response.headers['x-ratelimit-remaining']
                if int(remaining) < 5:
                    logger.warning(f"¡Pocas peticiones restantes! Quedan: {remaining}")
            
            # Manejar otros errores
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al realizar petición a {url}: {e}")
            return {}
    
    def fetch_teams(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene datos de equipos
        
        Args:
            **kwargs: Parámetros opcionales
                league: ID de la liga
                season: Temporada (ej. 2022)
                country: País
            
        Returns:
            Lista de diccionarios con información de equipos
        """
        endpoint = "/teams"
        params = {}
        
        # Filtrar por liga, temporada o país
        if 'league' in kwargs:
            params['league'] = kwargs['league']
        if 'season' in kwargs:
            params['season'] = kwargs['season']
        if 'country' in kwargs:
            params['country'] = kwargs['country']
            
        if not params:
            logger.warning("No se han especificado filtros para equipos. Se requiere al menos un filtro.")
            return []
        
        logger.info(f"Obteniendo equipos con los siguientes filtros: {params}")
        
        data = self._make_request(endpoint, params)
        teams = []
        
        if 'response' in data and data['response']:
            # Transformar datos al formato interno
            for team_data in data['response']:
                team = team_data.get('team', {})
                venue = team_data.get('venue', {})
                
                teams.append({
                    'id': team.get('id'),
                    'nombre': team.get('name'),
                    'nombre_corto': team.get('code'),
                    'pais': team.get('country'),
                    'fundacion': team.get('founded'),
                    'estadio': venue.get('name'),
                    'capacidad_estadio': venue.get('capacity'),
                    'ciudad': venue.get('city'),
                    'logo_url': team.get('logo')
                })
                
            # Guardar datos en cache
            filename = f"teams_{kwargs.get('league', '')}_{kwargs.get('season', '')}"
            self.save_to_json(teams, filename)
            
        logger.info(f"Equipos obtenidos: {len(teams)}")
        return teams
    
    def fetch_players(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene datos de jugadores
        
        Args:
            **kwargs: Parámetros opcionales
                team: ID del equipo
                league: ID de la liga
                season: Temporada
                id: ID del jugador
            
        Returns:
            Lista de diccionarios con información de jugadores
        """
        endpoint = "/players"
        params = {}
        
        # Filtrar por equipo, liga, temporada o ID
        if 'team' in kwargs:
            params['team'] = kwargs['team']
        if 'league' in kwargs:
            params['league'] = kwargs['league']
        if 'season' in kwargs and 'league' in params:
            # La temporada requiere que se especifique una liga
            params['season'] = kwargs['season']
        if 'id' in kwargs:
            params['id'] = kwargs['id']
            
        if not params:
            logger.warning("No se han especificado filtros para jugadores. Se requiere al menos un filtro.")
            return []
            
        # Añadir paginación para evitar límites de tasa
        params['page'] = kwargs.get('page', 1)
            
        logger.info(f"Obteniendo jugadores con los siguientes filtros: {params}")
        
        data = self._make_request(endpoint, params)
        players = []
        
        if 'response' in data and data['response']:
            # Transformar datos al formato interno
            for player_data in data['response']:
                player = player_data.get('player', {})
                statistics = player_data.get('statistics', [])
                
                player_info = {
                    'id': player.get('id'),
                    'nombre': player.get('name'),
                    'apellido': player.get('lastname'),
                    'edad': player.get('age'),
                    'fecha_nacimiento': player.get('birth', {}).get('date'),
                    'nacionalidad': player.get('nationality'),
                    'altura': player.get('height'),
                    'peso': player.get('weight'),
                    'foto_url': player.get('photo')
                }
                
                # Añadir estadísticas si están disponibles
                if statistics and len(statistics) > 0:
                    stat = statistics[0]  # Tomar las primeras estadísticas
                    team = stat.get('team', {})
                    league = stat.get('league', {})
                    games = stat.get('games', {})
                    
                    player_info.update({
                        'equipo_id': team.get('id'),
                        'equipo_nombre': team.get('name'),
                        'liga': league.get('name'),
                        'temporada': stat.get('league', {}).get('season'),
                        'posicion': stat.get('games', {}).get('position'),
                        'dorsal': stat.get('games', {}).get('number'),
                        'partidos_jugados': games.get('appearences'),
                        'minutos_jugados': games.get('minutes'),
                        'goles': stat.get('goals', {}).get('total'),
                        'asistencias': stat.get('goals', {}).get('assists')
                    })
                    
                players.append(player_info)
                
            # Guardar datos en cache
            team_id = kwargs.get('team', '')
            filename = f"players_team_{team_id}_page_{params['page']}"
            self.save_to_json(players, filename)
            
            # Comprobar si hay más páginas
            if data.get('paging', {}).get('current') < data.get('paging', {}).get('total'):
                logger.info(f"Hay más jugadores disponibles en páginas adicionales. Total: {data['paging']['total']}")
                
        logger.info(f"Jugadores obtenidos: {len(players)}")
        return players
    
    def fetch_matches(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene datos de partidos
        
        Args:
            **kwargs: Parámetros opcionales
                league: ID de la liga
                season: Temporada
                team: ID del equipo
                date: Fecha específica (YYYY-MM-DD)
                from: Fecha inicio (YYYY-MM-DD)
                to: Fecha fin (YYYY-MM-DD)
                status: Estado del partido (NS=No comenzado, FT=Finalizado, etc.)
            
        Returns:
            Lista de diccionarios con información de partidos
        """
        endpoint = "/fixtures"
        params = {}
        
        # Aplicar filtros
        for key in ['league', 'season', 'team', 'date', 'from', 'to', 'status']:
            if key in kwargs:
                params[key] = kwargs[key]
                
        # Si no hay filtros, usar la fecha actual
        if not params:
            params['date'] = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"Obteniendo partidos con los siguientes filtros: {params}")
        
        data = self._make_request(endpoint, params)
        matches = []
        
        if 'response' in data and data['response']:
            # Transformar datos al formato interno
            for match_data in data['response']:
                fixture = match_data.get('fixture', {})
                league = match_data.get('league', {})
                teams = match_data.get('teams', {})
                goals = match_data.get('goals', {})
                score = match_data.get('score', {})
                
                match_info = {
                    'id': fixture.get('id'),
                    'fecha': fixture.get('date'),
                    'estadio': fixture.get('venue', {}).get('name'),
                    'arbitro': fixture.get('referee'),
                    'estado': fixture.get('status', {}).get('short'),
                    'minuto_actual': fixture.get('status', {}).get('elapsed'),
                    'liga_id': league.get('id'),
                    'liga_nombre': league.get('name'),
                    'temporada': league.get('season'),
                    'jornada': league.get('round'),
                    'equipo_local_id': teams.get('home', {}).get('id'),
                    'equipo_local': teams.get('home', {}).get('name'),
                    'equipo_visitante_id': teams.get('away', {}).get('id'),
                    'equipo_visitante': teams.get('away', {}).get('name'),
                    'goles_local': goals.get('home'),
                    'goles_visitante': goals.get('away')
                }
                
                # Añadir resultados detallados si el partido ha finalizado
                if match_info['estado'] in ['FT', 'AET', 'PEN']:
                    match_info.update({
                        'resultado_primer_tiempo_local': score.get('halftime', {}).get('home'),
                        'resultado_primer_tiempo_visitante': score.get('halftime', {}).get('away'),
                        'resultado_segundo_tiempo_local': score.get('fulltime', {}).get('home'),
                        'resultado_segundo_tiempo_visitante': score.get('fulltime', {}).get('away'),
                        'resultado_prorroga_local': score.get('extratime', {}).get('home'),
                        'resultado_prorroga_visitante': score.get('extratime', {}).get('away'),
                        'resultado_penaltis_local': score.get('penalty', {}).get('home'),
                        'resultado_penaltis_visitante': score.get('penalty', {}).get('away')
                    })
                    
                matches.append(match_info)
                
            # Guardar datos en cache
            league_id = kwargs.get('league', 'all')
            date_str = kwargs.get('date', kwargs.get('from', datetime.now().strftime('%Y-%m-%d')))
            filename = f"matches_league_{league_id}_{date_str}"
            self.save_to_json(matches, filename)
            
        logger.info(f"Partidos obtenidos: {len(matches)}")
        return matches
    
    def fetch_leagues(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene información de ligas disponibles
        
        Args:
            **kwargs: Parámetros opcionales
                id: ID de la liga
                name: Nombre de la liga
                country: País
                season: Temporada
                current: Solo ligas actuales (True/False)
            
        Returns:
            Lista de diccionarios con información de ligas
        """
        endpoint = "/leagues"
        params = {}
        
        # Aplicar filtros
        for key in ['id', 'name', 'country', 'season', 'current']:
            if key in kwargs:
                params[key] = kwargs[key]
                
        logger.info(f"Obteniendo ligas con los siguientes filtros: {params}")
        
        data = self._make_request(endpoint, params)
        leagues = []
        
        if 'response' in data and data['response']:
            # Transformar datos al formato interno
            for league_data in data['response']:
                league = league_data.get('league', {})
                country = league_data.get('country', {})
                seasons = league_data.get('seasons', [])
                
                league_info = {
                    'id': league.get('id'),
                    'nombre': league.get('name'),
                    'tipo': league.get('type'),
                    'logo_url': league.get('logo'),
                    'pais': country.get('name'),
                    'codigo_pais': country.get('code'),
                    'bandera_url': country.get('flag'),
                    'temporadas_disponibles': len(seasons)
                }
                
                # Añadir información de la temporada actual si está disponible
                if seasons:
                    current_season = next((s for s in seasons if s.get('current')), seasons[-1])
                    league_info.update({
                        'temporada_actual': current_season.get('year'),
                        'fecha_inicio': current_season.get('start'),
                        'fecha_fin': current_season.get('end'),
                    })
                    
                leagues.append(league_info)
                
            # Guardar datos en cache
            filename = f"leagues_{kwargs.get('country', 'all')}_{kwargs.get('season', 'all')}"
            self.save_to_json(leagues, filename)
            
        logger.info(f"Ligas obtenidas: {len(leagues)}")
        return leagues
    
    def fetch_standings(self, **kwargs) -> Dict[str, Any]:
        """
        Obtiene clasificación de una liga
        
        Args:
            **kwargs: Parámetros opcionales
                league: ID de la liga (requerido)
                season: Temporada (requerido)
                team: ID del equipo (opcional)
            
        Returns:
            Diccionario con la clasificación
        """
        endpoint = "/standings"
        params = {}
        
        # Los parámetros league y season son obligatorios
        if 'league' not in kwargs:
            logger.error("Se requiere el ID de la liga para obtener la clasificación")
            return {}
            
        if 'season' not in kwargs:
            logger.error("Se requiere la temporada para obtener la clasificación")
            return {}
            
        params['league'] = kwargs['league']
        params['season'] = kwargs['season']
        
        if 'team' in kwargs:
            params['team'] = kwargs['team']
            
        logger.info(f"Obteniendo clasificación de liga {params['league']} temporada {params['season']}")
        
        data = self._make_request(endpoint, params)
        standings = {}
        
        if 'response' in data and data['response']:
            # La API puede devolver múltiples ligas
            for league_data in data['response']:
                league_info = league_data.get('league', {})
                league_id = league_info.get('id')
                league_name = league_info.get('name')
                
                league_standings = []
                
                # Puede haber múltiples grupos o clasificaciones
                for standing_group in league_info.get('standings', []):
                    group_name = "default"
                    if isinstance(standing_group, list):
                        # Formato para múltiples grupos
                        group_data = []
                        for team_data in standing_group:
                            group_data.append(self._transform_standing_team(team_data))
                        league_standings.append({
                            'group': group_name,
                            'teams': group_data
                        })
                    else:
                        # Caso para un único grupo
                        group_name = "default"
                        standings[league_id] = {
                            'league_name': league_name,
                            'season': params['season'],
                            'standings': [{
                                'group': group_name,
                                'teams': [self._transform_standing_team(standing_group)]
                            }]
                        }
                
                if league_standings:
                    standings[league_id] = {
                        'league_name': league_name,
                        'season': params['season'],
                        'standings': league_standings
                    }
            
            # Guardar datos en cache
            filename = f"standings_league_{params['league']}_season_{params['season']}"
            self.save_to_json(standings, filename)
            
        logger.info(f"Clasificaciones obtenidas para {len(standings)} ligas")
        return standings
    
    def _transform_standing_team(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma datos de un equipo en la clasificación al formato interno
        
        Args:
            team_data: Datos del equipo en la clasificación
            
        Returns:
            Diccionario con información transformada
        """
        team = team_data.get('team', {})
        stats = team_data.get('all', {})
        goals = stats.get('goals', {})
        
        return {
            'posicion': team_data.get('rank'),
            'equipo_id': team.get('id'),
            'equipo': team.get('name'),
            'puntos': team_data.get('points'),
            'jugados': stats.get('played'),
            'ganados': stats.get('win'),
            'empatados': stats.get('draw'),
            'perdidos': stats.get('lose'),
            'goles_favor': goals.get('for'),
            'goles_contra': goals.get('against'),
            'diferencia_goles': team_data.get('goalsDiff'),
            'forma': team_data.get('form'),
            'grupo': team_data.get('group')
        }
