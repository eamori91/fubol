"""
Configuración del Sistema Integrado de Análisis Predictivo de Fútbol
"""

import os
from datetime import timedelta

class ConfiguracionSistema:
    """Configuración general del sistema"""
    
    # Configuración de archivos y directorios
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    CACHE_DIR = os.path.join(BASE_DIR, 'cache')
    MODELS_DIR = os.path.join(DATA_DIR, 'modelos')
    RESULTS_DIR = os.path.join(DATA_DIR, 'resultados_integrados')
    EQUIPOS_DIR = os.path.join(DATA_DIR, 'equipos')
    
    # Crear directorios si no existen
    for directorio in [DATA_DIR, CACHE_DIR, MODELS_DIR, RESULTS_DIR, EQUIPOS_DIR]:
        os.makedirs(directorio, exist_ok=True)
    
    # Configuración de modelos
    MODELO_TRADICIONAL = {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42,
        'n_jobs': -1
    }
    
    MODELO_DEEP_LEARNING = {
        'epochs': 100,
        'batch_size': 32,
        'learning_rate': 0.001,
        'validation_split': 0.2,
        'early_stopping_patience': 10
    }
    
    # Configuración de simulaciones
    SIMULACION_MONTE_CARLO = {
        'n_simulaciones_default': 1000,
        'n_simulaciones_rapidas': 100,
        'semilla_aleatoria': 42
    }
    
    # Configuración de datos externos
    FUENTES_DATOS = {
        'football-data': {
            'url_base': 'https://api.football-data.org/v4',
            'api_key': os.getenv('FOOTBALL_DATA_API_KEY', ''),
            'rate_limit': 10,  # requests per minute
            'timeout': 30
        },
        'open-football': {
            'url_base': 'https://raw.githubusercontent.com/openfootball/football.json',
            'cache_duration': timedelta(hours=24)
        }
    }
    
    # Configuración de API
    API_CONFIG = {
        'host': '0.0.0.0',
        'port': 5000,
        'debug': os.getenv('FLASK_ENV') == 'development',
        'rate_limit': '100 per hour',
        'cors_enabled': True
    }
    
    # Configuración de cache
    CACHE_CONFIG = {
        'default_duration': timedelta(hours=6),
        'predicciones_duration': timedelta(hours=1),
        'datos_historicos_duration': timedelta(days=1),
        'modelos_duration': timedelta(days=7)
    }
    
    # Configuración de visualizaciones
    VISUALIZATION_CONFIG = {
        'figure_size': (12, 8),
        'dpi': 300,
        'style': 'seaborn-v0_8',
        'color_palette': 'viridis',
        'save_format': 'png'
    }
    
    # Configuración de logging
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': os.path.join(BASE_DIR, 'logs', 'sistema.log')
    }
    
    # Crear directorio de logs
    os.makedirs(os.path.dirname(LOGGING_CONFIG['file']), exist_ok=True)
    
    # Configuración de seguridad
    SECURITY_CONFIG = {
        'secret_key': os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
        'api_key_required': os.getenv('REQUIRE_API_KEY', 'False').lower() == 'true',
        'max_request_size': 16 * 1024 * 1024,  # 16MB
        'rate_limit_storage': 'memory'  # o 'redis' para producción
    }
    
    # Configuración de características
    FEATURES_CONFIG = {
        'historico_partidos_minimo': 10,
        'ventana_forma_reciente': 5,
        'peso_enfrentamientos_directos': 0.3,
        'peso_forma_reciente': 0.4,
        'peso_estadisticas_generales': 0.3,
        'caracteristicas_minimas': 15
    }
    
    # Configuración de validación
    VALIDATION_CONFIG = {
        'cross_validation_folds': 5,
        'test_size': 0.2,
        'validation_metrics': ['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
        'optimization_trials': 50
    }

class ConfiguracionEntorno:
    """Configuración específica por entorno"""
    
    @staticmethod
    def obtener_config():
        """Obtiene la configuración basada en el entorno actual"""
        env = os.getenv('ENVIRONMENT', 'development')
        
        if env == 'production':
            return ConfiguracionProduccion()
        elif env == 'testing':
            return ConfiguracionPruebas()
        else:
            return ConfiguracionDesarrollo()

class ConfiguracionDesarrollo(ConfiguracionSistema):
    """Configuración para entorno de desarrollo"""
    
    DEBUG = True
    TESTING = False
    
    # API más permisiva en desarrollo
    API_CONFIG = {
        **ConfiguracionSistema.API_CONFIG,
        'debug': True,
        'rate_limit': '1000 per hour'
    }
    
    # Cache más corto en desarrollo
    CACHE_CONFIG = {
        **ConfiguracionSistema.CACHE_CONFIG,
        'default_duration': timedelta(minutes=30)
    }
    
    # Logging más verboso
    LOGGING_CONFIG = {
        **ConfiguracionSistema.LOGGING_CONFIG,
        'level': 'DEBUG'
    }

class ConfiguracionProduccion(ConfiguracionSistema):
    """Configuración para entorno de producción"""
    
    DEBUG = False
    TESTING = False
    
    # Seguridad reforzada
    SECURITY_CONFIG = {
        **ConfiguracionSistema.SECURITY_CONFIG,
        'api_key_required': True,
        'rate_limit_storage': 'redis'
    }
    
    # Cache más agresivo
    CACHE_CONFIG = {
        **ConfiguracionSistema.CACHE_CONFIG,
        'default_duration': timedelta(hours=12),
        'datos_historicos_duration': timedelta(days=7)
    }
    
    # Logging menos verboso
    LOGGING_CONFIG = {
        **ConfiguracionSistema.LOGGING_CONFIG,
        'level': 'WARNING'
    }

class ConfiguracionPruebas(ConfiguracionSistema):
    """Configuración para entorno de pruebas"""
    
    DEBUG = False
    TESTING = True
    
    # Directorios temporales para pruebas
    import tempfile
    TEMP_DIR = tempfile.mkdtemp()
    
    DATA_DIR = os.path.join(TEMP_DIR, 'data')
    CACHE_DIR = os.path.join(TEMP_DIR, 'cache')
    MODELS_DIR = os.path.join(DATA_DIR, 'modelos')
    RESULTS_DIR = os.path.join(DATA_DIR, 'resultados')
    
    # Crear directorios de prueba
    for directorio in [DATA_DIR, CACHE_DIR, MODELS_DIR, RESULTS_DIR]:
        os.makedirs(directorio, exist_ok=True)
    
    # Simulaciones más rápidas para pruebas
    SIMULACION_MONTE_CARLO = {
        **ConfiguracionSistema.SIMULACION_MONTE_CARLO,
        'n_simulaciones_default': 10,
        'n_simulaciones_rapidas': 5
    }
    
    # Sin cache en pruebas
    CACHE_CONFIG = {
        **ConfiguracionSistema.CACHE_CONFIG,
        'default_duration': timedelta(seconds=1)
    }
    
    # Logging mínimo en pruebas
    LOGGING_CONFIG = {
        **ConfiguracionSistema.LOGGING_CONFIG,
        'level': 'ERROR',
        'file': os.path.join(TEMP_DIR, 'test.log')
    }

# Configuración por defecto
config = ConfiguracionEntorno.obtener_config()

# Funciones de utilidad para configuración
def obtener_ruta_modelo(nombre_modelo):
    """Obtiene la ruta completa para un archivo de modelo"""
    return os.path.join(config.MODELS_DIR, f'{nombre_modelo}.pkl')

def obtener_ruta_datos(nombre_archivo):
    """Obtiene la ruta completa para un archivo de datos"""
    return os.path.join(config.DATA_DIR, nombre_archivo)

def obtener_ruta_cache(nombre_archivo):
    """Obtiene la ruta completa para un archivo de cache"""
    return os.path.join(config.CACHE_DIR, nombre_archivo)

def obtener_ruta_resultados(nombre_archivo):
    """Obtiene la ruta completa para un archivo de resultados"""
    return os.path.join(config.RESULTS_DIR, nombre_archivo)

def configurar_logging():
    """Configura el sistema de logging"""
    import logging
    import logging.handlers
    
    # Crear logger principal
    logger = logging.getLogger('sistema_integrado')
    logger.setLevel(getattr(logging, config.LOGGING_CONFIG['level']))
    
    # Formatter
    formatter = logging.Formatter(config.LOGGING_CONFIG['format'])
    
    # Handler para archivo
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOGGING_CONFIG['file'],
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola en desarrollo
    if config.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Configurar logging al importar el módulo
logger = configurar_logging()

# Validar configuración
def validar_configuracion():
    """Valida que la configuración sea válida"""
    errores = []
    
    # Validar directorios
    directorios_requeridos = [config.DATA_DIR, config.CACHE_DIR, config.MODELS_DIR]
    for directorio in directorios_requeridos:
        if not os.path.exists(directorio):
            errores.append(f"Directorio no existe: {directorio}")
    
    # Validar configuración de API
    if config.API_CONFIG['port'] < 1 or config.API_CONFIG['port'] > 65535:
        errores.append("Puerto de API inválido")
    
    # Validar configuración de modelos
    if config.MODELO_TRADICIONAL['n_estimators'] < 1:
        errores.append("Número de estimadores debe ser mayor a 0")
    
    # Validar fuentes de datos
    for fuente, conf in config.FUENTES_DATOS.items():
        if 'url_base' not in conf:
            errores.append(f"URL base no configurada para fuente: {fuente}")
    
    if errores:
        logger.error("Errores de configuración encontrados:")
        for error in errores:
            logger.error(f"  - {error}")
        raise ValueError(f"Configuración inválida: {', '.join(errores)}")
    
    logger.info("Configuración validada correctamente")

# Validar configuración al importar
if not os.getenv('TESTING'):
    validar_configuracion()

# Exportar configuración principal
__all__ = [
    'config',
    'ConfiguracionSistema',
    'ConfiguracionEntorno',
    'obtener_ruta_modelo',
    'obtener_ruta_datos',
    'obtener_ruta_cache',
    'obtener_ruta_resultados',
    'configurar_logging',
    'validar_configuracion',
    'logger'
]
