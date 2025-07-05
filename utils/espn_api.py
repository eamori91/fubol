"""
Adaptador para la API no oficial de ESPN
https://github.com/eamori91/Public-ESPN-API

Este módulo proporciona una clase que implementa la interfaz BaseDataFetcher
para obtener datos de la API no oficial de ESPN.

NOTA: Esta API no es oficial y puede cambiar sin previo aviso.
ESPN no proporciona una API pública oficial documentada.
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from utils.data_fetcher import BaseDataFetcher

logger = logging.getLogger('ESPNAPI')

class ESPNAPI(BaseDataFetcher):
    """
    Adaptador para la API no oficial de ESPN
    Implementa la interfaz BaseDataFetcher
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el adaptador de ESPN API
        
        Args:
            config: Diccionario con configuración (opcional)
        """
        super().__init__(config if config is not None else {})
        
        # URLs base para las diferentes APIs de ESPN
        self.site_api_url = 'https://site.api.espn.com'
        self.core_api_url = 'https://sports.core.api.espn.com'
        self.web_api_url = 'https://site.web.api.espn.com'
        self.cdn_api_url = 'https://cdn.espn.com'
        
        # Mapeo de códigos de liga a identificadores ESPN
        self.league_mapping = {
            'PD': 'esp.1',      # LaLiga
            'PL': 'eng.1',      # Premier League
            'BL1': 'ger.1',     # Bundesliga
            'SA': 'ita.1',      # Serie A
            'FL1': 'fra.1',     # Ligue 1
            'PPL': 'por.1',     # Primeira Liga
            'DED': 'ned.1',     # Eredivisie
            'UCL': 'UEFA.CHAMPIONS', # UEFA Champions League
            'UEL': 'UEFA.EUROPA'     # UEFA Europa League
        }

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una petición a la API de ESPN
        
        Args:
            url: URL completa para la petición
            params: Parámetros de la petición
            
        Returns:
            Diccionario con la respuesta JSON
        """
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error en petición a ESPN API: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error al realizar petición a ESPN API: {str(e)}")
            return {}
    
    def fetch_leagues(self, current: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de ligas/competiciones disponibles
        
        Args:
            current: Si True, obtiene solo las ligas de la temporada actual
            
        Returns:
            Lista de ligas/competiciones
        """
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer"
        
        try:
            data = self._make_request(url)
            
            if not data or 'leagues' not in data:
                logger.warning("No se encontraron ligas en la respuesta de ESPN API")
                return []
            
            leagues = data['leagues']
            
            # Formatear datos al formato estándar del sistema
            formatted_leagues = []
            for league in leagues:
                formatted_league = {
                    'id': league.get('id', ''),
                    'nombre': league.get('name', ''),
                    'codigo': league.get('slug', ''),
                    'pais': league.get('groups', {}).get('countryCode', ''),
                    'temporada_actual': str(datetime.now().year),
                    'nivel': league.get('groups', {}).get('divisionId', 1),
                    'numero_equipos': 0,  # No disponible directamente
                    'fecha_inicio': None,  # No disponible directamente
                    'fecha_fin': None,     # No disponible directamente
                    'fuente': 'espn'
                }
                formatted_leagues.append(formatted_league)
                
            return formatted_leagues
            
        except Exception as e:
            logger.error(f"Error al obtener ligas desde ESPN API: {str(e)}")
            return []
    
    def fetch_teams(self, league: Optional[str] = None, season: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de equipos de una liga
        
        Args:
            league: Código de la liga (ej. PL, PD)
            season: Temporada (año)
            
        Returns:
            Lista de equipos
        """
        # Convertir código de liga al formato ESPN
        espn_league = self.league_mapping.get(league, league) if league else None
        
        if not espn_league:
            logger.warning(f"Código de liga no reconocido: {league}")
            return []
        
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer/{espn_league}/teams"
        
        try:
            data = self._make_request(url)
            
            if not data or 'teams' not in data:
                logger.warning(f"No se encontraron equipos para la liga {espn_league}")
                return []
            
            teams = data['teams']
            
            # Formatear datos al formato estándar del sistema
            formatted_teams = []
            for team in teams:
                formatted_team = {
                    'id': str(team.get('id', '')),
                    'nombre': team.get('name', ''),
                    'nombre_corto': team.get('shortDisplayName', ''),
                    'siglas': team.get('abbreviation', ''),
                    'pais': team.get('location', ''),
                    'fundacion': team.get('yearFounded', None),
                    'estadio': None,  # No disponible directamente
                    'entrenador': None,  # No disponible directamente
                    'escudo_url': team.get('logos', [{}])[0].get('href', '') if team.get('logos') else '',
                    'colores': None,  # No disponible directamente
                    'liga': league,
                    'fuente': 'espn'
                }
                formatted_teams.append(formatted_team)
                
            return formatted_teams
            
        except Exception as e:
            logger.error(f"Error al obtener equipos desde ESPN API: {str(e)}")
            return []
    
    def fetch_players(self, team_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de jugadores de un equipo
        
        Args:
            team_id: ID del equipo
            
        Returns:
            Lista de jugadores
        """
        if not team_id:
            logger.warning("No se proporcionó ID de equipo para obtener jugadores")
            return []
            
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer/teams/{team_id}/roster"
        
        try:
            data = self._make_request(url)
            
            if not data or 'athletes' not in data:
                logger.warning(f"No se encontraron jugadores para el equipo {team_id}")
                return []
                
            players = data['athletes']
            
            # Formatear datos al formato estándar del sistema
            formatted_players = []
            for player in players:
                # Obtener la posición formateada
                position = player.get('position', {}).get('name', '')
                
                # Convertir el formato de fecha si está disponible
                birth_date = None
                if 'birthDate' in player:
                    try:
                        birth_date = datetime.strptime(player['birthDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                    except Exception:
                        birth_date = None
                
                formatted_player = {
                    'id': str(player.get('id', '')),
                    'nombre': player.get('firstName', ''),
                    'apellido': player.get('lastName', ''),
                    'nombre_completo': player.get('fullName', ''),
                    'posicion': position,
                    'nacionalidad': player.get('citizenship', ''),
                    'fecha_nacimiento': birth_date,
                    'altura': player.get('height', 0),
                    'peso': player.get('weight', 0),
                    'dorsal': player.get('jersey', None),
                    'equipo_id': team_id,
                    'valor_mercado': None,  # No disponible directamente
                    'fuente': 'espn'
                }
                formatted_players.append(formatted_player)
                
            return formatted_players
            
        except Exception as e:
            logger.error(f"Error al obtener jugadores desde ESPN API: {str(e)}")
            return []
            
    def fetch_matches(self, league: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene partidos de una liga en un rango de fechas
        
        Args:
            league: Código de la liga (ej. PL, PD)
            date_from: Fecha inicial (YYYY-MM-DD)
            date_to: Fecha final (YYYY-MM-DD)
            
        Returns:
            Lista de partidos
        """
        # Convertir código de liga al formato ESPN
        espn_league = self.league_mapping.get(league, league) if league else None
        
        if not espn_league:
            logger.warning(f"Código de liga no reconocido: {league}")
            return []
            
        # Si no se proporciona fecha inicial, usar la actual
        if not date_from:
            date_from = datetime.now().strftime('%Y%m%d')
        else:
            # Convertir de YYYY-MM-DD a YYYYMMDD
            date_from = date_from.replace('-', '')
            
        # Si no se proporciona fecha final, usar 7 días después de la inicial
        if not date_to:
            date_to = (datetime.now() + timedelta(days=7)).strftime('%Y%m%d')
        else:
            # Convertir de YYYY-MM-DD a YYYYMMDD
            date_to = date_to.replace('-', '')
            
        # Construir URL para el scoreboard con rango de fechas
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer/{espn_league}/scoreboard"
        params = {
            'dates': f"{date_from}-{date_to}"
        }
        
        try:
            data = self._make_request(url, params)
            
            if not data or 'events' not in data:
                logger.warning(f"No se encontraron partidos para la liga {espn_league}")
                return []
                
            matches = data['events']
            
            # Formatear datos al formato estándar del sistema
            formatted_matches = []
            for match in matches:
                # Obtener datos de equipos
                competitors = match.get('competitions', [{}])[0].get('competitors', [])
                
                home_team = next((team for team in competitors if team.get('homeAway') == 'home'), {})
                away_team = next((team for team in competitors if team.get('homeAway') == 'away'), {})
                
                # Obtener resultado si está disponible
                home_score = home_team.get('score', 0)
                away_score = away_team.get('score', 0)
                
                # Estado del partido
                status = match.get('status', {}).get('type', {}).get('name', 'SCHEDULED')
                
                # Fecha y hora del partido en formato estándar
                match_date = match.get('date')
                formatted_date = None
                if match_date:
                    try:
                        formatted_date = datetime.strptime(match_date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%dT%H:%M:%S')
                    except Exception:
                        formatted_date = match_date
                        
                formatted_match = {
                    'id': str(match.get('id', '')),
                    'fecha': formatted_date,
                    'liga': league,
                    'equipo_local': home_team.get('team', {}).get('name', ''),
                    'equipo_local_id': str(home_team.get('team', {}).get('id', '')),
                    'equipo_visitante': away_team.get('team', {}).get('name', ''),
                    'equipo_visitante_id': str(away_team.get('team', {}).get('id', '')),
                    'resultado_local': int(home_score) if status == 'STATUS_FINAL' else None,
                    'resultado_visitante': int(away_score) if status == 'STATUS_FINAL' else None,
                    'estado': status,
                    'estadio': match.get('competitions', [{}])[0].get('venue', {}).get('fullName', ''),
                    'ciudad': match.get('competitions', [{}])[0].get('venue', {}).get('address', {}).get('city', ''),
                    'arbitro': None,  # No disponible directamente
                    'fuente': 'espn'
                }
                formatted_matches.append(formatted_match)
                
            return formatted_matches
            
        except Exception as e:
            logger.error(f"Error al obtener partidos desde ESPN API: {str(e)}")
            return []
            
    def fetch_standings(self, league: Optional[str] = None, season: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene la clasificación de una liga
        
        Args:
            league: Código de la liga (ej. PL, PD)
            season: Temporada (año)
            
        Returns:
            Lista de posiciones en la clasificación
        """
        # Convertir código de liga al formato ESPN
        espn_league = self.league_mapping.get(league, league) if league else None
        
        if not espn_league:
            logger.warning(f"Código de liga no reconocido: {league}")
            return []
            
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer/{espn_league}/standings"
        
        try:
            data = self._make_request(url)
            
            if not data or 'standings' not in data:
                logger.warning(f"No se encontró clasificación para la liga {espn_league}")
                return []
                
            standings_data = data['standings']
            
            # Extraer datos de clasificación
            formatted_standings = []
            
            # Buscar la sección de clasificación principal
            for entry in standings_data.get('entries', []):
                team_stats = entry.get('stats', [])
                
                # Buscar estadísticas relevantes
                rank = next((stat.get('value') for stat in team_stats if stat.get('name') == 'rank'), None)
                points = next((stat.get('value') for stat in team_stats if stat.get('name') == 'points'), None)
                games_played = next((stat.get('value') for stat in team_stats if stat.get('name') == 'gamesPlayed'), None)
                wins = next((stat.get('value') for stat in team_stats if stat.get('name') == 'wins'), None)
                losses = next((stat.get('value') for stat in team_stats if stat.get('name') == 'losses'), None)
                ties = next((stat.get('value') for stat in team_stats if stat.get('name') == 'ties'), None)
                goals_for = next((stat.get('value') for stat in team_stats if stat.get('name') == 'pointsFor'), None)
                goals_against = next((stat.get('value') for stat in team_stats if stat.get('name') == 'pointsAgainst'), None)
                
                team_data = entry.get('team', {})
                
                formatted_standing = {
                    'posicion': int(rank) if rank else 0,
                    'equipo': team_data.get('name', ''),
                    'equipo_id': str(team_data.get('id', '')),
                    'puntos': int(points) if points else 0,
                    'partidos_jugados': int(games_played) if games_played else 0,
                    'victorias': int(wins) if wins else 0,
                    'empates': int(ties) if ties else 0,
                    'derrotas': int(losses) if losses else 0,
                    'goles_favor': int(goals_for) if goals_for else 0,
                    'goles_contra': int(goals_against) if goals_against else 0,
                    'diferencia_goles': int(goals_for or 0) - int(goals_against or 0),
                    'liga': league,
                    'temporada': str(season) if season else str(datetime.now().year),
                    'fuente': 'espn'
                }
                formatted_standings.append(formatted_standing)
                
            return formatted_standings
            
        except Exception as e:
            logger.error(f"Error al obtener clasificación desde ESPN API: {str(e)}")
            return []

    def fetch_team_stats(self, team_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas de un equipo
        
        Args:
            team_id: ID del equipo
            
        Returns:
            Diccionario con estadísticas del equipo
        """
        if not team_id:
            logger.warning("No se proporcionó ID de equipo para obtener estadísticas")
            return {}
            
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer/teams/{team_id}/statistics"
        
        try:
            data = self._make_request(url)
            
            if not data or 'stats' not in data:
                logger.warning(f"No se encontraron estadísticas para el equipo {team_id}")
                return {}
                
            # Extraer estadísticas relevantes
            stats = data['stats']
            
            # Formatear al formato estándar del sistema
            formatted_stats = {
                'equipo_id': team_id,
                'goles_favor': next((stat.get('value') for stat in stats if stat.get('name') == 'goals'), 0),
                'goles_contra': next((stat.get('value') for stat in stats if stat.get('name') == 'goalsAgainst'), 0),
                'posesion': next((stat.get('value') for stat in stats if stat.get('name') == 'possessionPct'), 0),
                'pases_completados': next((stat.get('value') for stat in stats if stat.get('name') == 'passes'), 0),
                'precision_pases': next((stat.get('value') for stat in stats if stat.get('name') == 'passPct'), 0),
                'tiros': next((stat.get('value') for stat in stats if stat.get('name') == 'shots'), 0),
                'tiros_puerta': next((stat.get('value') for stat in stats if stat.get('name') == 'shotsOnTarget'), 0),
                'precision_tiros': next((stat.get('value') for stat in stats if stat.get('name') == 'shotPct'), 0),
                'faltas': next((stat.get('value') for stat in stats if stat.get('name') == 'foulsCommitted'), 0),
                'tarjetas_amarillas': next((stat.get('value') for stat in stats if stat.get('name') == 'yellowCards'), 0),
                'tarjetas_rojas': next((stat.get('value') for stat in stats if stat.get('name') == 'redCards'), 0),
                'fuera_juego': next((stat.get('value') for stat in stats if stat.get('name') == 'offsides'), 0),
                'tiros_esquina': next((stat.get('value') for stat in stats if stat.get('name') == 'corners'), 0),
                'fuente': 'espn'
            }
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas desde ESPN API: {str(e)}")
            return {}
        
    def fetch_team(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene los datos de un equipo específico
        
        Args:
            team_id: ID del equipo
            
        Returns:
            Diccionario con datos del equipo o diccionario vacío si no se encuentra
        """
        if not team_id:
            logger.warning("No se proporcionó ID de equipo")
            return {}
            
        url = f"{self.site_api_url}/apis/site/v2/sports/soccer/teams/{team_id}"
        
        try:
            data = self._make_request(url)
            
            if not data or 'team' not in data:
                logger.warning(f"No se encontró el equipo con ID {team_id}")
                return {}
                
            team = data['team']
            
            # Formatear datos al formato estándar del sistema
            formatted_team = {
                'id': f"espn-{str(team.get('id', ''))}",
                'nombre': team.get('name', ''),
                'nombre_corto': team.get('shortDisplayName', ''),
                'siglas': team.get('abbreviation', ''),
                'pais': team.get('location', ''),
                'fundacion': team.get('yearFounded', None),
                'estadio': None,  # No disponible directamente
                'entrenador': None,  # No disponible directamente
                'escudo_url': team.get('logos', [{}])[0].get('href', '') if team.get('logos') else '',
                'colores': None,  # No disponible directamente
                'liga': team.get('leagues', [{}])[0].get('name', '') if team.get('leagues') else '',
                'fuente': 'espn-api'
            }
                
            return formatted_team
            
        except Exception as e:
            logger.error(f"Error al obtener equipo {team_id} desde ESPN API: {str(e)}")
            return {}
        
        # --- Métodos de compatibilidad con UnifiedDataAdapter ---
    
    def get_proximos_partidos(self, dias: int = 7) -> List[Dict[str, Any]]:
        """
        Obtiene los partidos próximos a disputarse.
        
        Args:
            dias: Número de días hacia adelante para buscar
            
        Returns:
            Lista de partidos próximos en formato estándar
        """
        date_from = datetime.now().strftime("%Y%m%d")
        date_to = (datetime.now() + timedelta(days=dias)).strftime("%Y%m%d")
        
        matches = self.fetch_matches(date_from=date_from, date_to=date_to)
        
        # Convertir al formato estándar esperado por UnifiedDataAdapter
        proximos_partidos = []
        
        for match in matches:
            try:
                partido = {
                    "id": str(match.get("id", "")),
                    "local": match.get("home_team", {}).get("name", ""),
                    "visitante": match.get("away_team", {}).get("name", ""),
                    "fecha": match.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "liga": match.get("league", {}).get("name", ""),
                    "estadio": match.get("venue", {}).get("name", ""),
                    "fuente": "espn_api"
                }
                proximos_partidos.append(partido)
            except Exception as e:
                logger.error(f"Error al procesar partido de ESPN API: {e}")
                
        return proximos_partidos
        
    def get_equipo(self, nombre_equipo: str) -> Dict[str, Any]:
        """
        Busca un equipo por nombre.
        
        Args:
            nombre_equipo: Nombre del equipo a buscar
            
        Returns:
            Datos del equipo en formato estándar
        """
        # Primero necesitamos buscar todos los equipos
        equipos = self.fetch_teams()
        
        # Normalizar el nombre para comparación
        nombre_normalizado = nombre_equipo.lower()
        
        # Buscar coincidencias
        for equipo in equipos:
            if nombre_equipo.lower() in equipo.get("name", "").lower():
                # Convertir al formato estándar
                return {
                    "id": str(equipo.get("id", "")),
                    "nombre": equipo.get("name", ""),
                    "pais": equipo.get("country", ""),
                    "liga": equipo.get("league", {}).get("name", ""),
                    "logo": equipo.get("logo", ""),
                    "estadio": equipo.get("venue", {}).get("name", ""),
                    "fuente": "espn_api"
                }
                
        # Si no se encuentra, devolver vacío
        return {}
        
    def get_equipo_por_id(self, equipo_id: str) -> Dict[str, Any]:
        """
        Obtiene información de un equipo por su ID.
        
        Args:
            equipo_id: ID del equipo
            
        Returns:
            Datos del equipo en formato estándar
        """
        try:
            equipo = self.fetch_team(team_id=equipo_id)
            
            if not equipo:
                return {}
                
            # Convertir al formato estándar
            return {
                "id": str(equipo.get("id", "")),
                "nombre": equipo.get("name", ""),
                "pais": equipo.get("country", ""),
                "liga": equipo.get("league", {}).get("name", ""),
                "logo": equipo.get("logo", ""),
                "estadio": equipo.get("venue", {}).get("name", ""),
                "fuente": "espn_api"
            }
            
        except Exception as e:
            logger.error(f"Error al obtener equipo por ID desde ESPN API: {e}")
            return {}
            
    def get_equipos(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los equipos disponibles.
        
        Returns:
            Lista de equipos en formato estándar
        """
        try:
            equipos_raw = self.fetch_teams()
            equipos = []
            
            for equipo in equipos_raw:
                equipos.append({
                    "id": str(equipo.get("id", "")),
                    "nombre": equipo.get("name", ""),
                    "pais": equipo.get("country", ""),
                    "liga": equipo.get("league", {}).get("name", ""),
                    "logo": equipo.get("logo", ""),
                    "estadio": equipo.get("venue", {}).get("name", ""),
                    "fuente": "espn_api"
                })
                
            return equipos
            
        except Exception as e:
            logger.error(f"Error al obtener equipos desde ESPN API: {e}")
            return []
            
    def get_equipos_liga(self, liga: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los equipos de una liga específica.
        
        Args:
            liga: Nombre de la liga
            
        Returns:
            Lista de equipos en formato estándar
        """
        try:
            # Intentar mapear el nombre de la liga a su código
            liga_code = None
            for code, name in self.league_mapping.items():
                if liga.lower() in name.lower():
                    liga_code = code
                    break
            
            equipos_raw = self.fetch_teams(league=liga_code)
            equipos = []
            
            for equipo in equipos_raw:
                equipos.append({
                    "id": str(equipo.get("id", "")),
                    "nombre": equipo.get("name", ""),
                    "pais": equipo.get("country", ""),
                    "liga": equipo.get("league", {}).get("name", ""),
                    "logo": equipo.get("logo", ""),
                    "estadio": equipo.get("venue", {}).get("name", ""),
                    "fuente": "espn_api"
                })
                
            return equipos
            
        except Exception as e:
            logger.error(f"Error al obtener equipos de liga desde ESPN API: {e}")
            return []
