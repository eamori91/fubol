"""
Optimizador de base de datos para mejorar la eficiencia de las operaciones
con bases de datos SQLite y conexiones de bases de datos en general.
"""

import sqlite3
import logging
import threading
import time
import os
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from functools import wraps
from contextlib import contextmanager

# Configurar logging
logger = logging.getLogger('db_optimizer')

class ConnectionPool:
    """
    Pool de conexiones para SQLite que permite reutilizar conexiones y
    optimizar operaciones de bases de datos.
    """
    
    def __init__(
        self,
        db_path: str,
        max_connections: int = 5,
        timeout: float = 30.0,
        check_same_thread: bool = False
    ):
        """
        Inicializa el pool de conexiones.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            max_connections: Número máximo de conexiones en el pool
            timeout: Tiempo máximo (segundos) para esperar una conexión
            check_same_thread: Verificar mismo hilo (False para permitir compartir)
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        self.check_same_thread = check_same_thread
        
        # Inicializar pool vacío
        self._pool: List[sqlite3.Connection] = []
        self._in_use: Dict[int, sqlite3.Connection] = {}
        self._lock = threading.RLock()
        
        logger.info(f"Pool de conexiones inicializado para {db_path} "
                  f"(max={max_connections}, timeout={timeout}s)")
    
    def _create_connection(self) -> sqlite3.Connection:
        """
        Crea una nueva conexión a la base de datos.
        
        Returns:
            Conexión SQLite configurada
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=self.check_same_thread
        )
        
        # Optimizaciones para SQLite
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous = NORMAL")  # Menos sincronización a disco
        conn.execute("PRAGMA cache_size = 10000")   # Cache de 10MB
        conn.execute("PRAGMA temp_store = MEMORY")  # Tablas temporales en memoria
        conn.execute("PRAGMA foreign_keys = ON")    # Activar restricciones de clave foránea
        
        # Configurar para devolver filas como diccionarios
        conn.row_factory = sqlite3.Row
        
        return conn
    
    @contextmanager
    def get_connection(self):
        """
        Obtiene una conexión del pool. Si el pool está vacío y no se ha
        alcanzado el máximo, crea una nueva conexión.
        
        Yields:
            sqlite3.Connection: Conexión a la base de datos
        """
        conn = None
        conn_id = None
        
        with self._lock:
            # Intentar obtener del pool
            if self._pool:
                conn = self._pool.pop()
            # Si no hay conexiones disponibles y no hemos alcanzado el máximo, crear nueva
            elif len(self._in_use) < self.max_connections:
                conn = self._create_connection()
            # Si hemos alcanzado el máximo, esperar a que se libere una
            else:
                logger.warning(f"Pool de conexiones agotado para {self.db_path}, esperando...")
                
                # Esperar y reintentar
                max_attempts = 10
                attempt = 0
                
                while attempt < max_attempts and not conn:
                    # Liberar el lock mientras esperamos
                    self._lock.release()
                    time.sleep(0.1 * (attempt + 1))  # Backoff
                    self._lock.acquire()
                    
                    attempt += 1
                    
                    # Reintentar obtener una conexión
                    if self._pool:
                        conn = self._pool.pop()
                        break
                
                # Si aún no tenemos conexión, crear una temporalmente por encima del límite
                if not conn:
                    logger.warning(f"Creando conexión temporal por encima del límite para {self.db_path}")
                    conn = self._create_connection()
            
            # Marcar como en uso
            conn_id = id(conn)
            self._in_use[conn_id] = conn
        
        try:
            # Entregar conexión al usuario
            yield conn
        finally:
            # Devolver al pool
            with self._lock:
                # Si la conexión sigue en uso (no cerrada por error)
                if conn_id in self._in_use:
                    # Quitar de en_uso
                    del self._in_use[conn_id]
                    
                    try:
                        # Si hay transacciones abiertas, hacer rollback
                        conn.rollback()
                        # Devolver al pool
                        self._pool.append(conn)
                    except sqlite3.Error as e:
                        # Si la conexión está dañada, no devolver al pool
                        logger.warning(f"Conexión descartada por error: {e}")
                        try:
                            conn.close()
                        except:
                            pass
    
    def close_all(self):
        """Cierra todas las conexiones del pool."""
        with self._lock:
            # Cerrar conexiones en uso
            for conn in self._in_use.values():
                try:
                    conn.close()
                except:
                    pass
            
            # Cerrar conexiones en pool
            for conn in self._pool:
                try:
                    conn.close()
                except:
                    pass
            
            # Limpiar colecciones
            self._in_use.clear()
            self._pool.clear()
            
            logger.info(f"Todas las conexiones cerradas para {self.db_path}")


