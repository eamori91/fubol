"""
Módulo para la conexión y operaciones con la base de datos.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

def get_db_config() -> Dict[str, Any]:
    """
    Obtiene la configuración de la base de datos desde el archivo de configuración.
    
    Returns:
        Dict con la configuración de la base de datos.
    """
    config_file = os.path.join('config', 'database.json')
    if not os.path.exists(config_file):
        logger.error(f"Archivo de configuración no encontrado: {config_file}")
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_connection_url() -> str:
    """
    Obtiene la URL de conexión a la base de datos basada en la configuración.
    
    Returns:
        URL de conexión para SQLAlchemy.
    """
    try:
        config = get_db_config()
        db_type = config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = config.get('sqlite', {}).get('db_path', 'data/database/football.db')
            # Asegurar que sea una ruta absoluta
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
            
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"
            
        elif db_type == 'postgresql':
            pg_config = config.get('postgresql', {})
            user = pg_config.get('user', 'postgres')
            password = pg_config.get('password', '')
            host = pg_config.get('host', 'localhost')
            port = pg_config.get('port', '5432')
            database = pg_config.get('database', 'football_analytics')
            
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
        elif db_type == 'mysql':
            mysql_config = config.get('mysql', {})
            user = mysql_config.get('user', 'root')
            password = mysql_config.get('password', '')
            host = mysql_config.get('host', 'localhost')
            port = mysql_config.get('port', '3306')
            database = mysql_config.get('database', 'football_analytics')
            
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")
    except Exception as e:
        logger.error(f"Error al obtener URL de conexión: {e}")
        raise

class DatabaseManager:
    """
    Clase para gestionar la conexión y operaciones con la base de datos.
    """
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """
        Inicializa la conexión a la base de datos.
        """
        try:
            # Obtener URL de conexión
            connection_url = get_connection_url()
            logger.info(f"Conectando a la base de datos: {connection_url.split(':')[0]}")
            
            # Obtener opciones de configuración
            config = get_db_config()
            options = config.get('options', {})
            
            # Crear motor de conexión
            self._engine = create_engine(
                connection_url,
                pool_size=options.get('pool_size', 10),
                max_overflow=options.get('max_overflow', 20),
                pool_timeout=options.get('pool_timeout', 30),
                echo=options.get('echo', False)
            )
            
            # Crear fábrica de sesiones
            self._session_factory = scoped_session(sessionmaker(bind=self._engine))
            
            logger.info("Conexión a la base de datos inicializada")
        except Exception as e:
            logger.error(f"Error al inicializar la conexión a la base de datos: {e}")
            self._engine = None
            self._session_factory = None
            raise
    
    @property
    def engine(self):
        """Devuelve el motor de conexión SQLAlchemy."""
        if self._engine is None:
            self._initialize()
        return self._engine
    
    @contextmanager
    def session_scope(self):
        """
        Proporciona un contexto de sesión que cierra automáticamente la sesión al final.
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en la sesión de base de datos: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL y devuelve los resultados como una lista de diccionarios.
        
        Args:
            query: Consulta SQL a ejecutar.
            params: Parámetros para la consulta (opcional).
            
        Returns:
            Lista de diccionarios con los resultados.
        """
        try:
            with self.session_scope() as session:
                result = session.execute(text(query), params or {})
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except SQLAlchemyError as e:
            logger.error(f"Error al ejecutar consulta: {e}")
            return []
    
    def get_single_result(self, query: str, params: Dict = None) -> Optional[Dict[str, Any]]:
        """
        Ejecuta una consulta y devuelve un solo resultado.
        
        Args:
            query: Consulta SQL a ejecutar.
            params: Parámetros para la consulta (opcional).
            
        Returns:
            Diccionario con el resultado o None si no hay resultados.
        """
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Inserta un registro en la tabla especificada.
        
        Args:
            table: Nombre de la tabla.
            data: Datos a insertar (diccionario columna -> valor).
            
        Returns:
            ID del registro insertado o None si hubo un error.
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f':{key}' for key in data.keys()])
        
        query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        RETURNING id
        """
        
        try:
            with self.session_scope() as session:
                result = session.execute(text(query), data)
                session.commit()
                return result.fetchone()[0]
        except SQLAlchemyError as e:
            logger.error(f"Error al insertar en {table}: {e}")
            return None

# Crear instancia global
db_manager = DatabaseManager()
