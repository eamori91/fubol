"""
Módulo para simulación de partidos mediante técnicas Monte Carlo y simulación de eventos.
Complementa el análisis predictivo con simulaciones detalladas.
"""

import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import os
import json
from collections import defaultdict
import random

class SimuladorPartidos:
    def __init__(self, analizador_futuro=None):
        """
        Inicializa el simulador de partidos.
        
        Args:
            analizador_futuro: Instancia de AnalisisFuturo para utilizar sus modelos
        """
        self.analizador = analizador_futuro
        self.resultados_dir = os.path.join('data', 'simulaciones')
        os.makedirs(self.resultados_dir, exist_ok=True)
    
    def simular_partido_monte_carlo(self, equipo_local, equipo_visitante, fecha=None, n_simulaciones=1000):
        """
        Realiza múltiples simulaciones de un partido para generar distribuciones de resultados.
        
        Args:
            equipo_local: Nombre del equipo local
            equipo_visitante: Nombre del equipo visitante
            fecha: Fecha del partido (datetime)
            n_simulaciones: Número de simulaciones a realizar
            
        Returns:
            Diccionario con resultados de las simulaciones
        """
        if not self.analizador:
            raise ValueError("Se requiere un analizador inicializado con modelos cargados")
            
        fecha = fecha or datetime.now()
        
        # Obtener predicción base y características
        prediccion_base = self.analizador.predecir_partido_futuro(equipo_local, equipo_visitante, fecha)
        if not prediccion_base:
            return None
            
        # Estructuras para almacenar resultados
        resultados = {'victoria_local': 0, 'empate': 0, 'victoria_visitante': 0}
        goles_local = []
        goles_visitante = []
        
        # Obtener características para poder variarlas
        caracteristicas = self.analizador.obtener_caracteristicas_partido(equipo_local, equipo_visitante, fecha)
        if caracteristicas is None or caracteristicas.empty:
            print("No se pudieron obtener características para simular")
            return prediccion_base
        
        # Realizar simulaciones
        for _ in range(n_simulaciones):
            # Añadir pequeñas variaciones aleatorias a las características
            caract_sim = caracteristicas.copy()
            for col in caract_sim.columns:
                if col.startswith('stat_') or col.startswith('hist_'):  # Solo modificamos estadísticas, no identificadores
                    caract_sim[col] = caract_sim[col] * np.random.normal(1, 0.05)  # 5% de variación
            
            # Realizar predicciones con características variadas
            resultado = self.analizador.predecir_con_caracteristicas(caract_sim)
            if not resultado:
                continue
                
            # Contar resultados
            resultados[resultado['resultado_predicho']] += 1
            goles_local.append(resultado['goles_predichos']['local'])
            goles_visitante.append(resultado['goles_predichos']['visitante'])
        
        # Convertir a probabilidades
        total = sum(resultados.values())
        if total == 0:
            return prediccion_base
            
        probabilidades = {k: v/total for k, v in resultados.items()}
        
        # Generar histograma de goles
        hist_local = np.bincount(goles_local) if goles_local else np.array([0])
        hist_visitante = np.bincount(goles_visitante) if goles_visitante else np.array([0])
        
        # Normalizar histogramas para convertirlos en distribuciones
        dist_local = hist_local / len(goles_local) if goles_local else hist_local
        dist_visitante = hist_visitante / len(goles_visitante) if goles_visitante else hist_visitante
        
        # Crear resultado final de la simulación
        resultado_simulacion = {
            'equipos': {
                'local': equipo_local,
                'visitante': equipo_visitante
            },
            'fecha': fecha.strftime('%Y-%m-%d'),
            'n_simulaciones': n_simulaciones,
            'probabilidades': probabilidades,
            'goles_local': {
                'media': np.mean(goles_local) if goles_local else 0,
                'mediana': np.median(goles_local) if goles_local else 0,
                'moda': np.argmax(hist_local) if len(hist_local) > 0 else 0,
                'distribucion': dist_local.tolist() if len(dist_local) > 0 else [0]
            },
            'goles_visitante': {
                'media': np.mean(goles_visitante) if goles_visitante else 0, 
                'mediana': np.median(goles_visitante) if goles_visitante else 0,
                'moda': np.argmax(hist_visitante) if len(hist_visitante) > 0 else 0,
                'distribucion': dist_visitante.tolist() if len(dist_visitante) > 0 else [0]
            },
            'factores_clave': prediccion_base.get('factores_clave', [])
        }
        
        return resultado_simulacion
        
    def visualizar_distribucion_goles(self, resultado_simulacion, guardar_ruta=None):
        """
        Visualiza la distribución de goles de las simulaciones.
        
        Args:
            resultado_simulacion: Resultado de simular_partido_monte_carlo
            guardar_ruta: Ruta donde guardar la visualización (opcional)
        """
        if not resultado_simulacion:
            print("No hay resultados para visualizar")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Distribución de goles local
        dist_local = resultado_simulacion['goles_local']['distribucion']
        max_goles_local = len(dist_local)
        ax1.bar(range(max_goles_local), dist_local, alpha=0.7, color='blue')
        ax1.set_title(f"Distribución de goles: {resultado_simulacion['equipos']['local']}")
        ax1.set_xlabel("Número de goles")
        ax1.set_ylabel("Probabilidad")
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Distribución de goles visitante
        dist_visitante = resultado_simulacion['goles_visitante']['distribucion']
        max_goles_visitante = len(dist_visitante)
        ax2.bar(range(max_goles_visitante), dist_visitante, alpha=0.7, color='red')
        ax2.set_title(f"Distribución de goles: {resultado_simulacion['equipos']['visitante']}")
        ax2.set_xlabel("Número de goles")
        ax2.set_ylabel("Probabilidad")
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.suptitle(f"Simulación Monte Carlo ({resultado_simulacion['n_simulaciones']} iteraciones) - {resultado_simulacion['fecha']}")
        plt.tight_layout()
        
        if guardar_ruta:
            plt.savefig(guardar_ruta)
            print(f"Visualización guardada en {guardar_ruta}")
        else:
            plt.show()
    
    def guardar_resultado_simulacion(self, resultado_simulacion, nombre=None):
        """
        Guarda el resultado de una simulación en formato JSON.
        
        Args:
            resultado_simulacion: Resultado de simular_partido_monte_carlo
            nombre: Nombre personalizado para el archivo (opcional)
        """
        if not resultado_simulacion:
            return False
            
        if nombre:
            nombre_archivo = f"{nombre}.json"
        else:
            local = resultado_simulacion['equipos']['local'].replace(' ', '_')
            visitante = resultado_simulacion['equipos']['visitante'].replace(' ', '_')
            fecha = resultado_simulacion['fecha'].replace('-', '')
            nombre_archivo = f"sim_{local}_vs_{visitante}_{fecha}.json"
            
        ruta_completa = os.path.join(self.resultados_dir, nombre_archivo)
        
        try:
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                json.dump(resultado_simulacion, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error al guardar simulación: {e}")
            return False
            
    def simular_eventos_partido(self, equipo_local, equipo_visitante, fecha=None):
        """
        Simula los eventos clave de un partido minuto a minuto.
        
        Args:
            equipo_local: Nombre del equipo local
            equipo_visitante: Nombre del equipo visitante
            fecha: Fecha del partido (datetime)
            
        Returns:
            Diccionario con eventos del partido simulado
        """
        if not self.analizador:
            raise ValueError("Se requiere un analizador inicializado")
            
        fecha = fecha or datetime.now()
        
        # Obtener predicción base para tener datos iniciales
        prediccion_base = self.analizador.predecir_partido_futuro(equipo_local, equipo_visitante, fecha)
        if not prediccion_base:
            return None
            
        # Extraer probabilidades y características
        prob_victoria_local = prediccion_base['probabilidades'].get('victoria_local', 0.33)
        prob_empate = prediccion_base['probabilidades'].get('empate', 0.34)
        prob_victoria_visitante = prediccion_base['probabilidades'].get('victoria_visitante', 0.33)
        
        # Factores de fuerza de los equipos
        fuerza_local = prob_victoria_local / (prob_victoria_visitante + 0.001)  # Evitar división por cero
        fuerza_visitante = prob_victoria_visitante / (prob_victoria_local + 0.001)
        
        # Probabilidades base por minuto
        # La probabilidad total por partido normalmente sería entre 2-3 goles,
        # distribuidos en 90 minutos
        prob_gol_local_base = (prediccion_base['goles_predichos']['local'] / 90) * 1.2  # Factor de ajuste
        prob_gol_visitante_base = (prediccion_base['goles_predichos']['visitante'] / 90) * 1.2
        
        # Variables de simulación
        eventos = []
        minuto = 1
        estado_local = 100  # Energía/moral inicial (0-100)
        estado_visitante = 100
        goles_local = 0
        goles_visitante = 0
        tarjetas_local = {'amarilla': 0, 'roja': 0}
        tarjetas_visitante = {'amarilla': 0, 'roja': 0}
        posesion_local = 50 + (fuerza_local - fuerza_visitante) * 10  # Base de posesión
        posesion_local = max(30, min(70, posesion_local))  # Limitar entre 30% y 70%
        
        # Simulamos cada minuto del partido
        while minuto <= 90:
            # Modificar probabilidades según estado actual del partido
            momentum = (estado_local - estado_visitante) / 100
            
            # La probabilidad de gol se ajusta por el estado anímico/energético actual
            prob_gol_local = prob_gol_local_base * (1 + momentum * 0.2)
            prob_gol_visitante = prob_gol_visitante_base * (1 - momentum * 0.2)
            
            # Ajuste por resultado actual (equipos perdiendo tienden a arriesgar más)
            if goles_local < goles_visitante:
                prob_gol_local *= 1.3
                estado_local = min(100, estado_local + 2)  # Motivación por ir perdiendo
            elif goles_local > goles_visitante:
                prob_gol_visitante *= 1.3
                estado_visitante = min(100, estado_visitante + 2)
                
            # La probabilidad también se ve afectada por las tarjetas rojas
            prob_gol_local *= max(0.6, 1 - tarjetas_local['roja'] * 0.4)
            prob_gol_visitante *= max(0.6, 1 - tarjetas_visitante['roja'] * 0.4)
            
            # Simulamos probabilidades variables de eventos en cada minuto
            
            # 1. Goles
            if np.random.random() < prob_gol_local:
                goles_local += 1
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'gol',
                    'equipo': equipo_local,
                    'descripcion': f"¡GOL! {equipo_local}",
                    'marcador': f"{goles_local}-{goles_visitante}"
                })
                estado_local += 10
                estado_visitante -= 5
                
            if np.random.random() < prob_gol_visitante:
                goles_visitante += 1
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'gol',
                    'equipo': equipo_visitante,
                    'descripcion': f"¡GOL! {equipo_visitante}",
                    'marcador': f"{goles_local}-{goles_visitante}"
                })
                estado_visitante += 10
                estado_local -= 5
            
            # 2. Tarjetas
            # Las probabilidades aumentan en partidos cerrados y en los últimos minutos
            prob_tarjeta_base = 0.01 + (0.02 if abs(goles_local - goles_visitante) <= 1 else 0) + (0.01 if minuto > 70 else 0)
            
            # Tarjeta amarilla local
            if np.random.random() < prob_tarjeta_base:
                tarjetas_local['amarilla'] += 1
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_amarilla',
                    'equipo': equipo_local,
                    'descripcion': f"Tarjeta amarilla para {equipo_local}"
                })
                estado_local -= 2
                
            # Tarjeta amarilla visitante
            if np.random.random() < prob_tarjeta_base:
                tarjetas_visitante['amarilla'] += 1
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_amarilla',
                    'equipo': equipo_visitante,
                    'descripcion': f"Tarjeta amarilla para {equipo_visitante}"
                })
                estado_visitante -= 2
                
            # 3. Segunda amarilla/roja
            # Probabilidad de expulsión para jugadores con amarilla
            if tarjetas_local['amarilla'] > 0 and np.random.random() < 0.001:
                tarjetas_local['roja'] += 1
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_roja',
                    'equipo': equipo_local,
                    'descripcion': f"Tarjeta roja para {equipo_local}"
                })
                estado_local -= 15
                
            if tarjetas_visitante['amarilla'] > 0 and np.random.random() < 0.001:
                tarjetas_visitante['roja'] += 1
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_roja',
                    'equipo': equipo_visitante,
                    'descripcion': f"Tarjeta roja para {equipo_visitante}"
                })
                estado_visitante -= 15
            
            # 4. Ocasiones claras de gol (no convertidas)
            if np.random.random() < prob_gol_local * 2:  # Más ocasiones que goles
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'ocasion',
                    'equipo': equipo_local,
                    'descripcion': f"Ocasión clara para {equipo_local}"
                })
                
            if np.random.random() < prob_gol_visitante * 2:
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'ocasion',
                    'equipo': equipo_visitante,
                    'descripcion': f"Ocasión clara para {equipo_visitante}"
                })
            
            # 5. Simulación de posesión (se mueve ligeramente cada minuto)
            posesion_local += np.random.uniform(-2, 2)
            posesion_local = max(30, min(70, posesion_local))  # Limitar entre 30% y 70%
            
            # 6. Efectos de fatiga
            estado_local = max(50, estado_local - np.random.uniform(0.1, 0.5))
            estado_visitante = max(50, estado_visitante - np.random.uniform(0.1, 0.5))
            
            minuto += 1
            
            # Tiempo añadido para partidos con muchos eventos
            if minuto == 90 and len(eventos) > 15:
                minuto_adicional = np.random.randint(1, 6)  # 1-5 minutos añadidos
                print(f"Tiempo adicional: {minuto_adicional} minutos")
        
        # Resultado final
        resultado = "victoria_local" if goles_local > goles_visitante else \
                   "victoria_visitante" if goles_local < goles_visitante else "empate"
                   
        # Resumen de estadísticas
        estadisticas = {
            'posesion': {'local': posesion_local, 'visitante': 100 - posesion_local},
            'tarjetas': {
                'local': {'amarilla': tarjetas_local['amarilla'], 'roja': tarjetas_local['roja']},
                'visitante': {'amarilla': tarjetas_visitante['amarilla'], 'roja': tarjetas_visitante['roja']}
            },
            'tiros': {
                'local': sum(1 for e in eventos if e['equipo'] == equipo_local and 
                             (e['tipo'] == 'gol' or e['tipo'] == 'ocasion')),
                'visitante': sum(1 for e in eventos if e['equipo'] == equipo_visitante and 
                                (e['tipo'] == 'gol' or e['tipo'] == 'ocasion'))
            }
        }
        
        # Resumen final
        resultado_simulacion = {
            'equipos': {
                'local': equipo_local,
                'visitante': equipo_visitante
            },
            'fecha': fecha.strftime('%Y-%m-%d'),
            'eventos': eventos,
            'resultado_final': resultado,
            'marcador_final': f"{goles_local}-{goles_visitante}",
            'estadisticas': estadisticas
        }
        
        return resultado_simulacion
        
    def visualizar_eventos_partido(self, simulacion_eventos, guardar_ruta=None):
        """
        Visualiza la evolución del partido minuto a minuto.
        
        Args:
            simulacion_eventos: Resultado de simular_eventos_partido
            guardar_ruta: Ruta donde guardar la visualización (opcional)
        """
        if not simulacion_eventos or 'eventos' not in simulacion_eventos:
            print("No hay eventos para visualizar")
            return
        
        eventos = simulacion_eventos['eventos']
        if not eventos:
            return
            
        eq_local = simulacion_eventos['equipos']['local']
        eq_visitante = simulacion_eventos['equipos']['visitante']
        
        # Recopilamos datos para la evolución del marcador
        minutos = []
        goles_local = []
        goles_visitante = []
        
        gl, gv = 0, 0
        for evento in eventos:
            if evento['tipo'] == 'gol':
                minutos.append(evento['minuto'])
                if evento['equipo'] == eq_local:
                    gl += 1
                else:
                    gv += 1
                goles_local.append(gl)
                goles_visitante.append(gv)
        
        # Si no hay goles, no hay gráfico
        if not minutos:
            print("No hay goles para visualizar")
            return
            
        # Añadir el minuto final para completar el gráfico
        minutos.append(90)
        goles_local.append(gl)
        goles_visitante.append(gv)
        
        # Crear visualización
        plt.figure(figsize=(12, 6))
        plt.step(minutos, goles_local, where='post', label=eq_local, linewidth=2, color='blue')
        plt.step(minutos, goles_visitante, where='post', label=eq_visitante, linewidth=2, color='red')
        
        # Marcar eventos importantes
        for evento in eventos:
            if evento['tipo'] == 'gol':
                color = 'blue' if evento['equipo'] == eq_local else 'red'
                plt.plot(evento['minuto'], int(evento['marcador'].split('-')[0]) if evento['equipo'] == eq_local 
                       else int(evento['marcador'].split('-')[1]), 'o', color=color, markersize=8)
                
            elif evento['tipo'] == 'tarjeta_roja':
                color = 'blue' if evento['equipo'] == eq_local else 'red'
                plt.axvline(x=evento['minuto'], color=color, linestyle='--', alpha=0.5)
                plt.text(evento['minuto'], max(goles_local + goles_visitante) + 0.2, '🟥', 
                        color=color, fontsize=12)
        
        plt.xlabel('Minuto')
        plt.ylabel('Goles')
        plt.title(f"Evolución del marcador: {eq_local} vs {eq_visitante}")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        if guardar_ruta:
            plt.savefig(guardar_ruta)
            print(f"Visualización guardada en {guardar_ruta}")
        else:
            plt.show()
    
    def simular_partido_eventos(self, equipo_local, equipo_visitante, 
                              jugadores_local=None, jugadores_visitante=None, 
                              duracion=90, detalle_avanzado=False):
        """
        Simula un partido completo minuto a minuto con eventos detallados.
        
        Args:
            equipo_local: Nombre del equipo local
            equipo_visitante: Nombre del equipo visitante
            jugadores_local: Lista de jugadores del equipo local (opcional)
            jugadores_visitante: Lista de jugadores del equipo visitante (opcional)
            duracion: Duración del partido en minutos
            detalle_avanzado: Si True, genera eventos más detallados y específicos
        
        Returns:
            Un diccionario con el resultado final, eventos y estadísticas
        """
        # Inicialización
        eventos = []
        goles_local = 0
        goles_visitante = 0
        
        # Estadísticas del partido
        estadisticas = {
            'posesion': {'local': 50, 'visitante': 50},
            'tiros': {'local': 0, 'visitante': 0},
            'tiros_puerta': {'local': 0, 'visitante': 0},
            'corners': {'local': 0, 'visitante': 0},
            'faltas': {'local': 0, 'visitante': 0},
            'fueras_juego': {'local': 0, 'visitante': 0},
            'pases': {'local': 0, 'visitante': 0},
            'pases_completados': {'local': 0, 'visitante': 0}
        }
        
        # Tarjetas
        tarjetas_local = {'amarilla': 0, 'roja': 0}
        tarjetas_visitante = {'amarilla': 0, 'roja': 0}
        
        # Estados de forma durante el partido (varía según el cansancio, goles, etc.)
        estado_local = 100
        estado_visitante = 100
        
        # Conseguir predicción base
        if self.analizador:
            try:
                pred = self.analizador.predecir_partido(equipo_local, equipo_visitante)
                prob_local = pred.get('victoria_local', 0.45)
                prob_visitante = pred.get('victoria_visitante', 0.30)
                prob_empate = pred.get('empate', 0.25)
                
                # Normalizar
                total = prob_local + prob_visitante + prob_empate
                prob_local /= total
                prob_visitante /= total
                prob_empate /= total
                
                # Probabilidades base por minuto (ajustadas para dar resultados realistas)
                prob_gol_local = prob_local / 30
                prob_gol_visitante = prob_visitante / 30
            except:
                # Valores por defecto
                prob_gol_local = 0.03
                prob_gol_visitante = 0.02
        else:
            # Valores por defecto
            prob_gol_local = 0.03
            prob_gol_visitante = 0.02
        
        # Ajustes iniciales de posesión basados en fuerza relativa
        fuerza_relativa = 1.0
        try:
            if 'prob_local' in locals() and 'prob_visitante' in locals():
                if prob_visitante > 0:
                    fuerza_relativa = float(prob_local) / float(prob_visitante)
                else:
                    fuerza_relativa = 1.5
        except:
            fuerza_relativa = 1.0
        estadisticas['posesion']['local'] = min(75, max(35, int(50 * fuerza_relativa)))
        estadisticas['posesion']['visitante'] = 100 - estadisticas['posesion']['local']
            
        # Si tenemos información de jugadores
        jugadores_goleadores_local = []
        jugadores_goleadores_visitante = []
        
        if jugadores_local:
            # Extraer delanteros y mediocampistas ofensivos para goles
            jugadores_goleadores_local = [j for j in jugadores_local 
                                       if j.get('posicion') in ['delantero', 'mediocampista'] 
                                       and j.get('rol', '') in ['ofensivo', 'mixto']]
        
        if jugadores_visitante:
            jugadores_goleadores_visitante = [j for j in jugadores_visitante 
                                           if j.get('posicion') in ['delantero', 'mediocampista']
                                           and j.get('rol', '') in ['ofensivo', 'mixto']]
        
        # Probabilidad base de eventos por minuto
        prob_tarjeta_base = 0.01
        prob_corner_base = 0.06
        prob_falta_base = 0.08
        prob_fuera_juego_base = 0.02
        
        # Eventos dinámicos del partido - simulación minuto a minuto
        for minuto in range(1, duracion + 1):
            # Añadir tiempo extra si es final de tiempo
            tiempo_extra = 0
            if minuto == 45 or minuto == 90:
                tiempo_extra = np.random.randint(1, 6)
            
            # Fatiga: los equipos pierden rendimiento con el tiempo
            if minuto > 60:
                estado_local -= 0.1
                estado_visitante -= 0.1
            
            # Ajustar probabilidades según estado
            factor_local = estado_local / 100
            factor_visitante = estado_visitante / 100
            
            # 1. Goles
            # Probabilidad base modificada por estado actual
            prob_gol_local_actual = prob_gol_local * factor_local
            prob_gol_visitante_actual = prob_gol_visitante * factor_visitante
            
            # Local marca
            if np.random.random() < prob_gol_local_actual:
                goles_local += 1
                estadisticas['tiros']['local'] += 1
                estadisticas['tiros_puerta']['local'] += 1
                
                # Selección de jugador goleador
                goleador = "Jugador desconocido"
                if jugadores_goleadores_local:
                    # Elegir jugador ponderando por habilidad
                    weights = [j.get('habilidad', 70) for j in jugadores_goleadores_local]
                    goleador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_local], p=np.array(weights)/sum(weights))
                
                tipo_gol = "gol"
                detalle = ""
                
                # Añadir variedad a tipos de gol si detalle_avanzado
                if detalle_avanzado:
                    tipo_opciones = ["normal", "cabeza", "volea", "tiro libre", "penalti"]
                    prob_tipos = [0.6, 0.15, 0.1, 0.1, 0.05]
                    tipo_gol_detalle = np.random.choice(tipo_opciones, p=prob_tipos)
                    
                    if tipo_gol_detalle == "penalti":
                        tipo_gol = "penalti"
                    elif tipo_gol_detalle == "tiro libre":
                        tipo_gol = "tiro libre"
                    
                    # Añadir asistencia
                    if tipo_gol_detalle not in ["penalti", "tiro libre"] and jugadores_goleadores_local and np.random.random() < 0.7:
                        asistente = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_local 
                                                  if j.get('nombre') != goleador])
                        detalle = f" (Asistencia: {asistente})"
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': tipo_gol,
                    'equipo': equipo_local,
                    'jugador': goleador,
                    'descripcion': f"¡GOL! {equipo_local} ({goleador}){detalle}"
                })
                
                # Efecto anímico
                estado_local += 5
                estado_visitante -= 5
            
            # Visitante marca
            if np.random.random() < prob_gol_visitante_actual:
                goles_visitante += 1
                estadisticas['tiros']['visitante'] += 1
                estadisticas['tiros_puerta']['visitante'] += 1
                
                # Selección de jugador goleador
                goleador = "Jugador desconocido"
                if jugadores_goleadores_visitante:
                    # Elegir jugador ponderando por habilidad
                    weights = [j.get('habilidad', 70) for j in jugadores_goleadores_visitante]
                    goleador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_visitante], p=np.array(weights)/sum(weights))
                
                tipo_gol = "gol"
                detalle = ""
                
                # Añadir variedad a tipos de gol si detalle_avanzado
                if detalle_avanzado:
                    tipo_opciones = ["normal", "cabeza", "volea", "tiro libre", "penalti"]
                    prob_tipos = [0.6, 0.15, 0.1, 0.1, 0.05]
                    tipo_gol_detalle = np.random.choice(tipo_opciones, p=prob_tipos)
                    
                    if tipo_gol_detalle == "penalti":
                        tipo_gol = "penalti"
                    elif tipo_gol_detalle == "tiro libre":
                        tipo_gol = "tiro libre"
                    
                    # Añadir asistencia
                    if tipo_gol_detalle not in ["penalti", "tiro libre"] and jugadores_goleadores_visitante and np.random.random() < 0.7:
                        asistente = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_visitante 
                                                  if j.get('nombre') != goleador])
                        detalle = f" (Asistencia: {asistente})"
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': tipo_gol,
                    'equipo': equipo_visitante,
                    'jugador': goleador,
                    'descripcion': f"¡GOL! {equipo_visitante} ({goleador}){detalle}"
                })
                
                # Efecto anímico
                estado_local -= 5
                estado_visitante += 5
            
            # 2. Tarjetas
            # Tarjeta amarilla local
            if np.random.random() < prob_tarjeta_base * (1 + (90 - estado_local) / 100):
                tarjetas_local['amarilla'] += 1
                jugador = "Jugador"
                
                if jugadores_local:
                    # Los defensas y mediocampistas defensivos tienen más probabilidad de tarjeta
                    defensivos = [j for j in jugadores_local 
                                if j.get('posicion') in ['defensa', 'mediocampista'] 
                                and j.get('rol', '') in ['defensivo', 'mixto']]
                    
                    if defensivos:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in defensivos])
                    else:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_local])
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_amarilla',
                    'equipo': equipo_local,
                    'jugador': jugador,
                    'descripcion': f"Tarjeta amarilla para {jugador} ({equipo_local})"
                })
                estado_local -= 2
                
            # Tarjeta amarilla visitante
            if np.random.random() < prob_tarjeta_base * (1 + (90 - estado_visitante) / 100):
                tarjetas_visitante['amarilla'] += 1
                jugador = "Jugador"
                
                if jugadores_visitante:
                    # Los defensas y mediocampistas defensivos tienen más probabilidad de tarjeta
                    defensivos = [j for j in jugadores_visitante 
                                if j.get('posicion') in ['defensa', 'mediocampista'] 
                                and j.get('rol', '') in ['defensivo', 'mixto']]
                    
                    if defensivos:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in defensivos])
                    else:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_visitante])
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_amarilla',
                    'equipo': equipo_visitante,
                    'jugador': jugador,
                    'descripcion': f"Tarjeta amarilla para {jugador} ({equipo_visitante})"
                })
                estado_visitante -= 2
                
            # 3. Segunda amarilla/roja
            # Probabilidad de expulsión para jugadores con amarilla
            if tarjetas_local['amarilla'] > 0 and np.random.random() < 0.001 * (1 + tarjetas_local['amarilla'] / 3):
                tarjetas_local['roja'] += 1
                jugador = "Jugador"
                
                if jugadores_local:
                    jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_local])
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_roja',
                    'equipo': equipo_local,
                    'jugador': jugador,
                    'descripcion': f"Tarjeta roja para {jugador} ({equipo_local})"
                })
                estado_local -= 15
                
            if tarjetas_visitante['amarilla'] > 0 and np.random.random() < 0.001 * (1 + tarjetas_visitante['amarilla'] / 3):
                tarjetas_visitante['roja'] += 1
                jugador = "Jugador"
                
                if jugadores_visitante:
                    jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_visitante])
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tarjeta_roja',
                    'equipo': equipo_visitante,
                    'jugador': jugador,
                    'descripcion': f"Tarjeta roja para {jugador} ({equipo_visitante})"
                })
                estado_visitante -= 15
            
            # 4. Ocasiones claras de gol (no convertidas)
            if np.random.random() < prob_gol_local * 2:
                estadisticas['tiros']['local'] += 1
                if np.random.random() < 0.5:
                    estadisticas['tiros_puerta']['local'] += 1
                    
                jugador = "Jugador"
                if jugadores_goleadores_local:
                    weights = [j.get('habilidad', 70) for j in jugadores_goleadores_local]
                    jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_local], p=np.array(weights)/sum(weights))
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'ocasion',
                    'equipo': equipo_local,
                    'jugador': jugador,
                    'descripcion': f"Ocasión clara para {jugador} ({equipo_local})"
                })
                
            if np.random.random() < prob_gol_visitante * 2:
                estadisticas['tiros']['visitante'] += 1
                if np.random.random() < 0.5:
                    estadisticas['tiros_puerta']['visitante'] += 1
                    
                jugador = "Jugador"
                if jugadores_goleadores_visitante:
                    weights = [j.get('habilidad', 70) for j in jugadores_goleadores_visitante]
                    jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_visitante], p=np.array(weights)/sum(weights))
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'ocasion',
                    'equipo': equipo_visitante,
                    'jugador': jugador,
                    'descripcion': f"Ocasión clara para {jugador} ({equipo_visitante})"
                })
                
            # 5. Corners
            if np.random.random() < prob_corner_base * factor_local:
                estadisticas['corners']['local'] += 1
                if detalle_avanzado and np.random.random() < 0.2:  # 20% de corners generan un evento destacado
                    eventos.append({
                        'minuto': minuto,
                        'tipo': 'corner',
                        'equipo': equipo_local,
                        'descripcion': f"Corner peligroso para {equipo_local}"
                    })
                    
            if np.random.random() < prob_corner_base * factor_visitante:
                estadisticas['corners']['visitante'] += 1
                if detalle_avanzado and np.random.random() < 0.2:
                    eventos.append({
                        'minuto': minuto,
                        'tipo': 'corner',
                        'equipo': equipo_visitante,
                        'descripcion': f"Corner peligroso para {equipo_visitante}"
                    })
            
            # 6. Faltas
            if np.random.random() < prob_falta_base:
                estadisticas['faltas']['local'] += 1
                if detalle_avanzado and np.random.random() < 0.1:  # 10% de faltas generan un evento destacado
                    jugador = "Jugador"
                    if jugadores_local:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_local])
                        
                    eventos.append({
                        'minuto': minuto,
                        'tipo': 'falta',
                        'equipo': equipo_local,
                        'jugador': jugador,
                        'descripcion': f"Falta cometida por {jugador} ({equipo_local})"
                    })
                    
            if np.random.random() < prob_falta_base:
                estadisticas['faltas']['visitante'] += 1
                if detalle_avanzado and np.random.random() < 0.1:
                    jugador = "Jugador"
                    if jugadores_visitante:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_visitante])
                        
                    eventos.append({
                        'minuto': minuto,
                        'tipo': 'falta',
                        'equipo': equipo_visitante,
                        'jugador': jugador,
                        'descripcion': f"Falta cometida por {jugador} ({equipo_visitante})"
                    })
            
            # 7. Fueras de juego
            if np.random.random() < prob_fuera_juego_base * estadisticas['posesion']['local']/50:
                estadisticas['fueras_juego']['local'] += 1
                if detalle_avanzado and np.random.random() < 0.15:
                    jugador = "Jugador"
                    if jugadores_goleadores_local:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_local])
                        
                    eventos.append({
                        'minuto': minuto,
                        'tipo': 'fuera_juego',
                        'equipo': equipo_local,
                        'jugador': jugador,
                        'descripcion': f"Fuera de juego de {jugador} ({equipo_local})"
                    })
                
            if np.random.random() < prob_fuera_juego_base * estadisticas['posesion']['visitante']/50:
                estadisticas['fueras_juego']['visitante'] += 1
                if detalle_avanzado and np.random.random() < 0.15:
                    jugador = "Jugador"
                    if jugadores_goleadores_visitante:
                        jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_visitante])
                        
                    eventos.append({
                        'minuto': minuto,
                        'tipo': 'fuera_juego',
                        'equipo': equipo_visitante,
                        'jugador': jugador,
                        'descripcion': f"Fuera de juego de {jugador} ({equipo_visitante})"
                    })
            
            # 8. Pases
            num_pases_local = int(np.random.normal(estadisticas['posesion']['local']/5, 2))
            num_pases_visitante = int(np.random.normal(estadisticas['posesion']['visitante']/5, 2))
            
            estadisticas['pases']['local'] += max(0, num_pases_local)
            estadisticas['pases']['visitante'] += max(0, num_pases_visitante)
            
            # Éxito de pases basado en la calidad del equipo
            tasa_exito_local = 0.7 + 0.2 * factor_local
            tasa_exito_visitante = 0.7 + 0.2 * factor_visitante
            
            estadisticas['pases_completados']['local'] += int(num_pases_local * tasa_exito_local)
            estadisticas['pases_completados']['visitante'] += int(num_pases_visitante * tasa_exito_visitante)
            
            # 9. Eventos especiales
            if detalle_avanzado and minuto in [1, 45, 46, 90] or np.random.random() < 0.01:
                eventos_especiales = [
                    "Parada espectacular", "Jugada brillante", "Ataque peligroso", 
                    "Contraataque", "Recuperación importante", "Despeje crucial"
                ]
                tipo_evento = np.random.choice(eventos_especiales)
                
                # Determinar equipo para el evento especial
                if np.random.random() < estadisticas['posesion']['local']/100:
                    equipo = equipo_local
                    jugadores_lista = jugadores_local
                else:
                    equipo = equipo_visitante
                    jugadores_lista = jugadores_visitante
                
                jugador = "Jugador"
                if jugadores_lista:
                    jugador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_lista])
                
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'especial',
                    'equipo': equipo,
                    'jugador': jugador,
                    'descripcion': f"{tipo_evento} de {jugador} ({equipo})"
                })
            
            # Eventos de final de tiempo
            if minuto == 45 or minuto == 90:
                # Añadir tiempo añadido
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'tiempo_anadido',
                    'descripcion': f"{tiempo_extra} minutos de tiempo añadido"
                })
                
                # Simular minutos de tiempo añadido (probabilidad más alta de eventos)
                for t_extra in range(1, tiempo_extra + 1):
                    min_actual = minuto + t_extra
                    
                    # Mayor probabilidad de goles en tiempo añadido
                    if np.random.random() < prob_gol_local_actual * 1.5:
                        goles_local += 1
                        estadisticas['tiros']['local'] += 1
                        estadisticas['tiros_puerta']['local'] += 1
                        
                        goleador = "Jugador"
                        if jugadores_goleadores_local:
                            weights = [j.get('habilidad', 70) for j in jugadores_goleadores_local]
                            goleador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_local], 
                                                     p=np.array(weights)/sum(weights))
                        
                        eventos.append({
                            'minuto': f"{minuto}+{t_extra}",
                            'tipo': 'gol',
                            'equipo': equipo_local,
                            'jugador': goleador,
                            'descripcion': f"¡GOL EN EL TIEMPO AÑADIDO! {equipo_local} ({goleador})"
                        })
                    
                    if np.random.random() < prob_gol_visitante_actual * 1.5:
                        goles_visitante += 1
                        estadisticas['tiros']['visitante'] += 1
                        estadisticas['tiros_puerta']['visitante'] += 1
                        
                        goleador = "Jugador"
                        if jugadores_goleadores_visitante:
                            weights = [j.get('habilidad', 70) for j in jugadores_goleadores_visitante]
                            goleador = np.random.choice([j.get('nombre', "Jugador") for j in jugadores_goleadores_visitante], 
                                                     p=np.array(weights)/sum(weights))
                        
                        eventos.append({
                            'minuto': f"{minuto}+{t_extra}",
                            'tipo': 'gol',
                            'equipo': equipo_visitante,
                            'jugador': goleador,
                            'descripcion': f"¡GOL EN EL TIEMPO AÑADIDO! {equipo_visitante} ({goleador})"
                        })
        
        # Eventos de final de partido
        eventos.append({
            'minuto': 90,
            'tipo': 'final_partido',
            'descripcion': f"Final del partido. {equipo_local} {goles_local} - {goles_visitante} {equipo_visitante}"
        })
        
        # Ordenar eventos por minuto
        eventos = sorted(eventos, key=lambda x: 
                        int(x['minuto']) if isinstance(x['minuto'], int) else 
                        int(x['minuto'].split('+')[0]) + int(x['minuto'].split('+')[1])/10)
        
        return {
            'equipos': {
                'local': equipo_local,
                'visitante': equipo_visitante
            },
            'resultado': {
                'local': goles_local,
                'visitante': goles_visitante
            },
            'eventos': eventos,
            'estadisticas': estadisticas,
            'tarjetas': {
                'local': tarjetas_local,
                'visitante': tarjetas_visitante
            }
        }
    
    def visualizar_timeline_partido(self, eventos, equipo_local, equipo_visitante, resultado, guardar=False, ruta=None):
        """
        Crea una visualización timeline de los eventos del partido.
        
        Args:
            eventos: Lista de eventos del partido
            equipo_local: Nombre del equipo local
            equipo_visitante: Nombre del equipo visitante
            resultado: Dict con goles locales y visitantes
            guardar: Si True, guarda la visualización como imagen
            ruta: Ruta donde guardar la imagen (opcional)
            
        Returns:
            Figura de matplotlib
        """
        # Crear figura
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Configurar título con resultado
        goles_local = resultado['local']
        goles_visitante = resultado['visitante']
        titulo = f"{equipo_local} {goles_local} - {goles_visitante} {equipo_visitante}"
        fig.suptitle(titulo, fontsize=16)
        
        # Diccionario de colores por tipo de evento
        colores = {
            'gol': 'green',
            'penalti': 'darkgreen',
            'tarjeta_amarilla': 'gold',
            'tarjeta_roja': 'red',
            'corner': 'gray',
            'ocasion': 'blue',
            'falta': 'brown',
            'fuera_juego': 'purple',
            'especial': 'cyan',
            'tiro libre': 'darkgreen'
        }
        
        # Diccionario de símbolos por tipo de evento
        simbolos = {
            'gol': 'o',
            'penalti': 'P',
            'tarjeta_amarilla': 's',
            'tarjeta_roja': 'D',
            'corner': '^',
            'ocasion': 'v',
            'falta': 'x',
            'fuera_juego': '+',
            'especial': '*',
            'tiro libre': 'h'
        }
        
        # Dibujar línea de tiempo
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        
        # Dibujar eventos
        for evento in eventos:
            if 'tipo' not in evento or evento['tipo'] in ['tiempo_anadido', 'final_partido']:
                continue
                
            # Obtener minuto
            if isinstance(evento['minuto'], str) and '+' in evento['minuto']:
                partes = evento['minuto'].split('+')
                minuto = int(partes[0]) + int(partes[1])/10
            else:
                minuto = int(evento['minuto'])
            
            # Determinar posición vertical
            if evento.get('equipo') == equipo_local:
                y = 1  # Encima de la línea para equipo local
            else:
                y = -1  # Debajo de la línea para equipo visitante
            
            # Obtener color y símbolo
            color = colores.get(evento['tipo'], 'gray')
            simbolo = simbolos.get(evento['tipo'], 'o')
            
            # Dibujar marcador
            ax.scatter(minuto, y, color=color, marker=simbolo, s=100)
            
            # Añadir etiqueta para goles
            if evento['tipo'] in ['gol', 'penalti', 'tarjeta_roja']:
                # Nombre corto del jugador
                jugador = evento.get('jugador', '').split(',')[0] if evento.get('jugador') else ''
                
                # Formato de la etiqueta
                etiqueta = ""
                if evento['tipo'] == 'gol' or evento['tipo'] == 'penalti':
                    etiqueta = f"⚽ {jugador}"
                elif evento['tipo'] == 'tarjeta_roja':
                    etiqueta = f"🟥 {jugador}"
                
                ax.annotate(etiqueta, (minuto, y), 
                           xytext=(0, 10 if y > 0 else -15),
                           textcoords='offset points',
                           ha='center', fontsize=9)
        
        # Configurar ejes
        ax.set_xlim(-5, 95)
        ax.set_ylim(-2, 2)
        ax.set_yticks([])
        
        # Configurar etiquetas del eje X
        ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
        ax.set_xlabel('Minuto de partido')
        
        # Añadir nombre de equipos
        ax.text(-5, 1, equipo_local, ha='right', va='center', fontsize=12, fontweight='bold')
        ax.text(-5, -1, equipo_visitante, ha='right', va='center', fontsize=12, fontweight='bold')
        
        # Añadir líneas de medio tiempo
        ax.axvline(x=45, color='gray', linestyle='--', alpha=0.5)
        
        # Añadir leyenda
        for tipo, color in colores.items():
            if tipo in ['gol', 'tarjeta_amarilla', 'tarjeta_roja', 'ocasion']:
                ax.scatter([], [], color=color, marker=simbolos[tipo], s=100, 
                          label=tipo.replace('_', ' ').title())
        
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=4)
        
        plt.tight_layout()
        
        # Guardar si se solicita
        if guardar:
            if ruta is None:
                ruta = os.path.join(self.resultados_dir, 
                                   f"timeline_{equipo_local}_{equipo_visitante}_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
            plt.savefig(ruta, dpi=300, bbox_inches='tight')
            print(f"Timeline guardada en: {ruta}")
        
        return fig
    
    def visualizar_heatmap_eventos(self, eventos, estadisticas, equipo_local, equipo_visitante, resultado, guardar=False, ruta=None):
        """
        Crea un heatmap de eventos por período y equipo.
        
        Args:
            eventos: Lista de eventos del partido
            estadisticas: Diccionario de estadísticas del partido
            equipo_local: Nombre del equipo local
            equipo_visitante: Nombre del equipo visitante
            resultado: Dict con goles locales y visitantes
            guardar: Si True, guarda la visualización como imagen
            ruta: Ruta donde guardar la imagen (opcional)
            
        Returns:
            Figura de matplotlib
        """
        # Períodos de tiempo (15 minutos cada uno)
        periodos = ['1-15', '16-30', '31-45', '46-60', '61-75', '76-90']
        
        # Tipos de eventos a contabilizar
        tipos_eventos = ['gol', 'penalti', 'ocasion', 'tarjeta_amarilla', 'tarjeta_roja']
        
        # Inicializar contadores
        eventos_local = {tipo: [0, 0, 0, 0, 0, 0] for tipo in tipos_eventos}
        eventos_visitante = {tipo: [0, 0, 0, 0, 0, 0] for tipo in tipos_eventos}
        
        # Contar eventos por período
        for evento in eventos:
            if 'tipo' not in evento or evento['tipo'] not in tipos_eventos:
                continue
                
            tipo = evento['tipo']
            
            # Obtener minuto
            if isinstance(evento['minuto'], str) and '+' in evento['minuto']:
                partes = evento['minuto'].split('+')
                minuto = int(partes[0])
            else:
                minuto = int(evento['minuto'])
            
            # Determinar período
            if minuto <= 15:
                periodo = 0
            elif minuto <= 30:
                periodo = 1
            elif minuto <= 45:
                periodo = 2
            elif minuto <= 60:
                periodo = 3
            elif minuto <= 75:
                periodo = 4
            else:
                periodo = 5
            
            # Incrementar contador
            if evento.get('equipo') == equipo_local:
                eventos_local[tipo][periodo] += 1
            else:
                eventos_visitante[tipo][periodo] += 1
        
        # Crear figura para ambos equipos
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Matriz para heatmap
        data_local = np.zeros((len(tipos_eventos), len(periodos)))
        data_visitante = np.zeros((len(tipos_eventos), len(periodos)))
        
        for i, tipo in enumerate(tipos_eventos):
            for j in range(len(periodos)):
                data_local[i, j] = eventos_local[tipo][j]
                data_visitante[i, j] = eventos_visitante[tipo][j]
        
        # Plotear heatmap local
        im1 = ax1.imshow(data_local, cmap='YlOrRd')
        ax1.set_title(f"{equipo_local} - Eventos por período")
        ax1.set_xticks(np.arange(len(periodos)))
        ax1.set_yticks(np.arange(len(tipos_eventos)))
        ax1.set_xticklabels(periodos)
        ax1.set_yticklabels([t.replace('_', ' ').title() for t in tipos_eventos])
        
        # Añadir anotaciones
        for i in range(len(tipos_eventos)):
            for j in range(len(periodos)):
                if data_local[i, j] > 0:
                    ax1.text(j, i, int(data_local[i, j]), ha="center", va="center", color="black")
        
        # Plotear heatmap visitante
        im2 = ax2.imshow(data_visitante, cmap='YlOrRd')
        ax2.set_title(f"{equipo_visitante} - Eventos por período")
        ax2.set_xticks(np.arange(len(periodos)))
        ax2.set_yticks(np.arange(len(tipos_eventos)))
        ax2.set_xticklabels(periodos)
        ax2.set_yticklabels([t.replace('_', ' ').title() for t in tipos_eventos])
        
        # Añadir anotaciones
        for i in range(len(tipos_eventos)):
            for j in range(len(periodos)):
                if data_visitante[i, j] > 0:
                    ax2.text(j, i, int(data_visitante[i, j]), ha="center", va="center", color="black")
        
        # Título general
        titulo = f"{equipo_local} {resultado['local']} - {resultado['visitante']} {equipo_visitante}: Distribución de eventos"
        fig.suptitle(titulo, fontsize=16)
        
        # Añadir colorbar
        fig.colorbar(im1, ax=ax1, label="Cantidad de eventos")
        fig.colorbar(im2, ax=ax2, label="Cantidad de eventos")
        
        plt.tight_layout()
        fig.subplots_adjust(top=0.9)
        
        # Guardar si se solicita
        if guardar:
            if ruta is None:
                ruta = os.path.join(self.resultados_dir, 
                                   f"heatmap_{equipo_local}_{equipo_visitante}_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
            plt.savefig(ruta, dpi=300, bbox_inches='tight')
            print(f"Heatmap guardado en: {ruta}")
        
        return fig
