"""
Módulo de Análisis de Jugadores Clave
Analiza el impacto individual de jugadores en el rendimiento del equipo
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime, timedelta

class AnalisisJugadoresClave:
    """Clase para análisis detallado de jugadores clave"""
    
    def __init__(self):
        self.posiciones_clave = {
            'portero': {'peso_equipo': 0.20, 'metricas': ['paradas', 'goles_contra', 'distribucion']},
            'defensa_central': {'peso_equipo': 0.25, 'metricas': ['entradas', 'interceptaciones', 'liderazgo']},
            'mediocampista_organizador': {'peso_equipo': 0.30, 'metricas': ['pases', 'recuperaciones', 'vision']},
            'delantero_estrella': {'peso_equipo': 0.35, 'metricas': ['goles', 'asistencias', 'ocasiones']}
        }

    def identificar_jugadores_clave(self, equipo: str, temporada: str = "2024") -> Dict:
        """
        Identifica los jugadores más importantes del equipo
        
        Args:
            equipo: Nombre del equipo
            temporada: Temporada a analizar
            
        Returns:
            Diccionario con jugadores clave identificados
        """
        try:
            # Simular datos de jugadores (en producción vendría de base de datos)
            jugadores_candidatos = self._generar_plantilla_ejemplo(equipo)
            
            # Calcular índice de importancia para cada jugador
            jugadores_con_indice = []
            for jugador in jugadores_candidatos:
                indice_importancia = self._calcular_indice_importancia(jugador)
                jugador['indice_importancia'] = indice_importancia
                jugadores_con_indice.append(jugador)
            
            # Ordenar por importancia
            jugadores_ordenados = sorted(jugadores_con_indice, 
                                       key=lambda x: x['indice_importancia'], 
                                       reverse=True)
            
            # Seleccionar top jugadores clave
            jugadores_clave = jugadores_ordenados[:8]
            
            return {
                'equipo': equipo,
                'temporada': temporada,
                'jugadores_clave': jugadores_clave,
                'distribucion_por_posicion': self._analizar_distribucion_posiciones(jugadores_clave),
                'dependencia_equipo': self._calcular_dependencia_jugadores(jugadores_clave),
                'riesgo_lesiones': self._evaluar_riesgo_lesiones(jugadores_clave),
                'profundidad_plantilla': self._evaluar_profundidad_plantilla(jugadores_candidatos)
            }
            
        except Exception as e:
            return {'error': f'Error identificando jugadores clave: {str(e)}'}

    def analizar_impacto_individual(self, jugador: str, equipo: str, temporada: str = "2024") -> Dict:
        """
        Analiza el impacto individual de un jugador específico
        
        Args:
            jugador: Nombre del jugador
            equipo: Nombre del equipo
            temporada: Temporada a analizar
            
        Returns:
            Diccionario con análisis del impacto del jugador
        """
        try:
            # Simular datos del jugador
            datos_jugador = self._generar_datos_jugador(jugador, equipo)
            
            # Análisis de rendimiento con y sin el jugador
            rendimiento_con_jugador = self._simular_rendimiento_con_jugador()
            rendimiento_sin_jugador = self._simular_rendimiento_sin_jugador()
            
            # Análisis de momentos decisivos
            momentos_decisivos = self._analizar_momentos_decisivos(jugador)
            
            # Análisis de liderazgo e influencia
            liderazgo = self._analizar_liderazgo(jugador)
            
            return {
                'jugador': jugador,
                'equipo': equipo,
                'datos_basicos': datos_jugador,
                'impacto_estadistico': {
                    'con_jugador': rendimiento_con_jugador,
                    'sin_jugador': rendimiento_sin_jugador,
                    'diferencia_impacto': self._calcular_diferencia_impacto(
                        rendimiento_con_jugador, rendimiento_sin_jugador
                    )
                },
                'momentos_decisivos': momentos_decisivos,
                'liderazgo': liderazgo,
                'valor_mercado_estimado': self._estimar_valor_mercado(datos_jugador),
                'recomendaciones': self._generar_recomendaciones_jugador(datos_jugador)
            }
            
        except Exception as e:
            return {'error': f'Error analizando jugador {jugador}: {str(e)}'}

    def comparar_jugadores(self, jugador1: str, jugador2: str, 
                          equipo1: str = None, equipo2: str = None) -> Dict:
        """
        Compara dos jugadores de la misma posición
        
        Args:
            jugador1: Primer jugador
            jugador2: Segundo jugador
            equipo1: Equipo del primer jugador
            equipo2: Equipo del segundo jugador
            
        Returns:
            Diccionario con comparación detallada
        """
        try:
            # Obtener datos de ambos jugadores
            datos1 = self._generar_datos_jugador(jugador1, equipo1 or 'Equipo A')
            datos2 = self._generar_datos_jugador(jugador2, equipo2 or 'Equipo B')
            
            # Verificar que sean de la misma posición
            if datos1['posicion'] != datos2['posicion']:
                return {'error': 'Los jugadores deben ser de la misma posición para comparar'}
            
            # Comparación por categorías
            comparacion = {
                'jugadores': [jugador1, jugador2],
                'posicion': datos1['posicion'],
                'metricas_ofensivas': self._comparar_metricas_ofensivas(datos1, datos2),
                'metricas_defensivas': self._comparar_metricas_defensivas(datos1, datos2),
                'metricas_fisicas': self._comparar_metricas_fisicas(datos1, datos2),
                'metricas_mentales': self._comparar_metricas_mentales(datos1, datos2),
                'rendimiento_general': self._comparar_rendimiento_general(datos1, datos2),
                'veredicto': self._determinar_mejor_jugador(datos1, datos2),
                'fortalezas_relativas': {
                    jugador1: self._identificar_fortalezas_relativas(datos1, datos2),
                    jugador2: self._identificar_fortalezas_relativas(datos2, datos1)
                }
            }
            
            return comparacion
            
        except Exception as e:
            return {'error': f'Error comparando jugadores: {str(e)}'}

    def analizar_forma_fisica_actual(self, jugador: str, equipo: str) -> Dict:
        """
        Analiza la forma física actual de un jugador
        
        Args:
            jugador: Nombre del jugador
            equipo: Nombre del equipo
            
        Returns:
            Diccionario con análisis de forma física
        """
        try:
            # Simular datos de forma física
            forma_fisica = {
                'condicion_general': np.random.uniform(6.0, 9.5),
                'resistencia': np.random.uniform(6.5, 9.0),
                'velocidad': np.random.uniform(5.5, 9.5),
                'fuerza': np.random.uniform(6.0, 9.0),
                'agilidad': np.random.uniform(6.5, 9.5),
                'recuperacion': np.random.uniform(6.0, 9.0)
            }
            
            # Análisis de carga de trabajo
            carga_trabajo = self._analizar_carga_trabajo(jugador)
            
            # Riesgo de lesión
            riesgo_lesion = self._calcular_riesgo_lesion(forma_fisica, carga_trabajo)
            
            # Rendimiento reciente
            rendimiento_reciente = self._analizar_rendimiento_reciente(jugador)
            
            return {
                'jugador': jugador,
                'equipo': equipo,
                'forma_fisica': forma_fisica,
                'carga_trabajo': carga_trabajo,
                'riesgo_lesion': riesgo_lesion,
                'rendimiento_reciente': rendimiento_reciente,
                'recomendaciones_fisicas': self._generar_recomendaciones_fisicas(forma_fisica, carga_trabajo),
                'prediccion_rendimiento': self._predecir_rendimiento_proximo(forma_fisica, rendimiento_reciente)
            }
            
        except Exception as e:
            return {'error': f'Error analizando forma física: {str(e)}'}

    def analizar_enfrentamientos_directos(self, jugador1: str, jugador2: str, 
                                        historico_partidos: List[Dict] = None) -> Dict:
        """
        Analiza los enfrentamientos directos entre dos jugadores
        
        Args:
            jugador1: Primer jugador
            jugador2: Segundo jugador
            historico_partidos: Lista de partidos históricos
            
        Returns:
            Diccionario con análisis de enfrentamientos
        """
        try:
            # Simular historial de enfrentamientos
            enfrentamientos = self._simular_enfrentamientos_directos(jugador1, jugador2)
            
            # Análisis de tendencias
            tendencias = self._analizar_tendencias_enfrentamientos(enfrentamientos)
            
            # Factores psicológicos
            factores_psicologicos = self._analizar_factores_psicologicos(jugador1, jugador2)
            
            return {
                'jugadores': [jugador1, jugador2],
                'historial_enfrentamientos': enfrentamientos,
                'estadisticas_generales': {
                    'partidos_jugados': len(enfrentamientos),
                    'victorias_jugador1': sum(1 for e in enfrentamientos if e['ganador'] == jugador1),
                    'victorias_jugador2': sum(1 for e in enfrentamientos if e['ganador'] == jugador2),
                    'empates': sum(1 for e in enfrentamientos if e['ganador'] == 'Empate')
                },
                'tendencias': tendencias,
                'factores_psicologicos': factores_psicologicos,
                'prediccion_proximo_enfrentamiento': self._predecir_proximo_enfrentamiento(
                    enfrentamientos, tendencias
                )
            }
            
        except Exception as e:
            return {'error': f'Error analizando enfrentamientos: {str(e)}'}

    def evaluar_importancia_partido(self, jugador: str, tipo_partido: str, 
                                  contexto: Dict = None) -> Dict:
        """
        Evalúa cómo un jugador se desempeña en partidos importantes
        
        Args:
            jugador: Nombre del jugador
            tipo_partido: Tipo de partido (final, semifinal, clásico, etc.)
            contexto: Contexto adicional del partido
            
        Returns:
            Diccionario con evaluación de rendimiento en partidos importantes
        """
        try:
            # Simular historial en partidos importantes
            historial_importantes = self._simular_historial_partidos_importantes(jugador, tipo_partido)
            
            # Análisis de presión
            manejo_presion = self._analizar_manejo_presion(jugador)
            
            # Rendimiento bajo presión
            rendimiento_presion = self._calcular_rendimiento_bajo_presion(historial_importantes)
            
            return {
                'jugador': jugador,
                'tipo_partido': tipo_partido,
                'historial_partidos_importantes': historial_importantes,
                'manejo_presion': manejo_presion,
                'rendimiento_bajo_presion': rendimiento_presion,
                'factores_determinantes': self._identificar_factores_determinantes(
                    historial_importantes, manejo_presion
                ),
                'prediccion_rendimiento': self._predecir_rendimiento_partido_importante(
                    rendimiento_presion, manejo_presion, contexto or {}
                )
            }
            
        except Exception as e:
            return {'error': f'Error evaluando importancia del partido: {str(e)}'}

    # Métodos auxiliares para generación de datos
    def _generar_plantilla_ejemplo(self, equipo: str) -> List[Dict]:
        """Genera una plantilla de ejemplo con jugadores"""
        plantilla = []
        posiciones = ['Portero', 'Defensa', 'Mediocampo', 'Delantero']
        
        for i in range(20):  # 20 jugadores por plantilla
            jugador = {
                'nombre': f'Jugador {i+1}',
                'posicion': np.random.choice(posiciones),
                'edad': np.random.randint(18, 35),
                'partidos_jugados': np.random.randint(15, 35),
                'goles': np.random.randint(0, 20),
                'asistencias': np.random.randint(0, 15),
                'calificacion_media': np.random.uniform(6.0, 8.5),
                'valor_mercado': np.random.uniform(5, 100),  # Millones
                'importancia_tactica': np.random.uniform(5.0, 10.0)
            }
            plantilla.append(jugador)
        
        return plantilla

    def _calcular_indice_importancia(self, jugador: Dict) -> float:
        """Calcula el índice de importancia de un jugador"""
        # Factores que determinan importancia
        factor_partidos = min(jugador['partidos_jugados'] / 30, 1.0)
        factor_rendimiento = jugador['calificacion_media'] / 10
        factor_contribucion = (jugador['goles'] + jugador['asistencias']) / 25
        factor_tactico = jugador['importancia_tactica'] / 10
        
        # Peso por posición
        peso_posicion = 1.0
        if jugador['posicion'] in ['Mediocampo', 'Delantero']:
            peso_posicion = 1.2
        elif jugador['posicion'] == 'Defensa':
            peso_posicion = 1.1
        
        indice = (factor_partidos * 0.3 + 
                 factor_rendimiento * 0.3 + 
                 factor_contribucion * 0.2 + 
                 factor_tactico * 0.2) * peso_posicion
        
        return round(indice, 3)

    def _generar_datos_jugador(self, nombre: str, equipo: str) -> Dict:
        """Genera datos detallados de un jugador"""
        posiciones = ['Portero', 'Defensa', 'Mediocampo', 'Delantero']
        
        return {
            'nombre': nombre,
            'equipo': equipo,
            'posicion': np.random.choice(posiciones),
            'edad': np.random.randint(20, 33),
            'nacionalidad': np.random.choice(['España', 'Brasil', 'Argentina', 'Francia', 'Alemania']),
            'estadisticas': {
                'partidos': np.random.randint(25, 35),
                'goles': np.random.randint(0, 25),
                'asistencias': np.random.randint(0, 15),
                'tarjetas_amarillas': np.random.randint(2, 8),
                'tarjetas_rojas': np.random.randint(0, 2),
                'minutos_jugados': np.random.randint(2000, 3000)
            },
            'habilidades': {
                'tecnica': np.random.uniform(6.0, 9.5),
                'fisica': np.random.uniform(6.5, 9.0),
                'mental': np.random.uniform(6.0, 9.5),
                'tactica': np.random.uniform(6.5, 9.0)
            },
            'valor_mercado': np.random.uniform(10, 150),
            'salario': np.random.uniform(2, 25)  # Millones anuales
        }

    def _simular_rendimiento_con_jugador(self) -> Dict:
        """Simula el rendimiento del equipo con el jugador"""
        return {
            'partidos': np.random.randint(20, 30),
            'victorias': np.random.randint(12, 20),
            'empates': np.random.randint(3, 8),
            'derrotas': np.random.randint(2, 8),
            'goles_favor': np.random.randint(35, 65),
            'goles_contra': np.random.randint(20, 45),
            'puntos_por_partido': np.random.uniform(1.8, 2.5)
        }

    def _simular_rendimiento_sin_jugador(self) -> Dict:
        """Simula el rendimiento del equipo sin el jugador"""
        return {
            'partidos': np.random.randint(8, 15),
            'victorias': np.random.randint(3, 8),
            'empates': np.random.randint(2, 5),
            'derrotas': np.random.randint(2, 7),
            'goles_favor': np.random.randint(10, 25),
            'goles_contra': np.random.randint(8, 20),
            'puntos_por_partido': np.random.uniform(1.2, 2.0)
        }

    def _calcular_diferencia_impacto(self, con_jugador: Dict, sin_jugador: Dict) -> Dict:
        """Calcula la diferencia de impacto del jugador"""
        return {
            'diferencia_puntos_partido': round(
                con_jugador['puntos_por_partido'] - sin_jugador['puntos_por_partido'], 2
            ),
            'diferencia_goles_favor': round(
                (con_jugador['goles_favor'] / con_jugador['partidos']) - 
                (sin_jugador['goles_favor'] / sin_jugador['partidos']), 2
            ),
            'diferencia_goles_contra': round(
                (sin_jugador['goles_contra'] / sin_jugador['partidos']) - 
                (con_jugador['goles_contra'] / con_jugador['partidos']), 2
            ),
            'impacto_general': 'Alto' if con_jugador['puntos_por_partido'] - sin_jugador['puntos_por_partido'] > 0.5 else 'Medio'
        }

    def _analizar_momentos_decisivos(self, jugador: str) -> Dict:
        """Analiza la actuación en momentos decisivos"""
        return {
            'goles_minuto_90': np.random.randint(0, 5),
            'asistencias_decisivas': np.random.randint(0, 8),
            'penaltis_convertidos': f"{np.random.randint(3, 8)}/{np.random.randint(3, 10)}",
            'actuacion_clasicos': np.random.uniform(6.5, 9.0),
            'rendimiento_eliminatorias': np.random.uniform(6.0, 9.5),
            'liderazgo_momentos_criticos': np.random.uniform(6.5, 9.5)
        }

    def _analizar_liderazgo(self, jugador: str) -> Dict:
        """Analiza las cualidades de liderazgo"""
        return {
            'es_capitan': np.random.choice([True, False]),
            'experiencia_internacional': np.random.randint(0, 80),
            'influencia_vestuario': np.random.uniform(6.0, 9.5),
            'comunicacion_campo': np.random.uniform(6.5, 9.0),
            'ejemplo_profesional': np.random.uniform(7.0, 9.5),
            'capacidad_motivacion': np.random.uniform(6.0, 9.0)
        }

    def _estimar_valor_mercado(self, datos: Dict) -> Dict:
        """Estima el valor de mercado del jugador"""
        edad = datos['edad']
        goles = datos['estadisticas']['goles']
        asistencias = datos['estadisticas']['asistencias']
        
        # Factores que afectan el valor
        factor_edad = 1.0 if edad <= 25 else (1.0 - (edad - 25) * 0.05)
        factor_rendimiento = (goles + asistencias) / 20
        
        valor_base = datos['valor_mercado']
        valor_estimado = valor_base * factor_edad * (1 + factor_rendimiento)
        
        return {
            'valor_actual': round(valor_estimado, 1),
            'tendencia': 'Alza' if factor_edad > 0.8 and factor_rendimiento > 0.5 else 'Baja',
            'factores_valor': {
                'edad': f"{'Favorable' if factor_edad > 0.8 else 'Desfavorable'}",
                'rendimiento': f"{'Alto' if factor_rendimiento > 0.7 else 'Moderado'}",
                'posicion': datos['posicion']
            }
        }

    # Métodos de comparación
    def _comparar_metricas_ofensivas(self, datos1: Dict, datos2: Dict) -> Dict:
        """Compara métricas ofensivas entre dos jugadores"""
        return {
            'goles': {
                'jugador1': datos1['estadisticas']['goles'],
                'jugador2': datos2['estadisticas']['goles'],
                'ventaja': datos1['nombre'] if datos1['estadisticas']['goles'] > datos2['estadisticas']['goles'] else datos2['nombre']
            },
            'asistencias': {
                'jugador1': datos1['estadisticas']['asistencias'],
                'jugador2': datos2['estadisticas']['asistencias'],
                'ventaja': datos1['nombre'] if datos1['estadisticas']['asistencias'] > datos2['estadisticas']['asistencias'] else datos2['nombre']
            },
            'contribucion_total': {
                'jugador1': datos1['estadisticas']['goles'] + datos1['estadisticas']['asistencias'],
                'jugador2': datos2['estadisticas']['goles'] + datos2['estadisticas']['asistencias'],
            }
        }

    def _comparar_metricas_defensivas(self, datos1: Dict, datos2: Dict) -> Dict:
        """Compara métricas defensivas entre dos jugadores"""
        # Simular métricas defensivas
        defensiva1 = {
            'entradas': np.random.randint(40, 80),
            'interceptaciones': np.random.randint(30, 70),
            'despejes': np.random.randint(50, 120)
        }
        defensiva2 = {
            'entradas': np.random.randint(40, 80),
            'interceptaciones': np.random.randint(30, 70),
            'despejes': np.random.randint(50, 120)
        }
        
        return {
            'entradas': {
                'jugador1': defensiva1['entradas'],
                'jugador2': defensiva2['entradas'],
                'ventaja': datos1['nombre'] if defensiva1['entradas'] > defensiva2['entradas'] else datos2['nombre']
            },
            'interceptaciones': {
                'jugador1': defensiva1['interceptaciones'],
                'jugador2': defensiva2['interceptaciones'],
                'ventaja': datos1['nombre'] if defensiva1['interceptaciones'] > defensiva2['interceptaciones'] else datos2['nombre']
            }
        }

    def _comparar_metricas_fisicas(self, datos1: Dict, datos2: Dict) -> Dict:
        """Compara métricas físicas entre dos jugadores"""
        return {
            'condicion_fisica': {
                'jugador1': datos1['habilidades']['fisica'],
                'jugador2': datos2['habilidades']['fisica'],
                'ventaja': datos1['nombre'] if datos1['habilidades']['fisica'] > datos2['habilidades']['fisica'] else datos2['nombre']
            },
            'edad': {
                'jugador1': datos1['edad'],
                'jugador2': datos2['edad'],
                'ventaja': datos1['nombre'] if datos1['edad'] < datos2['edad'] else datos2['nombre']  # Menor edad es ventaja
            }
        }

    def _comparar_metricas_mentales(self, datos1: Dict, datos2: Dict) -> Dict:
        """Compara métricas mentales entre dos jugadores"""
        return {
            'fortaleza_mental': {
                'jugador1': datos1['habilidades']['mental'],
                'jugador2': datos2['habilidades']['mental'],
                'ventaja': datos1['nombre'] if datos1['habilidades']['mental'] > datos2['habilidades']['mental'] else datos2['nombre']
            },
            'vision_tactica': {
                'jugador1': datos1['habilidades']['tactica'],
                'jugador2': datos2['habilidades']['tactica'],
                'ventaja': datos1['nombre'] if datos1['habilidades']['tactica'] > datos2['habilidades']['tactica'] else datos2['nombre']
            }
        }

    def _comparar_rendimiento_general(self, datos1: Dict, datos2: Dict) -> Dict:
        """Compara el rendimiento general"""
        # Calcular índice de rendimiento general
        def calcular_indice(datos):
            contribucion = datos['estadisticas']['goles'] + datos['estadisticas']['asistencias']
            minutos = datos['estadisticas']['minutos_jugados']
            habilidad_promedio = sum(datos['habilidades'].values()) / len(datos['habilidades'])
            
            return (contribucion / 30) * 0.4 + (minutos / 3000) * 0.3 + (habilidad_promedio / 10) * 0.3
        
        indice1 = calcular_indice(datos1)
        indice2 = calcular_indice(datos2)
        
        return {
            'indice_jugador1': round(indice1, 3),
            'indice_jugador2': round(indice2, 3),
            'mejor_general': datos1['nombre'] if indice1 > indice2 else datos2['nombre'],
            'diferencia': abs(indice1 - indice2)
        }

    def _determinar_mejor_jugador(self, datos1: Dict, datos2: Dict) -> Dict:
        """Determina qué jugador es mejor globalmente"""
        # Análisis simple basado en múltiples factores
        puntos1 = 0
        puntos2 = 0
        
        # Contribución ofensiva
        contrib1 = datos1['estadisticas']['goles'] + datos1['estadisticas']['asistencias']
        contrib2 = datos2['estadisticas']['goles'] + datos2['estadisticas']['asistencias']
        if contrib1 > contrib2:
            puntos1 += 1
        else:
            puntos2 += 1
        
        # Habilidades promedio
        hab1 = sum(datos1['habilidades'].values()) / len(datos1['habilidades'])
        hab2 = sum(datos2['habilidades'].values()) / len(datos2['habilidades'])
        if hab1 > hab2:
            puntos1 += 1
        else:
            puntos2 += 1
        
        # Edad (menor es mejor)
        if datos1['edad'] < datos2['edad']:
            puntos1 += 1
        else:
            puntos2 += 1
        
        # Valor de mercado
        if datos1['valor_mercado'] > datos2['valor_mercado']:
            puntos1 += 1
        else:
            puntos2 += 1
        
        if puntos1 > puntos2:
            return {
                'mejor_jugador': datos1['nombre'],
                'puntuacion': f"{puntos1}-{puntos2}",
                'conclusion': 'Victoria clara' if puntos1 - puntos2 > 1 else 'Victoria ajustada'
            }
        elif puntos2 > puntos1:
            return {
                'mejor_jugador': datos2['nombre'],
                'puntuacion': f"{puntos2}-{puntos1}",
                'conclusion': 'Victoria clara' if puntos2 - puntos1 > 1 else 'Victoria ajustada'
            }
        else:
            return {
                'mejor_jugador': 'Empate',
                'puntuacion': f"{puntos1}-{puntos2}",
                'conclusion': 'Rendimiento muy equilibrado'
            }

    def _identificar_fortalezas_relativas(self, datos_propio: Dict, datos_rival: Dict) -> List[str]:
        """Identifica las fortalezas de un jugador respecto a otro"""
        fortalezas = []
        
        # Comparar estadísticas
        if datos_propio['estadisticas']['goles'] > datos_rival['estadisticas']['goles']:
            fortalezas.append('Mayor capacidad goleadora')
        if datos_propio['estadisticas']['asistencias'] > datos_rival['estadisticas']['asistencias']:
            fortalezas.append('Mayor creatividad ofensiva')
        if datos_propio['edad'] < datos_rival['edad']:
            fortalezas.append('Menor edad y mayor proyección')
        if datos_propio['habilidades']['fisica'] > datos_rival['habilidades']['fisica']:
            fortalezas.append('Superior condición física')
        if datos_propio['habilidades']['mental'] > datos_rival['habilidades']['mental']:
            fortalezas.append('Mayor fortaleza mental')
        
        return fortalezas if fortalezas else ['Perfil equilibrado']

    # Métodos auxiliares adicionales
    def _analizar_distribucion_posiciones(self, jugadores: List[Dict]) -> Dict:
        """Analiza la distribución de jugadores clave por posición"""
        distribucion = {}
        for jugador in jugadores:
            pos = jugador['posicion']
            distribucion[pos] = distribucion.get(pos, 0) + 1
        
        return distribucion

    def _calcular_dependencia_jugadores(self, jugadores: List[Dict]) -> Dict:
        """Calcula el nivel de dependencia del equipo de estos jugadores"""
        dependencia_total = sum(j['indice_importancia'] for j in jugadores)
        
        nivel_dependencia = 'Alta' if dependencia_total > 6.0 else 'Media' if dependencia_total > 4.0 else 'Baja'
        
        return {
            'nivel': nivel_dependencia,
            'puntuacion': round(dependencia_total, 2),
            'jugador_mas_importante': max(jugadores, key=lambda x: x['indice_importancia'])['nombre'],
            'equilibrio_dependencia': 'Equilibrado' if len(jugadores) > 5 else 'Concentrado'
        }

    def _evaluar_riesgo_lesiones(self, jugadores: List[Dict]) -> Dict:
        """Evalúa el riesgo si varios jugadores clave se lesionan"""
        riesgo_por_jugador = {}
        
        for jugador in jugadores:
            # Factores de riesgo simulados
            edad = jugador['edad']
            partidos = jugador['partidos_jugados']
            
            factor_edad = 1.0 if edad < 30 else 1.2
            factor_carga = 1.0 if partidos < 30 else 1.1
            
            riesgo = (factor_edad + factor_carga - 1) * jugador['indice_importancia']
            riesgo_por_jugador[jugador['nombre']] = round(riesgo, 2)
        
        riesgo_promedio = sum(riesgo_por_jugador.values()) / len(riesgo_por_jugador)
        
        return {
            'riesgo_promedio': round(riesgo_promedio, 2),
            'jugadores_alto_riesgo': [j for j, r in riesgo_por_jugador.items() if r > 1.5],
            'recomendacion': 'Rotar más jugadores' if riesgo_promedio > 1.3 else 'Riesgo controlado'
        }

    def _evaluar_profundidad_plantilla(self, plantilla_completa: List[Dict]) -> Dict:
        """Evalúa la profundidad de la plantilla"""
        # Contar jugadores por posición con calificación > 7.0
        jugadores_calidad = [j for j in plantilla_completa if j['calificacion_media'] > 7.0]
        
        distribucion_calidad = {}
        for jugador in jugadores_calidad:
            pos = jugador['posicion']
            distribucion_calidad[pos] = distribucion_calidad.get(pos, 0) + 1
        
        # Evaluar profundidad
        posiciones_problema = [pos for pos, count in distribucion_calidad.items() if count < 2]
        
        return {
            'jugadores_calidad_total': len(jugadores_calidad),
            'distribucion_por_posicion': distribucion_calidad,
            'posiciones_problema': posiciones_problema,
            'nivel_profundidad': 'Alta' if len(posiciones_problema) == 0 else 'Media' if len(posiciones_problema) < 2 else 'Baja'
        }

    def _generar_recomendaciones_jugador(self, datos: Dict) -> List[str]:
        """Genera recomendaciones para el jugador"""
        recomendaciones = []
        
        edad = datos['edad']
        goles = datos['estadisticas']['goles']
        asistencias = datos['estadisticas']['asistencias']
        
        if edad > 30:
            recomendaciones.append('Considerar rotación para preservar al jugador')
        if goles < 5 and datos['posicion'] == 'Delantero':
            recomendaciones.append('Trabajar en definición y movimientos en área')
        if asistencias < 3 and datos['posicion'] == 'Mediocampo':
            recomendaciones.append('Desarrollar más creatividad y pase final')
        if datos['estadisticas']['tarjetas_amarillas'] > 6:
            recomendaciones.append('Mejorar disciplina para evitar suspensiones')
            
        return recomendaciones if recomendaciones else ['Mantener nivel actual de rendimiento']

    # Métodos para análisis de forma física
    def _analizar_carga_trabajo(self, jugador: str) -> Dict:
        """Analiza la carga de trabajo del jugador"""
        return {
            'minutos_ultimos_5_partidos': np.random.randint(400, 450),
            'partidos_consecutivos': np.random.randint(3, 8),
            'intensidad_promedio': np.random.uniform(75, 95),  # %
            'distancia_recorrida_promedio': np.random.uniform(9.5, 12.5),  # km
            'sprints_por_partido': np.random.randint(15, 35),
            'nivel_fatiga': np.random.choice(['Bajo', 'Medio', 'Alto'])
        }

    def _calcular_riesgo_lesion(self, forma_fisica: Dict, carga_trabajo: Dict) -> Dict:
        """Calcula el riesgo de lesión del jugador"""
        # Factores de riesgo
        factor_condicion = 1.0 - (forma_fisica['condicion_general'] - 5) / 5
        factor_fatiga = {'Bajo': 0.1, 'Medio': 0.3, 'Alto': 0.6}[carga_trabajo['nivel_fatiga']]
        factor_carga = min(carga_trabajo['minutos_ultimos_5_partidos'] / 400, 1.2) - 1
        
        riesgo_total = (factor_condicion + factor_fatiga + factor_carga) / 3
        
        nivel_riesgo = 'Alto' if riesgo_total > 0.6 else 'Medio' if riesgo_total > 0.3 else 'Bajo'
        
        return {
            'nivel': nivel_riesgo,
            'puntuacion': round(riesgo_total, 2),
            'factores_principales': self._identificar_factores_riesgo(factor_condicion, factor_fatiga, factor_carga),
            'recomendacion_descanso': 'Necesario' if riesgo_total > 0.5 else 'Opcional'
        }

    def _identificar_factores_riesgo(self, condicion: float, fatiga: float, carga: float) -> List[str]:
        """Identifica los principales factores de riesgo"""
        factores = []
        
        if condicion > 0.3:
            factores.append('Condición física subóptima')
        if fatiga > 0.4:
            factores.append('Nivel de fatiga elevado')
        if carga > 0.2:
            factores.append('Sobrecarga de minutos')
            
        return factores if factores else ['Sin factores de riesgo significativos']

    def _analizar_rendimiento_reciente(self, jugador: str) -> Dict:
        """Analiza el rendimiento en los últimos 5 partidos"""
        return {
            'partidos_analizados': 5,
            'calificaciones': [np.random.uniform(6.0, 8.5) for _ in range(5)],
            'goles_recientes': np.random.randint(0, 4),
            'asistencias_recientes': np.random.randint(0, 3),
            'tendencia': np.random.choice(['Ascendente', 'Estable', 'Descendente']),
            'consistencia': np.random.uniform(6.0, 9.0)
        }

    def _generar_recomendaciones_fisicas(self, forma_fisica: Dict, carga_trabajo: Dict) -> List[str]:
        """Genera recomendaciones físicas para el jugador"""
        recomendaciones = []
        
        if forma_fisica['resistencia'] < 7.0:
            recomendaciones.append('Trabajar resistencia cardiovascular')
        if forma_fisica['fuerza'] < 7.0:
            recomendaciones.append('Fortalecer trabajo de gimnasio')
        if carga_trabajo['nivel_fatiga'] == 'Alto':
            recomendaciones.append('Periodo de descanso recomendado')
        if forma_fisica['recuperacion'] < 7.0:
            recomendaciones.append('Mejorar protocolos de recuperación')
            
        return recomendaciones if recomendaciones else ['Mantener programa actual de preparación física']

    def _predecir_rendimiento_proximo(self, forma_fisica: Dict, rendimiento_reciente: Dict) -> Dict:
        """Predice el rendimiento en los próximos partidos"""
        # Calcular índice de predicción
        indice_fisico = sum(forma_fisica.values()) / len(forma_fisica)
        indice_reciente = sum(rendimiento_reciente['calificaciones']) / len(rendimiento_reciente['calificaciones'])
        
        prediccion = (indice_fisico + indice_reciente) / 2
        
        return {
            'calificacion_esperada': round(prediccion, 1),
            'confianza_prediccion': np.random.uniform(70, 90),
            'factores_positivos': self._identificar_factores_positivos(forma_fisica, rendimiento_reciente),
            'areas_atencion': self._identificar_areas_atencion(forma_fisica, rendimiento_reciente)
        }

    def _identificar_factores_positivos(self, forma_fisica: Dict, rendimiento: Dict) -> List[str]:
        """Identifica factores positivos para el rendimiento futuro"""
        factores = []
        
        if forma_fisica['condicion_general'] > 8.0:
            factores.append('Excelente condición física')
        if rendimiento['tendencia'] == 'Ascendente':
            factores.append('Tendencia de rendimiento positiva')
        if rendimiento['consistencia'] > 8.0:
            factores.append('Alta consistencia en el rendimiento')
            
        return factores if factores else ['Rendimiento estable esperado']

    def _identificar_areas_atencion(self, forma_fisica: Dict, rendimiento: Dict) -> List[str]:
        """Identifica áreas que requieren atención"""
        areas = []
        
        if forma_fisica['velocidad'] < 7.0:
            areas.append('Velocidad por debajo del óptimo')
        if rendimiento['tendencia'] == 'Descendente':
            areas.append('Tendencia negativa en rendimiento')
        if forma_fisica['recuperacion'] < 7.0:
            areas.append('Capacidad de recuperación limitada')
            
        return areas if areas else ['Sin áreas críticas identificadas']

    # Métodos para enfrentamientos directos
    def _simular_enfrentamientos_directos(self, jugador1: str, jugador2: str) -> List[Dict]:
        """Simula un historial de enfrentamientos directos"""
        enfrentamientos = []
        num_enfrentamientos = np.random.randint(5, 12)
        
        for i in range(num_enfrentamientos):
            ganador = np.random.choice([jugador1, jugador2, 'Empate'], p=[0.4, 0.4, 0.2])
            enfrentamientos.append({
                'fecha': f'2024-{np.random.randint(1, 12):02d}-{np.random.randint(1, 28):02d}',
                'competicion': np.random.choice(['Liga', 'Copa', 'Champions']),
                'ganador': ganador,
                'estadisticas_j1': {
                    'goles': np.random.randint(0, 2),
                    'asistencias': np.random.randint(0, 1),
                    'calificacion': np.random.uniform(6.0, 8.5)
                },
                'estadisticas_j2': {
                    'goles': np.random.randint(0, 2),
                    'asistencias': np.random.randint(0, 1),
                    'calificacion': np.random.uniform(6.0, 8.5)
                }
            })
        
        return enfrentamientos

    def _analizar_tendencias_enfrentamientos(self, enfrentamientos: List[Dict]) -> Dict:
        """Analiza tendencias en los enfrentamientos"""
        if not enfrentamientos:
            return {'tendencia': 'Sin datos suficientes'}
        
        # Últimos 3 enfrentamientos
        ultimos_3 = enfrentamientos[-3:] if len(enfrentamientos) >= 3 else enfrentamientos
        
        ganadores_recientes = [e['ganador'] for e in ultimos_3]
        
        return {
            'ultimos_3_resultados': ganadores_recientes,
            'tendencia_reciente': 'Favorable J1' if ganadores_recientes.count(enfrentamientos[0]['estadisticas_j1']) > 1 else 'Equilibrada',
            'promedio_goles_j1': round(sum(e['estadisticas_j1']['goles'] for e in enfrentamientos) / len(enfrentamientos), 1),
            'promedio_goles_j2': round(sum(e['estadisticas_j2']['goles'] for e in enfrentamientos) / len(enfrentamientos), 1),
            'calificacion_promedio_j1': round(sum(e['estadisticas_j1']['calificacion'] for e in enfrentamientos) / len(enfrentamientos), 1),
            'calificacion_promedio_j2': round(sum(e['estadisticas_j2']['calificacion'] for e in enfrentamientos) / len(enfrentamientos), 1)
        }

    def _analizar_factores_psicologicos(self, jugador1: str, jugador2: str) -> Dict:
        """Analiza factores psicológicos del enfrentamiento"""
        return {
            'ventaja_psicologica': np.random.choice([jugador1, jugador2, 'Neutra']),
            'factor_experiencia': np.random.choice([jugador1, jugador2, 'Equilibrada']),
            'presion_mediatica': np.random.choice(['Alta', 'Media', 'Baja']),
            'importancia_historica': np.random.choice(['Alta', 'Media', 'Baja']),
            'motivacion_especial': np.random.choice([True, False])
        }

    def _predecir_proximo_enfrentamiento(self, enfrentamientos: List[Dict], tendencias: Dict) -> Dict:
        """Predice el resultado del próximo enfrentamiento"""
        if not enfrentamientos:
            return {'prediccion': 'Insuficientes datos históricos'}
        
        # Análisis simple basado en tendencias
        jugador1_victorias = sum(1 for e in enfrentamientos if 'J1' in e['ganador'])
        jugador2_victorias = sum(1 for e in enfrentamientos if 'J2' in e['ganador'])
        
        favorito = 'Jugador 1' if jugador1_victorias > jugador2_victorias else 'Jugador 2' if jugador2_victorias > jugador1_victorias else 'Equilibrado'
        
        return {
            'favorito': favorito,
            'confianza': np.random.uniform(60, 85),
            'factores_decisivos': ['Forma actual', 'Motivación', 'Contexto del partido'],
            'resultado_probable': np.random.choice(['Victoria J1', 'Victoria J2', 'Empate técnico'])
        }

    # Métodos para análisis en partidos importantes
    def _simular_historial_partidos_importantes(self, jugador: str, tipo_partido: str) -> List[Dict]:
        """Simula historial en partidos importantes"""
        partidos = []
        num_partidos = np.random.randint(3, 8)
        
        for i in range(num_partidos):
            partidos.append({
                'fecha': f'2024-{np.random.randint(1, 12):02d}-{np.random.randint(1, 28):02d}',
                'tipo': tipo_partido,
                'rival': f'Rival {i+1}',
                'resultado_equipo': np.random.choice(['Victoria', 'Empate', 'Derrota']),
                'calificacion_individual': np.random.uniform(5.5, 9.0),
                'goles': np.random.randint(0, 3),
                'asistencias': np.random.randint(0, 2),
                'momentos_clave': np.random.choice([True, False])
            })
        
        return partidos

    def _analizar_manejo_presion(self, jugador: str) -> Dict:
        """Analiza cómo maneja la presión el jugador"""
        return {
            'experiencia_grandes_partidos': np.random.randint(5, 25),
            'rendimiento_bajo_presion': np.random.uniform(6.0, 9.0),
            'estabilidad_emocional': np.random.uniform(6.5, 9.5),
            'liderazgo_momentos_criticos': np.random.uniform(6.0, 9.0),
            'concentracion': np.random.uniform(7.0, 9.5),
            'resistencia_criticas': np.random.uniform(6.0, 9.0)
        }

    def _calcular_rendimiento_bajo_presion(self, historial: List[Dict]) -> Dict:
        """Calcula el rendimiento bajo presión"""
        if not historial:
            return {'rendimiento': 'Sin datos suficientes'}
        
        calificacion_promedio = sum(p['calificacion_individual'] for p in historial) / len(historial)
        goles_importantes = sum(p['goles'] for p in historial)
        momentos_decisivos = sum(1 for p in historial if p['momentos_clave'])
        
        return {
            'calificacion_promedio_importantes': round(calificacion_promedio, 1),
            'goles_en_partidos_importantes': goles_importantes,
            'momentos_decisivos': momentos_decisivos,
            'porcentaje_aparicion': round((momentos_decisivos / len(historial)) * 100, 1),
            'nivel_clutch': 'Alto' if momentos_decisivos >= len(historial) * 0.6 else 'Medio' if momentos_decisivos >= len(historial) * 0.3 else 'Bajo'
        }

    def _identificar_factores_determinantes(self, historial: List[Dict], presion: Dict) -> List[str]:
        """Identifica factores determinantes en partidos importantes"""
        factores = []
        
        if presion['experiencia_grandes_partidos'] > 15:
            factores.append('Amplia experiencia en partidos importantes')
        if presion['rendimiento_bajo_presion'] > 8.0:
            factores.append('Excelente rendimiento bajo presión')
        
        goles_importantes = sum(p['goles'] for p in historial)
        if goles_importantes >= len(historial) * 0.5:
            factores.append('Capacidad goleadora en momentos clave')
        
        if presion['liderazgo_momentos_criticos'] > 8.0:
            factores.append('Liderazgo en situaciones críticas')
            
        return factores if factores else ['Rendimiento estándar en partidos importantes']

    def _predecir_rendimiento_partido_importante(self, rendimiento_presion: Dict, 
                                               manejo_presion: Dict, contexto: Dict) -> Dict:
        """Predice el rendimiento en un partido importante"""
        # Factores de predicción
        factor_experiencia = min(manejo_presion['experiencia_grandes_partidos'] / 20, 1.0)
        factor_presion = manejo_presion['rendimiento_bajo_presion'] / 10
        factor_historial = rendimiento_presion.get('calificacion_promedio_importantes', 7.0) / 10
        
        prediccion_base = (factor_experiencia + factor_presion + factor_historial) / 3
        
        # Ajustes por contexto
        if contexto.get('importancia') == 'Final':
            prediccion_base *= 0.95  # Ligera reducción por máxima presión
        elif contexto.get('importancia') == 'Semifinal':
            prediccion_base *= 0.98
        
        if contexto.get('apoyo_aficion') == 'Alto':
            prediccion_base *= 1.02
        
        calificacion_esperada = prediccion_base * 10
        
        return {
            'calificacion_esperada': round(calificacion_esperada, 1),
            'probabilidad_momento_decisivo': round(rendimiento_presion.get('porcentaje_aparicion', 30) / 100, 2),
            'confianza_prediccion': np.random.uniform(70, 90),
            'factores_clave': ['Experiencia previa', 'Manejo de presión', 'Contexto del partido'],
            'recomendacion_tecnica': 'Darle responsabilidades clave' if calificacion_esperada > 7.5 else 'Apoyo del equipo importante'
        }
