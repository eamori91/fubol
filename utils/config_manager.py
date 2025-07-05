"""
Sistema de configuración mejorado para la aplicación.
Soporta múltiples fuentes (env, archivos, base de datos),
validación, caché y recarga dinámica.
"""

import os
import sys
import json
import logging
import threading
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from functools import lru_cache
import time
from dotenv import load_dotenv
import yaml

# Configurar logging
logger = logging.getLogger('config_manager')

class ConfigManager:
    """
    Gestor centralizado de configuración para la aplicación.
    Soporta múltiples fuentes de configuración con prioridad.
    """
    
    def __init__(
        self,
        config_dir: str = 'config',
        env_prefix: str = 'FUBOL_',
        main_config_file: str = 'config.json',
        cache_duration: int = 300  # 5 minutos
    ):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_dir: Directorio para archivos de configuración
            env_prefix: Prefijo para variables de entorno
            main_config_file: Archivo principal de configuración
            cache_duration: Duración de caché de configuración (segundos)
        """
        self.config_dir = Path(config_dir)
        self.env_prefix = env_prefix
        self.main_config_file = main_config_file
        self.cache_duration = cache_duration
        
        # Crear directorio si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración en memoria
        self._config: Dict[str, Any] = {}
        self._last_load_time = 0
        self._lock = threading.RLock()
        self._file_watchers: Dict[str, Dict[str, Any]] = {}
        self._callbacks: List[Callable] = []
        
        # Cargar configuración inicial
        self._load_all_config()
        
        logger.info(f"Config Manager inicializado: dir={config_dir}")
    
    def _load_all_config(self) -> None:
        """Carga toda la configuración de todas las fuentes."""
        with self._lock:
            # 1. Cargar configuración predeterminada
            self._config = self._load_defaults()
            
            # 2. Cargar desde archivos
            config_from_files = self._load_from_files()
            self._merge_config(config_from_files)
            
            # 3. Cargar desde variables de entorno (mayor prioridad)
            env_config = self._load_from_env()
            self._merge_config(env_config)
            
            # Actualizar tiempo de carga
            self._last_load_time = time.time()
            
            logger.debug(f"Configuración cargada con {len(self._config)} claves principales")
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Fusiona configuración nueva con la existente.
        
        Args:
            new_config: Nueva configuración a fusionar
        """
        def deep_merge(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        deep_merge(self._config, new_config)
    
    def _load_defaults(self) -> Dict[str, Any]:
        """
        Carga la configuración predeterminada.
        
        Returns:
            Configuración predeterminada
        """
        return {
            "app": {
                "name": "Fubol - Sistema de Análisis de Fútbol",
                "version": "1.0.0",
                "debug": False,
                "env": "production"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/sistema.log",
                "max_size": 10485760,  # 10MB
                "backup_count": 5
            },
            "database": {
                "type": "sqlite",
                "path": "data/database/fubol.db",
                "pool_size": 5
            },
            "api": {
                "enabled": True,
                "port": 5000,
                "host": "0.0.0.0",
                "cors": True,
                "rate_limit": 100,  # peticiones por minuto
                "timeout": 30  # segundos
            },
            "cache": {
                "enabled": True,
                "expiry": 3600,  # 1 hora
                "max_items": 1000
            },
            "data_sources": {
                "football_data": {
                    "enabled": True,
                    "api_key": ""
                },
                "espn_api": {
                    "enabled": True,
                    "base_url": "https://site.api.espn.com"
                },
                "open_football": {
                    "enabled": True,
                    "base_url": "https://github.com/openfootball/football.json"
                },
                "espn_data": {
                    "enabled": True,
                    "base_url": "https://www.espn.com/soccer"
                },
                "world_football": {
                    "enabled": True,
                    "base_url": "https://www.football-data.co.uk/data.php"
                }
            }
        }
    
    def _load_from_files(self) -> Dict[str, Any]:
        """
        Carga configuración desde archivos.
        
        Returns:
            Configuración desde archivos
        """
        result = {}
        
        # Archivo principal
        main_config_path = self.config_dir / self.main_config_file
        if main_config_path.exists():
            try:
                # Detectar formato basado en extensión
                if main_config_path.suffix.lower() in ('.yaml', '.yml'):
                    with open(main_config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                else:  # Asumir JSON por defecto
                    with open(main_config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        
                if isinstance(config_data, dict):
                    result.update(config_data)
                    logger.debug(f"Configuración cargada desde {main_config_path}")
                    
                    # Registrar para vigilancia de cambios
                    self._file_watchers[str(main_config_path)] = {
                        'mtime': main_config_path.stat().st_mtime
                    }
            except Exception as e:
                logger.warning(f"Error al cargar configuración desde {main_config_path}: {e}")
        
        # Archivos por sección
        for file_path in self.config_dir.glob('*.json'):
            if file_path.name == self.main_config_file:
                continue  # Ya procesado
                
            section = file_path.stem  # Nombre del archivo sin extensión
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    section_data = json.load(f)
                    
                if isinstance(section_data, dict):
                    result[section] = section_data
                    logger.debug(f"Configuración de sección '{section}' cargada desde {file_path}")
                    
                    # Registrar para vigilancia de cambios
                    self._file_watchers[str(file_path)] = {
                        'mtime': file_path.stat().st_mtime
                    }
            except Exception as e:
                logger.warning(f"Error al cargar sección '{section}' desde {file_path}: {e}")
        
        return result
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Carga configuración desde variables de entorno.
        
        Returns:
            Configuración desde variables de entorno
        """
        result = {}
        
        # Cargar variables de entorno
        load_dotenv()
        
        # Procesar variables con el prefijo especificado
        for key, value in os.environ.items():
            if not key.startswith(self.env_prefix):
                continue
                
            # Quitar prefijo y separar por guiones bajos para crear estructura
            config_path = key[len(self.env_prefix):].lower().split('_')
            
            # Convertir valor al tipo adecuado
            if value.lower() in ('true', 'yes', 'on', '1'):
                typed_value = True
            elif value.lower() in ('false', 'no', 'off', '0'):
                typed_value = False
            elif value.isdigit():
                typed_value = int(value)
            elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                typed_value = float(value)
            else:
                typed_value = value
            
            # Construir estructura anidada
            current = result
            for i, part in enumerate(config_path):
                if i == len(config_path) - 1:
                    # Último elemento, asignar valor
                    current[part] = typed_value
                else:
                    # Crear estructura anidada si no existe
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración por clave.
        Las claves pueden usar notación de puntos para acceso anidado.
        
        Args:
            key: Clave a buscar (ej: 'app.debug', 'database.path')
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o valor por defecto
        """
        # Verificar caché y recargar si es necesario
        self._check_reload()
        
        # Separar clave en partes
        parts = key.split('.')
        
        # Navegar por la estructura
        with self._lock:
            current = self._config
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
            
            return current
    
    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave a establecer (ej: 'app.debug')
            value: Valor a establecer
            persist: Si True, guarda el cambio al archivo de configuración
        """
        # Separar clave en partes
        parts = key.split('.')
        
        with self._lock:
            # Navegar y crear estructura si no existe
            current = self._config
            for i, part in enumerate(parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            
            # Establecer valor
            last_part = parts[-1]
            current[last_part] = value
            
            # Guardar en archivo si se solicita
            if persist:
                self._save_to_file()
            
            # Notificar cambios
            self._notify_callbacks(key, value)
    
    def _save_to_file(self) -> None:
        """Guarda la configuración actual al archivo principal."""
        try:
            main_config_path = self.config_dir / self.main_config_file
            
            # Detectar formato basado en extensión
            if main_config_path.suffix.lower() in ('.yaml', '.yml'):
                with open(main_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config, f, default_flow_style=False)
            else:  # JSON por defecto
                with open(main_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=4, sort_keys=True)
                    
            logger.debug(f"Configuración guardada en {main_config_path}")
            
            # Actualizar tiempo de último cambio
            self._file_watchers[str(main_config_path)] = {
                'mtime': main_config_path.stat().st_mtime
            }
            
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
    
    def _check_reload(self) -> None:
        """
        Verifica si es necesario recargar la configuración
        por tiempo o cambios en archivos.
        """
        current_time = time.time()
        
        # Verificar caché por tiempo
        if current_time - self._last_load_time > self.cache_duration:
            self._load_all_config()
            return
            
        # Verificar cambios en archivos
        for file_path, info in self._file_watchers.items():
            try:
                path = Path(file_path)
                if path.exists():
                    current_mtime = path.stat().st_mtime
                    if current_mtime > info['mtime']:
                        logger.debug(f"Detectado cambio en {file_path}, recargando configuración")
                        self._load_all_config()
                        return
            except Exception as e:
                logger.warning(f"Error al verificar cambios en {file_path}: {e}")
    
    def reload(self) -> None:
        """Recarga explícitamente la configuración."""
        self._load_all_config()
        logger.info("Configuración recargada manualmente")
    
    def register_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Registra una función de callback para cambios de configuración.
        
        Args:
            callback: Función que recibe (key, new_value)
        """
        with self._lock:
            self._callbacks.append(callback)
    
    def _notify_callbacks(self, key: str, value: Any) -> None:
        """
        Notifica a los callbacks registrados sobre un cambio.
        
        Args:
            key: Clave que cambió
            value: Nuevo valor
        """
        for callback in self._callbacks:
            try:
                callback(key, value)
            except Exception as e:
                logger.warning(f"Error en callback de configuración: {e}")
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Devuelve toda la configuración como un diccionario.
        
        Returns:
            Diccionario con toda la configuración
        """
        with self._lock:
            # Hacer copia para evitar modificaciones externas
            return json.loads(json.dumps(self._config))
    
    def export_env_file(self, path: str = '.env') -> None:
        """
        Exporta la configuración a un archivo .env
        
        Args:
            path: Ruta del archivo .env
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                # Función recursiva para aplanar el diccionario
                def flatten_dict(d, prefix=''):
                    for key, value in d.items():
                        if isinstance(value, dict):
                            yield from flatten_dict(value, f"{prefix}{key}_")
                        else:
                            if isinstance(value, bool):
                                value = "1" if value else "0"
                            yield f"{self.env_prefix}{prefix}{key.upper()}={value}"
                
                # Escribir cada línea
                for line in flatten_dict(self._config):
                    f.write(f"{line}\n")
                
                logger.info(f"Configuración exportada a {path}")
        except Exception as e:
            logger.error(f"Error al exportar configuración a {path}: {e}")


# Instancia global para uso en toda la aplicación
config_manager = ConfigManager()


@lru_cache(maxsize=128)
def get_config(key: str, default: Any = None) -> Any:
    """
    Función de conveniencia para obtener configuración con caché.
    
    Args:
        key: Clave a obtener
        default: Valor por defecto
        
    Returns:
        Valor de configuración
    """
    return config_manager.get(key, default)
