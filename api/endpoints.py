"""
Módulo para proporcionar endpoints API para acceder a predicciones y datos del sistema.
"""

from flask import Blueprint, jsonify, request, current_app, url_for
import os
import json
from datetime import datetime, timedelta
import pandas as pd

from analisis.futuro import AnalisisFuturo
from analisis.simulador import SimuladorPartidos
from analisis.entidades import GestorEquipos
from utils.data_loader import DataLoader
from utils.conversor import CSVtoJSON, JSONtoCSV
from utils.data_fetcher import DataFetcher
from utils.unified_data_adapter import UnifiedDataAdapter

try:
    from analisis.deep_learning import DeepLearningPredictor
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False

# Crear un Blueprint para la API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Instancias compartidas
analizador = AnalisisFuturo()
simulador = SimuladorPartidos(analizador)
gestor = GestorEquipos()
data_loader = DataLoader()
data_fetcher = DataFetcher()
conversor = CSVtoJSON()
deep_learning = DeepLearningPredictor() if DEEP_LEARNING_AVAILABLE else None
unified_adapter = UnifiedDataAdapter()  # Nuevo adaptador unificado

def inicializar_componentes(cache_manager=None, http_optimizer=None, db_optimizer=None):
    """
    Inicializa componentes necesarios para la API
    
    Args:
        cache_manager: Instancia de CacheManager (opcional)
        http_optimizer: Instancia de HTTPOptimizer (opcional)
        db_optimizer: Instancia de DBOptimizer (opcional)
    """
    # Utilizar cache para datos históricos si existe cache_manager
    if cache_manager:
        # Intentar obtener datos desde caché
        datos = cache_manager.get('partidos_historicos')
        if datos is not None:
            analizador.datos = datos
            return
    
    # Si no hay caché o no hay datos en caché, cargar desde archivo
    ruta_datos = os.path.join('cache', 'partidos_historicos.csv')
    if os.path.exists(ruta_datos):
        datos = data_loader.cargar_datos_csv(ruta_datos)
        analizador.datos = datos
        
        # Guardar en caché si existe cache_manager
        if cache_manager:
            cache_manager.set('partidos_historicos', datos, expiry=3600)
    else:
        analizador.datos = analizador.generar_datos_ejemplo()
    
    # Cargar modelos predictivos optimizados
    analizador.cargar_modelos()
    
    # Cargar datos de equipos si existen
    gestor.cargar_datos()
    
    # Cargar modelos de deep learning si están disponibles
    if DEEP_LEARNING_AVAILABLE:
        deep_learning.cargar_modelos()

# Formato estándar para partidos (inspirado en football.json)
def partido_a_json(equipo_local, equipo_visitante, fecha, resultado=None, prediccion=None):
    """
    Convierte los datos de un partido a formato JSON estandarizado.
    
    Args:
        equipo_local: Nombre del equipo local
        equipo_visitante: Nombre del equipo visitante
        fecha: Fecha del partido
        resultado: Resultado real del partido (opcional)
        prediccion: Predicción del partido (opcional)
    
    Returns:
        Diccionario en formato JSON estandarizado
    """
    partido = {
        "date": fecha.strftime("%Y-%m-%d") if isinstance(fecha, datetime) else fecha,
        "team1": equipo_local,
        "team2": equipo_visitante
    }
    
    # Añadir resultado si existe
    if resultado:
        if isinstance(resultado, dict) and 'goles_local' in resultado and 'goles_visitante' in resultado:
            partido["score"] = {
                "ft": [resultado['goles_local'], resultado['goles_visitante']]
            }
        elif isinstance(resultado, list) and len(resultado) >= 2:
            partido["score"] = {
                "ft": [resultado[0], resultado[1]]
            }
    
    # Añadir predicción si existe
    if prediccion:
        partido["prediction"] = {
            "probabilities": {
                "home_win": prediccion['probabilidades']['victoria_local'],
                "draw": prediccion['probabilidades']['empate'],
                "away_win": prediccion['probabilidades']['victoria_visitante']
            },
            "score": [
                round(prediccion['goles_predichos']['local']),
                round(prediccion['goles_predichos']['visitante'])
            ]
        }
        
        # Añadir factores clave si existen
        if 'factores_clave' in prediccion:
            partido["prediction"]["key_factors"] = prediccion['factores_clave']
    
    return partido

