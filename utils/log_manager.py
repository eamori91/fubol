"""
Sistema de logging avanzado y personalizado para la aplicación.
Configura múltiples handlers, formatos y filtros para una mejor
monitorización y depuración.
"""

import os
import sys
import logging
import logging.handlers
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
from pathlib import Path
import json
import threading
import time

class ColoredFormatter(logging.Formatter):
    """Formateador con colores para la consola."""
    
    # Colores ANSI
    COLORS = {
        'DEBUG': '\033[94m',     # Azul
        'INFO': '\033[92m',      # Verde
        'WARNING': '\033[93m',   # Amarillo
        'ERROR': '\033[91m',     # Rojo
        'CRITICAL': '\033[91m\033[1m',  # Rojo Brillante
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Formatea un registro de log con colores."""
        # Guardar el mensaje original
        msg = record.msg
        
        # Aplicar color al nivel de log
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Dar formato usando el formateador base
        formatted_message = super().format(record)
        
        # Restaurar mensaje original
        record.msg = msg
        
        return formatted_message


class JSONFormatter(logging.Formatter):
    """Formateador para salida en formato JSON."""
    
    def format(self, record):
        """Convierte un registro de log a formato JSON."""
        # Crear diccionario base
        log_dict = {
            'timestamp': self.formatTime(record, self.datefmt or '%Y-%m-%d %H:%M:%S,%f'),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage()
        }
        
        # Agregar información contextual
        if hasattr(record, 'request_id'):
            log_dict['request_id'] = record.request_id
            
        # Agregar información de excepción si existe
        if record.exc_info:
            log_dict['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Agregar atributos personalizados
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'id', 'levelname', 'levelno', 'lineno',
                          'module', 'msecs', 'message', 'msg', 'name', 'pathname',
                          'process', 'processName', 'relativeCreated', 'stack_info',
                          'thread', 'threadName']:
                try:
                    # Intentar serializar a JSON
                    json.dumps({key: value})
                    log_dict[key] = value
                except (TypeError, OverflowError):
                    # Si no se puede serializar, usar representación string
                    log_dict[key] = str(value)
        
        return json.dumps(log_dict)


class RequestIDFilter(logging.Filter):
    """Filtro para agregar un ID de solicitud a los registros de log."""
    
    def __init__(self):
        super().__init__()
        self._local = threading.local()
    
    def filter(self, record):
        """Aplica el filtro agregando el ID de solicitud."""
        request_id = getattr(self._local, 'request_id', None)
        if request_id:
            record.request_id = request_id
        return True
    
    def set_request_id(self, request_id: str):
        """Establece el ID de solicitud para el hilo actual."""
        self._local.request_id = request_id
    
    def clear_request_id(self):
        """Limpia el ID de solicitud para el hilo actual."""
        if hasattr(self._local, 'request_id'):
            del self._local.request_id


class PerformanceTracker:
    """
    Utilidad para rastrear el rendimiento de operaciones.
    """
    
    def __init__(self, logger_name='performance'):
        """Inicializa el rastreador de rendimiento."""
        self.logger = logging.getLogger(logger_name)
        self._local = threading.local()
    
    def start_operation(self, operation_name: str, **context):
        """
        Inicia una operación a rastrear.
        
        Args:
            operation_name: Nombre de la operación
            **context: Información contextual adicional
        """
        # Guardar operaciones en una pila para permitir anidamiento
        if not hasattr(self._local, 'operations'):
            self._local.operations = {}
            
        self._local.operations[operation_name] = {
            'start_time': time.time(),
            'context': context
        }
        
    def end_operation(self, operation_name: str, status='success', **extra_data):
        """
        Finaliza una operación y registra su tiempo de ejecución.
        
        Args:
            operation_name: Nombre de la operación
            status: Estado final ('success', 'error', etc.)
            **extra_data: Datos adicionales para el log
        """
        if (not hasattr(self._local, 'operations') or 
                operation_name not in self._local.operations):
            self.logger.warning(f"Intentando finalizar operación '{operation_name}' no iniciada")
            return
        
        start_data = self._local.operations.pop(operation_name)
        duration = time.time() - start_data['start_time']
        
        # Combinar contexto original con datos extra
        log_data = {
            **start_data['context'],
            **extra_data,
            'operation': operation_name,
            'duration': duration,
            'duration_ms': int(duration * 1000),
            'status': status
        }
        
        # Log con nivel apropiado según el estado
        if status == 'error':
            self.logger.error(f"Operación '{operation_name}' completada con error en {duration:.3f}s", extra=log_data)
        else:
            self.logger.info(f"Operación '{operation_name}' completada en {duration:.3f}s", extra=log_data)


class LogManager:
    """
    Gestor centralizado de logs para la aplicación.
    """
    
    def __init__(self, app_name: str = "fubol", log_dir: str = "logs"):
        """
        Inicializa el gestor de logs.
        
        Args:
            app_name: Nombre de la aplicación
            log_dir: Directorio para los archivos de log
        """
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear filtro de ID de solicitud
        self.request_id_filter = RequestIDFilter()
        
        # Inicializar rastreador de rendimiento
        self.performance = PerformanceTracker()
        
        # Inicialización diferida
        self._initialized = False
    
    def configure(
        self,
        console_level: str = 'INFO',
        file_level: str = 'DEBUG',
        json_logs: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        enable_metrics: bool = True
    ):
        """
        Configura el sistema de logs.
        
        Args:
            console_level: Nivel de log para la consola
            file_level: Nivel de log para los archivos
            json_logs: Si True, guarda logs en formato JSON
            max_file_size: Tamaño máximo de los archivos de log
            backup_count: Número de archivos de respaldo
            enable_metrics: Habilitar métricas de rendimiento
        """
        if self._initialized:
            return
        
        # Obtener logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Nivel más bajo para permitir filtrado después
        
        # Limpiar handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Formato de consola
        console_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        
        # Handler de consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level))
        console_handler.setFormatter(ColoredFormatter(console_format))
        console_handler.addFilter(self.request_id_filter)
        root_logger.addHandler(console_handler)
        
        # Handler de archivo principal
        main_log_file = self.log_dir / f"{self.app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=main_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, file_level))
        
        if json_logs:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_format = '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
            file_handler.setFormatter(logging.Formatter(file_format))
            
        file_handler.addFilter(self.request_id_filter)
        root_logger.addHandler(file_handler)
        
        # Handler de errores (solo ERROR y CRITICAL)
        error_log_file = self.log_dir / f"{self.app_name}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        if json_logs:
            error_handler.setFormatter(JSONFormatter())
        else:
            error_format = '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
            error_handler.setFormatter(logging.Formatter(error_format))
            
        error_handler.addFilter(self.request_id_filter)
        root_logger.addHandler(error_handler)
        
        # Handler de métricas de rendimiento
        if enable_metrics:
            metrics_log_file = self.log_dir / f"{self.app_name}_metrics.log"
            metrics_handler = logging.handlers.RotatingFileHandler(
                filename=metrics_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            metrics_handler.setLevel(logging.INFO)
            metrics_handler.setFormatter(JSONFormatter())
            
            # Aplicar solo al logger de performance
            perf_logger = logging.getLogger('performance')
            perf_logger.setLevel(logging.INFO)
            perf_logger.addHandler(metrics_handler)
            perf_logger.propagate = False  # Evitar duplicación en el logger raíz
        
        # Ajustar nivel de bibliotecas externas
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        
        self._initialized = True
        
        logger = logging.getLogger(self.app_name)
        logger.info(f"Sistema de logs configurado: console={console_level}, file={file_level}, "
                   f"json={json_logs}, métricas={enable_metrics}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtiene un logger configurado.
        
        Args:
            name: Nombre del logger
            
        Returns:
            Logger configurado
        """
        if not self._initialized:
            self.configure()
            
        if name != self.app_name and not name.startswith(f"{self.app_name}."):
            name = f"{self.app_name}.{name}"
            
        return logging.getLogger(name)
    
    def set_request_id(self, request_id: Optional[str] = None):
        """
        Establece un ID de solicitud para el hilo actual.
        Si no se proporciona, genera uno automáticamente.
        
        Args:
            request_id: ID de solicitud opcional
        """
        import uuid
        self.request_id_filter.set_request_id(request_id or str(uuid.uuid4()))
    
    def clear_request_id(self):
        """Limpia el ID de solicitud para el hilo actual."""
        self.request_id_filter.clear_request_id()


def log_execution_time(func=None, logger_name=None, level=logging.INFO):
    """
    Decorador para registrar el tiempo de ejecución de una función.
    
    Args:
        func: Función a decorar
        logger_name: Nombre del logger a utilizar
        level: Nivel de log para el mensaje
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener logger apropiado
            log = logging.getLogger(logger_name or func.__module__)
            
            # Registrar inicio
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            try:
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Registrar tiempo
                elapsed = time.time() - start_time
                log.log(level, f"Función {func_name} ejecutada en {elapsed:.3f}s")
                
                return result
            except Exception as e:
                # Registrar tiempo en caso de error
                elapsed = time.time() - start_time
                log.error(f"Error en {func_name} después de {elapsed:.3f}s: {str(e)}")
                raise
                
        return wrapper
    
    # Permitir uso como @log_execution_time o @log_execution_time()
    if func is None:
        return decorator
    return decorator(func)


# Instancia global para uso en toda la aplicación
log_manager = LogManager()


# Configurar contexto de excepción para incluir más información
def configure_exception_hooks():
    """
    Configura hooks para mejorar el manejo de excepciones no capturadas.
    """
    original_hook = sys.excepthook
    
    def exception_hook(exc_type, exc_value, exc_traceback):
        """Hook personalizado para excepciones no capturadas."""
        logger = logging.getLogger('root')
        logger.critical(
            "Excepción no capturada: %s",
            ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        )
        # Llamar al hook original
        original_hook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_hook
