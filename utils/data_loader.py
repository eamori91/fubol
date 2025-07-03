"""
Módulo para cargar y preprocesar datos de diferentes fuentes.
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
import logging
import importlib

# Configurar el proveedor de datos
HAS_REAL_DATA = False
data_provider = None

# Verificar e importar el proveedor de datos reales (si está disponible)
try:
    data_provider_module = importlib.import_module('utils.data_provider')
    data_provider = data_provider_module.data_provider
    HAS_REAL_DATA = True
except (ImportError, AttributeError) as e:
    HAS_REAL_DATA = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_loader')

class DataLoader:
    def __init__(self):
        self.cache_dir = 'cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        self.use_real_data = HAS_REAL_DATA
    
    def cargar_datos_csv(self, ruta):
        """Carga datos desde un archivo CSV"""
        try:
            return pd.read_csv(ruta)
        except Exception as e:
            print(f"Error al cargar CSV: {e}")
            return None
    
    def cargar_datos_excel(self, ruta):
        """Carga datos desde un archivo Excel"""
        try:
            return pd.read_excel(ruta)
        except Exception as e:
            print(f"Error al cargar Excel: {e}")
            return None
    
    def cargar_datos_api(self, url, params=None, api_key=None):
        """Carga datos desde una API externa"""
        headers = {}
        if api_key:
            headers['X-Auth-Token'] = api_key
            
        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error en la solicitud API: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error al conectar con API: {e}")
            return None
    
    def obtener_partidos_historicos(self, equipo=None, temporada=None, liga=None):
        """
        Obtiene datos de partidos históricos con filtros opcionales.
        
        Args:
            equipo: Nombre del equipo para filtrar
            temporada: Temporada para filtrar (ej: "2023-24")
            liga: Nombre o código de la liga
            
        Returns:
            DataFrame con los partidos históricos o DataFrame vacío si no hay datos
        """
        # Intentar usar datos reales si está disponible
        if self.use_real_data and data_provider is not None:
            try:
                equipo_id = None
                liga_id = None
                
                # Buscar ID del equipo si se proporciona
                if equipo:
                    equipo_info = data_provider.buscar_equipo_por_nombre(equipo)
                    if equipo_info:
                        equipo_id = equipo_info['id']
                        logger.info(f"Equipo encontrado: {equipo} (ID: {equipo_id})")
                    else:
                        logger.warning(f"No se encontró el equipo: {equipo}")
                
                # Obtener datos desde la base de datos real
                df = data_provider.obtener_partidos_dataframe(
                    equipo_id=equipo_id,
                    temporada=temporada
                )
                
                if not df.empty:
                    logger.info(f"Obtenidos {len(df)} partidos de la base de datos real")
                    return df
                else:
                    logger.warning("No se encontraron partidos en la base de datos real")
            except Exception as e:
                logger.error(f"Error al obtener datos reales: {e}")
        
        # Fallback a datos en caché si no hay datos reales
        ruta = os.path.join(self.cache_dir, 'partidos_historicos.csv')
        if os.path.exists(ruta):
            logger.info(f"Cargando datos desde caché: {ruta}")
            df = self.cargar_datos_csv(ruta)
            
            # Verificar que el DataFrame no sea None
            if df is None:
                logger.error("El archivo de caché existe pero no se pudo cargar")
                return pd.DataFrame()  # Devolver DataFrame vacío en lugar de None
            
            # Aplicar filtros
            if equipo:
                df = df[(df['equipo_local'] == equipo) | (df['equipo_visitante'] == equipo)]
            if temporada:
                df = df[df['temporada'] == temporada]
            if liga:
                df = df[df['liga'] == liga]
                
            return df
        else:
            logger.warning("No se encontraron datos históricos en caché")
            return pd.DataFrame()  # Devolver DataFrame vacío en lugar de None
    
    def obtener_partidos_proximos(self, dias=7, equipo=None, liga=None):
        """
        Obtiene datos de partidos próximos a jugarse.
        
        Args:
            dias: Número de días hacia adelante para buscar partidos
            equipo: Nombre del equipo para filtrar
            liga: Nombre o código de la liga
            
        Returns:
            DataFrame con los partidos próximos o DataFrame vacío si no hay datos
        """
        # Intentar usar datos reales si está disponible
        if self.use_real_data and data_provider is not None:
            try:
                equipo_id = None
                liga_id = None
                
                # Buscar ID del equipo si se proporciona
                if equipo:
                    equipo_info = data_provider.buscar_equipo_por_nombre(equipo)
                    if equipo_info:
                        equipo_id = equipo_info['id']
                
                # Fechas para filtrar
                fecha_desde = datetime.now().strftime('%Y-%m-%d')
                fecha_hasta = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')
                
                # Obtener partidos programados
                partidos = data_provider.obtener_partidos(
                    equipo_id=equipo_id,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    estado='SCHEDULED',  # Solo partidos programados
                    limite=100
                )
                
                if partidos:
                    logger.info(f"Obtenidos {len(partidos)} partidos próximos de la base de datos real")
                    
                    # Convertir a DataFrame en el formato esperado
                    df = pd.DataFrame({
                        'fecha': [p['fecha'] for p in partidos],
                        'liga': [p['liga_nombre'] for p in partidos],
                        'equipo_local': [p['equipo_local'] for p in partidos],
                        'equipo_visitante': [p['equipo_visitante'] for p in partidos],
                        'estadio': [p.get('estadio', 'No disponible') for p in partidos],
                        'probabilidad_local': [None] * len(partidos),  # Se completarán después
                        'probabilidad_empate': [None] * len(partidos),
                        'probabilidad_visitante': [None] * len(partidos)
                    })
                    
                    return df
            except Exception as e:
                logger.error(f"Error al obtener partidos próximos reales: {e}")
        
        # Fallback a datos simulados o caché
        logger.info("Generando datos simulados para partidos próximos")
        columnas = ['fecha', 'liga', 'equipo_local', 'equipo_visitante', 'estadio', 
                   'probabilidad_local', 'probabilidad_empate', 'probabilidad_visitante']
        df = pd.DataFrame(columns=columnas)
        
        # Aquí podría implementarse lógica para generar datos simulados más realistas
        # basados en equipos conocidos de la caché
        
        return df
    
    def obtener_estadisticas_jugadores(self, equipo=None, temporada=None):
        """
        Obtiene estadísticas de jugadores con filtros opcionales.
        
        Args:
            equipo: Nombre del equipo para filtrar
            temporada: Temporada para filtrar (ej: "2023-24")
            
        Returns:
            DataFrame con estadísticas de jugadores o DataFrame vacío si no hay datos
        """
        # Intentar usar datos reales si está disponible
        if self.use_real_data and data_provider is not None:
            try:
                equipo_id = None
                
                # Buscar ID del equipo si se proporciona
                if equipo:
                    equipo_info = data_provider.buscar_equipo_por_nombre(equipo)
                    if equipo_info:
                        equipo_id = equipo_info['id']
                
                # Obtener jugadores
                jugadores = data_provider.obtener_jugadores(equipo_id=equipo_id)
                
                if jugadores:
                    logger.info(f"Obtenidos {len(jugadores)} jugadores de la base de datos real")
                    
                    # Convertir a DataFrame
                    df_jugadores = pd.DataFrame(jugadores)
                    
                    # TODO: Obtener estadísticas de los jugadores para la temporada especificada
                    # Esto requeriría implementar una función adicional en data_provider
                    
                    return df_jugadores
                else:
                    logger.warning(f"No se encontraron jugadores para el equipo: {equipo}")
            except Exception as e:
                logger.error(f"Error al obtener estadísticas de jugadores: {e}")
        
        # Fallback a datos simulados o vacíos
        logger.info("No hay datos reales de jugadores disponibles")
        return pd.DataFrame()
    
    def obtener_equipos(self, liga=None):
        """
        Obtiene la lista de equipos, opcionalmente filtrados por liga.
        
        Args:
            liga: Nombre o código de la liga
            
        Returns:
            Lista de equipos o lista vacía si no hay datos
        """
        # Intentar usar datos reales si está disponible
        if self.use_real_data and data_provider is not None:
            try:
                liga_id = None
                
                # TODO: Implementar búsqueda de liga por nombre/código si se necesita
                
                # Obtener equipos
                equipos = data_provider.obtener_equipos(liga_id=liga_id)
                
                if equipos:
                    logger.info(f"Obtenidos {len(equipos)} equipos de la base de datos real")
                    return equipos
                else:
                    logger.warning("No se encontraron equipos en la base de datos real")
            except Exception as e:
                logger.error(f"Error al obtener equipos: {e}")
        
        # Fallback a datos en caché o datos ficticios
        equipos_ejemplo = [
            {"id": 1, "nombre": "Real Madrid", "liga": "La Liga", "pais": "España"},
            {"id": 2, "nombre": "Barcelona", "liga": "La Liga", "pais": "España"},
            {"id": 3, "nombre": "Atlético Madrid", "liga": "La Liga", "pais": "España"},
            {"id": 4, "nombre": "Sevilla", "liga": "La Liga", "pais": "España"},
            {"id": 5, "nombre": "Valencia", "liga": "La Liga", "pais": "España"}
        ]
        
        logger.info("Devolviendo lista de equipos de ejemplo")
        return equipos_ejemplo
    
    def obtener_ligas(self):
        """
        Obtiene la lista de ligas disponibles.
        
        Returns:
            Lista de ligas o lista vacía si no hay datos
        """
        # Intentar usar datos reales si está disponible
        if self.use_real_data and data_provider is not None:
            try:
                ligas = data_provider.obtener_ligas()
                
                if ligas:
                    logger.info(f"Obtenidas {len(ligas)} ligas de la base de datos real")
                    return ligas
                else:
                    logger.warning("No se encontraron ligas en la base de datos real")
            except Exception as e:
                logger.error(f"Error al obtener ligas: {e}")
        
        # Fallback a datos ficticios
        ligas_ejemplo = [
            {"id": 1, "codigo": "PD", "nombre": "Primera División", "pais": "España"},
            {"id": 2, "codigo": "PL", "nombre": "Premier League", "pais": "Inglaterra"},
            {"id": 3, "codigo": "SA", "nombre": "Serie A", "pais": "Italia"},
            {"id": 4, "codigo": "BL1", "nombre": "Bundesliga", "pais": "Alemania"},
            {"id": 5, "codigo": "FL1", "nombre": "Ligue 1", "pais": "Francia"}
        ]
        
        logger.info("Devolviendo lista de ligas de ejemplo")
        return ligas_ejemplo
    
    def guardar_en_cache(self, df, nombre):
        """
        Guarda un DataFrame en caché para uso futuro.
        
        Args:
            df: DataFrame a guardar
            nombre: Nombre del archivo (sin extensión)
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            ruta = os.path.join(self.cache_dir, f"{nombre}.csv")
            df.to_csv(ruta, index=False)
            logger.info(f"Datos guardados en {ruta}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar en caché: {e}")
            return False