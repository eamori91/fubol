#!/usr/bin/env python
"""
Script de prueba para probar la integración con la API no oficial de ESPN.
Basado en el repositorio: https://github.com/eamori91/Public-ESPN-API
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.espn_api import ESPNAPI

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('test_espn_api')

def test_get_leagues():
    """Prueba la obtención de ligas desde ESPN API."""
    logger.info("=" * 80)
    logger.info("PRUEBA: Obtener ligas desde ESPN API")
    logger.info("=" * 80)
    
    espn_api = ESPNAPI()
    leagues = espn_api.fetch_leagues()
    
    if not leagues:
        logger.error("No se pudieron obtener ligas desde ESPN API")
        return False
        
    logger.info(f"Se encontraron {len(leagues)} ligas:")
    for i, league in enumerate(leagues[:5], 1):
        logger.info(f"  {i}. {league.get('nombre', 'N/A')} ({league.get('codigo', 'N/A')})")
    
    if len(leagues) > 5:
        logger.info(f"  ... y {len(leagues) - 5} más.")
        
    return True
    
def test_get_teams():
    """Prueba la obtención de equipos desde ESPN API."""
    logger.info("=" * 80)
    logger.info("PRUEBA: Obtener equipos desde ESPN API")
    logger.info("=" * 80)
    
    espn_api = ESPNAPI()
    
    # Probar con LaLiga
    league_code = "PD"
    league_name = "LaLiga"
    
    logger.info(f"Obteniendo equipos de {league_name} ({league_code})...")
    teams = espn_api.fetch_teams(league=league_code)
    
    if not teams:
        logger.error(f"No se pudieron obtener equipos de {league_name}")
        return False
        
    logger.info(f"Se encontraron {len(teams)} equipos en {league_name}:")
    for i, team in enumerate(teams[:5], 1):
        logger.info(f"  {i}. {team.get('nombre', 'N/A')} ({team.get('nombre_corto', 'N/A')})")
        
    if len(teams) > 5:
        logger.info(f"  ... y {len(teams) - 5} más.")
        
    # Guardar resultados en un archivo JSON
    output_dir = os.path.join('data', 'test_espn_api')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f'teams_{league_code}.json'), 'w', encoding='utf-8') as f:
        json.dump(teams, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Equipos guardados en {os.path.join(output_dir, f'teams_{league_code}.json')}")
    
    return True
    
def test_get_players():
    """Prueba la obtención de jugadores desde ESPN API."""
    logger.info("=" * 80)
    logger.info("PRUEBA: Obtener jugadores desde ESPN API")
    logger.info("=" * 80)
    
    espn_api = ESPNAPI()
    
    # Primero obtenemos un equipo para tener su ID
    logger.info("Obteniendo equipos de LaLiga...")
    teams = espn_api.fetch_teams(league="PD")
    
    if not teams:
        logger.error("No se pudieron obtener equipos de LaLiga")
        return False
        
    # Seleccionar el Real Madrid o Barcelona
    team = next((t for t in teams if 'madrid' in t.get('nombre', '').lower() or 'barcelona' in t.get('nombre', '').lower()), teams[0])
    team_name = team.get('nombre', 'Equipo desconocido')
    team_id = team.get('id', '')
    
    logger.info(f"Obteniendo jugadores de {team_name} (ID: {team_id})...")
    players = espn_api.fetch_players(team_id=team_id)
    
    if not players:
        logger.error(f"No se pudieron obtener jugadores de {team_name}")
        return False
        
    logger.info(f"Se encontraron {len(players)} jugadores en {team_name}:")
    for i, player in enumerate(players[:5], 1):
        logger.info(f"  {i}. {player.get('nombre_completo', 'N/A')} - {player.get('posicion', 'N/A')} ({player.get('dorsal', 'N/A')})")
        
    if len(players) > 5:
        logger.info(f"  ... y {len(players) - 5} más.")
        
    # Guardar resultados en un archivo JSON
    output_dir = os.path.join('data', 'test_espn_api')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f'players_{team_id}.json'), 'w', encoding='utf-8') as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Jugadores guardados en {os.path.join(output_dir, f'players_{team_id}.json')}")
    
    return True

def test_get_matches():
    """Prueba la obtención de partidos desde ESPN API."""
    logger.info("=" * 80)
    logger.info("PRUEBA: Obtener partidos desde ESPN API")
    logger.info("=" * 80)
    
    espn_api = ESPNAPI()
    
    # Probar con la Premier League
    league_code = "PL"
    league_name = "Premier League"
    
    # Fechas para la próxima semana
    date_from = datetime.now().strftime('%Y-%m-%d')
    date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    logger.info(f"Obteniendo partidos de {league_name} entre {date_from} y {date_to}...")
    matches = espn_api.fetch_matches(league=league_code, date_from=date_from, date_to=date_to)
    
    if not matches:
        logger.error(f"No se pudieron obtener partidos de {league_name}")
        return False
        
    logger.info(f"Se encontraron {len(matches)} partidos en {league_name}:")
    for i, match in enumerate(matches[:5], 1):
        fecha = match.get('fecha', 'Fecha desconocida')
        local = match.get('equipo_local', 'Local')
        visitante = match.get('equipo_visitante', 'Visitante')
        logger.info(f"  {i}. [{fecha}] {local} vs {visitante}")
        
    if len(matches) > 5:
        logger.info(f"  ... y {len(matches) - 5} más.")
        
    # Guardar resultados en un archivo JSON
    output_dir = os.path.join('data', 'test_espn_api')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f'matches_{league_code}.json'), 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Partidos guardados en {os.path.join(output_dir, f'matches_{league_code}.json')}")
    
    return True

def test_get_standings():
    """Prueba la obtención de clasificaciones desde ESPN API."""
    logger.info("=" * 80)
    logger.info("PRUEBA: Obtener clasificación desde ESPN API")
    logger.info("=" * 80)
    
    espn_api = ESPNAPI()
    
    # Probar con LaLiga
    league_code = "PD"
    league_name = "LaLiga"
    
    logger.info(f"Obteniendo clasificación de {league_name}...")
    standings = espn_api.fetch_standings(league=league_code)
    
    if not standings:
        logger.error(f"No se pudo obtener la clasificación de {league_name}")
        return False
        
    logger.info(f"Clasificación de {league_name}:")
    for i, team in enumerate(standings[:5], 1):
        pos = team.get('posicion', i)
        nombre = team.get('equipo', 'Equipo desconocido')
        pts = team.get('puntos', 0)
        pj = team.get('partidos_jugados', 0)
        pg = team.get('victorias', 0)
        pe = team.get('empates', 0)
        pp = team.get('derrotas', 0)
        gf = team.get('goles_favor', 0)
        gc = team.get('goles_contra', 0)
        
        logger.info(f"  {pos}. {nombre} - {pts}pts ({pg}G {pe}E {pp}P) {gf}:{gc}")
        
    if len(standings) > 5:
        logger.info(f"  ... y {len(standings) - 5} más.")
        
    # Guardar resultados en un archivo JSON
    output_dir = os.path.join('data', 'test_espn_api')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f'standings_{league_code}.json'), 'w', encoding='utf-8') as f:
        json.dump(standings, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Clasificación guardada en {os.path.join(output_dir, f'standings_{league_code}.json')}")
    
    return True

if __name__ == "__main__":
    logger.info("Iniciando prueba de integración con ESPN API...")
    
    # Crear directorio para resultados
    output_dir = os.path.join('data', 'test_espn_api')
    os.makedirs(output_dir, exist_ok=True)
    
    # Ejecutar pruebas
    results = {
        "get_leagues": test_get_leagues(),
        "get_teams": test_get_teams(),
        "get_players": test_get_players(),
        "get_matches": test_get_matches(),
        "get_standings": test_get_standings()
    }
    
    # Mostrar resumen
    logger.info("\n" + "=" * 80)
    logger.info("RESUMEN DE PRUEBAS")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ ÉXITO" if result else "✗ FALLO"
        logger.info(f"{status} - {test_name}")
        
    # Guardar resultados
    with open(os.path.join(output_dir, 'test_results.json'), 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": {k: "success" if v else "failure" for k, v in results.items()}
        }, f, indent=2)
        
    logger.info(f"Resultados de prueba guardados en {os.path.join(output_dir, 'test_results.json')}")
