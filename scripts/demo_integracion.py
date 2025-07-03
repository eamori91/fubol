#!/usr/bin/env python
"""
Script de demostración para probar la integración con datos reales.

Este script realiza pruebas de las diferentes funcionalidades implementadas:
- Adaptadores de Football-Data.org y API-Football
- Actualización de equipos y jugadores
- Configuración de la base de datos

Uso:
    python demo_integracion.py [--source SOURCE]

Argumentos:
    --source SOURCE    Fuente de datos a probar (football-data, api-football)
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime, timedelta
import time

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.football_data_api import FootballDataAPI
    from utils.api_football import APIFootball
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
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('demo_integracion')

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Demuestra la integración con datos reales')
    parser.add_argument('--source', choices=['football-data', 'api-football', 'all'],
                        default='all', help='Fuente de datos a probar')
    parser.add_argument('--output', type=str, default='demo_output',
                        help='Directorio de salida para los datos')
    return parser.parse_args()

def test_football_data_api(output_dir):
    """
    Prueba la integración con Football-Data.org.
    
    Args:
        output_dir: Directorio para guardar resultados de prueba
    """
    logger.info("\n" + "="*80)
    logger.info("PRUEBA DE FOOTBALL-DATA.ORG API")
    logger.info("="*80)
    
    # Verificar API key
    api_key = os.environ.get('FOOTBALL_DATA_API_KEY', '')
    if not api_key:
        logger.warning("No se encontró la API key para Football-Data.org")
        logger.warning("Por favor, configura la variable de entorno FOOTBALL_DATA_API_KEY")
        return
    
    try:
        # Inicializar API
        api = FootballDataAPI({'api_key': api_key})
        logger.info("API inicializada correctamente")
        
        # Directorio para resultados
        fd_output_dir = os.path.join(output_dir, 'football-data')
        os.makedirs(fd_output_dir, exist_ok=True)
        
        # 1. Obtener competiciones
        logger.info("\n1. Obteniendo competiciones disponibles...")
        competitions = api.fetch_competitions()
        
        with open(os.path.join(fd_output_dir, 'competitions.json'), 'w', encoding='utf-8') as f:
            json.dump(competitions, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(competitions)} competiciones")
        
        # 2. Obtener equipos de LaLiga
        logger.info("\n2. Obteniendo equipos de LaLiga (PD)...")
        teams = api.fetch_teams(competition_code="PD")
        
        with open(os.path.join(fd_output_dir, 'teams_laliga.json'), 'w', encoding='utf-8') as f:
            json.dump(teams, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(teams)} equipos")
        
        # 3. Obtener jugadores de un equipo (Real Madrid)
        if teams:
            team_id = next((team['id'] for team in teams if 'Madrid' in team['nombre']), None)
            if team_id:
                logger.info(f"\n3. Obteniendo jugadores del Real Madrid (ID: {team_id})...")
                players = api.fetch_players(team_id=team_id)
                
                with open(os.path.join(fd_output_dir, f'players_team_{team_id}.json'), 'w', encoding='utf-8') as f:
                    json.dump(players, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"Se obtuvieron {len(players)} jugadores")
        
        # 4. Obtener partidos de LaLiga (últimos 30 días)
        logger.info("\n4. Obteniendo partidos de LaLiga (últimos 30 días)...")
        date_to = datetime.now().strftime('%Y-%m-%d')
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        matches = api.fetch_matches(competition_code="PD", date_from=date_from, date_to=date_to)
        
        with open(os.path.join(fd_output_dir, 'matches_laliga.json'), 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(matches)} partidos")
        
        # 5. Obtener clasificación de LaLiga
        logger.info("\n5. Obteniendo clasificación de LaLiga...")
        standings = api.fetch_standings(competition_code="PD")
        
        with open(os.path.join(fd_output_dir, 'standings_laliga.json'), 'w', encoding='utf-8') as f:
            json.dump(standings, f, ensure_ascii=False, indent=2)
            
        logger.info("Clasificación obtenida correctamente")
        
    except Exception as e:
        logger.error(f"Error en la prueba de Football-Data.org: {e}")

def test_api_football(output_dir):
    """
    Prueba la integración con API-Football.
    
    Args:
        output_dir: Directorio para guardar resultados de prueba
    """
    logger.info("\n" + "="*80)
    logger.info("PRUEBA DE API-FOOTBALL")
    logger.info("="*80)
    
    # Verificar API key
    api_key = os.environ.get('API_FOOTBALL_KEY', '')
    api_host = os.environ.get('API_FOOTBALL_HOST', '')
    
    if not api_key or not api_host:
        logger.warning("No se encontraron las credenciales para API-Football")
        logger.warning("Por favor, configura las variables de entorno API_FOOTBALL_KEY y API_FOOTBALL_HOST")
        return
    
    try:
        # Inicializar API
        api = APIFootball({'api_key': api_key, 'api_host': api_host})
        logger.info("API inicializada correctamente")
        
        # Directorio para resultados
        af_output_dir = os.path.join(output_dir, 'api-football')
        os.makedirs(af_output_dir, exist_ok=True)
        
        # 1. Obtener ligas disponibles
        logger.info("\n1. Obteniendo ligas disponibles...")
        leagues = api.fetch_leagues(current=True)
        
        with open(os.path.join(af_output_dir, 'leagues.json'), 'w', encoding='utf-8') as f:
            json.dump(leagues, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(leagues)} ligas")
        
        # 2. Obtener equipos de LaLiga (ID: 140)
        logger.info("\n2. Obteniendo equipos de LaLiga (ID: 140)...")
        current_year = datetime.now().year
        teams = api.fetch_teams(league=140, season=current_year)
        
        with open(os.path.join(af_output_dir, 'teams_laliga.json'), 'w', encoding='utf-8') as f:
            json.dump(teams, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(teams)} equipos")
        
        # 3. Obtener jugadores de un equipo (Barcelona, ID: 529)
        logger.info("\n3. Obteniendo jugadores del Barcelona (ID: 529)...")
        players = api.fetch_players(team=529, league=140, season=current_year)
        
        with open(os.path.join(af_output_dir, 'players_barcelona.json'), 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(players)} jugadores")
        
        # 4. Obtener partidos de LaLiga (últimos 30 días)
        logger.info("\n4. Obteniendo partidos de LaLiga (últimos 30 días)...")
        date_to = datetime.now().strftime('%Y-%m-%d')
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        matches = api.fetch_matches(league=140, from_=date_from, to=date_to)
        
        with open(os.path.join(af_output_dir, 'matches_laliga.json'), 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Se obtuvieron {len(matches)} partidos")
        
        # 5. Obtener clasificación de LaLiga
        logger.info("\n5. Obteniendo clasificación de LaLiga...")
        standings = api.fetch_standings(league=140, season=current_year)
        
        with open(os.path.join(af_output_dir, 'standings_laliga.json'), 'w', encoding='utf-8') as f:
            json.dump(standings, f, ensure_ascii=False, indent=2)
            
        logger.info("Clasificación obtenida correctamente")
        
    except Exception as e:
        logger.error(f"Error en la prueba de API-Football: {e}")

def main():
    """Función principal del script."""
    args = parse_args()
    
    # Crear directorio para resultados
    os.makedirs(args.output, exist_ok=True)
    
    logger.info("Iniciando demostración de integración con datos reales")
    logger.info(f"Los resultados se guardarán en: {os.path.abspath(args.output)}")
    
    if args.source in ['football-data', 'all']:
        test_football_data_api(args.output)
        
    if args.source in ['api-football', 'all']:
        # Pequeña pausa para evitar problemas de límite de tasa
        if args.source == 'all':
            time.sleep(2)
            
        test_api_football(args.output)
        
    logger.info("\nDemostración completada. Revisa los resultados en el directorio de salida.")

if __name__ == '__main__':
    main()
