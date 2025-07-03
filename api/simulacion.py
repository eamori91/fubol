"""
Módulo para los endpoints de simulación.
Este módulo proporciona API endpoints para la simulación de partidos.
"""

from flask import Blueprint, request, jsonify
import random
from datetime import datetime
import numpy as np

# Blueprint para los endpoints de simulación
simulacion_bp = Blueprint('simulacion', __name__, url_prefix='/api/simulacion')

@simulacion_bp.route('/<equipo_local>/<equipo_visitante>', methods=['GET'])
def simular_partido(equipo_local, equipo_visitante):
    """
    Simula un partido entre dos equipos usando técnicas Monte Carlo.
    
    Args:
        equipo_local (str): Nombre del equipo local
        equipo_visitante (str): Nombre del equipo visitante
        
    Query Params:
        simulaciones (int): Número de simulaciones a realizar (default=1000)
        
    Returns:
        dict: Resultado de la simulación
    """
    try:
        # Verificar si se especifica el número de simulaciones
        n_simulaciones = int(request.args.get('simulaciones', 1000))
        n_simulaciones = min(max(n_simulaciones, 100), 5000)  # Limitar entre 100 y 5000
        
        # Simular resultados (en producción usaría un simulador real)
        victorias_local = 0
        empates = 0
        victorias_visitante = 0
        goles_local = []
        goles_visitante = []
        
        # Realizar simulaciones básicas
        for _ in range(n_simulaciones):
            gl = np.random.poisson(1.5)  # Media de goles local
            gv = np.random.poisson(1.2)  # Media de goles visitante
            
            goles_local.append(gl)
            goles_visitante.append(gv)
            
            if gl > gv:
                victorias_local += 1
            elif gl < gv:
                victorias_visitante += 1
            else:
                empates += 1
        
        # Calcular probabilidades
        total = victorias_local + empates + victorias_visitante
        prob_local = victorias_local / total
        prob_empate = empates / total
        prob_visitante = victorias_visitante / total
        
        # Calcular promedios
        media_gl = sum(goles_local) / len(goles_local)
        media_gv = sum(goles_visitante) / len(goles_visitante)
        
        # Determinar resultado más probable
        # Contar ocurrencias de cada resultado
        resultados = {}
        for gl, gv in zip(goles_local, goles_visitante):
            resultado = f"{gl}-{gv}"
            resultados[resultado] = resultados.get(resultado, 0) + 1
        
        # Ordenar resultados por frecuencia
        resultados_ordenados = sorted(resultados.items(), key=lambda x: x[1], reverse=True)
        resultado_mas_probable = resultados_ordenados[0][0] if resultados_ordenados else "1-0"
        
        # Construir resultado
        resultado = {
            'equipos': {'local': equipo_local, 'visitante': equipo_visitante},
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'simulaciones': n_simulaciones,
            'probabilidades': {
                'victoria_local': round(prob_local, 2),
                'empate': round(prob_empate, 2),
                'victoria_visitante': round(prob_visitante, 2)
            },
            'goles_promedio': {
                'local': round(media_gl, 1),
                'visitante': round(media_gv, 1)
            },
            'resultado_mas_probable': resultado_mas_probable,
            'resultados_frecuentes': [
                {'resultado': k, 'frecuencia': v / total} 
                for k, v in resultados_ordenados[:5]
            ] if resultados_ordenados else []
        }
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': f"Error en simulación de partido: {str(e)}"}), 500

@simulacion_bp.route('/eventos/<equipo_local>/<equipo_visitante>', methods=['GET'])
def simular_eventos_partido(equipo_local, equipo_visitante):
    """
    Simula los eventos de un partido minuto a minuto.
    
    Args:
        equipo_local (str): Nombre del equipo local
        equipo_visitante (str): Nombre del equipo visitante
        
    Returns:
        dict: Eventos simulados del partido
    """
    try:
        # Lista de posibles tipos de eventos
        tipos_eventos = [
            "gol", "tarjeta_amarilla", "tarjeta_roja", "corner", 
            "tiro_libre", "fuera_juego", "ocasion_clara", "parada"
        ]
        
        # Lista para almacenar los eventos
        eventos = []
        
        # Simular número de goles para cada equipo
        goles_local = np.random.poisson(1.5)
        goles_visitante = np.random.poisson(1.2)
        
        # Simular minutos de los goles
        minutos_goles_local = sorted(np.random.randint(1, 90, size=goles_local))
        minutos_goles_visitante = sorted(np.random.randint(1, 90, size=goles_visitante))
        
        # Generar eventos de gol
        for minuto in minutos_goles_local:
            eventos.append({
                "minuto": minuto,
                "tipo": "gol",
                "equipo": equipo_local,
                "jugador": f"Jugador {np.random.randint(1, 11)} de {equipo_local}"
            })
        
        for minuto in minutos_goles_visitante:
            eventos.append({
                "minuto": minuto,
                "tipo": "gol",
                "equipo": equipo_visitante,
                "jugador": f"Jugador {np.random.randint(1, 11)} de {equipo_visitante}"
            })
        
        # Simular otros eventos
        n_otros_eventos = np.random.randint(15, 30)
        for _ in range(n_otros_eventos):
            minuto = np.random.randint(1, 90)
            tipo = np.random.choice(tipos_eventos[1:])  # Excluimos "gol" que ya lo hemos tratado
            equipo = np.random.choice([equipo_local, equipo_visitante])
            
            eventos.append({
                "minuto": minuto,
                "tipo": tipo,
                "equipo": equipo,
                "jugador": f"Jugador {np.random.randint(1, 11)} de {equipo}"
            })
        
        # Ordenar eventos por minuto
        eventos_ordenados = sorted(eventos, key=lambda x: x["minuto"])
        
        # Calcular estadísticas
        estadisticas = {
            equipo_local: {
                "goles": goles_local,
                "posesion": np.random.randint(35, 65),
                "tiros": np.random.randint(5, 20),
                "tiros_puerta": np.random.randint(3, 12),
                "corners": len([e for e in eventos if e["tipo"] == "corner" and e["equipo"] == equipo_local]),
                "tarjetas_amarillas": len([e for e in eventos if e["tipo"] == "tarjeta_amarilla" and e["equipo"] == equipo_local]),
                "tarjetas_rojas": len([e for e in eventos if e["tipo"] == "tarjeta_roja" and e["equipo"] == equipo_local])
            },
            equipo_visitante: {
                "goles": goles_visitante,
                "posesion": 100 - np.random.randint(35, 65),
                "tiros": np.random.randint(5, 20),
                "tiros_puerta": np.random.randint(3, 12),
                "corners": len([e for e in eventos if e["tipo"] == "corner" and e["equipo"] == equipo_visitante]),
                "tarjetas_amarillas": len([e for e in eventos if e["tipo"] == "tarjeta_amarilla" and e["equipo"] == equipo_visitante]),
                "tarjetas_rojas": len([e for e in eventos if e["tipo"] == "tarjeta_roja" and e["equipo"] == equipo_visitante])
            }
        }
        
        return jsonify({
            "partido": {
                "equipos": {"local": equipo_local, "visitante": equipo_visitante},
                "resultado": {"local": goles_local, "visitante": goles_visitante},
                "fecha": datetime.now().strftime('%Y-%m-%d')
            },
            "eventos": eventos_ordenados,
            "estadisticas": estadisticas
        })
    except Exception as e:
        return jsonify({'error': f"Error en simulación de eventos: {str(e)}"}), 500
