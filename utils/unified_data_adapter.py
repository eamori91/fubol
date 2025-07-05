"""
Adaptador unificado para integrar datos de múltiples fuentes gratuitas.

Este módulo se encarga de recopilar datos de diversas fuentes gratuitas como:
- Open Football Data (JSON)
- ESPN FC (Web scraping)
- World Football Data (CSV)
- Football-data.org (API con plan gratuito)
- ESPN API (API no oficial)

Los datos se unifican en un formato estándar para ser utilizados por el sistema.
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
import concurrent.futures
import re
import csv
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import threading
import time
import random
import sqlite3

# Importar el nuevo adaptador de ESPN API
from utils.espn_api import ESPNAPI

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('unified_data_adapter')

# Importar gestores de optimización
from utils.cache_manager import CacheManager
from utils.http_optimizer import HTTPOptimizer
from utils.db_optimizer import DBOptimizer
from utils.log_manager import LogManager
from utils.analytics_optimizer import AnalyticsOptimizer

# Instancias por defecto (se reemplazarán en initialize)
_cache_manager = None
_http_optimizer = None
_db_optimizer = None

# Variables globales mínimas para compatibilidad con código anterior
_cache_lock = threading.Lock()
_cached_data = {
    "equipos": {"timestamp": 0, "data": []},
    "jugadores": {"timestamp": 0, "data": {}},
    "arbitros": {"timestamp": 0, "data": []},
    "partidos_historicos": {"timestamp": 0, "data": pd.DataFrame()}
}
# Tiempo de caducidad de caché (en segundos)
CACHE_EXPIRY = 3600  # 1 hora


class UnifiedDataAdapter:
    """Adaptador unificado para múltiples fuentes de datos."""

    def __init__(self, cache_manager=None, http_optimizer=None, db_optimizer=None):
        """Inicializa el adaptador con componentes optimizados y configuración de variables de entorno."""
        
        # Usar instancias proporcionadas o crear por defecto
        self.cache_manager = cache_manager or CacheManager(cache_dir="data/cache")
        self.http_optimizer = http_optimizer or HTTPOptimizer()
        self.db_optimizer = db_optimizer or DBOptimizer()
        
        # Inicializar adaptador de ESPN
        self.espn_api = ESPNAPI()
        
        # Football-Data.org API
        self.football_data_api_key = os.environ.get('FOOTBALL_DATA_API_KEY', '')
        self.use_football_data_api = bool(self.football_data_api_key)
        
        # Open Football Data (JSON)
        self.use_open_football = os.environ.get('USE_OPEN_FOOTBALL_DATA', 'true').lower() == 'true'
        self.open_football_url = os.environ.get('OPEN_FOOTBALL_DATA_URL', 
                                               'https://github.com/openfootball/football.json')
        
        # ESPN FC Data (Scraping)
        self.use_espn_data = os.environ.get('USE_ESPN_DATA', 'true').lower() == 'true'
        self.espn_base_url = os.environ.get('ESPN_BASE_URL', 'https://www.espn.com/soccer')
        
        # ESPN API (API no oficial)
        self.use_espn_api = os.environ.get('USE_ESPN_API', 'true').lower() == 'true'
        
        # World Football Data (CSV)
        self.use_world_football = os.environ.get('USE_WORLD_FOOTBALL', 'true').lower() == 'true'
        self.world_football_url = os.environ.get('WORLD_FOOTBALL_URL', 
                                                'https://www.football-data.co.uk/data.php')
        
        # Cache directory
        self.cache_dir = Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Adaptador unificado inicializado con {self._count_active_sources()} fuentes activas")
    
    def _count_active_sources(self) -> int:
        """Cuenta el número de fuentes de datos activas."""
        count = 0
        if self.use_football_data_api:
            count += 1
        if self.use_open_football:
            count += 1
        if self.use_espn_data:
            count += 1
        if self.use_espn_api:
            count += 1
        if self.use_world_football:
            count += 1
        return count

    def _parse_fecha(self, fecha_str: str) -> datetime:
        """Parsea una fecha en formato string a un objeto datetime."""
        if not fecha_str:
            return datetime.now()
        try:
            # Formato: 2024-07-20T20:00:00Z
            return datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Formato: Sat, 20 Jul 2024 20:00:00 GMT
                return datetime.strptime(fecha_str, '%a, %d %b %Y %H:%M:%S %Z')
            except ValueError:
                logger.warning(f"No se pudo parsear la fecha: {fecha_str}")
                return datetime.now()

    def _eliminar_duplicados_partidos(self, partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina partidos duplicados basados en equipos y fecha."""
        partidos_unicos = []
        claves_vistas = set()
        for partido in partidos:
            fecha = self._parse_fecha(partido.get('fecha', '')).strftime('%Y-%m-%d')
            clave = (
                partido.get('equipo_local', '').lower(),
                partido.get('equipo_visitante', '').lower(),
                fecha
            )
            if clave not in claves_vistas:
                partidos_unicos.append(partido)
                claves_vistas.add(clave)
        return partidos_unicos

    def _normalizar_nombre_equipo(self, nombre: str) -> str:
        """Normaliza el nombre de un equipo para comparación."""
        return nombre.lower().strip()
    
    def obtener_proximos_partidos(self, dias: int = 7, liga: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene los partidos próximos a disputarse desde fuentes gratuitas.
        
        Args:
            dias: Número de días hacia adelante para buscar
            liga: Liga específica para filtrar (opcional)
            
        Returns:
            Lista de partidos próximos en formato estándar
        """
        cache_key = "proximos_partidos"
        
        # Verificar caché
        with _cache_lock:
            cache_entry = _cached_data[cache_key]
            if time.time() - cache_entry["timestamp"] < CACHE_EXPIRY:
                logger.info(f"Usando datos en caché para {cache_key}")
                partidos = cache_entry["data"]
                if liga:
                    partidos = [p for p in partidos if p.get('liga', '').lower() == liga.lower()]
                
                # Filtrar por días
                fecha_limite = datetime.now() + timedelta(days=dias)
                partidos = [p for p in partidos if self._parse_fecha(p.get('fecha', '')) <= fecha_limite]
                
                return partidos
        
        # Si no hay caché válido, obtener datos frescos
        partidos = []
        
        # Lista de funciones para obtener datos de diferentes fuentes
        source_functions = []
        
        if self.use_football_data_api:
            source_functions.append(self._get_proximos_partidos_football_data_api)
        
        if self.use_open_football:
            source_functions.append(self._get_proximos_partidos_open_football)
        
        if self.use_espn_data:
            source_functions.append(self._get_proximos_partidos_espn)
            
        if self.use_espn_api:
            source_functions.append(self._get_proximos_partidos_espn_api)
        
        # Ejecutar en paralelo
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(func) for func in source_functions]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        partidos.extend(result)
                except Exception as e:
                    logger.error(f"Error al obtener próximos partidos: {e}")
        
        # Eliminar duplicados basados en equipos y fecha
        partidos = self._eliminar_duplicados_partidos(partidos)
        
        # Almacenar en caché
        with _cache_lock:
            _cached_data[cache_key] = {"timestamp": time.time(), "data": partidos}
        
        # Aplicar filtros
        if liga:
            partidos = [p for p in partidos if p.get('liga', '').lower() == liga.lower()]
        
        # Filtrar por días
        fecha_limite = datetime.now() + timedelta(days=dias)
        partidos = [p for p in partidos if self._parse_fecha(p.get('fecha', '')) <= fecha_limite]
        
        # Ordenar por fecha
        partidos = sorted(partidos, key=lambda x: self._parse_fecha(x.get('fecha', '')))
        
        return partidos
    
    def obtener_datos_equipo(self, nombre_equipo: str) -> Dict[str, Any]:
        """
        Obtiene datos históricos y actuales de un equipo.
        
        Args:
            nombre_equipo: Nombre del equipo a buscar
            
        Returns:
            Diccionario con información del equipo
        """
        # Normalizar nombre del equipo para búsquedas
        nombre_normalizado = self._normalizar_nombre_equipo(nombre_equipo)
        
        # Verificar caché de equipos
        with _cache_lock:
            cache_entry = _cached_data["equipos"]
            if time.time() - cache_entry["timestamp"] < CACHE_EXPIRY:
                for equipo in cache_entry["data"]:
                    if self._normalizar_nombre_equipo(equipo.get('nombre', '')) == nombre_normalizado:
                        return equipo
        
        # Si no está en caché, buscar en diferentes fuentes
        equipo_info = {}
        
        # Lista de funciones para obtener datos de diferentes fuentes
        source_functions = []
        
        if self.use_football_data_api:
            source_functions.append(lambda: self._get_equipo_football_data_api(nombre_equipo))
        
        if self.use_open_football:
            source_functions.append(lambda: self._get_equipo_open_football(nombre_equipo))
        
        if self.use_espn_data:
            source_functions.append(lambda: self._get_equipo_espn(nombre_equipo))
            
        if self.use_espn_api:
            source_functions.append(lambda: self._get_equipo_espn_api(nombre_equipo))
        
        # Ejecutar en paralelo
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(func): func.__name__ for func in source_functions}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        # Combinar la información de diferentes fuentes
                        if not equipo_info:
                            equipo_info = result
                        else:
                            for key, value in result.items():
                                if key not in equipo_info or not equipo_info[key]:
                                    equipo_info[key] = value
                except Exception as e:
                    logger.error(f"Error al obtener datos del equipo {nombre_equipo}: {e}")
        
        # Si no se encontró información, devolver diccionario vacío
        if not equipo_info:
            return {}
        
        # Añadir a caché de equipos
        with _cache_lock:
            equipos = _cached_data["equipos"]["data"]
            # Reemplazar si ya existe
            for i, equipo in enumerate(equipos):
                if self._normalizar_nombre_equipo(equipo.get('nombre', '')) == nombre_normalizado:
                    equipos[i] = equipo_info
                    break
            else:
                equipos.append(equipo_info)
            _cached_data["equipos"] = {"timestamp": time.time(), "data": equipos}
        
        return equipo_info
    
    # --- CRUD y gestión de jugadores ---
    def obtener_jugadores_equipo(self, equipo_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los jugadores de un equipo específico desde las fuentes activas.
        
        Args:
            equipo_id: ID del equipo
            
        Returns:
            Lista de jugadores con sus datos
        """
        jugadores = []
        # Buscar en caché primero
        with _cache_lock:
            cache_entry = _cached_data["jugadores"]
            if equipo_id in cache_entry["data"] and time.time() - cache_entry["timestamp"] < CACHE_EXPIRY:
                return cache_entry["data"][equipo_id]
        # Si no está en caché, buscar en las fuentes
        if self.use_espn_api:
            jugadores = self._get_jugadores_espn_api(equipo_id)
        # TODO: Agregar otras fuentes si es necesario
        # Actualizar caché
        with _cache_lock:
            cache_entry = _cached_data["jugadores"]
            cache_entry["data"][equipo_id] = jugadores
            cache_entry["timestamp"] = time.time()
        return jugadores

    def obtener_jugador_por_id(self, jugador_id: str, equipo_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene un jugador por su ID (y opcionalmente equipo).
        
        Args:
            jugador_id: ID del jugador a buscar
            equipo_id: ID del equipo (opcional)
            
        Returns:
            Diccionario con información del jugador o None si no se encuentra
        """
        jugadores = []
        if equipo_id:
            jugadores = self.obtener_jugadores_equipo(equipo_id)
        else:
            # Buscar en todas las fuentes si no se especifica equipo
            # (No eficiente, pero útil para pruebas)
            if self.use_espn_api:
                # Buscar en ligas principales
                for liga in ["PD", "PL", "BL1", "SA", "FL1"]:
                    equipos = self._get_equipos_liga_espn_api(liga)
                    for equipo in equipos:
                        jugadores = self._get_jugadores_espn_api(equipo.get('id'))
                        for jugador in jugadores:
                            if str(jugador.get('id')) == str(jugador_id):
                                return jugador
        for jugador in jugadores:
            if str(jugador.get('id')) == str(jugador_id):
                return jugador
        return None

    def obtener_partidos_historicos(self, dias: int = 30, liga: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene un DataFrame con los partidos históricos de los últimos `dias`.
        Combina datos de múltiples fuentes si es necesario.
        """
        cache_key = f"partidos_historicos_{dias}_{liga or 'all'}"
        cached_df = self.cache_manager.get(cache_key)
        if cached_df is not None and not cached_df.empty:
            logger.info(f"Usando caché para partidos históricos: {cache_key}")
            return cached_df

        logger.info(f"No hay caché para '{cache_key}', obteniendo datos frescos...")
        
        # Fechas para la consulta
        fecha_fin = datetime.now()
        fecha_inicio = fecha_fin - timedelta(days=dias)

        # Lista de funciones para obtener datos de diferentes fuentes
        source_functions = []
        if self.use_world_football:
            source_functions.append(lambda: self._get_partidos_historicos_world_football(fecha_inicio, fecha_fin, liga))
        if self.use_espn_api:
            source_functions.append(lambda: self._get_partidos_historicos_espn_api(fecha_inicio, fecha_fin, liga))

        # Ejecutar en paralelo
        all_partidos = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(func) for func in source_functions]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if not result.empty:
                        all_partidos.append(result)
                except Exception as e:
                    logger.error(f"Error al obtener partidos históricos de una fuente: {e}")

        if not all_partidos:
            logger.warning("No se pudieron obtener datos históricos de ninguna fuente.")
            return pd.DataFrame()

        # Consolidar y eliminar duplicados
        df_consolidado = pd.concat(all_partidos, ignore_index=True)
        df_consolidado.drop_duplicates(subset=['fecha', 'equipo_local', 'equipo_visitante'], inplace=True)
        df_consolidado.sort_values(by='fecha', ascending=False, inplace=True)

        # Guardar en caché
        self.cache_manager.set(cache_key, df_consolidado, expiry_seconds=CACHE_EXPIRY)
        
        return df_consolidado

    def _get_partidos_historicos_world_football(self, fecha_inicio: datetime, fecha_fin: datetime, liga: Optional[str]) -> pd.DataFrame:
        """Obtiene partidos históricos de World Football Data (CSV)."""
        # Lógica de ejemplo, se necesitaría una implementación real para descargar y parsear CSV
        logger.info("Obteniendo datos de World Football Data (simulado)")
        try:
            # Simulación: en un caso real, aquí se descargaría el CSV y se procesaría
            # Por ejemplo, usando requests y pandas.read_csv
            cached_file = self.cache_dir / "partidos_historicos.csv"
            if not cached_file.exists():
                logger.warning(f"Archivo de caché no encontrado: {cached_file}")
                return pd.DataFrame()

            df = pd.read_csv(cached_file)
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Filtrar por fecha y liga
            df_filtrado = df[(df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)]
            if liga:
                df_filtrado = df_filtrado[df_filtrado['liga'].str.lower() == liga.lower()]
            
            return df_filtrado
        except Exception as e:
            logger.error(f"Error en _get_partidos_historicos_world_football: {e}")
            return pd.DataFrame()

    def _get_partidos_historicos_espn_api(self, fecha_inicio: datetime, fecha_fin: datetime, liga: Optional[str]) -> pd.DataFrame:
        """Obtiene partidos históricos de la API de ESPN."""
        logger.info(f"Obteniendo datos de ESPN API para el rango {fecha_inicio.strftime('%Y-%m-%d')} a {fecha_fin.strftime('%Y-%m-%d')}")
        try:
            # Usar el adaptador de ESPN para obtener los datos
            partidos = self.espn_api.fetch_historical_matches(fecha_inicio, fecha_fin, liga)
            if not partidos:
                return pd.DataFrame()
            
            # Convertir a DataFrame
            df = pd.DataFrame(partidos)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        except Exception as e:
            logger.error(f"Error en _get_partidos_historicos_espn_api: {e}")
            return pd.DataFrame()

    def obtener_historial_arbitro(self, nombre_arbitro: str, equipo: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de partidos de un árbitro con un equipo específico.

        Args:
            nombre_arbitro: Nombre del árbitro.
            equipo: Nombre del equipo.

        Returns:
            Una lista de diccionarios, donde cada diccionario es un partido.
        """
        logger.info(f"Buscando historial para árbitro '{nombre_arbitro}' y equipo '{equipo}'")
        
        # Obtener todos los partidos históricos
        partidos_df = self.obtener_partidos_historicos(dias=365*5) # 5 años de historial

        if partidos_df.empty:
            logger.warning("No se encontraron partidos históricos.")
            return []

        # Filtrar por árbitro
        partidos_arbitro_df = partidos_df[partidos_df['arbitro'].str.lower() == nombre_arbitro.lower()]

        if partidos_arbitro_df.empty:
            logger.warning(f"No se encontraron partidos para el árbitro '{nombre_arbitro}'.")
            return []

        # Filtrar por equipo (local o visitante)
        equipo_lower = equipo.lower()
        historial_df = partidos_arbitro_df[
            (partidos_arbitro_df['equipo_local'].str.lower() == equipo_lower) |
            (partidos_arbitro_df['equipo_visitante'].str.lower() == equipo_lower)
        ]

        if historial_df.empty:
            logger.warning(f"No se encontró historial para el árbitro '{nombre_arbitro}' con el equipo '{equipo}'.")
            return []
        
        # Convertir a formato de diccionario
        historial = historial_df.to_dict('records')
        
        logger.info(f"Se encontraron {len(historial)} partidos para el árbitro '{nombre_arbitro}' con el equipo '{equipo}'.")
        return historial

    def guardar_jugador(self, jugador_datos: Dict[str, Any], equipo_id: str) -> Dict[str, Any]:
        """
        Guarda un nuevo jugador en la base de datos local (por equipo).
        
        Args:
            jugador_datos: Datos del jugador
            equipo_id: ID del equipo al que pertenece el jugador
            
        Returns:
            Diccionario con resultado de la operación
        """
        # TODO: Implementar almacenamiento local (sqlite o archivo)
        return {'success': False, 'error': 'No implementado'}

    def actualizar_jugador(self, jugador_id: str, jugador_datos: Dict[str, Any], equipo_id: str) -> Dict[str, Any]:
        """
        Actualiza un jugador existente en la base de datos local (por equipo).
        
        Args:
            jugador_id: ID del jugador a actualizar
            jugador_datos: Nuevos datos del jugador
            equipo_id: ID del equipo al que pertenece el jugador
            
        Returns:
            Diccionario con resultado de la operación
        """
        # TODO: Implementar actualización local
        return {'success': False, 'error': 'No implementado'}

    def eliminar_jugador(self, jugador_id: str, equipo_id: str) -> Dict[str, Any]:
        """
        Elimina un jugador de la base de datos local (por equipo).
        
        Args:
            jugador_id: ID del jugador a eliminar
            equipo_id: ID del equipo del que se eliminará el jugador
            
        Returns:
            Diccionario con resultado de la operación
        """
        # TODO: Implementar eliminación local
        return {'success': False, 'error': 'No implementado'}

    def importar_jugadores(self, jugadores: List[Dict[str, Any]], equipo_id: str, sobrescribir: bool = False) -> Dict[str, Any]:
        """
        Importa una lista de jugadores a la base de datos local (por equipo).
        
        Args:
            jugadores: Lista de jugadores a importar
            equipo_id: ID del equipo al que pertenecen los jugadores
            sobrescribir: Si es True, sobrescribe jugadores existentes con el mismo ID o nombre
            
        Returns:
            Diccionario con resultado de la operación
        """
        # TODO: Implementar importación local
        return {'success': False, 'error': 'No implementado'}

    def _get_jugadores_espn_api(self, equipo_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene jugadores de un equipo usando ESPN API.
        """
        try:
            espn = ESPNAPI()
            return espn.fetch_players(team_id=equipo_id)
        except Exception as e:
            logger.error(f"Error obteniendo jugadores ESPN API: {e}")
            return []

    # --- Métodos para equipos ---
    def obtener_equipos_liga(self, liga: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los equipos de una liga específica.
        
        Args:
            liga: Nombre de la liga
            
        Returns:
            Lista de equipos de la liga
        """
        equipos = []
        
        # Buscar en caché primero
        with _cache_lock:
            cache_entry = _cached_data["equipos"]
            if time.time() - cache_entry["timestamp"] < CACHE_EXPIRY:
                equipos = [e for e in cache_entry["data"] if e.get('liga', '').lower() == liga.lower()]
                if equipos:
                    return equipos
        
        # Si no hay datos en caché, buscar en todas las fuentes configuradas
        source_functions = []
        
        if self.use_football_data_api:
            source_functions.append(lambda: self._get_equipos_liga_football_data_api(liga))
        
        if self.use_espn_data:
            source_functions.append(lambda: self._get_equipos_liga_espn(liga))
            
        if self.use_espn_api:
            source_functions.append(lambda: self._get_equipos_liga_espn_api(liga))
            
        if self.use_open_football:
            source_functions.append(lambda: self._get_equipos_liga_open_football(liga))
        
        # Ejecutar en paralelo
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(func) for func in source_functions]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        for equipo in result:
                            # Evitar duplicados por nombre
                            if not any(e.get('nombre', '').lower() == equipo.get('nombre', '').lower() for e in equipos):
                                equipos.append(equipo)
                except Exception as e:
                    logger.error(f"Error al obtener equipos de la liga {liga}: {e}")
        
        # Actualizar caché
        if equipos:
            with _cache_lock:
                cache_equipos = _cached_data["equipos"]["data"]
                for equipo in equipos:
                    # Reemplazar o añadir equipos
                    for i, eq in enumerate(cache_equipos):
                        if eq.get('nombre', '').lower() == equipo.get('nombre', '').lower():
                            cache_equipos[i] = equipo
                            break
                    else:
                        cache_equipos.append(equipo)
                _cached_data["equipos"] = {"timestamp": time.time(), "data": cache_equipos}
        
        return equipos
    
    def obtener_equipo_por_id(self, equipo_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un equipo por su ID.
        
        Args:
            equipo_id: ID del equipo a buscar
            
        Returns:
            Diccionario con información del equipo o None si no se encuentra
        """
        # Buscar en caché primero
        with _cache_lock:
            cache_entry = _cached_data["equipos"]
            if time.time() - cache_entry["timestamp"] < CACHE_EXPIRY:
                for equipo in cache_entry["data"]:
                    if str(equipo.get('id', '')) == str(equipo_id):
                        return equipo
        
        # Si no está en caché, buscar en la base de datos local
        try:
            db_path = os.path.join(self.cache_dir, 'equipos_db.sqlite')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM equipos WHERE id = ?", (equipo_id,))
                row = cursor.fetchone()
                
                if row:
                    equipo = dict(row)
                    conn.close()
                    return equipo
                
                conn.close()
        except Exception as e:
            logger.error(f"Error al buscar equipo en base de datos: {e}")
        
        # Como último recurso, intentar obtener el equipo de las fuentes
        if self.use_football_data_api and equipo_id.startswith('fd-'):
            equipo = self._get_equipo_por_id_football_data_api(equipo_id)
            if equipo:
                return equipo
                
        if self.use_espn_api and equipo_id.startswith('espn-'):
            equipo = self._get_equipo_por_id_espn_api(equipo_id)
            if equipo:
                return equipo
        
        return None
    
    def guardar_equipo(self, equipo_datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Guarda un nuevo equipo en la base de datos local.
        
        Args:
            equipo_datos: Datos del equipo
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Generar ID si no existe
            if 'id' not in equipo_datos or not equipo_datos['id']:
                fuente = equipo_datos.get('fuente', 'manual')
                equipo_datos['id'] = f"{fuente}-{str(uuid.uuid4())[:8]}"
            
            # Validar campos requeridos
            if not equipo_datos.get('nombre'):
                return {'success': False, 'error': 'El nombre del equipo es obligatorio'}
            
            # Preparar directorio de base de datos
            db_path = os.path.join(self.cache_dir, 'equipos_db.sqlite')
            crear_tabla = not os.path.exists(db_path)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            if crear_tabla:
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipos (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    nombre_corto TEXT,
                    pais TEXT,
                    liga TEXT,
                    fundacion INTEGER,
                    estadio TEXT,
                    entrenador TEXT,
                    colores TEXT,
                    web TEXT,
                    escudo_url TEXT,
                    fuente TEXT,
                    fecha_creacion TEXT,
                    fecha_actualizacion TEXT
                )
                ''')
            
            # Verificar si ya existe un equipo con el mismo nombre
            cursor.execute("SELECT id FROM equipos WHERE LOWER(nombre) = LOWER(?)", 
                           (equipo_datos.get('nombre', ''),))
            existente = cursor.fetchone()
            
            if existente:
                conn.close()
                return {'success': False, 'error': f"Ya existe un equipo con el nombre {equipo_datos.get('nombre')}"}
            
            # Preparar datos para inserción
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            equipo_datos['fecha_creacion'] = ahora
            equipo_datos['fecha_actualizacion'] = ahora
            
            # Insertar equipo
            columnas = equipo_datos.keys()
            placeholders = ', '.join(['?'] * len(columnas))
            columnas_str = ', '.join(columnas)
            
            query = f"INSERT INTO equipos ({columnas_str}) VALUES ({placeholders})"
            cursor.execute(query, list(equipo_datos.values()))
            
            conn.commit()
            conn.close()
            
            # Actualizar caché
            with _cache_lock:
                cache_equipos = _cached_data["equipos"]["data"]
                cache_equipos.append(equipo_datos)
                _cached_data["equipos"] = {"timestamp": time.time(), "data": cache_equipos}
            
            return {'success': True, 'id': equipo_datos['id']}
            
        except Exception as e:
            logger.error(f"Error al guardar equipo: {e}")
            return {'success': False, 'error': str(e)}
    
    def actualizar_equipo(self, equipo_id: str, equipo_datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un equipo existente en la base de datos local.
        
        Args:
            equipo_id: ID del equipo a actualizar
            equipo_datos: Nuevos datos del equipo
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Validar campos requeridos
            if not equipo_datos.get('nombre'):
                return {'success': False, 'error': 'El nombre del equipo es obligatorio'}
            
            # Preparar directorio de base de datos
            db_path = os.path.join(self.cache_dir, 'equipos_db.sqlite')
            if not os.path.exists(db_path):
                return {'success': False, 'error': 'La base de datos no existe'}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si el equipo existe
            cursor.execute("SELECT id FROM equipos WHERE id = ?", (equipo_id,))
            existente = cursor.fetchone()
            
            if not existente:
                conn.close()
                return {'success': False, 'error': f"No existe un equipo con el ID {equipo_id}"}
            
            # Verificar si hay otro equipo con el mismo nombre (excepto este)
            cursor.execute("SELECT id FROM equipos WHERE LOWER(nombre) = LOWER(?) AND id != ?", 
                           (equipo_datos.get('nombre', ''), equipo_id))
            duplicado = cursor.fetchone()
            
            if duplicado:
                conn.close()
                return {'success': False, 'error': f"Ya existe otro equipo con el nombre {equipo_datos.get('nombre')}"}
            
            # Preparar datos para actualización
            equipo_datos['fecha_actualizacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Actualizar equipo
            update_cols = []
            update_values = []
            
            for key, value in equipo_datos.items():
                if key != 'id':  # No actualizamos el ID
                    update_cols.append(f"{key} = ?")
                    update_values.append(value)
            
            # Añadir ID para la condición WHERE
            update_values.append(equipo_id)
            
            query = f"UPDATE equipos SET {', '.join(update_cols)} WHERE id = ?"
            cursor.execute(query, update_values)
            
            conn.commit()
            conn.close()
            
            # Actualizar caché
            with _cache_lock:
                cache_equipos = _cached_data["equipos"]["data"]
                for i, equipo in enumerate(cache_equipos):
                    if equipo.get('id') == equipo_id:
                        cache_equipos[i] = equipo_datos
                        break
                _cached_data["equipos"] = {"timestamp": time.time(), "data": cache_equipos}
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error al actualizar equipo: {e}")
            return {'success': False, 'error': str(e)}
    
    def eliminar_equipo(self, equipo_id: str) -> Dict[str, Any]:
        """
        Elimina un equipo de la base de datos local.
        
        Args:
            equipo_id: ID del equipo a eliminar
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Preparar directorio de base de datos
            db_path = os.path.join(self.cache_dir, 'equipos_db.sqlite')
            if not os.path.exists(db_path):
                return {'success': False, 'error': 'La base de datos no existe'}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si el equipo existe
            cursor.execute("SELECT id FROM equipos WHERE id = ?", (equipo_id,))
            existente = cursor.fetchone()
            
            if not existente:
                conn.close()
                return {'success': False, 'error': f"No existe un equipo con el ID {equipo_id}"}
            
            # Eliminar equipo
            cursor.execute("DELETE FROM equipos WHERE id = ?", (equipo_id,))
            
            conn.commit()
            conn.close()
            
            # Actualizar caché
            with _cache_lock:
                cache_equipos = _cached_data["equipos"]["data"]
                cache_equipos = [e for e in cache_equipos if e.get('id') != equipo_id]
                _cached_data["equipos"] = {"timestamp": time.time(), "data": cache_equipos}
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error al eliminar equipo: {e}")
            return {'success': False, 'error': str(e)}
    
    def importar_equipos(self, equipos: List[Dict[str, Any]], sobrescribir: bool = False) -> Dict[str, Any]:
        """
        Importa una lista de equipos a la base de datos local.
        
        Args:
            equipos: Lista de equipos a importar
            sobrescribir: Si es True, sobrescribe equipos existentes con el mismo ID o nombre
            
        Returns:
            Diccionario con resultado de la operación
        """
        importados = 0
        errores = 0
        
        for equipo in equipos:
            try:
                # Generar ID si no existe
                if 'id' not in equipo or not equipo['id']:
                    fuente = equipo.get('fuente', 'import')
                    equipo['id'] = f"{fuente}-{str(uuid.uuid4())[:8]}"
                
                # Buscar si ya existe
                equipo_existente = self.obtener_equipo_por_id(equipo['id'])
                existe_por_nombre = False
                
                if not equipo_existente and 'nombre' in equipo:
                    # Buscar por nombre
                    with _cache_lock:
                        cache_equipos = _cached_data["equipos"]["data"]
                        for e in cache_equipos:
                            if e.get('nombre', '').lower() == equipo['nombre'].lower():
                                existe_por_nombre = True
                                equipo_existente = e
                                break
                
                if equipo_existente and not sobrescribir:
                    # Saltar este equipo si ya existe y no se debe sobrescribir
                    errores += 1
                    continue
                
                if equipo_existente and sobrescribir:
                    # Actualizar equipo existente
                    if existe_por_nombre:
                        equipo['id'] = equipo_existente['id']
                    
                    resultado = self.actualizar_equipo(equipo['id'], equipo)
                    if resultado.get('success'):
                        importados += 1
                    else:
                        errores += 1
                else:
                    # Crear nuevo equipo
                    resultado = self.guardar_equipo(equipo)
                    if resultado.get('success'):
                        importados += 1
                    else:
                        errores += 1
            
            except Exception as e:
                logger.error(f"Error importando equipo: {e}")
                errores += 1
        
        return {
            'success': importados > 0,
            'importados': importados,
            'errores': errores,
            'total': len(equipos)
        }
    
    # --- CRUD y gestión de partidos (matches) ---
    def obtener_partidos_liga(self, liga: str, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de una liga específica en un rango de fechas.
        """
        partidos = []
        if self.use_espn_api:
            partidos = self._get_partidos_espn_api(liga, fecha_inicio, fecha_fin)
        # TODO: Agregar otras fuentes si es necesario
        return partidos

    def obtener_partido_por_id(self, partido_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un partido por su ID.
        
        Args:
            partido_id: ID del partido a buscar
            
        Returns:
            Datos del partido o None si no se encuentra
        """
        # Buscar en todos los partidos
        partidos = self.obtener_partidos()
        for partido in partidos:
            if str(partido.get('id', '')) == str(partido_id):
                return partido
        
        # Si no se encontró, intentar obtener directamente de cada fuente
        return self._obtener_partido_por_id_directo(partido_id)

    def _obtener_partido_por_id_directo(self, partido_id: str) -> Optional[Dict[str, Any]]:
        """Intenta obtener un partido directamente de las fuentes disponibles."""
        # ESPN API
        if self.use_espn_api:
            try:
                espn_api = ESPNAPI()
                partido = espn_api.fetch_match(partido_id)
                if partido:
                    return self._standardize_match(partido, 'espn_api')
            except Exception as e:
                logger.error(f"Error al obtener partido {partido_id} de ESPN API: {str(e)}")
        
        # Football Data API
        if self.use_football_data_api:
            try:
                # Implementar obtención directa si la API lo soporta
                pass
            except Exception as e:
                logger.error(f"Error al obtener partido {partido_id} de Football Data API: {str(e)}")
        
        return None

    def guardar_partido(self, partido_datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Guarda un nuevo partido en el sistema.
        
        Args:
            partido_datos: Diccionario con los datos del partido
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Validar datos mínimos requeridos
            if 'equipo_local' not in partido_datos or 'equipo_visitante' not in partido_datos or 'fecha' not in partido_datos:
                return {'success': False, 'error': 'Datos incompletos. Se requiere equipo_local, equipo_visitante y fecha.'}
            
            # Crear ID único si no se proporciona
            if 'id' not in partido_datos:
                partido_datos['id'] = str(uuid.uuid4())
            
            # Buscar si el partido ya existe
            partido_existente = self.obtener_partido_por_id(partido_datos['id'])
            if partido_existente:
                return {'success': False, 'error': f"Ya existe un partido con ID {partido_datos['id']}"}
            
            # Guardar en base de datos o archivo
            self._guardar_partido_en_bd(partido_datos)
            
            # Actualizar caché
            self._actualizar_cache_partidos(partido_datos)
            
            return {'success': True, 'partido_id': partido_datos['id']}
        
        except Exception as e:
            logger.error(f"Error al guardar partido: {str(e)}")
            return {'success': False, 'error': str(e)}

    def actualizar_partido(self, partido_id: str, partido_datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un partido existente.
        
        Args:
            partido_id: ID del partido a actualizar
            partido_datos: Nuevos datos del partido
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Verificar que el partido existe
            partido_existente = self.obtener_partido_por_id(partido_id)
            if not partido_existente:
                return {'success': False, 'error': f"No existe un partido con ID {partido_id}"}
            
            # Asegurarse de que el ID no cambia
            partido_datos['id'] = partido_id
            
            # Actualizar en base de datos o archivo
            self._actualizar_partido_en_bd(partido_id, partido_datos)
            
            # Actualizar caché
            self._actualizar_cache_partidos(partido_datos, actualizar=True)
            
            return {'success': True, 'partido_id': partido_id}
        
        except Exception as e:
            logger.error(f"Error al actualizar partido: {str(e)}")
            return {'success': False, 'error': str(e)}

    def eliminar_partido(self, partido_id: str) -> Dict[str, Any]:
        """
        Elimina un partido.
        
        Args:
            partido_id: ID del partido a eliminar
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Verificar que el partido existe
            partido_existente = self.obtener_partido_por_id(partido_id)
            if not partido_existente:
                return {'success': False, 'error': f"No existe un partido con ID {partido_id}"}
            
            # Eliminar de base de datos o archivo
            self._eliminar_partido_de_bd(partido_id)
            
            # Actualizar caché
            self._eliminar_partido_de_cache(partido_id)
            
            return {'success': True}
        
        except Exception as e:
            logger.error(f"Error al eliminar partido: {str(e)}")
            return {'success': False, 'error': str(e)}

    def importar_partidos(self, partidos: List[Dict[str, Any]], sobrescribir: bool = False) -> Dict[str, Any]:
        """
        Importa una lista de partidos.
        
        Args:
            partidos: Lista de diccionarios con datos de partidos
            sobrescribir: Si se debe sobrescribir partidos existentes
            
        Returns:
            Diccionario con resultados de la operación
        """
        importados = 0
        errores = 0
        
        for partido in partidos:
            try:
                # Verificar si el partido ya existe
                partido_existente = None
                if 'id' in partido:
                    partido_existente = self.obtener_partido_por_id(partido['id'])
                
                # Si no existe o se debe sobrescribir, guardar/actualizar
                if not partido_existente:
                    resultado = self.guardar_partido(partido)
                    if resultado.get('success'):
                        importados += 1
                    else:
                        errores += 1
                        logger.warning(f"Error al importar partido: {resultado.get('error')}")
                elif sobrescribir:
                    resultado = self.actualizar_partido(partido['id'], partido)
                    if resultado.get('success'):
                        importados += 1
                    else:
                        errores += 1
                        logger.warning(f"Error al actualizar partido: {resultado.get('error')}")
                
            except Exception as e:
                errores += 1
                logger.error(f"Error al procesar partido durante importación: {str(e)}")
        
        return {
            'success': importados > 0,
            'importados': importados,
            'errores': errores
        }

    # --- Métodos para obtener próximos partidos ---
    def _get_proximos_partidos_football_data_api(self) -> List[Dict[str, Any]]:
        """
        Obtiene próximos partidos de football-data.org
        """
        # Lógica de ejemplo
        return []

    def _get_proximos_partidos_open_football(self) -> List[Dict[str, Any]]:
        """
        Obtiene próximos partidos de open football data
        """
        # Lógica de ejemplo
        return []

    def _get_proximos_partidos_espn(self) -> List[Dict[str, Any]]:
        """
        Obtiene próximos partidos de ESPN (scraping)
        """
        # Lógica de ejemplo
        return []

    def _get_proximos_partidos_espn_api(self) -> List[Dict[str, Any]]:
        """
        Obtiene próximos partidos de ESPN API
        """
        try:
            return self.espn_api.get_proximos_partidos(dias=14)
        except Exception as e:
            logger.error(f"Error en _get_proximos_partidos_espn_api: {e}")
            return []

    def _get_equipo_football_data_api(self, nombre_equipo: str) -> Optional[Dict[str, Any]]:
        return None

    def _get_equipo_open_football(self, nombre_equipo: str) -> Optional[Dict[str, Any]]:
        return None

    def _get_equipo_espn(self, nombre_equipo: str) -> Optional[Dict[str, Any]]:
        return None

    def _get_equipo_espn_api(self, nombre_equipo: str) -> Optional[Dict[str, Any]]:
        try:
            return self.espn_api.get_equipo(nombre_equipo)
        except Exception:
            return None

    def _get_equipos_liga_football_data_api(self, liga: str) -> List[Dict[str, Any]]:
        return []

    def _get_equipos_liga_espn(self, liga: str) -> List[Dict[str, Any]]:
        return []

    def _get_equipos_liga_open_football(self, liga: str) -> List[Dict[str, Any]]:
        return []

    def _get_equipos_liga_espn_api(self, liga: str) -> List[Dict[str, Any]]:
        try:
            return self.espn_api.get_equipos_liga(liga)
        except Exception:
            return []

    def _standardize_match(self, match: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Estandariza el formato de un partido de una fuente específica."""
        # Esta es una función de ejemplo, necesitarás adaptarla a los datos reales
        if source == 'espn_api':
            return {
                'id': match.get('id'),
                'fecha': match.get('date'),
                'liga': match.get('league', {}).get('name'),
                'equipo_local': match.get('competitors', [{}, {}])[0].get('team', {}).get('name'),
                'equipo_visitante': match.get('competitors', [{}, {}])[1].get('team', {}).get('name'),
                'resultado_local': match.get('competitors', [{}, {}])[0].get('score'),
                'resultado_visitante': match.get('competitors', [{}, {}])[1].get('score'),
                'estado': match.get('status', {}).get('type', {}).get('name'),
                'fuente': source
            }
        return match

    def _guardar_partido_en_bd(self, partido_datos: Dict[str, Any]):
        logger.info(f"Guardando partido en BD (simulado): {partido_datos.get('id')}")
    
    def _actualizar_cache_partidos(self, partido_datos: Dict[str, Any], actualizar: bool = False):
        logger.info(f"Actualizando caché de partidos (simulado): {partido_datos.get('id')}")

    def _actualizar_partido_en_bd(self, partido_id: str, partido_datos: Dict[str, Any]):
        logger.info(f"Actualizando partido en BD (simulado): {partido_id}")

    def _eliminar_partido_de_bd(self, partido_id: str):
        logger.info(f"Eliminando partido de BD (simulado): {partido_id}")

    def _eliminar_partido_de_cache(self, partido_id: str):
        logger.info(f"Eliminando partido de caché (simulado): {partido_id}")

    def obtener_partidos(self) -> List[Dict[str, Any]]:
        return []

    def __del__(self):
        if self.db_optimizer:
            self.db_optimizer.close_all()
