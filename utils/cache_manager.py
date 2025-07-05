"""
Sistema de caché avanzado para el sistema de análisis de fútbol.
Permite el almacenamiento en memoria y en disco de datos frecuentemente
utilizados, con control de tiempo de expiración y estrategias de invalidación.
"""

import os
import json
import time
import pickle
import logging
import hashlib
import threading
from typing import Dict, Any, Optional, Tuple, Callable, Union
from pathlib import Path
from functools import wraps
import pandas as pd

# Configurar logging
logger = logging.getLogger('cache_manager')

class CacheManager:
    """
    Gestor centralizado de caché para datos frecuentemente utilizados.
    Soporta almacenamiento en memoria y persistencia en disco.
    """
    
    def __init__(
        self, 
        cache_dir: str = 'data/cache',
        memory_expiry: int = 3600,  # 1 hora por defecto
        disk_expiry: int = 86400,   # 24 horas por defecto
        max_memory_items: int = 100,
        enabled: bool = True
    ):
        """
        Inicializa el gestor de caché.
        
        Args:
            cache_dir: Directorio para almacenamiento persistente
            memory_expiry: Tiempo de expiración en memoria (segundos)
            disk_expiry: Tiempo de expiración en disco (segundos)
            max_memory_items: Número máximo de elementos en caché de memoria
            enabled: Si el caché está habilitado
        """
        self.cache_dir = Path(cache_dir)
        self.memory_expiry = memory_expiry
        self.disk_expiry = disk_expiry
        self.max_memory_items = max_memory_items
        self.enabled = enabled
        
        # Crear directorio de caché si no existe
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Caché en memoria: {key: (timestamp, data)}
        self._memory_cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.RLock()
        
        logger.info(f"Cache Manager inicializado: dir={cache_dir}, "
                   f"mem_expiry={memory_expiry}s, disk_expiry={disk_expiry}s")
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Genera una clave única basada en los parámetros.
        
        Args:
            prefix: Prefijo para la clave (ej: 'teams', 'matches')
            params: Parámetros que identifican el elemento
            
        Returns:
            Clave única para el elemento
        """
        # Convertir parámetros a string ordenado
        params_str = json.dumps(params, sort_keys=True)
        # Generar hash MD5
        hash_obj = hashlib.md5(params_str.encode())
        return f"{prefix}_{hash_obj.hexdigest()}"
    
    def _disk_path(self, key: str) -> Path:
        """
        Obtiene la ruta en disco para una clave.
        
        Args:
            key: Clave de caché
            
        Returns:
            Ruta completa al archivo de caché
        """
        return self.cache_dir / f"{key}.cache"
    
    def get(self, prefix: str, params: Dict[str, Any], 
            fetch_function: Optional[Callable[[], Any]] = None) -> Optional[Any]:
        """
        Obtiene un elemento de la caché, o lo genera si no existe o expiró.
        
        Args:
            prefix: Prefijo para la clave
            params: Parámetros que identifican el elemento
            fetch_function: Función para obtener el dato si no está en caché
            
        Returns:
            Datos almacenados en caché, o None si no existen y no hay función
        """
        if not self.enabled:
            return fetch_function() if fetch_function else None
            
        key = self._generate_key(prefix, params)
        current_time = time.time()
        
        # Intento 1: Buscar en memoria
        with self._lock:
            if key in self._memory_cache:
                timestamp, data = self._memory_cache[key]
                if current_time - timestamp <= self.memory_expiry:
                    logger.debug(f"Cache hit (memory): {key}")
                    return data
                else:
                    # Expiró en memoria, eliminar
                    del self._memory_cache[key]
        
        # Intento 2: Buscar en disco
        disk_path = self._disk_path(key)
        if disk_path.exists():
            try:
                with open(disk_path, 'rb') as f:
                    timestamp, data = pickle.load(f)
                    
                if current_time - timestamp <= self.disk_expiry:
                    # Actualizar caché en memoria
                    with self._lock:
                        self._manage_memory_size()
                        self._memory_cache[key] = (timestamp, data)
                    logger.debug(f"Cache hit (disk): {key}")
                    return data
                else:
                    # Expiró en disco, eliminar
                    disk_path.unlink(missing_ok=True)
            except (pickle.PickleError, EOFError, IOError) as e:
                logger.warning(f"Error al leer caché de disco para {key}: {e}")
                # Intentar eliminar archivo corrupto
                disk_path.unlink(missing_ok=True)
        
        # No encontrado o expirado, generar nuevo
        if fetch_function:
            try:
                data = fetch_function()
                self.set(prefix, params, data)
                return data
            except Exception as e:
                logger.error(f"Error al generar datos para caché {key}: {e}")
                return None
        
        return None
    
    def set(self, prefix: str, params: Dict[str, Any], data: Any) -> None:
        """
        Almacena un elemento en caché.
        
        Args:
            prefix: Prefijo para la clave
            params: Parámetros que identifican el elemento
            data: Datos a almacenar
        """
        if not self.enabled:
            return
            
        key = self._generate_key(prefix, params)
        timestamp = time.time()
        
        # Guardar en memoria
        with self._lock:
            self._manage_memory_size()
            self._memory_cache[key] = (timestamp, data)
        
        # Guardar en disco
        disk_path = self._disk_path(key)
        try:
            with open(disk_path, 'wb') as f:
                pickle.dump((timestamp, data), f)
            logger.debug(f"Guardado en caché: {key}")
        except (pickle.PickleError, IOError) as e:
            logger.warning(f"Error al guardar caché en disco para {key}: {e}")
    
    def invalidate(self, prefix: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Invalida elementos de caché para un prefijo y parámetros.
        Si params es None, invalida todos los elementos con ese prefijo.
        
        Args:
            prefix: Prefijo para la clave
            params: Parámetros específicos o None para invalidar todo el prefijo
        """
        if params:
            # Invalidar elemento específico
            key = self._generate_key(prefix, params)
            with self._lock:
                if key in self._memory_cache:
                    del self._memory_cache[key]
            
            # Eliminar de disco
            disk_path = self._disk_path(key)
            disk_path.unlink(missing_ok=True)
            logger.debug(f"Invalidado caché: {key}")
        else:
            # Invalidar todos los elementos con ese prefijo
            with self._lock:
                keys_to_delete = [k for k in self._memory_cache if k.startswith(f"{prefix}_")]
                for key in keys_to_delete:
                    del self._memory_cache[key]
            
            # Eliminar archivos de disco
            for path in self.cache_dir.glob(f"{prefix}_*.cache"):
                path.unlink(missing_ok=True)
            logger.debug(f"Invalidados todos los cachés con prefijo: {prefix}")
    
    def _manage_memory_size(self) -> None:
        """
        Gestiona el tamaño de la caché en memoria, eliminando los elementos
        más antiguos si se supera el límite.
        """
        if len(self._memory_cache) <= self.max_memory_items:
            return
            
        # Ordenar por timestamp (más antiguos primero)
        sorted_items = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1][0]  # Ordenar por timestamp
        )
        
        # Eliminar elementos más antiguos hasta cumplir el límite
        items_to_remove = len(sorted_items) - self.max_memory_items
        for i in range(items_to_remove):
            key, _ = sorted_items[i]
            del self._memory_cache[key]
        
        logger.debug(f"Eliminados {items_to_remove} elementos antiguos de caché en memoria")
    
    def clear_all(self) -> None:
        """Limpia toda la caché (memoria y disco)."""
        # Limpiar memoria
        with self._lock:
            self._memory_cache.clear()
        
        # Limpiar disco
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink(missing_ok=True)
        
        logger.info("Caché completamente limpiada")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del uso de caché.
        
        Returns:
            Diccionario con estadísticas
        """
        disk_files = list(self.cache_dir.glob("*.cache"))
        disk_size = sum(f.stat().st_size for f in disk_files)
        
        return {
            "memory_items": len(self._memory_cache),
            "disk_items": len(disk_files),
            "disk_size_bytes": disk_size,
            "disk_size_mb": round(disk_size / (1024 * 1024), 2),
            "max_memory_items": self.max_memory_items,
            "memory_expiry": self.memory_expiry,
            "disk_expiry": self.disk_expiry,
            "enabled": self.enabled
        }


# Instancia global para uso en toda la aplicación
cache_manager = CacheManager()


def cached(prefix: str, expiry: Optional[int] = None):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        prefix: Prefijo para la clave de caché
        expiry: Tiempo de expiración personalizado (opcional)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar diccionario de parámetros para la clave
            params = {
                "args": args,
                "kwargs": kwargs
            }
            
            # Obtener de caché o ejecutar función
            def fetch_data():
                return func(*args, **kwargs)
            
            return cache_manager.get(prefix, params, fetch_data)
        return wrapper
    return decorator


def dataframe_to_dict(df: pd.DataFrame) -> Dict:
    """
    Convierte un DataFrame a un formato compatible con caché.
    
    Args:
        df: DataFrame a convertir
        
    Returns:
        Diccionario con los datos y metadatos del DataFrame
    """
    return {
        "columns": df.columns.tolist(),
        "index": df.index.tolist(),
        "data": df.values.tolist()
    }


def dict_to_dataframe(data_dict: Dict) -> pd.DataFrame:
    """
    Convierte un diccionario de caché a DataFrame.
    
    Args:
        data_dict: Diccionario con datos de DataFrame
        
    Returns:
        DataFrame reconstruido
    """
    return pd.DataFrame(
        data=data_dict["data"],
        columns=data_dict["columns"],
        index=data_dict["index"]
    )
