"""
Aplicación web para el Analizador Deportivo de Fútbol
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import json
import random
import matplotlib
matplotlib.use('Agg')  # Para usar matplotlib con Flask
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import sqlite3
import time
from datetime import datetime, timedelta

from analisis.historico import AnalisisHistorico
from analisis.proximo import AnalisisProximo
from analisis.futuro import AnalisisFuturo
from analisis.tactico import AnalisisTactico
from analisis.posiciones import AnalisisPosiciones
from analisis.jugadores_clave import AnalisisJugadoresClave
from utils.data_loader import DataLoader
from utils.visualizacion import Visualizador
from utils.unified_data_adapter import UnifiedDataAdapter

# Importar componentes de API
from api import api_bp, inicializar_componentes
from analisis.simulador import SimuladorPartidos
from analisis.entidades import GestorEquipos

app = Flask(__name__)

# Registrar blueprint de API
app.register_blueprint(api_bp)

# Inicializar componentes
data_loader = DataLoader()
visualizador = Visualizador()
analisis_historico = AnalisisHistorico()
analisis_proximo = AnalisisProximo()
analisis_futuro = AnalisisFuturo()
analisis_tactico = AnalisisTactico()
analisis_posiciones = AnalisisPosiciones()
analisis_jugadores = AnalisisJugadoresClave()
simulador = SimuladorPartidos(analisis_futuro)
gestor_equipos = GestorEquipos()
unified_adapter = UnifiedDataAdapter()  # Nuevo adaptador unificado

# Añadir funciones globales a Jinja2
app.jinja_env.globals.update(max=max)
app.jinja_env.globals.update(min=min)
app.jinja_env.globals.update(len=len)

# Inicializar componentes de API
inicializar_componentes()

@app.route('/')
def index():
    return render_template('index_mejorado.html')

@app.route('/dashboard')
def dashboard():
    """Ruta para el dashboard mejorado con widgets interactivos"""
    return render_template('dashboard_mejorado.html')

@app.route('/index-simple')
def index_simple():
    """Ruta para la página principal simple original"""
    return render_template('index.html')

@app.route('/historico', methods=['GET', 'POST'])
def historico():
    """Ruta para análisis histórico mejorado"""
    return render_template('historico_mejorado.html')

@app.route('/historico-simple', methods=['GET', 'POST'])
def historico_simple():
    """Ruta para análisis histórico simple original"""
    if request.method == 'POST':
        equipo = request.form.get('equipo')
        temporada = request.form.get('temporada')
        
        # Cargar datos de ejemplo (esto debería conectarse a tus datos reales)
        datos = data_loader.obtener_partidos_historicos(equipo, temporada)
        if datos is None:
            return render_template('historico.html', error="No se pudieron cargar los datos")
            
        analisis_historico.datos = datos
        resultados = analisis_historico.analizar_equipo_local(equipo, temporada)
        
        # Crear gráfico
        fig = visualizador.grafico_rendimiento_equipo(datos, equipo, temporada)
        if fig:
            # Convertir gráfico a imagen base64 para mostrar en HTML
            buf = BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
        else:
            img_base64 = None
            
        return render_template('historico.html', 
                              resultados=resultados, 
                              equipo=equipo,
                              temporada=temporada,
                              img_grafico=img_base64)
    
    return render_template('historico.html')

@app.route('/proximo', methods=['GET', 'POST'])
def proximo():
    if request.method == 'POST':
        equipo_local = request.form.get('equipo_local')
        equipo_visitante = request.form.get('equipo_visitante')
        
        # Aquí cargaríamos datos reales y realizaríamos el análisis
        # Por simplicidad, devolvemos datos de ejemplo
        
        analisis = {
            'forma_local': {'racha': 'VVEVD', 'puntos_ultimos5': 10},
            'forma_visitante': {'racha': 'EDVDV', 'puntos_ultimos5': 7},
            'prediccion': {
                'victoria_local': 0.55, 
                'empate': 0.25, 
                'victoria_visitante': 0.20,
                'resultado_probable': '2-1'
            },
            'jugadores_clave': [
                {'nombre': 'Jugador A', 'equipo': equipo_local, 'prob_gol': 0.4},
                {'nombre': 'Jugador B', 'equipo': equipo_visitante, 'prob_gol': 0.3}
            ]
        }
        
        # Crear gráfico de predicción
        fig = visualizador.grafico_prediccion_resultado(analisis['prediccion'])
        if fig:
            buf = BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
        else:
            img_base64 = None
            
        return render_template('proximo.html',
                              equipo_local=equipo_local,
                              equipo_visitante=equipo_visitante,
                              analisis=analisis,
                              img_prediccion=img_base64)
    
    return render_template('proximo.html')

@app.route('/futuro', methods=['GET', 'POST'])
def futuro():
    """Ruta para análisis de partidos futuros (mejorada con datos unificados)"""
    # Obtener próximos partidos usando el adaptador unificado
    try:
        dias = request.args.get('dias', default=7, type=int)
        liga = request.args.get('liga', default=None, type=str)
        
        # Usar adaptador unificado para obtener próximos partidos
        proximos_partidos = unified_adapter.obtener_proximos_partidos(dias=dias, liga=liga)
        
        # Datos adicionales
        ligas_disponibles = list(set([p.get('liga') for p in proximos_partidos if p.get('liga')]))
        
        return render_template('futuro_mejorado.html', 
                              partidos=proximos_partidos, 
                              dias=dias,
                              liga_actual=liga,
                              ligas_disponibles=ligas_disponibles,
                              total_partidos=len(proximos_partidos))
    except Exception as e:
        return render_template('futuro_mejorado.html', 
                              error=f"Error al obtener partidos: {str(e)}",
                              partidos=[],
                              dias=7,
                              ligas_disponibles=[])

@app.route('/futuro-simple')
def futuro_simple():
    """Ruta para análisis de partidos futuros (versión simple original)"""
    return render_template('futuro.html')

@app.route('/equipo/<nombre_equipo>')
def vista_equipo(nombre_equipo):
    """Vista detallada de un equipo usando datos unificados"""
    try:
        # Obtener datos del equipo
        datos_equipo = unified_adapter.obtener_datos_equipo(nombre_equipo)
        
        if not datos_equipo:
            return render_template('error.html', 
                                  mensaje=f"No se encontró información para el equipo: {nombre_equipo}")
        
        # Obtener jugadores
        jugadores = unified_adapter.obtener_jugadores_equipo(nombre_equipo)
        
        # Devolver la página con los datos
        return render_template('equipo.html',
                              equipo=datos_equipo,
                              jugadores=jugadores)
    except Exception as e:
        return render_template('error.html',
                              mensaje=f"Error al obtener datos del equipo: {str(e)}")

@app.route('/arbitro/<nombre_arbitro>')
def vista_arbitro(nombre_arbitro):
    """Vista detallada de un árbitro usando datos unificados"""
    try:
        # Obtener parámetro opcional de equipo
        equipo = request.args.get('equipo', default=None, type=str)
        
        # Obtener datos del árbitro
        datos_arbitro = unified_adapter.obtener_historial_arbitro(nombre_arbitro, equipo)
        
        if not datos_arbitro:
            return render_template('error.html',
                                  mensaje=f"No se encontró información para el árbitro: {nombre_arbitro}")
        
        # Devolver la página con los datos
        return render_template('arbitro.html',
                              arbitro=datos_arbitro,
                              equipo_filtrado=equipo)
    except Exception as e:
        return render_template('error.html',
                              mensaje=f"Error al obtener datos del árbitro: {str(e)}")

@app.route('/api/equipos', methods=['GET'])
def api_equipos():
    # Esta ruta devolvería la lista de equipos disponibles en la base de datos
    # Por simplicidad, devolvemos una lista estática
    equipos = [
        "FC Barcelona", "Real Madrid", "Atlético Madrid", "Sevilla FC",
        "Manchester City", "Manchester United", "Liverpool", "Chelsea",
        "Bayern Munich", "Borussia Dortmund", "PSG", "Juventus"
    ]
    return jsonify(equipos)

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """API endpoint para estadísticas del dashboard"""
    try:
        # Obtener estadísticas reales del sistema
        total_predictions = len(analisis_futuro.datos) if analisis_futuro.datos is not None else 0
        
        # Calcular precisión promedio (simulada por ahora)
        import random
        accuracy_rate = round(85 + random.uniform(0, 10), 1)
        
        # Contar equipos únicos
        teams_count = len(gestor_equipos.equipos) if gestor_equipos.equipos else 250
        
        stats = {
            'total_predictions': total_predictions,
            'accuracy_rate': accuracy_rate,
            'teams_analyzed': teams_count,
            'leagues_covered': 15,
            'last_update': 'Hace 5 min',
            'matches_today': random.randint(8, 15)
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/featured-matches')
def featured_matches():
    """API endpoint para partidos destacados"""
    try:
        # Generar partidos destacados (en producción vendría de BD)
        matches = [
            {
                'home_team': 'Real Madrid',
                'away_team': 'FC Barcelona',
                'time': 'Hoy 21:00',
                'prediction': 'Victoria Local',
                'confidence': 67,
                'home_logo': '/static/img/real_madrid.png',
                'away_logo': '/static/img/barcelona.png'
            },
            {
                'home_team': 'Manchester City',
                'away_team': 'Liverpool',
                'time': 'Mañana 16:30',
                'prediction': 'Empate',
                'confidence': 45,
                'home_logo': '/static/img/man_city.png',
                'away_logo': '/static/img/liverpool.png'
            },
            {
                'home_team': 'Bayern Munich',
                'away_team': 'Borussia Dortmund',
                'time': 'Sábado 18:30',
                'prediction': 'Victoria Local',
                'confidence': 72,
                'home_logo': '/static/img/bayern.png',
                'away_logo': '/static/img/dortmund.png'
            }
        ]
        
        return jsonify(matches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/dashboard')
def get_dashboard_stats():
    """Obtener estadísticas en tiempo real para el dashboard"""
    try:
        # Aquí conectarías con tu base de datos real
        stats = {
            'predictions_today': 127,
            'accuracy_rate': 87.3,
            'total_matches': 1247,
            'active_users': 32
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches/featured')
def get_featured_matches():
    """Obtener partidos destacados del día"""
    try:
        featured_matches = [
            {
                'equipo_local': 'Real Madrid',
                'equipo_visitante': 'Barcelona',
                'prediccion': 'Local',
                'confianza': 73,
                'fecha': '2025-07-02T20:00:00Z'
            },
            {
                'equipo_local': 'Manchester City',
                'equipo_visitante': 'Liverpool',
                'prediccion': 'Empate',
                'confianza': 61,
                'fecha': '2025-07-02T18:30:00Z'
            },
            {
                'equipo_local': 'Bayern Munich',
                'equipo_visitante': 'Borussia Dortmund',
                'prediccion': 'Local',
                'confianza': 68,
                'fecha': '2025-07-02T19:30:00Z'
            }
        ]
        return jsonify(featured_matches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams/trending')
def get_trending_teams():
    """Obtener equipos más buscados/trending"""
    try:
        trending_teams = [
            {
                'nombre': 'Real Madrid',
                'tendencia': 'up',
                'cambio': 15
            },
            {
                'nombre': 'FC Barcelona',
                'tendencia': 'up',
                'cambio': 12
            },
            {
                'nombre': 'Manchester City',
                'tendencia': 'up',
                'cambio': 8
            },
            {
                'nombre': 'Paris Saint-Germain',
                'tendencia': 'down',
                'cambio': -3
            }
        ]
        return jsonify(trending_teams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/teams')
def search_teams():
    """Búsqueda inteligente de equipos"""
    query = request.args.get('q', '').lower()
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        # Lista de equipos de ejemplo (en producción vendría de base de datos)
        all_teams = [
            {'nombre': 'Real Madrid', 'liga': 'La Liga'},
            {'nombre': 'FC Barcelona', 'liga': 'La Liga'},
            {'nombre': 'Atletico Madrid', 'liga': 'La Liga'},
            {'nombre': 'Manchester United', 'liga': 'Premier League'},
            {'nombre': 'Manchester City', 'liga': 'Premier League'},
            {'nombre': 'Liverpool', 'liga': 'Premier League'},
            {'nombre': 'Chelsea', 'liga': 'Premier League'},
            {'nombre': 'Arsenal', 'liga': 'Premier League'},
            {'nombre': 'Bayern Munich', 'liga': 'Bundesliga'},
            {'nombre': 'Borussia Dortmund', 'liga': 'Bundesliga'},
            {'nombre': 'Paris Saint-Germain', 'liga': 'Ligue 1'},
            {'nombre': 'Juventus', 'liga': 'Serie A'},
            {'nombre': 'AC Milan', 'liga': 'Serie A'},
            {'nombre': 'Inter Milan', 'liga': 'Serie A'}
        ]
        
        # Filtrar equipos que coincidan con la búsqueda
        filtered_teams = [
            team for team in all_teams 
            if query in team['nombre'].lower()
        ]
        
        # Limitar resultados
        return jsonify(filtered_teams[:8])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/quick', methods=['POST'])
def quick_analysis():
    """Análisis rápido para el dashboard"""
    try:
        data = request.get_json()
        team_name = data.get('team_name')
        analysis_type = data.get('type', 'basic')
        
        # Aquí implementarías el análisis real
        result = {
            'team': team_name,
            'type': analysis_type,
            'results': {
                'form': 'VVDVE',
                'last_5_points': 10,
                'position': 3,
                'goals_for': 45,
                'goals_against': 21
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/tactical', methods=['POST'])
def tactical_analysis():
    """Análisis táctico avanzado"""
    try:
        data = request.get_json()
        equipo = data.get('equipo')
        
        if not equipo:
            return jsonify({'error': 'Equipo requerido'}), 400
            
        # Cargar datos simulados para análisis
        datos_simulados = pd.DataFrame({
            'equipo_local': [equipo] * 10,
            'equipo_visitante': ['Rival ' + str(i) for i in range(10)],
            'goles_local': np.random.randint(0, 4, 10),
            'goles_visitante': np.random.randint(0, 4, 10)
        })
        
        # Realizar análisis táctico
        estilo = analisis_tactico.analizar_estilo_juego(equipo, datos_simulados)
        formacion = analisis_tactico.analizar_formacion_preferida(equipo, datos_simulados)
        transiciones = analisis_tactico.analizar_transiciones(equipo, datos_simulados)
        
        result = {
            'equipo': equipo,
            'estilo_juego': estilo,
            'formacion_preferida': formacion,
            'transiciones': transiciones,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/positional', methods=['POST'])
def positional_analysis():
    """Análisis por posiciones"""
    try:
        data = request.get_json()
        equipo = data.get('equipo')
        posicion = data.get('posicion', 'todas')
        temporada = data.get('temporada', '2024')
        
        if not equipo:
            return jsonify({'error': 'Equipo requerido'}), 400
            
        result = {}
        
        if posicion == 'todas' or posicion == 'defensa':
            result['defensa'] = analisis_posiciones.analizar_linea_defensiva(equipo, temporada)
            
        # Para otros análisis de posiciones, usamos la misma función por ahora
        if posicion == 'todas' or posicion == 'mediocampo':
            # Simulamos análisis de mediocampo
            result['mediocampo'] = {
                'precision_pases': random.uniform(70, 90),
                'recuperaciones': random.randint(30, 60),
                'creacion_jugadas': random.uniform(5, 15),
                'valoracion': random.uniform(6.5, 8.5)
            }
            
        if posicion == 'todas' or posicion == 'ataque':
            # Simulamos análisis de ataque
            result['ataque'] = {
                'goles_por_partido': random.uniform(0.8, 2.5),
                'tiros_por_partido': random.uniform(10, 20),
                'precision_tiro': random.uniform(30, 60),
                'valoracion': random.uniform(6.0, 9.0)
            }
            
        if posicion == 'todas':
            # Simulamos evaluación de equilibrio
            result['equilibrio'] = {
                'balance_defensa_ataque': random.uniform(0.6, 1.4),
                'versatilidad_tactica': random.randint(6, 10),
                'rendimiento_global': random.uniform(6.0, 8.5)
            }
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/key-players', methods=['POST'])
def key_players_analysis():
    """Análisis de jugadores clave"""
    try:
        data = request.get_json()
        equipo = data.get('equipo')
        temporada = data.get('temporada', '2024')
        
        if not equipo:
            return jsonify({'error': 'Equipo requerido'}), 400
            
        # Obtener jugadores clave
        analisis = analisis_jugadores.identificar_jugadores_clave(equipo, temporada)
        
        # Si no hay análisis directo, simulamos datos adicionales
        if not analisis or 'error' in analisis:
            # Crear datos simulados
            analisis = {
                'equipo': equipo,
                'temporada': temporada,
                'jugadores_clave': [
                    {
                        'nombre': f'Jugador Clave 1 - {equipo}',
                        'posicion': 'Delantero',
                        'indice_importancia': random.uniform(8.0, 9.5),
                        'contribucion_goles': random.uniform(0.4, 0.7)
                    },
                    {
                        'nombre': f'Jugador Clave 2 - {equipo}',
                        'posicion': 'Mediocampista',
                        'indice_importancia': random.uniform(7.5, 8.9),
                        'contribucion_goles': random.uniform(0.2, 0.5)
                    }
                ],
                'distribucion_por_posicion': {
                    'delanteros': random.uniform(0.3, 0.5),
                    'mediocampistas': random.uniform(0.25, 0.4),
                    'defensas': random.uniform(0.1, 0.3),
                    'porteros': random.uniform(0.05, 0.15)
                }
            }
        
        # Añadir datos de dependencia (simulados)
        dependencia = {
            'indice_dependencia': random.uniform(30, 80),
            'jugador_mas_determinante': f'Jugador Estrella - {equipo}',
            'nivel_dependencia': random.choice(['Alta', 'Media', 'Baja'])
        }
        
        # Añadir alternativas (simuladas)
        alternativas = [
            {
                'nombre': f'Alternativa 1 - {equipo}',
                'posicion': 'Delantero',
                'compatibilidad': random.uniform(60, 90)
            },
            {
                'nombre': f'Alternativa 2 - {equipo}',
                'posicion': 'Mediocampista',
                'compatibilidad': random.uniform(50, 85)
            }
        ]
        
        # Añadir riesgo de lesiones (simulado)
        riesgo_lesiones = {
            'indice_global': random.uniform(10, 40),
            'jugadores_riesgo': random.randint(1, 4),
            'impacto_estimado': random.choice(['Alto', 'Medio', 'Bajo'])
        }
        
        # Combinar todos los resultados
        result = analisis
        result['analisis_dependencia'] = dependencia
        result['alternativas'] = alternativas
        result['riesgo_lesiones'] = riesgo_lesiones
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/comparative', methods=['POST'])
def comparative_analysis():
    """Análisis comparativo entre equipos"""
    try:
        data = request.get_json()
        equipo1 = data.get('equipo1')
        equipo2 = data.get('equipo2')
        tipo_analisis = data.get('tipo', 'completo')
        
        if not equipo1 or not equipo2:
            return jsonify({'error': 'Ambos equipos son requeridos'}), 400
            
        result = {
            'equipos': [equipo1, equipo2],
            'tipo_analisis': tipo_analisis
        }
        
        if tipo_analisis in ['completo', 'tactico']:
            # Simulación de formaciones
            formaciones = {
                'equipo1': random.choice(['4-3-3', '4-4-2', '3-5-2', '4-2-3-1']),
                'equipo2': random.choice(['4-3-3', '4-4-2', '3-5-2', '4-2-3-1'])
            }
            
            # Simulación de análisis táctico
            estilos = {
                equipo1: {
                    'posesion': random.uniform(40, 70),
                    'presion': random.choice(['Alta', 'Media', 'Baja']),
                    'transiciones': random.choice(['Rápidas', 'Elaboradas']),
                    'estilo_dominante': random.choice(['Posesión', 'Contraataque', 'Presión alta', 'Juego directo'])
                },
                equipo2: {
                    'posesion': random.uniform(30, 60),
                    'presion': random.choice(['Alta', 'Media', 'Baja']),
                    'transiciones': random.choice(['Rápidas', 'Elaboradas']),
                    'estilo_dominante': random.choice(['Posesión', 'Contraataque', 'Presión alta', 'Juego directo'])
                }
            }
            
            # Ventajas tácticas
            ventajas = []
            if estilos[equipo1]['posesion'] > estilos[equipo2]['posesion'] + 10:
                ventajas.append(f"{equipo1} tiene ventaja en posesión")
            elif estilos[equipo2]['posesion'] > estilos[equipo1]['posesion'] + 10:
                ventajas.append(f"{equipo2} tiene ventaja en posesión")
                
            ventajas.append(f"El {random.choice([equipo1, equipo2])} tiene ventaja en juego aéreo")
            
            # Combinar resultados
            result['comparacion_tactica'] = {
                'formaciones': {equipo1: formaciones['equipo1'], equipo2: formaciones['equipo2']},
                'estilos': estilos,
                'ventajas': ventajas
            }
            
        if tipo_analisis in ['completo', 'posicional']:
            # Comparación posicional
            defensa1 = analisis_posiciones.analizar_linea_defensiva(equipo1)
            defensa2 = analisis_posiciones.analizar_linea_defensiva(equipo2)
            
            result['comparacion_posicional'] = {
                'defensas': {equipo1: defensa1, equipo2: defensa2}
            }
            
        if tipo_analisis in ['completo', 'jugadores']:
            # Comparación de jugadores clave
            clave1 = analisis_jugadores.identificar_jugadores_clave(equipo1)
            clave2 = analisis_jugadores.identificar_jugadores_clave(equipo2)
            
            result['comparacion_jugadores'] = {
                'jugadores_clave': {equipo1: clave1, equipo2: clave2}
            }
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comparativo')
def api_analisis_comparativo():
    """Endpoint para comparar equipos"""
    try:
        # Obtener equipos a comparar
        equipo1 = request.args.get('equipo1')
        equipo2 = request.args.get('equipo2')
        
        if not equipo1 or not equipo2:
            return jsonify({'error': "Se requieren dos equipos para comparar"}), 400
        
        # Simular comparación de equipos (en producción usarías datos reales)
        comparacion = {
            'equipos': [equipo1, equipo2],
            'valoracion_global': {
                equipo1: round(random.uniform(65, 95), 1),
                equipo2: round(random.uniform(65, 95), 1)
            },
            'fortalezas': {
                equipo1: ['Posesión', 'Transiciones ofensivas', 'Juego aéreo'],
                equipo2: ['Presión alta', 'Contraataques', 'Defensa organizada']
            },
            'enfrentamientos_directos': {
                'total': 10,
                'victorias_' + equipo1: random.randint(3, 6),
                'empates': random.randint(1, 3),
                'victorias_' + equipo2: random.randint(2, 5)
            }
        }
        
        return jsonify(comparacion)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/simulation', methods=['POST'])
def match_simulation():
    """Simulación interactiva de partido"""
    try:
        data = request.get_json()
        equipo_local = data.get('equipo_local')
        equipo_visitante = data.get('equipo_visitante')
        escenarios = data.get('escenarios', [])
        
        if not equipo_local or not equipo_visitante:
            return jsonify({'error': 'Ambos equipos son requeridos'}), 400
            
        # Simulación básica con el simulador que ya tenemos importado
        num_simulaciones = data.get('num_simulaciones', 1000)
        
        # Configurar escenarios
        configuracion = {
            'clima': data.get('clima', 'normal'),
            'motivacion': data.get('motivacion', {}),
            'lesiones': data.get('lesiones', []),
            'tacticas': data.get('tacticas', {})
        }
        
        # Ejecutar simulaciones con el simulador existente
        try:
            # Intentar con el simulador de partidos ya importado
            fecha = datetime.now() + timedelta(days=14)  # 2 semanas en adelante
            resultado_simulacion = simulador.simular_partido_monte_carlo(
                equipo_local,
                equipo_visitante,
                fecha,
                num_simulaciones
            )
            
            if not resultado_simulacion:
                raise ValueError("La simulación no produjo resultados")
                
            return jsonify(resultado_simulacion)
            
        except Exception as sim_error:
            # Si falla, crear una simulación básica
            print(f"Error en simulación original: {str(sim_error)}")
            
            # Crear resultados de simulación manualmente
            distribucion_goles_local = {
                '0': random.uniform(0.1, 0.3),
                '1': random.uniform(0.2, 0.4),
                '2': random.uniform(0.15, 0.3),
                '3+': random.uniform(0.05, 0.2)
            }
            
            distribucion_goles_visitante = {
                '0': random.uniform(0.1, 0.4),
                '1': random.uniform(0.2, 0.4),
                '2': random.uniform(0.1, 0.25),
                '3+': random.uniform(0.05, 0.15)
            }
            
            # Normalizar probabilidades
            def normalizar_prob(dist):
                total = sum(dist.values())
                return {k: v/total for k, v in dist.items()}
            
            distribucion_goles_local = normalizar_prob(distribucion_goles_local)
            distribucion_goles_visitante = normalizar_prob(distribucion_goles_visitante)
            
            # Crear resultado
            resultado = {
                'equipos': {
                    'local': equipo_local,
                    'visitante': equipo_visitante
                },
                'predicciones': {
                    'victoria_local': random.uniform(0.35, 0.55),
                    'empate': random.uniform(0.2, 0.35),
                    'victoria_visitante': random.uniform(0.2, 0.4)
                },
                'distribucion_goles': {
                    'local': distribucion_goles_local,
                    'visitante': distribucion_goles_visitante
                },
                'resultado_mas_probable': f"{random.randint(1, 3)}-{random.randint(0, 2)}",
                'num_simulaciones': num_simulaciones,
                'escenarios': {
                    'clima': configuracion['clima'],
                    'lesiones': len(configuracion['lesiones']),
                }
            }
            
            # Normalizar predicciones
            total_pred = sum(resultado['predicciones'].values())
            for k in resultado['predicciones']:
                resultado['predicciones'][k] /= total_pred
            
            return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/export', methods=['POST'])
def export_data():
    """Exportar datos a PDF o Excel"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'pdf')
        content_type = data.get('content_type', 'analysis')
        data_content = data.get('data', {})
        
        if format_type not in ['pdf', 'excel', 'csv']:
            return jsonify({'error': 'Formato no soportado'}), 400
            
        # En una implementación real, aquí generaríamos el archivo
        # Para este ejemplo, simulamos una respuesta exitosa
        
        response = {
            'success': True,
            'message': f'Datos exportados correctamente en formato {format_type}',
            'download_url': f'/static/downloads/temp_{content_type}_{datetime.now().strftime("%Y%m%d%H%M%S")}.{format_type}'
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/share', methods=['POST'])
def share_analysis():
    """Compartir análisis en redes sociales o por email"""
    try:
        data = request.get_json()
        share_type = data.get('type', 'link')  # link, twitter, facebook, email
        content_id = data.get('content_id')
        
        if not content_id:
            return jsonify({'error': 'ID de contenido requerido'}), 400
            
        # En una implementación real, generaríamos enlaces para compartir
        # Para este ejemplo, simulamos respuestas
        
        base_url = request.host_url
        share_url = f"{base_url}share/{share_type}/{content_id}"
        
        response = {
            'success': True,
            'share_url': share_url,
            'social_text': f"Mira este análisis de fútbol que encontré #FootballAI #{content_id}"
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/favorites', methods=['GET'])
def get_favorites():
    """Obtener equipos favoritos del usuario"""
    try:
        # En producción, obtendríamos los favoritos del usuario desde BD
        # Para este ejemplo, devolvemos datos de muestra
        favorites = [
            {'id': 1, 'nombre': 'FC Barcelona', 'liga': 'La Liga', 'logo': '/static/img/barcelona.png'},
            {'id': 2, 'nombre': 'Manchester City', 'liga': 'Premier League', 'logo': '/static/img/man_city.png'},
            {'id': 3, 'nombre': 'Bayern Munich', 'liga': 'Bundesliga', 'logo': '/static/img/bayern.png'}
        ]
        return jsonify(favorites)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/user/favorites', methods=['POST'])
def add_favorite():
    """Añadir equipo a favoritos"""
    try:
        data = request.get_json()
        team_id = data.get('team_id')
        team_name = data.get('team_name')
        
        if not team_id or not team_name:
            return jsonify({'error': 'ID y nombre del equipo requeridos'}), 400
            
        # En producción, guardaríamos en BD
        return jsonify({
            'success': True,
            'message': f'{team_name} añadido a favoritos',
            'team_id': team_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/user/favorites/<int:team_id>', methods=['DELETE'])
def remove_favorite(team_id):
    """Eliminar equipo de favoritos"""
    try:
        if not team_id:
            return jsonify({'error': 'ID del equipo requerido'}), 400
            
        # En producción, eliminaríamos de BD
        return jsonify({
            'success': True,
            'message': 'Equipo eliminado de favoritos',
            'team_id': team_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/save', methods=['POST'])
def save_comparison():
    """Guardar una comparación para compartir"""
    try:
        data = request.get_json()
        teams = data.get('teams', [])
        analysis_type = data.get('analysis_type', 'complete')
        
        if len(teams) < 2:
            return jsonify({'error': 'Se requieren al menos 2 equipos para comparar'}), 400
            
        # Generar ID único para la comparación
        import uuid
        comparison_id = str(uuid.uuid4())[:8]
        
        # En producción, guardaríamos en BD
        response = {
            'success': True,
            'comparison_id': comparison_id,
            'share_url': f"{request.host_url}compare/{comparison_id}",
            'teams': teams,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoints para facilitar la integración con datos reales

@app.route('/api/integracion/configuracion', methods=['GET'])
def api_config_integracion():
    """
    Endpoint para obtener la configuración de integración con datos reales.
    Esto ayudará a cualquier sistema externo a entender cómo conectarse.
    """
    configuracion = {
        "version_api": "1.0.0",
        "formatos_soportados": ["json", "csv"],
        "endpoints_principales": {
            "equipos": "/api/equipos",
            "jugadores": "/api/jugadores",
            "predicciones": "/api/predicciones/{equipo_local}/{equipo_visitante}",
            "historico": "/api/historico/{equipo}",
            "estadisticas": "/api/stats/dashboard"
        },
        "frecuencia_actualizacion": "diaria",
        "fuentes_datos_recomendadas": [
            {"nombre": "API-Football", "url": "https://www.api-football.com/"},
            {"nombre": "Football-Data.org", "url": "https://www.football-data.org/"},
            {"nombre": "StatsBomb", "url": "https://statsbomb.com/data/"}
        ],
        "estructura_datos_requerida": {
            "equipo": ["id", "nombre", "liga", "pais"],
            "jugador": ["id", "nombre", "equipo_id", "posicion", "estadisticas"],
            "partido": ["id", "fecha", "equipo_local_id", "equipo_visitante_id", "resultado_local", "resultado_visitante"]
        }
    }
    return jsonify(configuracion)

@app.route('/api/integracion/test-conexion', methods=['POST'])
def test_conexion_datos():
    """
    Endpoint para probar la conexión con una fuente de datos externa.
    """
    try:
        datos = request.json
        if not datos:
            return jsonify({"estado": "error", "mensaje": "No se recibieron datos"}), 400
            
        # Aquí iría la lógica para probar la conexión a la fuente externa
        # Por ahora simulamos una conexión exitosa
        resultado = {
            "estado": "exitoso",
            "mensaje": "Conexión establecida correctamente",
            "detalles": {
                "latencia": "120ms",
                "formato_correcto": True,
                "campos_validados": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

@app.route('/api/integracion/importar-datos', methods=['POST'])
def importar_datos_externos():
    """
    Endpoint para importar datos desde una fuente externa.
    """
    try:
        datos = request.json
        
        if not datos or 'tipo' not in datos:
            return jsonify({"estado": "error", "mensaje": "Formato de datos incorrecto"}), 400
            
        tipo_datos = datos['tipo']
        contenido = datos.get('datos', [])
        
        if not contenido:
            return jsonify({"estado": "error", "mensaje": "No hay datos para importar"}), 400
        
        # Simulamos procesamiento según el tipo de datos
        resultados = {
            "estado": "exitoso",
            "mensaje": f"Datos de {tipo_datos} importados correctamente",
            "estadisticas": {
                "total_procesados": len(contenido),
                "nuevos_registros": len(contenido),
                "actualizados": 0,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # En una implementación real, aquí guardaríamos los datos en archivos o BD
        
        return jsonify(resultados)
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

@app.route('/api/integracion/estado', methods=['GET'])
def estado_integracion():
    """
    Endpoint para verificar el estado actual de la integración con datos reales.
    """
    # En una implementación real, esto verificaría conexiones activas, 
    # última actualización, etc.
    
    estado = {
        "estado_general": "ready",
        "conexiones_activas": 0,
        "ultima_actualizacion": (datetime.now() - timedelta(days=1)).isoformat(),
        "proxima_actualizacion": datetime.now().isoformat(),
        "fuentes_configuradas": 0,
        "mensajes_sistema": [
            {
                "tipo": "info",
                "mensaje": "Sistema listo para recibir datos externos",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    
    return jsonify(estado)

# Rutas para PWA
@app.route('/manifest.json')
def manifest():
    """Servir el archivo manifest para PWA"""
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    """Servir el service worker"""
    response = app.send_static_file('sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    return response

# Meta rutas para documentación
@app.route('/docs')
def docs():
    """Ruta para documentación del sistema"""
    return render_template('docs.html')

@app.route('/about')
def about():
    """Información sobre el sistema"""
    return render_template('about.html')

@app.route('/api/analisis/posicional/<equipo>', methods=['GET'])
def api_analisis_posicional(equipo):
    """
    Endpoint para obtener análisis posicional de un equipo.
    """
    try:
        # Obtener parámetros opcionales
        temporada = request.args.get('temporada', '2024-2025')
        
        # Si hay datos reales disponibles
        linea_defensiva = analisis_posiciones.analizar_linea_defensiva(equipo, temporada)
        medio_campo = analisis_posiciones.analizar_medio_campo(equipo, temporada)
        
        # Combinar resultados
        resultado = {
            'equipo': equipo,
            'temporada': temporada,
            'analisis_defensivo': linea_defensiva,
            'analisis_medio_campo': medio_campo,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': f"Error en análisis posicional: {str(e)}"}), 500

@app.route('/api/jugadores-clave/<equipo>')
def api_jugadores_clave(equipo):
    """Endpoint para jugadores clave"""
    try:
        # Obtener parámetros opcionales
        temporada = request.args.get('temporada', '2024-2025')
        
        # Realizar análisis de jugadores clave
        jugadores = analisis_jugadores.identificar_jugadores_clave(equipo, temporada)
        
        return jsonify({
            'equipo': equipo,
            'temporada': temporada,
            'jugadores_clave': jugadores
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from api.simulacion import simulacion_bp
app.register_blueprint(simulacion_bp)

@app.route('/explorar-db')
def explorar_db():
    """
    Ruta para explorar la base de datos
    """
    # Importar utilidades de base de datos
    from utils.database_explorer import get_db_connection, get_table_names
    
    # Obtener parámetros
    tabla = request.args.get('tabla', default=None, type=str)
    pagina = request.args.get('pagina', default=1, type=int)
    limite = request.args.get('limite', default=50, type=int)
    
    # Validar límite
    if limite < 1:
        limite = 50
    elif limite > 1000:
        limite = 1000
    
    # Obtener conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener lista de tablas
    tablas = get_table_names()
    
    # Variables para almacenar resultados
    datos = []
    columnas = []
    total_filas = 0
    total_paginas = 1
    
    # Si se especificó una tabla
    if tabla and tabla in tablas:
        # Obtener número total de filas
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total_filas = cursor.fetchone()[0]
        
        # Calcular total de páginas
        total_paginas = (total_filas + limite - 1) // limite
        
        # Ajustar página actual
        if pagina < 1:
            pagina = 1
        elif pagina > total_paginas and total_paginas > 0:
            pagina = total_paginas
        
        # Obtener datos de la página actual
        offset = (pagina - 1) * limite
        cursor.execute(f"SELECT * FROM {tabla} LIMIT {limite} OFFSET {offset}")
        datos = cursor.fetchall()
        
        # Obtener nombres de columnas
        cursor.execute(f"PRAGMA table_info({tabla})")
        columnas = [col[1] for col in cursor.fetchall()]
    
    conn.close()
    
    return render_template('explorar_db.html', 
                          tablas=tablas,
                          tabla_actual=tabla,
                          datos=datos,
                          columnas=columnas,
                          pagina=pagina,
                          limite=limite,
                          total_filas=total_filas,
                          total_paginas=total_paginas)

@app.route('/ejecutar-consulta', methods=['POST'])
def ejecutar_consulta():
    """
    Ruta para ejecutar consultas SQL personalizadas
    """
    # Importar utilidades de base de datos
    from utils.database_explorer import get_db_connection
    
    consulta = request.form.get('consulta', '')
    
    # Verificar si la consulta es válida (básico)
    if not consulta.strip():
        return redirect(url_for('explorar_db'))
    
    # Palabras prohibidas para prevenir modificaciones
    palabras_prohibidas = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE']
    for palabra in palabras_prohibidas:
        if palabra in consulta.upper():
            return render_template('error.html', 
                                  mensaje=f"Consulta no permitida. No se permiten operaciones {palabra}.")
    
    # Obtener conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Medir tiempo de ejecución
        tiempo_inicio = time.time()
        cursor.execute(consulta)
        datos = cursor.fetchall()
        tiempo_fin = time.time()
        tiempo_ejecucion = round(tiempo_fin - tiempo_inicio, 3)
        
        # Obtener nombres de columnas
        columnas = [description[0] for description in cursor.description] if cursor.description else []
        
        conn.close()
        
        # Devolver resultados
        resultado = {
            'consulta': consulta,
            'datos': datos,
            'columnas': columnas,
            'tiempo': tiempo_ejecucion
        }
        
        # Decidir si renderizar en la misma página o en una nueva
        if len(datos) > 100:
            # Para muchos resultados, usar página separada
            return render_template('resultados_consulta.html',
                                  consulta=consulta,
                                  datos=datos,
                                  columnas=columnas)
        else:
            # Para pocos resultados, mostrar en la misma página
            return render_template('explorar_db.html',
                                  tablas=[],
                                  tabla_actual=None,
                                  datos=[],
                                  columnas=[],
                                  pagina=1,
                                  limite=50,
                                  total_filas=0,
                                  total_paginas=0,
                                  resultado_consulta=resultado)
    
    except sqlite3.Error as e:
        conn.close()
        return render_template('error.html', mensaje=f"Error en la consulta SQL: {str(e)}")

@app.route('/importar-datos-prueba')
def importar_datos_prueba():
    """
    Importa datos de prueba en la base de datos
    """
    from utils.database_explorer import save_dataframe_to_table, get_db_path
    import pandas as pd
    
    try:
        # Crear directorio de base de datos si no existe
        os.makedirs(os.path.join('data', 'database'), exist_ok=True)
        
        # Obtener ruta de la base de datos
        db_path = get_db_path()
        
        # Datos de equipos
        equipos = [
            {'id': 1, 'nombre': 'Real Madrid', 'pais': 'España', 'liga': 'LaLiga', 'estadio': 'Santiago Bernabéu', 'fundacion': 1902},
            {'id': 2, 'nombre': 'Barcelona', 'pais': 'España', 'liga': 'LaLiga', 'estadio': 'Camp Nou', 'fundacion': 1899},
            {'id': 3, 'nombre': 'Manchester United', 'pais': 'Inglaterra', 'liga': 'Premier League', 'estadio': 'Old Trafford', 'fundacion': 1878},
            {'id': 4, 'nombre': 'Liverpool', 'pais': 'Inglaterra', 'liga': 'Premier League', 'estadio': 'Anfield', 'fundacion': 1892},
            {'id': 5, 'nombre': 'Bayern Munich', 'pais': 'Alemania', 'liga': 'Bundesliga', 'estadio': 'Allianz Arena', 'fundacion': 1900},
            {'id': 6, 'nombre': 'PSG', 'pais': 'Francia', 'liga': 'Ligue 1', 'estadio': 'Parc des Princes', 'fundacion': 1970},
            {'id': 7, 'nombre': 'Juventus', 'pais': 'Italia', 'liga': 'Serie A', 'estadio': 'Allianz Stadium', 'fundacion': 1897},
            {'id': 8, 'nombre': 'Manchester City', 'pais': 'Inglaterra', 'liga': 'Premier League', 'estadio': 'Etihad Stadium', 'fundacion': 1880},
        ]
        df_equipos = pd.DataFrame(equipos)
        save_dataframe_to_table(df_equipos, 'equipos', 'replace')
        
        # Datos de jugadores
        jugadores = [
            {'id': 1, 'nombre': 'Vinicius Jr', 'equipo_id': 1, 'posicion': 'Delantero', 'edad': 25, 'pais': 'Brasil', 'dorsal': 7},
            {'id': 2, 'nombre': 'Jude Bellingham', 'equipo_id': 1, 'posicion': 'Centrocampista', 'edad': 22, 'pais': 'Inglaterra', 'dorsal': 5},
            {'id': 3, 'nombre': 'Robert Lewandowski', 'equipo_id': 2, 'posicion': 'Delantero', 'edad': 36, 'pais': 'Polonia', 'dorsal': 9},
            {'id': 4, 'nombre': 'Pedri', 'equipo_id': 2, 'posicion': 'Centrocampista', 'edad': 22, 'pais': 'España', 'dorsal': 8},
            {'id': 5, 'nombre': 'Bruno Fernandes', 'equipo_id': 3, 'posicion': 'Centrocampista', 'edad': 30, 'pais': 'Portugal', 'dorsal': 8},
            {'id': 6, 'nombre': 'Marcus Rashford', 'equipo_id': 3, 'posicion': 'Delantero', 'edad': 27, 'pais': 'Inglaterra', 'dorsal': 10},
            {'id': 7, 'nombre': 'Mohamed Salah', 'equipo_id': 4, 'posicion': 'Delantero', 'edad': 33, 'pais': 'Egipto', 'dorsal': 11},
            {'id': 8, 'nombre': 'Virgil van Dijk', 'equipo_id': 4, 'posicion': 'Defensa', 'edad': 33, 'pais': 'Países Bajos', 'dorsal': 4},
            {'id': 9, 'nombre': 'Harry Kane', 'equipo_id': 5, 'posicion': 'Delantero', 'edad': 31, 'pais': 'Inglaterra', 'dorsal': 9},
            {'id': 10, 'nombre': 'Kylian Mbappé', 'equipo_id': 1, 'posicion': 'Delantero', 'edad': 26, 'pais': 'Francia', 'dorsal': 9},
            {'id': 11, 'nombre': 'Gavi', 'equipo_id': 2, 'posicion': 'Centrocampista', 'edad': 21, 'pais': 'España', 'dorsal': 6},
            {'id': 12, 'nombre': 'Erling Haaland', 'equipo_id': 8, 'posicion': 'Delantero', 'edad': 25, 'pais': 'Noruega', 'dorsal': 9},
        ]
        df_jugadores = pd.DataFrame(jugadores)
        save_dataframe_to_table(df_jugadores, 'jugadores', 'replace')
        
        # Datos de árbitros
        arbitros = [
            {'id': 1, 'nombre': 'Mateu Lahoz', 'pais': 'España', 'competicion_principal': 'LaLiga'},
            {'id': 2, 'nombre': 'Michael Oliver', 'pais': 'Inglaterra', 'competicion_principal': 'Premier League'},
            {'id': 3, 'nombre': 'Daniele Orsato', 'pais': 'Italia', 'competicion_principal': 'Serie A'},
            {'id': 4, 'nombre': 'Felix Brych', 'pais': 'Alemania', 'competicion_principal': 'Bundesliga'},
            {'id': 5, 'nombre': 'Clément Turpin', 'pais': 'Francia', 'competicion_principal': 'Ligue 1'},
        ]
        df_arbitros = pd.DataFrame(arbitros)
        save_dataframe_to_table(df_arbitros, 'arbitros', 'replace')
        
        # Datos de partidos
        partidos = [
            {'id': 1, 'fecha': '2025-07-10', 'equipo_local_id': 1, 'equipo_visitante_id': 2, 'goles_local': None, 'goles_visitante': None, 
             'liga': 'LaLiga', 'temporada': '2025/26', 'estadio': 'Santiago Bernabéu', 'arbitro_id': 1, 'estado': 'programado'},
            {'id': 2, 'fecha': '2025-07-15', 'equipo_local_id': 3, 'equipo_visitante_id': 4, 'goles_local': None, 'goles_visitante': None, 
             'liga': 'Premier League', 'temporada': '2025/26', 'estadio': 'Old Trafford', 'arbitro_id': 2, 'estado': 'programado'},
            {'id': 3, 'fecha': '2025-06-15', 'equipo_local_id': 1, 'equipo_visitante_id': 5, 'goles_local': 2, 'goles_visitante': 1, 
             'liga': 'Champions League', 'temporada': '2024/25', 'estadio': 'Santiago Bernabéu', 'arbitro_id': 4, 'estado': 'finalizado'},
            {'id': 4, 'fecha': '2025-06-01', 'equipo_local_id': 2, 'equipo_visitante_id': 7, 'goles_local': 3, 'goles_visitante': 0, 
             'liga': 'Amistoso', 'temporada': '2024/25', 'estadio': 'Camp Nou', 'arbitro_id': 3, 'estado': 'finalizado'},
            {'id': 5, 'fecha': '2025-07-20', 'equipo_local_id': 6, 'equipo_visitante_id': 8, 'goles_local': None, 'goles_visitante': None, 
             'liga': 'Champions League', 'temporada': '2025/26', 'estadio': 'Parc des Princes', 'arbitro_id': 5, 'estado': 'programado'},
        ]
        df_partidos = pd.DataFrame(partidos)
        save_dataframe_to_table(df_partidos, 'partidos', 'replace')
        
        mensaje = "Datos de prueba importados correctamente en la base de datos"
        return render_template('error.html', mensaje=mensaje)  # Usamos error.html para mostrar mensaje de éxito
        
    except Exception as e:
        mensaje = f"Error al importar datos de prueba: {str(e)}"
        return render_template('error.html', mensaje=mensaje)
