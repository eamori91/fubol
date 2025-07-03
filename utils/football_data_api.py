"""
Adaptador para la API de Football-Data.org
https://www.football-data.org/

Este módulo proporciona una clase que implementa la interfaz BaseDataFetcher
para obtener datos de football-data.org
"""

import requests
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, TypedDict

from utils.data_fetcher import BaseDataFetcher

logger = logging.getLogger('FootballDataAPI')

class FootballDataAPI(BaseDataFetcher):
    """
    Adaptador para la API Football-Data.org
    Implementa la interfaz BaseDataFetcher
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el adaptador de Football-Data.org
        
        Args:
            config: Diccionario con configuración (api_key, etc.)
        """
        super().__init__(config if config is not None else {})
        self.base_url = 'https://api.football-data.org/v4'
        self.api_key = config.get('api_key', '') if config else os.environ.get('FOOTBALL_DATA_API_KEY', '')
        
        if not self.api_key:
            logger.warning("No se ha proporcionado API key para Football-Data.org")
        
        self.headers = {'X-Auth-Token': self.api_key}
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una petición a la API
        
        Args:
            endpoint: Endpoint de la API (ej. /competitions)
            params: Parámetros de la petición
            
        Returns:
            Diccionario con la respuesta JSON
        """
        if not self.api_key:
            raise ValueError("Se requiere API key para Football-Data.org")
        
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Control de errores y límites de tasa
            if response.status_code == 429:
                # Too many requests
                logger.warning(f"Límite de tasa alcanzado. Esperando antes de reintentar.")
                self.rate_limit_wait(60)  # Esperar 60 segundos
                return self._make_request(endpoint, params)
            
            # Manejar otros errores
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al realizar petición a {url}: {e}")
            return {}
    
    def fetch_teams(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene datos de equipos para una competición específica
        
        Args:
            **kwargs: Parámetros opcionales
                competition_code: Código de la competición (ej. PD=La Liga, PL=Premier League)
                season: Temporada (ej. 2022)
            
        Returns:
            Lista de diccionarios con información de equipos
        """
        competition_code = kwargs.get('competition_code', "PD")
        season = kwargs.get('season')
        """
        Obtiene datos de equipos para una competición específica
        
        Args:
            competition_code: Código de la competición (ej. PD=La Liga, PL=Premier League)
            season: Temporada (ej. 2022)
            
        Returns:
            Lista de diccionarios con información de equipos
        """
        endpoint = f"/competitions/{competition_code}/teams"
        params = {}
        if season:
            params['season'] = season
        
        logger.info(f"Obteniendo equipos de la competición {competition_code}")
        
        data = self._make_request(endpoint, params)
        teams = []
        
        if 'teams' in data:
            # Transformar datos al formato interno
            for team in data['teams']:
                teams.append({
                    'id': team.get('id'),
                    'nombre': team.get('name'),
                    'nombre_corto': team.get('shortName', team.get('tla')),
                    'pais': team.get('area', {}).get('name'),
                    'fundacion': team.get('founded'),
                    'estadio': team.get('venue'),
                    'escudo_url': team.get('crestUrl'),
                    'liga': data.get('competition', {}).get('name'),
                    'codigo_liga': competition_code
                })
                
            # Guardar datos en cache
            self.save_to_json(teams, f"teams_{competition_code}_{season or 'latest'}")
        
        logger.info(f"Equipos obtenidos: {len(teams)}")
        return teams
    
    def fetch_players(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene datos de jugadores para un equipo específico
        
        Args:
            **kwargs: Parámetros opcionales
                team_id: ID del equipo
            
        Returns:
            Lista de diccionarios con información de jugadores
        """
        team_id = kwargs.get('team_id')
        if not team_id:
            logger.error("Se requiere ID de equipo para obtener jugadores")
            return []
            
        endpoint = f"/teams/{team_id}"
        
        logger.info(f"Obteniendo jugadores del equipo {team_id}")
        
        data = self._make_request(endpoint)
        players = []
        
        if 'squad' in data:
            # Transformar datos al formato interno
            for player in data['squad']:
                players.append({
                    'id': player.get('id'),
                    'nombre': player.get('name'),
                    'posicion': player.get('position', 'Desconocido'),
                    'nacionalidad': player.get('nationality'),
                    'fecha_nacimiento': player.get('dateOfBirth'),
                    'equipo_id': team_id,
                    'equipo_nombre': data.get('name'),
                    'dorsal': player.get('shirtNumber')
                })
                
            # Guardar datos en cache
            self.save_to_json(players, f"players_team_{team_id}")
        
        logger.info(f"Jugadores obtenidos: {len(players)}")
        return players
    
    def fetch_matches(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Obtiene datos de partidos
        
        Args:
            **kwargs: Parámetros opcionales
                competition_code: Código de la competición
                date_from: Fecha de inicio (formato: YYYY-MM-DD)
                date_to: Fecha de fin (formato: YYYY-MM-DD)
                team_id: ID del equipo
                status: Estado del partido (SCHEDULED, FINISHED, etc.)
            
        Returns:
            Lista de diccionarios con información de partidos
        """
        competition_code = kwargs.get('competition_code')
        date_from = kwargs.get('date_from')
        date_to = kwargs.get('date_to')
        team_id = kwargs.get('team_id')
        status = kwargs.get('status')
        
        # Construir endpoint base
        if competition_code:
            endpoint = f"/competitions/{competition_code}/matches"
        elif team_id:
            endpoint = f"/teams/{team_id}/matches"
        else:
            endpoint = "/matches"
            
        # Si no se especifican fechas, usar últimos 30 días
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
            
        # Construir parámetros
        params = {
            'dateFrom': date_from,
            'dateTo': date_to
        }
        
        if status:
            params['status'] = status
            
        logger.info(f"Obteniendo partidos desde {date_from} hasta {date_to}")
        
        data = self._make_request(endpoint, params)
        matches = []
        
        if 'matches' in data:
            # Transformar datos al formato interno
            for match in data['matches']:
                matches.append({
                    'id': match.get('id'),
                    'competicion': match.get('competition', {}).get('name'),
                    'fecha': match.get('utcDate'),
                    'jornada': match.get('matchday'),
                    'equipo_local': match.get('homeTeam', {}).get('name'),
                    'equipo_local_id': match.get('homeTeam', {}).get('id'),
                    'equipo_visitante': match.get('awayTeam', {}).get('name'),
                    'equipo_visitante_id': match.get('awayTeam', {}).get('id'),
                    'goles_local': match.get('score', {}).get('fullTime', {}).get('homeTeam'),
                    'goles_visitante': match.get('score', {}).get('fullTime', {}).get('awayTeam'),
                    'estado': match.get('status'),
                    'temporada': match.get('season', {}).get('startDate', '')[:4]
                })
                
            # Guardar datos en cache
            filename = f"matches_{competition_code or 'all'}_{date_from}_to_{date_to}"
            self.save_to_json(matches, filename)
            
        logger.info(f"Partidos obtenidos: {len(matches)}")
        return matches

    def fetch_competitions(self) -> List[Dict]:
        """
        Obtiene lista de competiciones disponibles
        
        Returns:
            Lista de diccionarios con información de competiciones
        """
        endpoint = "/competitions"
        
        logger.info("Obteniendo lista de competiciones")
        
        data = self._make_request(endpoint)
        competitions = []
        
        if 'competitions' in data:
            for competition in data['competitions']:
                competitions.append({
                    'id': competition.get('id'),
                    'nombre': competition.get('name'),
                    'codigo': competition.get('code'),
                    'tipo': competition.get('type'),
                    'pais': competition.get('area', {}).get('name'),
                    'temporada_actual': competition.get('currentSeason', {}).get('startDate', '')[:4]
                })
                
            # Guardar datos en cache
            self.save_to_json(competitions, "competitions")
            
        logger.info(f"Competiciones obtenidas: {len(competitions)}")
        return competitions

    def fetch_standings(self, competition_code: str, season: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene clasificación de una competición
        
        Args:
            competition_code: Código de la competición
            season: Temporada (opcional)
            
        Returns:
            Diccionario con la clasificación
        """
        endpoint = f"/competitions/{competition_code}/standings"
        params = {}
        if season:
            params['season'] = season
            
        logger.info(f"Obteniendo clasificación de {competition_code}")
        
        data = self._make_request(endpoint, params)
        standings = {}
        
        if 'standings' in data:
            # Transformar datos al formato interno
            for standing_type in data['standings']:
                tipo = standing_type.get('type', 'TOTAL')
                tabla = []
                
                for row in standing_type.get('table', []):
                    tabla.append({
                        'posicion': row.get('position'),
                        'equipo': row.get('team', {}).get('name'),
                        'equipo_id': row.get('team', {}).get('id'),
                        'jugados': row.get('playedGames'),
                        'ganados': row.get('won'),
                        'empatados': row.get('draw'),
                        'perdidos': row.get('lost'),
                        'goles_favor': row.get('goalsFor'),
                        'goles_contra': row.get('goalsAgainst'),
                        'diferencia_goles': row.get('goalDifference'),
                        'puntos': row.get('points')
                    })
                
                standings[tipo] = tabla
                
            # Guardar datos en cache
            self.save_to_json(standings, f"standings_{competition_code}_{season or 'latest'}")
            
        logger.info(f"Clasificación obtenida para {competition_code}")
        return standings
