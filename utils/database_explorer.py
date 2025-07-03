"""
Utilidades para trabajar con la base de datos SQLite.

Este módulo proporciona funciones para facilitar el acceso y manipulación
de la base de datos SQLite del sistema.
"""

import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Union


def get_db_path() -> str:
    """
    Obtiene la ruta de la base de datos SQLite.
    
    Returns:
        Ruta a la base de datos o ':memory:' si no existe
    """
    db_path = os.path.join('data', 'database', 'futbol.db')
    if not os.path.exists(db_path):
        # Si no existe el directorio, crearlo
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Inicializar la base de datos
        initialize_db(db_path)
    
    return db_path


def initialize_db(db_path: str) -> None:
    """
    Inicializa la base de datos con tablas básicas si no existen.
    
    Args:
        db_path: Ruta de la base de datos
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas básicas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        pais TEXT,
        liga TEXT,
        estadio TEXT,
        fundacion INTEGER,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jugadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        equipo_id INTEGER,
        posicion TEXT,
        edad INTEGER,
        pais TEXT,
        dorsal INTEGER,
        FOREIGN KEY (equipo_id) REFERENCES equipos(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS arbitros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        pais TEXT,
        competicion_principal TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        equipo_local_id INTEGER,
        equipo_visitante_id INTEGER,
        goles_local INTEGER,
        goles_visitante INTEGER,
        liga TEXT,
        temporada TEXT,
        estadio TEXT,
        arbitro_id INTEGER,
        estado TEXT DEFAULT 'programado',
        FOREIGN KEY (equipo_local_id) REFERENCES equipos(id),
        FOREIGN KEY (equipo_visitante_id) REFERENCES equipos(id),
        FOREIGN KEY (arbitro_id) REFERENCES arbitros(id)
    )
    ''')
    
    conn.commit()
    conn.close()


def get_db_connection():
    """
    Obtiene una conexión a la base de datos.
    
    Returns:
        Conexión a la base de datos SQLite
    """
    db_path = get_db_path()
    return sqlite3.connect(db_path)


def execute_query(query: str, params: tuple = ()) -> List[tuple]:
    """
    Ejecuta una consulta SELECT en la base de datos.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros para la consulta
        
    Returns:
        Lista de filas con los resultados
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results


def execute_write_query(query: str, params: tuple = ()) -> int:
    """
    Ejecuta una consulta de escritura (INSERT, UPDATE, DELETE) en la base de datos.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros para la consulta
        
    Returns:
        Número de filas afectadas o el id de la última fila insertada
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    # Obtener ID de la última fila insertada o el número de filas afectadas
    last_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return last_id


def query_to_dataframe(query: str, params: tuple = ()) -> pd.DataFrame:
    """
    Ejecuta una consulta y devuelve los resultados como un DataFrame de pandas.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros para la consulta
        
    Returns:
        DataFrame con los resultados
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_table_names() -> List[str]:
    """
    Obtiene la lista de tablas en la base de datos.
    
    Returns:
        Lista de nombres de tablas
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    Obtiene el esquema de una tabla.
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        Lista de diccionarios con información de las columnas
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    
    schema = []
    for col in cursor.fetchall():
        schema.append({
            'id': col[0],
            'name': col[1],
            'type': col[2],
            'not_null': col[3] == 1,
            'default_value': col[4],
            'primary_key': col[5] == 1
        })
    
    conn.close()
    return schema


def save_dataframe_to_table(df: pd.DataFrame, table_name: str, if_exists: str = 'replace') -> int:
    """
    Guarda un DataFrame en una tabla de la base de datos.
    
    Args:
        df: DataFrame a guardar
        table_name: Nombre de la tabla
        if_exists: Comportamiento si la tabla existe ('fail', 'replace', 'append')
        
    Returns:
        Número de filas insertadas
    """
    conn = get_db_connection()
    rows = df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    conn.close()
    return rows


def import_from_csv(csv_path: str, table_name: str, if_exists: str = 'replace') -> int:
    """
    Importa datos desde un archivo CSV a una tabla en la base de datos.
    
    Args:
        csv_path: Ruta al archivo CSV
        table_name: Nombre de la tabla donde importar
        if_exists: Comportamiento si la tabla existe ('fail', 'replace', 'append')
        
    Returns:
        Número de filas importadas
    """
    try:
        df = pd.read_csv(csv_path)
        return save_dataframe_to_table(df, table_name, if_exists)
    except Exception as e:
        print(f"Error al importar datos desde CSV: {e}")
        return 0