class DBOptimizer:
    """
    Optimizador de operaciones de base de datos SQLite.
    """
    
    def __init__(self):
        """Inicializa el optimizador de base de datos."""
        # Almacenar pools por ruta de BD
        self._pools: Dict[str, ConnectionPool] = {}
        self._lock = threading.RLock()
    
    def get_pool(
        self, 
        db_path: str,
        max_connections: int = 5,
        timeout: float = 30.0,
        check_same_thread: bool = False
    ) -> ConnectionPool:
        """
        Obtiene un pool de conexiones para la base de datos.
        Si no existe, lo crea.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            max_connections: Número máximo de conexiones en el pool
            timeout: Tiempo máximo (segundos) para esperar una conexión
            check_same_thread: Verificar mismo hilo
            
        Returns:
            Pool de conexiones
        """
        with self._lock:
            if db_path not in self._pools:
                self._pools[db_path] = ConnectionPool(
                    db_path=db_path,
                    max_connections=max_connections,
                    timeout=timeout,
                    check_same_thread=check_same_thread
                )
                
            return self._pools[db_path]
    
    @contextmanager
    def connection(
        self,
        db_path: str,
        max_connections: int = 5,
        timeout: float = 30.0,
        check_same_thread: bool = False
    ):
        """
        Obtiene una conexión del pool para la base de datos especificada.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            max_connections: Número máximo de conexiones en el pool
            timeout: Tiempo máximo (segundos) para esperar una conexión
            check_same_thread: Verificar mismo hilo
            
        Yields:
            sqlite3.Connection: Conexión a la base de datos
        """
        pool = self.get_pool(
            db_path=db_path,
            max_connections=max_connections,
            timeout=timeout,
            check_same_thread=check_same_thread
        )
        
        with pool.get_connection() as conn:
            yield conn
    
    def execute_query(
        self,
        db_path: str,
        query: str,
        params: Union[Tuple, Dict, List] = (),
        fetch_one: bool = False,
        as_dict: bool = True
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Ejecuta una consulta SQL y devuelve los resultados.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            fetch_one: Si True, devuelve solo la primera fila
            as_dict: Si True, convierte los resultados a diccionarios
            
        Returns:
            Resultados de la consulta como lista de diccionarios, un diccionario o None
        """
        start_time = time.time()
        try:
            with self.connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                    if result and as_dict:
                        return {k: result[k] for k in result.keys()}
                    return result
                else:
                    results = cursor.fetchall()
                    if as_dict:
                        return [{k: row[k] for k in row.keys()} for row in results]
                    return results
                    
        except Exception as e:
            logger.error(f"Error ejecutando consulta en {db_path}: {str(e)}")
            logger.debug(f"Query: {query}, Params: {params}")
            raise
        finally:
            execution_time = time.time() - start_time
            if execution_time > 0.5:  # Log queries lentas (>500ms)
                logger.warning(f"Consulta lenta ({execution_time:.2f}s) en {db_path}: {query[:100]}...")
    
    def execute_script(self, db_path: str, script: str) -> None:
        """
        Ejecuta un script SQL completo.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            script: Script SQL a ejecutar
        """
        start_time = time.time()
        try:
            with self.connection(db_path) as conn:
                conn.executescript(script)
                conn.commit()
        except Exception as e:
            logger.error(f"Error ejecutando script en {db_path}: {str(e)}")
            raise
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Script ejecutado en {execution_time:.2f}s en {db_path}")
    
    def execute_transaction(
        self,
        db_path: str,
        operations: List[Tuple[str, Union[Tuple, Dict, List]]],
        commit: bool = True
    ) -> None:
        """
        Ejecuta múltiples operaciones en una transacción.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            operations: Lista de tuplas (query, params)
            commit: Si True, hace commit al final
        """
        start_time = time.time()
        try:
            with self.connection(db_path) as conn:
                cursor = conn.cursor()
                
                for query, params in operations:
                    cursor.execute(query, params)
                
                if commit:
                    conn.commit()
        except Exception as e:
            logger.error(f"Error en transacción en {db_path}: {str(e)}")
            raise
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Transacción con {len(operations)} operaciones "
                       f"completada en {execution_time:.2f}s en {db_path}")
    
    def batch_insert(
        self,
        db_path: str,
        table: str,
        records: List[Dict[str, Any]],
        replace: bool = False,
        batch_size: int = 100
    ) -> int:
        """
        Inserta múltiples registros de forma eficiente.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            table: Nombre de la tabla
            records: Lista de diccionarios con los datos a insertar
            replace: Si True, usa REPLACE INTO en vez de INSERT INTO
            batch_size: Tamaño del lote para cada operación
            
        Returns:
            Número total de registros insertados
        """
        if not records:
            return 0
            
        start_time = time.time()
        total_inserted = 0
        
        try:
            with self.connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Procesar en lotes
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    
                    if not batch:
                        continue
                    
                    # Extraer columnas del primer registro
                    columns = list(batch[0].keys())
                    
                    # Construir consulta
                    placeholders = ", ".join(["?" for _ in columns])
                    column_str = ", ".join(columns)
                    
                    operation = "REPLACE INTO" if replace else "INSERT INTO"
                    query = f"{operation} {table} ({column_str}) VALUES ({placeholders})"
                    
                    # Extraer valores en el mismo orden que las columnas
                    values = []
                    for record in batch:
                        row_values = [record.get(col) for col in columns]
                        values.append(row_values)
                    
                    # Ejecutar inserciones en lote
                    cursor.executemany(query, values)
                    
                    batch_count = len(batch)
                    total_inserted += batch_count
                    
                    logger.debug(f"Insertados {batch_count} registros en {table} "
                               f"(lote {i//batch_size + 1}/{(len(records)-1)//batch_size + 1})")
                
                # Commit al final
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error en inserción masiva en {db_path}.{table}: {str(e)}")
            raise
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Inserción masiva de {total_inserted} registros completada "
                       f"en {execution_time:.2f}s en {table}")
        
        return total_inserted
    
    def optimize_database(self, db_path: str) -> None:
        """
        Optimiza la base de datos ejecutando VACUUM y análisis.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        start_time = time.time()
        try:
            with self.connection(db_path) as conn:
                # Ejecutar VACUUM para compactar la base de datos
                conn.execute("VACUUM")
                
                # Actualizar estadísticas para el optimizador
                conn.execute("ANALYZE")
                
                # Limpiar cachés internas
                conn.execute("PRAGMA optimize")
                
                logger.info(f"Base de datos optimizada: {db_path}")
        except Exception as e:
            logger.error(f"Error optimizando base de datos {db_path}: {str(e)}")
            raise
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Optimización completada en {execution_time:.2f}s")
    
    def close_all_pools(self) -> None:
        """Cierra todos los pools de conexiones."""
        with self._lock:
            for path, pool in self._pools.items():
                try:
                    pool.close_all()
                except Exception as e:
                    logger.warning(f"Error al cerrar pool {path}: {str(e)}")
            
            self._pools.clear()


# Instancia global para uso en toda la aplicación
db_optimizer = DBOptimizer()


def with_db_connection(db_path: str):
    """
    Decorador para proporcionar una conexión de base de datos optimizada a una función.
    
    Args:
        db_path: Ruta al archivo de base de datos SQLite
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with db_optimizer.connection(db_path) as conn:
                # Inyectar la conexión como primer argumento o como argumento con nombre
                if 'conn' in kwargs:
                    original_conn = kwargs['conn']
                    kwargs['conn'] = conn
                    try:
                        return func(*args, **kwargs)
                    finally:
                        kwargs['conn'] = original_conn
                else:
                    return func(conn, *args, **kwargs)
        return wrapper
    return decorator