# Endpoint para obtener predicción de un partido
@api_bp.route('/predicciones/<equipo_local>/<equipo_visitante>', methods=['GET'])
def obtener_prediccion(equipo_local, equipo_visitante):
    """Endpoint para obtener predicciones vía API"""
    try:
        # Extraer parámetros
        fecha_str = request.args.get('fecha', None)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d') if fecha_str else datetime.now()
        usar_simulacion = request.args.get('simular', 'false').lower() == 'true'
        
        # Verificar que los modelos están cargados
        if analizador.modelo_resultado is None:
            analizador.cargar_modelos()
        
        # Realizar predicción
        prediccion = analizador.predecir_partido_futuro(equipo_local, equipo_visitante, fecha)
        
        if not prediccion:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se pudo generar la predicción'
            }), 404
        
        # Realizar simulación Monte Carlo si se solicita
        if usar_simulacion:
            simulacion = simulador.simular_partido_monte_carlo(
                equipo_local, equipo_visitante, fecha, n_simulaciones=1000
            )
            
            if simulacion:
                # Actualizar predicción con resultados de la simulación
                prediccion['probabilidades'] = simulacion['probabilidades']
                prediccion['goles_predichos'] = {
                    'local': simulacion['goles_local']['moda'],
                    'visitante': simulacion['goles_visitante']['moda']
                }
                
                # Añadir datos adicionales de la simulación
                prediccion['simulacion'] = {
                    'n_simulaciones': simulacion['n_simulaciones'],
                    'distribucion_goles_local': simulacion['goles_local']['distribucion'],
                    'distribucion_goles_visitante': simulacion['goles_visitante']['distribucion']
                }
        
        # Convertir a formato estandarizado
        partido_json = partido_a_json(equipo_local, equipo_visitante, fecha, prediccion=prediccion)
        
        return jsonify({
            'estado': 'exito',
            'partido': partido_json,
            'prediccion_detallada': prediccion
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para obtener datos de un equipo
@api_bp.route('/equipos/<nombre_equipo>', methods=['GET'])
def obtener_equipo(nombre_equipo):
    """Endpoint para obtener datos de un equipo vía API"""
    try:
        # Verificar que el gestor tiene datos
        if not gestor.equipos:
            gestor.cargar_datos()
            
        # Buscar equipo por nombre
        equipo = gestor.obtener_equipo_por_nombre(nombre_equipo)
        
        if not equipo:
            return jsonify({
                'estado': 'error',
                'mensaje': f'No se encontró el equipo: {nombre_equipo}'
            }), 404
        
        # Convertir a diccionario simplificado
        equipo_dict = {
            'nombre': equipo.nombre,
            'liga': equipo.liga,
            'pais': equipo.pais,
            'estilo_juego': equipo.estilo_juego,
            'estadisticas': equipo.estadisticas,
            'jugadores': [
                {
                    'nombre': j.nombre,
                    'posicion': j.posicion,
                    'edad': j.edad,
                    'estadisticas': j.estadisticas
                } for j in equipo.jugadores
            ]
        }
        
        return jsonify({
            'estado': 'exito',
            'equipo': equipo_dict
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para obtener historial de partidos
@api_bp.route('/partidos/historico', methods=['GET'])
def obtener_partidos_historico():
    """Endpoint para obtener historial de partidos vía API"""
    try:
        # Extraer parámetros
        equipo = request.args.get('equipo', None)
        liga = request.args.get('liga', None)
        temporada = request.args.get('temporada', None)
        limite = request.args.get('limite', 10, type=int)
        
        # Cargar datos históricos
        datos = data_loader.obtener_partidos_historicos(equipo, temporada, liga)
        
        if datos is None or datos.empty:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se encontraron partidos históricos con los filtros especificados'
            }), 404
        
        # Limitar resultados
        datos = datos.head(limite)
        
        # Convertir a formato JSON estándar
        partidos = []
        for _, partido in datos.iterrows():
            fecha = pd.to_datetime(partido['fecha']) if 'fecha' in partido else None
            local = partido['equipo_local'] if 'equipo_local' in partido else ''
            visitante = partido['equipo_visitante'] if 'equipo_visitante' in partido else ''
            
            resultado = None
            if 'goles_local' in partido and 'goles_visitante' in partido:
                resultado = {
                    'goles_local': partido['goles_local'],
                    'goles_visitante': partido['goles_visitante']
                }
            
            partidos.append(partido_a_json(local, visitante, fecha, resultado))
        
        return jsonify({
            'estado': 'exito',
            'partidos': partidos,
            'total': len(partidos),
            'filtros': {
                'equipo': equipo,
                'liga': liga,
                'temporada': temporada
            }
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para realizar simulación de eventos
@api_bp.route('/simulaciones/eventos/<equipo_local>/<equipo_visitante>', methods=['GET'])
def simular_eventos(equipo_local, equipo_visitante):
    """Endpoint para simular eventos de un partido vía API"""
    try:
        # Extraer parámetros
        fecha_str = request.args.get('fecha', None)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d') if fecha_str else datetime.now()
        
        # Verificar que los modelos están cargados
        if analizador.modelo_resultado is None:
            analizador.cargar_modelos()
        
        # Realizar simulación de eventos
        simulacion = simulador.simular_eventos_partido(equipo_local, equipo_visitante, fecha)
        
        if not simulacion:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se pudo generar la simulación de eventos'
            }), 404
        
        return jsonify({
            'estado': 'exito',
            'simulacion': simulacion
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para convertir datos a formato JSON estándar
@api_bp.route('/convertir', methods=['POST'])
def convertir_datos():
    """Endpoint para convertir datos a formato JSON estándar"""
    try:
        # Obtener datos del cuerpo de la petición
        datos = request.json
        
        if not datos:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se proporcionaron datos para convertir'
            }), 400
        
        # Determinar el formato de entrada
        formato = datos.get('formato', 'csv')
        contenido = datos.get('contenido', None)
        
        if not contenido:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se proporcionó contenido para convertir'
            }), 400
        
        # Convertir según formato
        if formato == 'csv':
            # Convertir CSV a JSON
            try:
                # Crear un DataFrame desde el CSV
                import io
                df = pd.read_csv(io.StringIO(contenido))
                
                # Convertir a formato estándar
                partidos = []
                for _, fila in df.iterrows():
                    # Verificar columnas necesarias
                    if 'equipo_local' in fila and 'equipo_visitante' in fila:
                        local = fila['equipo_local']
                        visitante = fila['equipo_visitante']
                        
                        # Intentar extraer fecha
                        fecha = None
                        if 'fecha' in fila:
                            try:
                                fecha = pd.to_datetime(fila['fecha'])
                            except:
                                fecha = datetime.now()
                        else:
                            fecha = datetime.now()
                        
                        # Extraer resultado si existe
                        resultado = None
                        if 'goles_local' in fila and 'goles_visitante' in fila:
                            resultado = {
                                'goles_local': fila['goles_local'],
                                'goles_visitante': fila['goles_visitante']
                            }
                        
                        partidos.append(partido_a_json(local, visitante, fecha, resultado))
                
                # Crear estructura de datos estándar
                datos_json = {
                    'name': datos.get('nombre', 'Dataset Convertido'),
                    'matches': partidos
                }
                
                return jsonify({
                    'estado': 'exito',
                    'datos_convertidos': datos_json
                }), 200
                
            except Exception as e:
                return jsonify({
                    'estado': 'error',
                    'mensaje': f'Error al convertir CSV: {str(e)}'
                }), 500
        else:
            return jsonify({
                'estado': 'error',
                'mensaje': f'Formato no soportado: {formato}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para obtener documentación de la API
@api_bp.route('/', methods=['GET'])
def documentacion_api():
    """Endpoint para obtener documentación de la API"""
    endpoints = [
        {
            'ruta': url_for('api.obtener_prediccion', equipo_local='equipo_local', equipo_visitante='equipo_visitante'),
            'metodo': 'GET',
            'descripcion': 'Obtiene predicción para un partido',
            'parametros': [
                {'nombre': 'fecha', 'tipo': 'string', 'formato': 'YYYY-MM-DD', 'obligatorio': False},
                {'nombre': 'simular', 'tipo': 'boolean', 'descripcion': 'Usar simulación Monte Carlo', 'obligatorio': False}
            ]
        },
        {
            'ruta': url_for('api.prediccion_deep_learning', equipo_local='equipo_local', equipo_visitante='equipo_visitante'),
            'metodo': 'GET',
            'descripcion': 'Obtiene predicción usando modelos de deep learning',
            'parametros': [
                {'nombre': 'fecha', 'tipo': 'string', 'formato': 'YYYY-MM-DD', 'obligatorio': False}
            ]
        },
        {
            'ruta': url_for('api.comparar_predicciones', equipo_local='equipo_local', equipo_visitante='equipo_visitante'),
            'metodo': 'GET',
            'descripcion': 'Compara predicciones de modelos tradicionales vs deep learning',
            'parametros': [
                {'nombre': 'fecha', 'tipo': 'string', 'formato': 'YYYY-MM-DD', 'obligatorio': False}
            ]
        },
        {
            'ruta': url_for('api.obtener_equipo', nombre_equipo='nombre_equipo'),
            'metodo': 'GET',
            'descripcion': 'Obtiene datos de un equipo'
        },
        {
            'ruta': url_for('api.obtener_partidos_historico'),
            'metodo': 'GET',
            'descripcion': 'Obtiene historial de partidos',
            'parametros': [
                {'nombre': 'equipo', 'tipo': 'string', 'obligatorio': False},
                {'nombre': 'liga', 'tipo': 'string', 'obligatorio': False},
                {'nombre': 'temporada', 'tipo': 'string', 'obligatorio': False},
                {'nombre': 'limite', 'tipo': 'integer', 'obligatorio': False}
            ]
        },
        {
            'ruta': url_for('api.simular_eventos', equipo_local='equipo_local', equipo_visitante='equipo_visitante'),
            'metodo': 'GET',
            'descripcion': 'Simula eventos de un partido',
            'parametros': [
                {'nombre': 'fecha', 'tipo': 'string', 'formato': 'YYYY-MM-DD', 'obligatorio': False}
            ]
        },
        {
            'ruta': url_for('api.convertir_datos'),
            'metodo': 'POST',
            'descripcion': 'Convierte datos a formato JSON estándar',
            'cuerpo': {
                'formato': 'string (csv)',
                'contenido': 'string',
                'nombre': 'string (opcional)'
            }
        },
        {
            'ruta': url_for('api.actualizar_datos'),
            'metodo': 'POST',
            'descripcion': 'Actualiza datos desde fuentes externas',
            'cuerpo': {
                'fuente': 'string (football-data, etc.)',
                'liga': 'string (opcional)',
                'temporada': 'string (opcional)',
                'forzar': 'boolean (opcional)'
            }
        },
        {
            'ruta': url_for('api.obtener_metricas'),
            'metodo': 'GET',
            'descripcion': 'Obtiene métricas de rendimiento del sistema'
        },
        {
            'ruta': url_for('api.entrenar_modelos'),
            'metodo': 'POST',
            'descripcion': 'Reentrena los modelos con datos actualizados',
            'cuerpo': {
                'tipo': 'string (tradicional, deep_learning, todos)',
                'optimizar': 'boolean (opcional)'
            }
        }
    ]
    
    return jsonify({
        'api': 'Analizador Predictivo de Fútbol',
        'version': '1.0',
        'endpoints': endpoints,
        'formato_estandar': {
            'partido': {
                'date': 'YYYY-MM-DD',
                'team1': 'Nombre del equipo local',
                'team2': 'Nombre del equipo visitante',
                'score': {
                    'ft': [0, 0]  # Goles equipo local, Goles equipo visitante
                },
                'prediction': {
                    'probabilities': {
                        'home_win': 0.0,
                        'draw': 0.0,
                        'away_win': 0.0
                    },
                    'score': [0, 0],  # Goles predichos local, Goles predichos visitante
                    'key_factors': ['Factor 1', 'Factor 2']
                }
            }
        }
    }), 200

# Endpoint para predicción con deep learning
@api_bp.route('/predicciones/deep-learning/<equipo_local>/<equipo_visitante>', methods=['GET'])
def prediccion_deep_learning(equipo_local, equipo_visitante):
    """Endpoint para obtener predicciones usando modelos de deep learning"""
    try:
        if not DEEP_LEARNING_AVAILABLE:
            return jsonify({
                'estado': 'error',
                'mensaje': 'Los modelos de deep learning no están disponibles'
            }), 503
        
        # Extraer parámetros
        fecha_str = request.args.get('fecha', None)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d') if fecha_str else datetime.now()
        
        # Realizar predicción con deep learning
        prediccion = deep_learning.predecir_partido(equipo_local, equipo_visitante, fecha)
        
        if not prediccion:
            return jsonify({
                'estado': 'error',
                'mensaje': 'No se pudo generar la predicción con deep learning'
            }), 404
        
        # Convertir a formato estandarizado
        partido_json = partido_a_json(equipo_local, equipo_visitante, fecha, prediccion=prediccion)
        
        return jsonify({
            'estado': 'exito',
            'partido': partido_json,
            'prediccion_detallada': prediccion,
            'modelo': 'deep_learning'
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para comparar predicciones de diferentes modelos
@api_bp.route('/predicciones/comparacion/<equipo_local>/<equipo_visitante>', methods=['GET'])
def comparar_predicciones(equipo_local, equipo_visitante):
    """Endpoint para comparar predicciones de modelos tradicionales vs deep learning"""
    try:
        # Extraer parámetros
        fecha_str = request.args.get('fecha', None)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d') if fecha_str else datetime.now()
        
        # Verificar que los modelos están cargados
        if analizador.modelo_resultado is None:
            analizador.cargar_modelos()
        
        # Predicción con modelo tradicional
        prediccion_tradicional = analizador.predecir_partido_futuro(equipo_local, equipo_visitante, fecha)
        
        resultados = {
            'partido': {
                'equipo_local': equipo_local,
                'equipo_visitante': equipo_visitante,
                'fecha': fecha.strftime('%Y-%m-%d')
            },
            'predicciones': {
                'tradicional': prediccion_tradicional
            }
        }
        
        # Predicción con deep learning si está disponible
        if DEEP_LEARNING_AVAILABLE:
            prediccion_dl = deep_learning.predecir_partido(equipo_local, equipo_visitante, fecha)
            resultados['predicciones']['deep_learning'] = prediccion_dl
            
            # Calcular diferencias
            if prediccion_tradicional and prediccion_dl:
                diferencias = {
                    'probabilidad_victoria_local': abs(
                        prediccion_tradicional['probabilidades']['victoria_local'] - 
                        prediccion_dl['probabilidades']['victoria_local']
                    ),
                    'probabilidad_empate': abs(
                        prediccion_tradicional['probabilidades']['empate'] - 
                        prediccion_dl['probabilidades']['empate']
                    ),
                    'probabilidad_victoria_visitante': abs(
                        prediccion_tradicional['probabilidades']['victoria_visitante'] - 
                        prediccion_dl['probabilidades']['victoria_visitante']
                    )
                }
                resultados['diferencias'] = diferencias
        
        return jsonify({
            'estado': 'exito',
            'comparacion': resultados
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para actualizar datos desde fuentes externas
@api_bp.route('/datos/actualizar', methods=['POST'])
def actualizar_datos():
    """Endpoint para actualizar datos desde fuentes externas"""
    try:
        # Obtener parámetros
        datos_request = request.json or {}
        fuente = datos_request.get('fuente', 'football-data')
        liga = datos_request.get('liga', None)
        temporada = datos_request.get('temporada', None)
        forzar = datos_request.get('forzar', False)
        
        # Actualizar datos usando el data fetcher
        resultado = data_fetcher.actualizar_datos(
            fuente=fuente,
            liga=liga,
            temporada=temporada,
            forzar_actualizacion=forzar
        )
        
        if resultado['exito']:
            # Recargar datos en el analizador
            analizador.datos = data_loader.cargar_datos_csv(resultado['archivo'])
            
            return jsonify({
                'estado': 'exito',
                'mensaje': 'Datos actualizados correctamente',
                'detalles': resultado
            }), 200
        else:
            return jsonify({
                'estado': 'error',
                'mensaje': f'Error al actualizar datos: {resultado["error"]}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para obtener métricas del sistema
@api_bp.route('/metricas', methods=['GET'])
def obtener_metricas():
    """Endpoint para obtener métricas de rendimiento del sistema"""
    try:
        # Métricas básicas
        metricas = {
            'sistema': {
                'version': '1.0',
                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'datos': {
                'partidos_historicos': len(analizador.datos) if analizador.datos is not None else 0,
                'equipos_registrados': len(gestor.equipos) if gestor.equipos else 0
            },
            'modelos': {
                'tradicional_cargado': analizador.modelo_resultado is not None,
                'deep_learning_disponible': DEEP_LEARNING_AVAILABLE
            }
        }
        
        # Métricas adicionales si los modelos están cargados
        if analizador.modelo_resultado is not None:
            # Obtener características del modelo
            try:
                importancia = analizador.obtener_importancia_caracteristicas()
                if importancia:
                    metricas['modelos']['caracteristicas_importantes'] = importancia[:5]  # Top 5
            except:
                pass
        
        # Métricas de deep learning si está disponible
        if DEEP_LEARNING_AVAILABLE and deep_learning:
            try:
                metricas_dl = deep_learning.obtener_metricas()
                metricas['modelos']['deep_learning'] = metricas_dl
            except:
                pass
        
        return jsonify({
            'estado': 'exito',
            'metricas': metricas
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# Endpoint para entrenar modelos
@api_bp.route('/modelos/entrenar', methods=['POST'])
def entrenar_modelos():
    """Endpoint para reentrenar los modelos con datos actualizados"""
    try:
        # Obtener parámetros
        datos_request = request.json or {}
        tipo_modelo = datos_request.get('tipo', 'todos')  # 'tradicional', 'deep_learning', 'todos'
        optimizar = datos_request.get('optimizar', False)
        
        resultados = {}
        
        # Entrenar modelo tradicional
        if tipo_modelo in ['tradicional', 'todos']:
            try:
                resultado_tradicional = analizador.entrenar_modelos(optimizar_hiperparametros=optimizar)
                resultados['tradicional'] = resultado_tradicional
            except Exception as e:
                resultados['tradicional'] = {'error': str(e)}
        
        # Entrenar modelo de deep learning
        if tipo_modelo in ['deep_learning', 'todos'] and DEEP_LEARNING_AVAILABLE:
            try:
                resultado_dl = deep_learning.entrenar_modelo(analizador.datos)
                resultados['deep_learning'] = resultado_dl
            except Exception as e:
                resultados['deep_learning'] = {'error': str(e)}
        
        return jsonify({
            'estado': 'exito',
            'mensaje': 'Entrenamiento completado',
            'resultados': resultados
        }), 200
            
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        }), 500

# ====================================================================
# Nuevos endpoints utilizando el adaptador unificado de datos gratuitos
# ====================================================================

@api_bp.route('/datos-unificados/proximos-partidos')
def proximos_partidos():
    """
    Obtiene los próximos partidos utilizando el adaptador unificado
    
    Query params:
    - dias: Número de días hacia adelante (default: 7)
    - liga: Liga específica para filtrar (opcional)
    """
    dias = request.args.get('dias', default=7, type=int)
    liga = request.args.get('liga', default=None, type=str)
    
    try:
        # Usar adaptador unificado para obtener datos de fuentes gratuitas
        partidos = unified_adapter.obtener_proximos_partidos(dias=dias, liga=liga)
        
        # Convertir a formato estándar
        resultado = []
        for partido in partidos:
            fecha_partido = partido.get('fecha')
            # Convertir a objeto datetime si es string
            if isinstance(fecha_partido, str):
                try:
                    fecha_partido = datetime.fromisoformat(fecha_partido.replace('Z', '+00:00'))
                except ValueError:
                    # Si hay error, dejar como string
                    pass
            
            partido_json = partido_a_json(
                partido.get('equipo_local', ''),
                partido.get('equipo_visitante', ''),
                fecha_partido,
                None,  # No hay resultado aún
                None   # No hay predicción aún
            )
            
            # Añadir datos adicionales si existen
            if 'estadio' in partido:
                partido_json['venue'] = partido.get('estadio')
            if 'arbitro' in partido:
                partido_json['referee'] = partido.get('arbitro')
            if 'liga' in partido:
                partido_json['competition'] = partido.get('liga')
            if 'estado' in partido:
                partido_json['status'] = partido.get('estado')
            if 'fuente' in partido:
                partido_json['source'] = partido.get('fuente')
                
            resultado.append(partido_json)
        
        return jsonify({
            'success': True,
            'count': len(resultado),
            'matches': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/datos-unificados/equipo/<nombre_equipo>')
def datos_equipo(nombre_equipo):
    """
    Obtiene información detallada de un equipo
    """
    try:
        # Usar adaptador unificado
        datos_equipo = unified_adapter.obtener_datos_equipo(nombre_equipo)
        
        if not datos_equipo:
            return jsonify({
                'success': False,
                'error': f'No se encontró información para el equipo: {nombre_equipo}'
            }), 404
        
        # Intentar obtener jugadores también
        jugadores = unified_adapter.obtener_jugadores_equipo(nombre_equipo)
        
        # Añadir jugadores al resultado si existen
        if jugadores:
            datos_equipo['squad'] = jugadores
        
        return jsonify({
            'success': True,
            'team': datos_equipo
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/datos-unificados/arbitros')
def lista_arbitros():
    """
    Obtiene lista de árbitros disponibles
    """
    try:
        # Usar adaptador unificado
        arbitros = unified_adapter.obtener_arbitros()
        
        return jsonify({
            'success': True,
            'count': len(arbitros),
            'referees': arbitros
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/datos-unificados/arbitro/<nombre_arbitro>')
def datos_arbitro(nombre_arbitro):
    """
    Obtiene estadísticas de un árbitro específico
    
    Query params:
    - equipo: Nombre del equipo para filtrar estadísticas (opcional)
    """
    equipo = request.args.get('equipo', default=None, type=str)
    
    try:
        # Usar adaptador unificado
        estadisticas = unified_adapter.obtener_historial_arbitro(nombre_arbitro, equipo)
        
        if not estadisticas:
            return jsonify({
                'success': False,
                'error': f'No se encontró información para el árbitro: {nombre_arbitro}'
            }), 404
        
        return jsonify({
            'success': True,
            'referee': estadisticas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
