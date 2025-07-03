"""
Módulo para automatizar la actualización de datos desde fuentes abiertas.
Compatible con repositorios como open-football/football.json y otras APIs públicas.
"""

from abc import ABC, abstractmethod
import os
import requests
import json
import pandas as pd
import csv
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Any, Union

from utils.conversor import CSVtoJSON, JSONtoCSV

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'data_fetcher.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DataFetcher')

class BaseDataFetcher(ABC):
    """Clase base abstracta para todos los adaptadores de datos"""
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el adaptador base
        
        Args:
            config: Diccionario con configuración (api_keys, urls, etc.)
        """
        self.config = config or {}
        self.output_dir = os.path.join('data', 'external')
        os.makedirs(self.output_dir, exist_ok=True)
        
    @abstractmethod
    def fetch_teams(self, **kwargs) -> List[Dict]:
        """
        Obtiene datos de equipos
        
        Returns:
            Lista de diccionarios con información de equipos
        """
        pass
        
    @abstractmethod
    def fetch_players(self, **kwargs) -> List[Dict]:
        """
        Obtiene datos de jugadores
        
        Returns:
            Lista de diccionarios con información de jugadores
        """
        pass
        
    @abstractmethod
    def fetch_matches(self, **kwargs) -> List[Dict]:
        """
        Obtiene datos de partidos
        
        Returns:
            Lista de diccionarios con información de partidos
        """
        pass
        
    def save_to_json(self, data: Any, filename: str) -> str:
        """
        Guarda datos en formato JSON
        
        Args:
            data: Datos a guardar
            filename: Nombre del archivo (sin extensión)
            
        Returns:
            Ruta del archivo guardado
        """
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Datos guardados en {filepath}")
        return filepath
        
    def save_to_csv(self, data: List[Dict], filename: str) -> str:
        """
        Guarda datos en formato CSV
        
        Args:
            data: Lista de diccionarios para convertir a CSV
            filename: Nombre del archivo (sin extensión)
            
        Returns:
            Ruta del archivo guardado
        """
        if not data:
            logger.warning(f"No hay datos para guardar en {filename}.csv")
            return ""
            
        df = pd.DataFrame(data)
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Datos guardados en {filepath}")
        return filepath
    
    def rate_limit_wait(self, seconds: int = 1):
        """
        Espera para respetar límites de tasa de las APIs
        
        Args:
            seconds: Segundos a esperar
        """
        time.sleep(seconds)

class DataFetcher(BaseDataFetcher):
    """
    Implementación existente del DataFetcher
    """
    def __init__(self, config: Dict = None):
        super().__init__(config)
        # URLs base para las diferentes fuentes
        self.sources = {
            'openfootball': {
                'base_url': 'https://raw.githubusercontent.com/openfootball/football.json/master',
                'leagues': {
                    'premier-league': '2020-21/en.1.json',
                    'la-liga': '2020-21/es.1.json',
                    'bundesliga': '2020-21/de.1.json',
                    'serie-a': '2020-21/it.1.json',
                    'ligue-1': '2020-21/fr.1.json'
                }
            },
            'football-data': {
                'base_url': 'https://api.football-data.org/v2',
                'endpoints': {
                    'competitions': '/competitions',
                    'matches': '/matches',
                    'teams': '/teams'
                },
                'api_key': None  # Requiere API key, añadir desde variables de entorno
            },
            'api-football': {
                'base_url': 'https://api-football-v1.p.rapidapi.com/v3',
                'endpoints': {
                    'fixtures': '/fixtures',
                    'leagues': '/leagues',
                    'teams': '/teams'
                },
                'headers': None  # Requiere headers de autenticación
            }
        }
        
        # Intentar cargar API keys desde variables de entorno o archivo de configuración
        self._cargar_api_keys()
    
    def _cargar_api_keys(self):
        """
        Carga las API keys desde variables de entorno o archivo de configuración.
        """
        try:
            # Buscar en variables de entorno
            import os
            football_data_key = os.environ.get('FOOTBALL_DATA_API_KEY')
            if football_data_key:
                self.sources['football-data']['api_key'] = football_data_key
            
            api_football_key = os.environ.get('API_FOOTBALL_KEY')
            api_football_host = os.environ.get('API_FOOTBALL_HOST')
            if api_football_key and api_football_host:
                self.sources['api-football']['headers'] = {
                    'x-rapidapi-key': api_football_key,
                    'x-rapidapi-host': api_football_host
                }
                
            # Si no hay variables de entorno, intentar cargar desde archivo
            if not football_data_key or not api_football_key:
                config_path = os.path.join('data', 'config', 'api_keys.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                    if not self.sources['football-data']['api_key'] and 'football_data_key' in config:
                        self.sources['football-data']['api_key'] = config['football_data_key']
                        
                    if not self.sources['api-football']['headers'] and 'api_football_key' in config:
                        self.sources['api-football']['headers'] = {
                            'x-rapidapi-key': config['api_football_key'],
                            'x-rapidapi-host': config['api_football_host']
                        }
        except Exception as e:
            logger.error(f"Error al cargar API keys: {e}")
    
    def fetch_openfootball_data(self, league=None, season=None):
        """
        Obtiene datos de open-football GitHub repository.
        
        Args:
            league: Liga específica a obtener (si None, obtiene todas)
            season: Temporada específica (formato: "2020-21")
            
        Returns:
            Ruta al archivo JSON descargado o None si hubo un error
        """
        source = self.sources['openfootball']
        base_url = source['base_url']
        
        leagues = {}
        if league and league in source['leagues']:
            leagues[league] = source['leagues'][league]
        else:
            leagues = source['leagues']
        
        # Si se especifica una temporada, actualiza las rutas
        if season:
            for key in leagues:
                leagues[key] = leagues[key].replace('2020-21', season)
        
        results = {}
        for league_name, path in leagues.items():
            url = f"{base_url}/{path}"
            logger.info(f"Descargando datos de {league_name} desde {url}")
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Guardar archivo JSON
                    output_file = os.path.join(self.output_dir, f"{league_name}_{path.split('/')[-1]}")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    # Convertir a CSV para integración con el sistema
                    csv_file = output_file.replace('.json', '.csv')
                    df = JSONtoCSV.convert_openfootball_to_df(data)
                    df.to_csv(csv_file, index=False)
                    
                    results[league_name] = {
                        'json_path': output_file,
                        'csv_path': csv_file,
                        'match_count': len(df) if df is not None else 0
                    }
                    
                    logger.info(f"Datos de {league_name} guardados en {output_file} y {csv_file}")
                else:
                    logger.error(f"Error {response.status_code} al descargar {league_name}")
            except Exception as e:
                logger.error(f"Error al procesar datos de {league_name}: {e}")
        
        return results
    
    def fetch_footballdata_api(self, competition_id=None, date_from=None, date_to=None):
        """
        Obtiene datos de la API de football-data.org.
        
        Args:
            competition_id: ID de la competición (ej. PL, PD, BL1, SA, FL1)
            date_from: Fecha de inicio (formato ISO: YYYY-MM-DD)
            date_to: Fecha final (formato ISO: YYYY-MM-DD)
            
        Returns:
            Ruta al archivo JSON descargado o None si hubo un error
        """
        if not self.sources['football-data']['api_key']:
            logger.error("No se ha configurado API key para football-data.org")
            return None
        
        base_url = self.sources['football-data']['base_url']
        headers = {'X-Auth-Token': self.sources['football-data']['api_key']}
        
        # Si no se especifican fechas, usar últimos 30 días
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        # Construir URL
        url = f"{base_url}/matches"
        params = {
            'dateFrom': date_from,
            'dateTo': date_to
        }
        
        if competition_id:
            params['competitions'] = competition_id
        
        logger.info(f"Consultando API football-data.org para partidos desde {date_from} hasta {date_to}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                
                # Guardar archivo JSON
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                competition_str = competition_id if competition_id else "all"
                output_file = os.path.join(
                    self.output_dir, 
                    f"footballdata_{competition_str}_{date_from}_{date_to}_{timestamp}.json"
                )
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Convertir a CSV para integración con el sistema
                csv_file = output_file.replace('.json', '.csv')
                df = JSONtoCSV.convert_footballdata_api_to_df(data)
                
                if df is not None:
                    df.to_csv(csv_file, index=False)
                    logger.info(f"Datos guardados en {output_file} y {csv_file} ({len(df)} partidos)")
                    
                    return {
                        'json_path': output_file,
                        'csv_path': csv_file,
                        'match_count': len(df)
                    }
                else:
                    logger.warning("No se pudieron convertir los datos a formato CSV")
            else:
                logger.error(f"Error {response.status_code} al consultar la API: {response.text}")
        except Exception as e:
            logger.error(f"Error al procesar datos de football-data.org: {e}")
        
        return None
    
    def update_all_sources(self, days_back=30):
        """
        Actualiza los datos de todas las fuentes disponibles.
        
        Args:
            days_back: Número de días hacia atrás para buscar datos
            
        Returns:
            Dict con resultados de las actualizaciones
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # Open Football GitHub repo (datos históricos)
        try:
            logger.info("Actualizando datos de openfootball...")
            results['sources']['openfootball'] = self.fetch_openfootball_data()
        except Exception as e:
            logger.error(f"Error al actualizar openfootball: {e}")
            results['sources']['openfootball'] = {'error': str(e)}
        
        # Football-data.org API (datos más recientes)
        if self.sources['football-data']['api_key']:
            try:
                date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                date_to = datetime.now().strftime('%Y-%m-%d')
                
                logger.info("Actualizando datos de football-data.org API...")
                results['sources']['football-data'] = self.fetch_footballdata_api(
                    date_from=date_from,
                    date_to=date_to
                )
            except Exception as e:
                logger.error(f"Error al actualizar football-data.org: {e}")
                results['sources']['football-data'] = {'error': str(e)}
        else:
            results['sources']['football-data'] = {'error': 'API key no configurada'}
        
        # Guardar resumen de la actualización
        output_summary = os.path.join(
            self.output_dir,
            f"update_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_summary, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Resumen de actualización guardado en {output_summary}")
        
        return results
    
    def schedule_regular_updates(self, interval_hours=24):
        """
        Programa actualizaciones regulares de datos.
        
        Args:
            interval_hours: Intervalo de horas entre actualizaciones
        """
        logger.info(f"Programando actualizaciones cada {interval_hours} horas")
        
        while True:
            try:
                # Realizar actualización
                self.update_all_sources()
                
                # Esperar hasta la próxima actualización
                logger.info(f"Próxima actualización en {interval_hours} horas")
                time.sleep(interval_hours * 3600)  # Convertir horas a segundos
            except KeyboardInterrupt:
                logger.info("Actualizaciones programadas interrumpidas")
                break
            except Exception as e:
                logger.error(f"Error en actualización programada: {e}")
                # Esperar 1 hora antes de reintentar en caso de error
                time.sleep(3600)
    
    def fetch_teams(self, league: str = 'premier-league') -> List[Dict]:
        """
        Obtiene datos de equipos de una liga específica
        
        Args:
            league: Liga de la cual obtener equipos (por defecto Premier League)
            
        Returns:
            Lista de equipos con sus detalles
        """
        try:
            source = self.sources['openfootball']
            if league not in source['leagues']:
                logger.error(f"Liga {league} no encontrada en las fuentes disponibles")
                return []
                
            url = f"{source['base_url']}/{source['leagues'][league]}"
            logger.info(f"Descargando datos de equipos desde {url}")
            
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Error {response.status_code} al descargar datos")
                return []
                
            data = response.json()
            
            # Extraer equipos
            teams = []
            if 'clubs' in data:
                teams = data['clubs']
            elif 'teams' in data:
                teams = data['teams']
            else:
                # Extraer equipos de los partidos
                unique_teams = set()
                for round_data in data.get('rounds', []):
                    for match in round_data.get('matches', []):
                        team1 = match.get('team1', {})
                        team2 = match.get('team2', {})
                        
                        if isinstance(team1, dict) and 'name' in team1 and team1['name'] not in unique_teams:
                            teams.append(team1)
                            unique_teams.add(team1['name'])
                            
                        if isinstance(team2, dict) and 'name' in team2 and team2['name'] not in unique_teams:
                            teams.append(team2)
                            unique_teams.add(team2['name'])
            
            # Guardar datos
            self.save_to_json(teams, f"teams_{league}")
            
            return teams
            
        except Exception as e:
            logger.error(f"Error al obtener equipos: {str(e)}")
            return []
            
    def fetch_players(self, team_id: str = None) -> List[Dict]:
        """
        Obtiene datos de jugadores (simula datos ya que openfootball no tiene jugadores)
        
        Args:
            team_id: ID del equipo (opcional)
            
        Returns:
            Lista de jugadores
        """
        logger.warning("La fuente actual no proporciona datos de jugadores. Generando datos simulados.")
        
        # Generar algunos jugadores simulados
        players = []
        teams = self.fetch_teams()
        
        for i, team in enumerate(teams):
            team_name = team.get('name', f"Equipo {i}")
            team_id = team.get('code', str(i))
            
            # Si se especificó un team_id y no coincide, saltar este equipo
            if team_id and team_id != team_id:
                continue
                
            # Generar 20 jugadores por equipo
            for j in range(1, 21):
                player = {
                    'id': f"{team_id}_{j:02d}",
                    'name': f"Jugador {j}",
                    'team': team_name,
                    'position': self._get_random_position(j),
                    'nationality': "País ejemplo",
                    'age': 20 + (j % 15),
                    'height': 170 + (j % 25),
                    'weight': 65 + (j % 30)
                }
                players.append(player)
                
        # Guardar datos
        if players:
            suffix = f"_{team_id}" if team_id else ""
            self.save_to_json(players, f"players{suffix}")
            
        return players
        
    def fetch_matches(self, league: str = 'premier-league', season: str = None) -> List[Dict]:
        """
        Obtiene datos de partidos de una liga
        
        Args:
            league: Liga de la cual obtener partidos
            season: Temporada específica (si None, usa la configurada)
            
        Returns:
            Lista de partidos
        """
        try:
            source = self.sources['openfootball']
            if league not in source['leagues']:
                logger.error(f"Liga {league} no encontrada en las fuentes disponibles")
                return []
                
            url = f"{source['base_url']}/{source['leagues'][league]}"
            logger.info(f"Descargando datos de partidos desde {url}")
            
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Error {response.status_code} al descargar datos")
                return []
                
            data = response.json()
            
            # Extraer partidos
            matches = []
            for round_data in data.get('rounds', []):
                round_name = round_data.get('name', '')
                
                for match in round_data.get('matches', []):
                    match_data = {
                        'round': round_name,
                        'date': match.get('date', ''),
                        'team1': match.get('team1', {}).get('name', '') if isinstance(match.get('team1'), dict) else match.get('team1', ''),
                        'team2': match.get('team2', {}).get('name', '') if isinstance(match.get('team2'), dict) else match.get('team2', ''),
                        'score1': match.get('score1', None),
                        'score2': match.get('score2', None),
                        'league': league
                    }
                    matches.append(match_data)
            
            # Guardar datos
            if matches:
                self.save_to_json(matches, f"matches_{league}")
                self.save_to_csv(matches, f"matches_{league}")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error al obtener partidos: {str(e)}")
            return []
            
    def _get_random_position(self, num: int) -> str:
        """
        Devuelve una posición basada en un número
        
        Args:
            num: Número del jugador
            
        Returns:
            Posición del jugador
        """
        positions = {
            1: 'Portero',
            2: 'Defensa',
            3: 'Defensa',
            4: 'Defensa',
            5: 'Defensa',
            6: 'Mediocentro',
            7: 'Mediocentro',
            8: 'Mediocentro',
            9: 'Delantero',
            10: 'Mediapunta',
            11: 'Delantero'
        }
        
        return positions.get(num % 11 + 1, 'Mediocentro')
