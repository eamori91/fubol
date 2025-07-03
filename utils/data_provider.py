"""
Módulo para obtener datos reales desde la base de datos.

Este módulo proporciona funciones para obtener datos de equipos, jugadores,
partidos y otras entidades desde la base de datos.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import json
from datetime import datetime, timedelta

# Importar gestor de base de datos
from utils.database import db_manager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_provider')

class RealDataProvider:
    """
    Clase para proporcionar datos reales desde la base de datos.
    """
    
    @staticmethod
    def obtener_ligas() -> List[Dict[str, Any]]:
        """
        Obtiene la lista de ligas disponibles.
        
        Returns:
            Lista de ligas como diccionarios.
        """
        query = """
        SELECT id, codigo, nombre, pais, temporada_actual
        FROM ligas
        ORDER BY nombre
        """
        
        try:
            return db_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Error al obtener ligas: {e}")
            return []
    
    @staticmethod
    def obtener_equipos(liga_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de equipos, opcionalmente filtrados por liga.
        
        Args:
            liga_id: ID de la liga para filtrar (opcional).
            
        Returns:
            Lista de equipos como diccionarios.
        """
        query = """
        SELECT e.id, e.nombre, e.nombre_corto, e.pais, e.fundacion, 
               e.estadio, e.escudo_url, l.nombre as liga_nombre
        FROM equipos e
        LEFT JOIN ligas l ON e.liga_id = l.id
        """
        
        params = {}
        if liga_id is not None:
            query += " WHERE e.liga_id = :liga_id"
            params['liga_id'] = liga_id
            
        query += " ORDER BY e.nombre"
        
        try:
            return db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error al obtener equipos: {e}")
            return []
    
    @staticmethod
    def obtener_equipo(equipo_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un equipo por su ID.
        
        Args:
            equipo_id: ID del equipo.
            
        Returns:
            Diccionario con datos del equipo o None si no existe.
        """
        query = """
        SELECT e.id, e.nombre, e.nombre_corto, e.pais, e.fundacion, 
               e.estadio, e.escudo_url, l.nombre as liga_nombre, l.id as liga_id
        FROM equipos e
        LEFT JOIN ligas l ON e.liga_id = l.id
        WHERE e.id = :equipo_id
        """
        
        try:
            return db_manager.get_single_result(query, {'equipo_id': equipo_id})
        except Exception as e:
            logger.error(f"Error al obtener equipo {equipo_id}: {e}")
            return None
    
    @staticmethod
    def buscar_equipo_por_nombre(nombre: str) -> Optional[Dict[str, Any]]:
        """
        Busca un equipo por su nombre.
        
        Args:
            nombre: Nombre o parte del nombre del equipo.
            
        Returns:
            Diccionario con datos del equipo o None si no existe.
        """
        query = """
        SELECT e.id, e.nombre, e.nombre_corto, e.pais, e.fundacion, 
               e.estadio, e.escudo_url, l.nombre as liga_nombre, l.id as liga_id
        FROM equipos e
        LEFT JOIN ligas l ON e.liga_id = l.id
        WHERE LOWER(e.nombre) LIKE :nombre OR LOWER(e.nombre_corto) LIKE :nombre
        LIMIT 1
        """
        
        try:
            nombre_param = f"%{nombre.lower()}%"
            return db_manager.get_single_result(query, {'nombre': nombre_param})
        except Exception as e:
            logger.error(f"Error al buscar equipo '{nombre}': {e}")
            return None
    
    @staticmethod
    def obtener_jugadores(equipo_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de jugadores, opcionalmente filtrados por equipo.
        
        Args:
            equipo_id: ID del equipo para filtrar (opcional).
            
        Returns:
            Lista de jugadores como diccionarios.
        """
        query = """
        SELECT j.id, j.nombre, j.apellido, j.posicion, j.nacionalidad, 
               j.fecha_nacimiento, j.altura, j.peso, j.dorsal, j.foto_url,
               e.id as equipo_id, e.nombre as equipo_nombre
        FROM jugadores j
        LEFT JOIN equipos e ON j.equipo_id = e.id
        """
        
        params = {}
        if equipo_id is not None:
            query += " WHERE j.equipo_id = :equipo_id"
            params['equipo_id'] = equipo_id
            
        query += " ORDER BY j.apellido, j.nombre"
        
        try:
            return db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error al obtener jugadores: {e}")
            return []
    
    @staticmethod
    def obtener_partidos(
        liga_id: Optional[int] = None, 
        equipo_id: Optional[int] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        temporada: Optional[str] = None,
        estado: Optional[str] = None,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene partidos con filtros opcionales.
        
        Args:
            liga_id: ID de la liga.
            equipo_id: ID del equipo.
            fecha_desde: Fecha mínima (formato YYYY-MM-DD).
            fecha_hasta: Fecha máxima (formato YYYY-MM-DD).
            temporada: Temporada (ej: "2023-24").
            estado: Estado del partido (SCHEDULED, FINISHED, etc).
            limite: Límite de resultados a obtener.
            
        Returns:
            Lista de partidos como diccionarios.
        """
        query = """
        SELECT p.id, p.fecha, p.jornada, p.goles_local, p.goles_visitante,
               p.estado, p.temporada, l.nombre as liga_nombre,
               el.id as equipo_local_id, el.nombre as equipo_local,
               ev.id as equipo_visitante_id, ev.nombre as equipo_visitante,
               p.resultado_primer_tiempo_local, p.resultado_primer_tiempo_visitante
        FROM partidos p
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        JOIN ligas l ON p.liga_id = l.id
        WHERE 1=1
        """
        
        params = {}
        
        if liga_id is not None:
            query += " AND p.liga_id = :liga_id"
            params['liga_id'] = liga_id
            
        if equipo_id is not None:
            query += " AND (p.equipo_local_id = :equipo_id OR p.equipo_visitante_id = :equipo_id)"
            params['equipo_id'] = equipo_id
            
        if fecha_desde is not None:
            query += " AND p.fecha >= :fecha_desde"
            params['fecha_desde'] = fecha_desde
            
        if fecha_hasta is not None:
            query += " AND p.fecha <= :fecha_hasta"
            params['fecha_hasta'] = fecha_hasta
            
        if temporada is not None:
            query += " AND p.temporada = :temporada"
            params['temporada'] = temporada
            
        if estado is not None:
            query += " AND p.estado = :estado"
            params['estado'] = estado
            
        query += " ORDER BY p.fecha DESC LIMIT :limite"
        params['limite'] = limite
        
        try:
            return db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error al obtener partidos: {e}")
            return []
    
    @staticmethod
    def obtener_partido(partido_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un partido por su ID.
        
        Args:
            partido_id: ID del partido.
            
        Returns:
            Diccionario con datos del partido o None si no existe.
        """
        query = """
        SELECT p.id, p.fecha, p.jornada, p.goles_local, p.goles_visitante,
               p.estado, p.temporada, l.nombre as liga_nombre, l.id as liga_id,
               el.id as equipo_local_id, el.nombre as equipo_local,
               ev.id as equipo_visitante_id, ev.nombre as equipo_visitante,
               p.resultado_primer_tiempo_local, p.resultado_primer_tiempo_visitante,
               p.estadio, p.arbitro
        FROM partidos p
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        JOIN ligas l ON p.liga_id = l.id
        WHERE p.id = :partido_id
        """
        
        try:
            return db_manager.get_single_result(query, {'partido_id': partido_id})
        except Exception as e:
            logger.error(f"Error al obtener partido {partido_id}: {e}")
            return None
    
    @staticmethod
    def obtener_eventos_partido(partido_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los eventos de un partido.
        
        Args:
            partido_id: ID del partido.
            
        Returns:
            Lista de eventos del partido.
        """
        query = """
        SELECT e.id, e.minuto, e.tipo, e.detalle,
               j1.id as jugador_id, j1.nombre as jugador_nombre, j1.apellido as jugador_apellido,
               j2.id as jugador2_id, j2.nombre as jugador2_nombre, j2.apellido as jugador2_apellido,
               eq.id as equipo_id, eq.nombre as equipo_nombre
        FROM eventos_partido e
        JOIN equipos eq ON e.equipo_id = eq.id
        LEFT JOIN jugadores j1 ON e.jugador_id = j1.id
        LEFT JOIN jugadores j2 ON e.jugador2_id = j2.id
        WHERE e.partido_id = :partido_id
        ORDER BY e.minuto
        """
        
        try:
            return db_manager.execute_query(query, {'partido_id': partido_id})
        except Exception as e:
            logger.error(f"Error al obtener eventos del partido {partido_id}: {e}")
            return []
    
    @staticmethod
    def obtener_clasificacion(liga_id: int, temporada: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Calcula la clasificación de una liga.
        
        Args:
            liga_id: ID de la liga.
            temporada: Temporada (ej: "2023-24"), si es None se usa la actual.
            
        Returns:
            Lista con la clasificación de equipos.
        """
        # Si no se proporciona temporada, obtener la actual
        if temporada is None:
            liga_query = "SELECT temporada_actual FROM ligas WHERE id = :liga_id"
            liga = db_manager.get_single_result(liga_query, {'liga_id': liga_id})
            if liga:
                temporada = liga['temporada_actual']
            else:
                return []
        
        query = """
        SELECT 
            e.id as equipo_id,
            e.nombre as equipo,
            COUNT(p.id) as partidos_jugados,
            SUM(CASE WHEN 
                (p.equipo_local_id = e.id AND p.goles_local > p.goles_visitante) OR 
                (p.equipo_visitante_id = e.id AND p.goles_visitante > p.goles_local) 
                THEN 1 ELSE 0 END) as partidos_ganados,
            SUM(CASE WHEN p.goles_local = p.goles_visitante THEN 1 ELSE 0 END) as partidos_empatados,
            SUM(CASE WHEN 
                (p.equipo_local_id = e.id AND p.goles_local < p.goles_visitante) OR 
                (p.equipo_visitante_id = e.id AND p.goles_visitante < p.goles_local) 
                THEN 1 ELSE 0 END) as partidos_perdidos,
            SUM(CASE WHEN p.equipo_local_id = e.id THEN p.goles_local ELSE p.goles_visitante END) as goles_favor,
            SUM(CASE WHEN p.equipo_local_id = e.id THEN p.goles_visitante ELSE p.goles_local END) as goles_contra,
            SUM(CASE WHEN 
                (p.equipo_local_id = e.id AND p.goles_local > p.goles_visitante) OR 
                (p.equipo_visitante_id = e.id AND p.goles_visitante > p.goles_local) 
                THEN 3 ELSE (CASE WHEN p.goles_local = p.goles_visitante THEN 1 ELSE 0 END) END) as puntos
        FROM equipos e
        JOIN partidos p ON (p.equipo_local_id = e.id OR p.equipo_visitante_id = e.id)
        WHERE p.liga_id = :liga_id
        AND p.temporada = :temporada
        AND p.estado = 'FINISHED'
        GROUP BY e.id, e.nombre
        ORDER BY puntos DESC, (goles_favor - goles_contra) DESC, goles_favor DESC
        """
        
        try:
            return db_manager.execute_query(query, {'liga_id': liga_id, 'temporada': temporada})
        except Exception as e:
            logger.error(f"Error al obtener clasificación: {e}")
            return []
    
    @staticmethod
    def obtener_partidos_dataframe(
        equipo_id: Optional[int] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        temporada: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Obtiene partidos como un DataFrame de pandas.
        
        Args:
            equipo_id: ID del equipo para filtrar.
            fecha_desde: Fecha mínima (formato YYYY-MM-DD).
            fecha_hasta: Fecha máxima (formato YYYY-MM-DD).
            temporada: Temporada (ej: "2023-24").
            
        Returns:
            DataFrame con los partidos o DataFrame vacío si hay error.
        """
        # Obtener partidos como lista de diccionarios
        partidos = RealDataProvider.obtener_partidos(
            equipo_id=equipo_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            temporada=temporada,
            estado='FINISHED',  # Solo partidos terminados
            limite=1000  # Suficiente para análisis
        )
        
        if not partidos:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df = pd.DataFrame(partidos)
        
        # Procesar para formato común usado en análisis
        df_procesado = pd.DataFrame({
            'fecha': pd.to_datetime(df['fecha']),
            'temporada': df['temporada'],
            'jornada': df['jornada'],
            'equipo_local': df['equipo_local'],
            'equipo_visitante': df['equipo_visitante'],
            'goles_local': df['goles_local'],
            'goles_visitante': df['goles_visitante'],
            'resultado': df.apply(lambda x: 
                'H' if x['goles_local'] > x['goles_visitante'] else 
                'A' if x['goles_local'] < x['goles_visitante'] else 'D', axis=1)
        })
        
        return df_procesado


# Crear instancia global
data_provider = RealDataProvider()
