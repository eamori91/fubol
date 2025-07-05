"""
Optimizador del sistema de análisis de datos para mejorar la eficiencia
de las operaciones de procesamiento de datos, cálculos estadísticos,
y generación de resultados.
"""

import numpy as np
import pandas as pd
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from functools import wraps
import pickle
from pathlib import Path
import concurrent.futures
from datetime import datetime, timedelta

# Importaciones opcionales con manejo de errores
try:
    import dask.dataframe as dd
    has_dask = True
except ImportError:
    has_dask = False

try:
    import numba
    has_numba = True
except ImportError:
    has_numba = False

try:
    from joblib import Parallel, delayed
    has_joblib = True
except ImportError:
    has_joblib = False

# Configurar logging
logger = logging.getLogger('analytics_optimizer')

class AnalyticsOptimizer:
    """
    Optimizador para operaciones de análisis de datos.
    Implementa técnicas de paralelización, computación diferida,
    y optimizaciones para mejorar el rendimiento de los cálculos.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        cache_dir: str = 'data/cache',
        use_dask: bool = True,
        use_numba: bool = True
    ):
        """
        Inicializa el optimizador de análisis.
        
        Args:
            max_workers: Número máximo de trabajadores para procesamiento paralelo
            cache_dir: Directorio para almacenamiento de caché
            use_dask: Utilizar Dask para operaciones con datos grandes
            use_numba: Utilizar Numba para compilación JIT
        """
        self.max_workers = max_workers
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar opciones según disponibilidad
        self.use_dask = use_dask and has_dask
        self.use_numba = use_numba and has_numba
        self.has_joblib = has_joblib
        
        # Configurar ThreadPoolExecutor para paralelización
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        
        # Desactivar warnings de copia en pandas
        pd.options.mode.chained_assignment = None
        
        logger.info(f"Analytics Optimizer inicializado: workers={max_workers}, "
                   f"dask={self.use_dask}, numba={self.use_numba}")
        
        # Configurar optimizaciones por defecto
        self._configure_pandas_optimizations()
    
    def _configure_pandas_optimizations(self):
        """Configura optimizaciones de pandas para mejorar rendimiento."""
        # Usar memoria compartida para operaciones de concatenación
        pd.set_option('compute.use_bottleneck', True)
        pd.set_option('compute.use_numexpr', True)
        
        # Aumentar umbral para conservar memoria
        pd.set_option('display.max_rows', 100)
        pd.set_option('display.max_columns', 100)
        pd.set_option('display.width', 1000)
        
        # Optimizaciones de rendimiento
        pd.set_option('mode.use_inf_as_na', True)  # Tratar infinitos como NA
    
    def parallelize_dataframe(
        self,
        df: pd.DataFrame,
        func: Callable,
        n_partitions: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Paraleliza operaciones en un DataFrame dividiéndolo en particiones.
        
        Args:
            df: DataFrame a procesar
            func: Función a aplicar a cada partición
            n_partitions: Número de particiones (por defecto max_workers)
            
        Returns:
            DataFrame procesado
        """
        if df.empty:
            return df
            
        n_partitions = n_partitions or self.max_workers
        n_partitions = min(n_partitions, len(df))
        
        if n_partitions <= 1:
            return func(df)
        
        # Dividir DataFrame en particiones
        df_split = np.array_split(df, n_partitions)
        
        # Procesar en paralelo
        start_time = time.time()
        
        if self.has_joblib:
            # Usar joblib si está disponible
            with Parallel(n_jobs=n_partitions) as parallel:
                results = parallel(delayed(func)(partition) for partition in df_split)
        else:
            # Usar ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=n_partitions) as executor:
                results = list(executor.map(func, df_split))
        
        # Combinar resultados
        result = pd.concat(results)
        
        elapsed = time.time() - start_time
        logger.debug(f"Procesamiento paralelo completado en {elapsed:.3f}s con {n_partitions} particiones")
        
        return result
    
    def cached_computation(self, cache_key: str, expiry_seconds: int = 3600):
        """
        Decorador para cachear resultados de funciones de cálculo.
        
        Args:
            cache_key: Clave base para la caché
            expiry_seconds: Tiempo de expiración en segundos
            
        Returns:
            Decorador configurado
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generar clave única con argumentos
                args_str = '_'.join([str(arg).replace(' ', '') for arg in args])
                kwargs_str = '_'.join([f"{k}={v}".replace(' ', '') 
                                     for k, v in sorted(kwargs.items())])
                
                # Limpiar la clave para uso como nombre de archivo
                unique_key = f"{cache_key}_{args_str}_{kwargs_str}"
                safe_key = ''.join(c if c.isalnum() else '_' for c in unique_key)
                safe_key = safe_key[:100]  # Limitar longitud
                
                cache_file = self.cache_dir / f"{safe_key}.pkl"
                
                # Verificar caché válida
                if cache_file.exists():
                    file_age = time.time() - cache_file.stat().st_mtime
                    if file_age < expiry_seconds:
                        try:
                            with open(cache_file, 'rb') as f:
                                result = pickle.load(f)
                                logger.debug(f"Resultado cargado de caché: {cache_key}")
                                return result
                        except (pickle.PickleError, EOFError, IOError) as e:
                            logger.warning(f"Error al leer caché {cache_file}: {e}")
                
                # Calcular resultado
                result = func(*args, **kwargs)
                
                # Guardar en caché
                try:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(result, f)
                    logger.debug(f"Resultado guardado en caché: {cache_key}")
                except (pickle.PickleError, IOError) as e:
                    logger.warning(f"Error al guardar caché {cache_file}: {e}")
                
                return result
            return wrapper
        return decorator
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimiza un DataFrame para reducir uso de memoria.
        
        Args:
            df: DataFrame a optimizar
            
        Returns:
            DataFrame optimizado
        """
        start_size = df.memory_usage(deep=True).sum()
        
        # Copia para no modificar el original
        result = df.copy()
        
        # Convertir tipos de datos a más eficientes
        for col in result.columns:
            col_type = result[col].dtype
            
            # Optimizar enteros
            if col_type == 'int64' and result[col].min() >= 0:
                if result[col].max() < 2**8:
                    result[col] = result[col].astype('uint8')
                elif result[col].max() < 2**16:
                    result[col] = result[col].astype('uint16')
                elif result[col].max() < 2**32:
                    result[col] = result[col].astype('uint32')
            
            # Optimizar flotantes
            elif col_type == 'float64':
                result[col] = result[col].astype('float32')
            
            # Optimizar cadenas a categorías cuando sea apropiado
            elif col_type == 'object':
                if result[col].nunique() < len(result[col]) * 0.5:  # < 50% valores únicos
                    result[col] = result[col].astype('category')
        
        # Calcular reducción
        end_size = result.memory_usage(deep=True).sum()
        reduction = 1 - (end_size / start_size) if start_size > 0 else 0
        
        logger.debug(f"DataFrame optimizado: {start_size/1e6:.2f} MB -> {end_size/1e6:.2f} MB "
                    f"({reduction*100:.1f}% reducción)")
        
        return result
    
    def to_dask_dataframe(self, df: pd.DataFrame, npartitions: Optional[int] = None) -> Any:
        """
        Convierte un DataFrame pandas a Dask para operaciones diferidas.
        
        Args:
            df: DataFrame pandas
            npartitions: Número de particiones (opcional)
            
        Returns:
            DataFrame Dask o el DataFrame original si Dask no está disponible
        """
        if not self.use_dask or not has_dask:
            logger.warning("Dask no está disponible. Usando pandas regular.")
            return df
            
        npartitions = npartitions or max(1, self.max_workers)
        return dd.from_pandas(df, npartitions=npartitions)
    
    def apply_dask_optimized(self, df: pd.DataFrame, func: Callable, **kwargs) -> pd.DataFrame:
        """
        Aplica una función a un DataFrame con optimizaciones de Dask.
        
        Args:
            df: DataFrame a procesar
            func: Función a aplicar
            **kwargs: Argumentos adicionales para la función
            
        Returns:
            DataFrame procesado
        """
        if self.use_dask and has_dask and len(df) > 100000:  # Solo para DataFrames grandes
            ddf = self.to_dask_dataframe(df)
            result = func(ddf, **kwargs).compute()
            return result
        else:
            return func(df, **kwargs)
    
    def numba_optimized(self, func=None, **numba_kwargs):
        """
        Decorador para optimizar funciones con Numba JIT.
        
        Args:
            func: Función a optimizar
            **numba_kwargs: Argumentos para el decorador numba.jit
            
        Returns:
            Función optimizada con Numba o la original si Numba no está disponible
        """
        def decorator(func):
            if not self.use_numba or not has_numba:
                return func
                
            return numba.jit(**numba_kwargs)(func)
            
        if func is None:
            return decorator
        return decorator(func)
    
    def process_in_batches(
        self,
        items: List[Any],
        process_func: Callable,
        batch_size: int = 1000,
        parallel: bool = True,
        **kwargs
    ) -> List[Any]:
        """
        Procesa una lista de elementos en lotes para evitar problemas de memoria.
        
        Args:
            items: Lista de elementos a procesar
            process_func: Función para procesar cada lote
            batch_size: Tamaño de cada lote
            parallel: Si True, procesa los lotes en paralelo
            **kwargs: Argumentos adicionales para process_func
            
        Returns:
            Lista combinada de resultados
        """
        if not items:
            return []
            
        # Dividir en lotes
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        logger.debug(f"Procesando {len(items)} elementos en {len(batches)} lotes de {batch_size}")
        
        start_time = time.time()
        results = []
        
        if parallel and len(batches) > 1:
            # Procesar en paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(batches))) as executor:
                batch_results = list(executor.map(lambda batch: process_func(batch, **kwargs), batches))
                
            # Combinar resultados
            for batch_result in batch_results:
                results.extend(batch_result)
        else:
            # Procesar secuencialmente
            for batch in batches:
                batch_result = process_func(batch, **kwargs)
                results.extend(batch_result)
        
        elapsed = time.time() - start_time
        logger.debug(f"Procesamiento por lotes completado en {elapsed:.3f}s")
        
        return results
    
    def moving_average(self, series: pd.Series, window: int = 3) -> pd.Series:
        """
        Calcula media móvil optimizada para una serie.
        
        Args:
            series: Serie de datos
            window: Tamaño de la ventana
            
        Returns:
            Serie con media móvil
        """
        # Usar rolling built-in de pandas que está optimizado
        return series.rolling(window=window, min_periods=1).mean()
    
    def exponential_moving_average(self, series: pd.Series, alpha: float = 0.3) -> pd.Series:
        """
        Calcula media móvil exponencial optimizada.
        
        Args:
            series: Serie de datos
            alpha: Factor de suavizado
            
        Returns:
            Serie con media móvil exponencial
        """
        return series.ewm(alpha=alpha).mean()
    
    def calculate_stats(self, df: pd.DataFrame, group_cols: List[str], value_cols: List[str]) -> pd.DataFrame:
        """
        Calcula estadísticas optimizadas para grupos de columnas.
        
        Args:
            df: DataFrame con los datos
            group_cols: Columnas de agrupación
            value_cols: Columnas para calcular estadísticas
            
        Returns:
            DataFrame con estadísticas calculadas
        """
        # Optimizar DataFrame primero
        df_opt = self.optimize_dataframe(df)
        
        # Definir funciones de agregación
        agg_funcs = {
            col: ['count', 'mean', 'median', 'min', 'max', 'std']
            for col in value_cols
        }
        
        # Usar Dask para DataFrames grandes
        if self.use_dask and has_dask and len(df_opt) > 100000:
            ddf = self.to_dask_dataframe(df_opt)
            stats = ddf.groupby(group_cols).agg(agg_funcs).compute()
        else:
            stats = df_opt.groupby(group_cols).agg(agg_funcs)
        
        # Aplanar columnas multiíndice
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        stats = stats.reset_index()
        
        return stats


# Instancia global para uso en toda la aplicación
analytics_optimizer = AnalyticsOptimizer()


def performance_monitor(func=None, threshold_seconds=0.5):
    """
    Decorador para monitorear rendimiento de funciones de análisis.
    
    Args:
        func: Función a monitorear
        threshold_seconds: Umbral para alertas de rendimiento
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Medir tiempo
            execution_time = time.time() - start_time
            
            # Log basado en tiempo de ejecución
            if execution_time > threshold_seconds:
                logger.warning(f"Operación lenta: {func.__name__} ejecutada en {execution_time:.3f}s")
            else:
                logger.debug(f"Operación {func.__name__} ejecutada en {execution_time:.3f}s")
                
            return result
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)
