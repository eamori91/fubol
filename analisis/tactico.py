"""
Módulo de Análisis Táctico Avanzado
Implementa análisis de estilos de juego, formaciones y tácticas de equipos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime, timedelta

class AnalisisTactico:
    """Clase para análisis táctico avanzado de equipos"""
    
    def __init__(self):
        self.estilos_juego = {
            'posesion_alta': {'min_posesion': 60, 'toques_promedio': 7},
            'contraataque': {'min_velocidad_transicion': 80, 'pases_largos': 0.3},
            'presion_alta': {'recuperaciones_campo_rival': 0.4, 'linea_defensiva_alta': True},
            'juego_directo': {'pases_largos': 0.4, 'centros_area': 0.6}
        }
        
        self.formaciones_comunes = {
            '4-4-2': {'defensas': 4, 'mediocampistas': 4, 'delanteros': 2},
            '4-3-3': {'defensas': 4, 'mediocampistas': 3, 'delanteros': 3},
            '3-5-2': {'defensas': 3, 'mediocampistas': 5, 'delanteros': 2},
            '4-2-3-1': {'defensas': 4, 'mediocampistas': 5, 'delanteros': 1},
            '5-3-2': {'defensas': 5, 'mediocampistas': 3, 'delanteros': 2}
        }

    def analizar_estilo_juego(self, equipo: str, partidos_datos: pd.DataFrame) -> Dict:
        """
        Analiza el estilo de juego predominante de un equipo
        
        Args:
            equipo: Nombre del equipo
            partidos_datos: DataFrame con datos de partidos
            
        Returns:
            Diccionario con análisis de estilo de juego
        """
        try:
            # Filtrar partidos del equipo
            partidos_equipo = partidos_datos[
                (partidos_datos['equipo_local'] == equipo) | 
                (partidos_datos['equipo_visitante'] == equipo)
            ]
            
            if partidos_equipo.empty:
                return {'error': 'No se encontraron datos del equipo'}
            
            # Análisis de posesión
            posesion_promedio = self._calcular_posesion_promedio(partidos_equipo, equipo)
            
            # Análisis de velocidad de juego
            velocidad_juego = self._calcular_velocidad_juego(partidos_equipo, equipo)
            
            # Análisis de presión
            nivel_presion = self._calcular_nivel_presion(partidos_equipo, equipo)
            
            # Análisis de juego aéreo vs terrestre
            preferencia_juego = self._analizar_preferencia_juego(partidos_equipo, equipo)
            
            # Determinar estilo predominante
            estilo_predominante = self._determinar_estilo_predominante({
                'posesion': posesion_promedio,
                'velocidad': velocidad_juego,
                'presion': nivel_presion,
                'preferencia': preferencia_juego
            })
            
            return {
                'equipo': equipo,
                'estilo_predominante': estilo_predominante,
                'metricas': {
                    'posesion_promedio': posesion_promedio,
                    'velocidad_juego': velocidad_juego,
                    'nivel_presion': nivel_presion,
                    'preferencia_juego': preferencia_juego
                },
                'fortalezas_tacticas': self._identificar_fortalezas(estilo_predominante),
                'debilidades_tacticas': self._identificar_debilidades(estilo_predominante)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis táctico: {str(e)}'}

    def analizar_formacion_preferida(self, equipo: str, partidos_datos: pd.DataFrame) -> Dict:
        """
        Analiza las formaciones más utilizadas por un equipo
        
        Args:
            equipo: Nombre del equipo
            partidos_datos: DataFrame con datos de partidos
            
        Returns:
            Diccionario con análisis de formaciones
        """
        try:
            # Simular datos de formaciones (en producción vendría de datos reales)
            formaciones_utilizadas = {
                '4-3-3': 45,  # porcentaje de partidos
                '4-4-2': 30,
                '4-2-3-1': 20,
                '3-5-2': 5
            }
            
            formacion_principal = max(formaciones_utilizadas.items(), key=lambda x: x[1])[0]
            
            return {
                'equipo': equipo,
                'formacion_principal': formacion_principal,
                'distribucion_formaciones': formaciones_utilizadas,
                'efectividad_por_formacion': self._calcular_efectividad_formaciones(
                    equipo, formaciones_utilizadas
                ),
                'adaptabilidad_tactica': self._evaluar_adaptabilidad(formaciones_utilizadas)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis de formación: {str(e)}'}

    def analizar_transiciones(self, equipo: str, partidos_datos: pd.DataFrame) -> Dict:
        """
        Analiza las transiciones defensa-ataque y ataque-defensa
        
        Args:
            equipo: Nombre del equipo
            partidos_datos: DataFrame con datos de partidos
            
        Returns:
            Diccionario con análisis de transiciones
        """
        try:
            # Simular métricas de transiciones
            transiciones = {
                'velocidad_transicion_ataque': np.random.uniform(6.5, 9.2),  # segundos
                'efectividad_transicion': np.random.uniform(0.15, 0.35),     # porcentaje
                'recuperaciones_rapidas': np.random.randint(8, 15),          # por partido
                'contraataques_exitosos': np.random.uniform(0.3, 0.7),      # porcentaje
                'pressing_triggers': np.random.randint(20, 35)               # por partido
            }
            
            return {
                'equipo': equipo,
                'transiciones_ofensivas': {
                    'velocidad_promedio': transiciones['velocidad_transicion_ataque'],
                    'efectividad': transiciones['efectividad_transicion'],
                    'contraataques_por_partido': transiciones['contraataques_exitosos'] * 10
                },
                'transiciones_defensivas': {
                    'recuperaciones_rapidas': transiciones['recuperaciones_rapidas'],
                    'pressing_triggers': transiciones['pressing_triggers'],
                    'efectividad_pressing': np.random.uniform(0.4, 0.8)
                },
                'calificacion_transiciones': self._calificar_transiciones(transiciones)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis de transiciones: {str(e)}'}

    def comparar_estilos_tacticos(self, equipo1: str, equipo2: str, 
                                 partidos_datos: pd.DataFrame) -> Dict:
        """
        Compara los estilos tácticos de dos equipos
        
        Args:
            equipo1: Nombre del primer equipo
            equipo2: Nombre del segundo equipo
            partidos_datos: DataFrame con datos de partidos
            
        Returns:
            Diccionario con comparación táctica
        """
        try:
            estilo1 = self.analizar_estilo_juego(equipo1, partidos_datos)
            estilo2 = self.analizar_estilo_juego(equipo2, partidos_datos)
            
            if 'error' in estilo1 or 'error' in estilo2:
                return {'error': 'Error obteniendo datos de uno o ambos equipos'}
            
            compatibilidad = self._calcular_compatibilidad_estilos(
                estilo1['estilo_predominante'], 
                estilo2['estilo_predominante']
            )
            
            return {
                'equipos': [equipo1, equipo2],
                'estilos': {
                    equipo1: estilo1['estilo_predominante'],
                    equipo2: estilo2['estilo_predominante']
                },
                'compatibilidad': compatibilidad,
                'prediccion_estilo_partido': self._predecir_estilo_partido(estilo1, estilo2),
                'ventajas_tacticas': {
                    equipo1: self._calcular_ventajas_tacticas(estilo1, estilo2),
                    equipo2: self._calcular_ventajas_tacticas(estilo2, estilo1)
                }
            }
            
        except Exception as e:
            return {'error': f'Error en comparación táctica: {str(e)}'}

    def _calcular_posesion_promedio(self, partidos: pd.DataFrame, equipo: str) -> float:
        """Calcula la posesión promedio del equipo"""
        # Simulación - en producción vendría de datos reales
        return np.random.uniform(45, 65)

    def _calcular_velocidad_juego(self, partidos: pd.DataFrame, equipo: str) -> str:
        """Determina la velocidad de juego del equipo"""
        velocidades = ['Muy Lenta', 'Lenta', 'Media', 'Rápida', 'Muy Rápida']
        return np.random.choice(velocidades)

    def _calcular_nivel_presion(self, partidos: pd.DataFrame, equipo: str) -> str:
        """Determina el nivel de presión del equipo"""
        niveles = ['Baja', 'Media-Baja', 'Media', 'Media-Alta', 'Alta']
        return np.random.choice(niveles)

    def _analizar_preferencia_juego(self, partidos: pd.DataFrame, equipo: str) -> str:
        """Analiza si prefiere juego aéreo o terrestre"""
        preferencias = ['Aéreo', 'Terrestre', 'Mixto']
        return np.random.choice(preferencias)

    def _determinar_estilo_predominante(self, metricas: Dict) -> str:
        """Determina el estilo predominante basado en métricas"""
        if metricas['posesion'] > 60:
            return 'Posesión'
        elif metricas['velocidad'] in ['Rápida', 'Muy Rápida']:
            return 'Contraataque'
        elif metricas['presion'] in ['Alta', 'Media-Alta']:
            return 'Presión Alta'
        else:
            return 'Mixto'

    def _identificar_fortalezas(self, estilo: str) -> List[str]:
        """Identifica fortalezas del estilo de juego"""
        fortalezas_por_estilo = {
            'Posesión': ['Control del partido', 'Paciencia en ataque', 'Desgaste del rival'],
            'Contraataque': ['Velocidad en transiciones', 'Eficiencia ofensiva', 'Orden defensivo'],
            'Presión Alta': ['Recuperación alta', 'Intensidad', 'Presión sobre rival'],
            'Mixto': ['Adaptabilidad', 'Versatilidad táctica', 'Impredecibilidad']
        }
        return fortalezas_por_estilo.get(estilo, ['Estilo equilibrado'])

    def _identificar_debilidades(self, estilo: str) -> List[str]:
        """Identifica debilidades del estilo de juego"""
        debilidades_por_estilo = {
            'Posesión': ['Vulnerable al contraataque', 'Puede ser predecible', 'Dependiente de creatividad'],
            'Contraataque': ['Menor control del partido', 'Dependiente de errores rivales', 'Riesgo defensivo'],
            'Presión Alta': ['Desgaste físico', 'Espacios a la espalda', 'Riesgo de tarjetas'],
            'Mixto': ['Falta de especialización', 'Posible confusión táctica']
        }
        return debilidades_por_estilo.get(estilo, ['Sin debilidades identificadas'])

    def _calcular_efectividad_formaciones(self, equipo: str, formaciones: Dict) -> Dict:
        """Calcula la efectividad de cada formación"""
        efectividad = {}
        for formacion, porcentaje in formaciones.items():
            # Simular efectividad basada en uso
            base_efectividad = porcentaje / 100
            efectividad[formacion] = {
                'puntos_por_partido': np.random.uniform(1.0, 2.5) * base_efectividad + 0.5,
                'goles_favor': np.random.uniform(1.0, 3.0) * base_efectividad + 0.5,
                'goles_contra': np.random.uniform(0.5, 2.0) * (1 - base_efectividad) + 0.5
            }
        return efectividad

    def _evaluar_adaptabilidad(self, formaciones: Dict) -> str:
        """Evalúa la adaptabilidad táctica del equipo"""
        num_formaciones = len([f for f, p in formaciones.items() if p > 10])
        
        if num_formaciones >= 4:
            return 'Muy Alta'
        elif num_formaciones == 3:
            return 'Alta'
        elif num_formaciones == 2:
            return 'Media'
        else:
            return 'Baja'

    def _calificar_transiciones(self, transiciones: Dict) -> str:
        """Califica la calidad de las transiciones del equipo"""
        score = 0
        
        if transiciones['velocidad_transicion_ataque'] < 7.0:
            score += 2
        elif transiciones['velocidad_transicion_ataque'] < 8.0:
            score += 1
            
        if transiciones['efectividad_transicion'] > 0.25:
            score += 2
        elif transiciones['efectividad_transicion'] > 0.20:
            score += 1
            
        if transiciones['contraataques_exitosos'] > 0.5:
            score += 2
        elif transiciones['contraataques_exitosos'] > 0.4:
            score += 1
            
        calificaciones = ['Deficiente', 'Regular', 'Buena', 'Muy Buena', 'Excelente']
        return calificaciones[min(score, 4)]

    def _calcular_compatibilidad_estilos(self, estilo1: str, estilo2: str) -> Dict:
        """Calcula la compatibilidad entre dos estilos de juego"""
        compatibilidades = {
            ('Posesión', 'Contraataque'): {'nivel': 'Alta', 'descripcion': 'Estilos complementarios'},
            ('Posesión', 'Presión Alta'): {'nivel': 'Media', 'descripcion': 'Ambos buscan control'},
            ('Contraataque', 'Presión Alta'): {'nivel': 'Alta', 'descripcion': 'Intensidades opuestas'},
            ('Posesión', 'Mixto'): {'nivel': 'Media', 'descripcion': 'Adaptabilidad vs estructura'},
            ('Contraataque', 'Mixto'): {'nivel': 'Alta', 'descripcion': 'Velocidad vs adaptación'},
            ('Presión Alta', 'Mixto'): {'nivel': 'Media', 'descripcion': 'Intensidad vs versatilidad'}
        }
        
        key = (estilo1, estilo2) if (estilo1, estilo2) in compatibilidades else (estilo2, estilo1)
        return compatibilidades.get(key, {'nivel': 'Media', 'descripcion': 'Estilos similares'})

    def _predecir_estilo_partido(self, estilo1: Dict, estilo2: Dict) -> Dict:
        """Predice el estilo que tendrá el partido"""
        estilos_partido = [
            'Partido abierto con muchos goles',
            'Partido táctico y cerrado',
            'Dominio de un equipo',
            'Partido físico e intenso',
            'Partido técnico con buenas jugadas'
        ]
        
        return {
            'estilo_probable': np.random.choice(estilos_partido),
            'intensidad_esperada': np.random.choice(['Baja', 'Media', 'Alta', 'Muy Alta']),
            'goles_esperados': np.random.uniform(1.5, 4.0)
        }

    def _calcular_ventajas_tacticas(self, estilo_propio: Dict, estilo_rival: Dict) -> List[str]:
        """Calcula las ventajas tácticas de un equipo sobre otro"""
        ventajas_posibles = [
            'Mayor control del balón',
            'Superioridad en transiciones',
            'Mejor presión defensiva',
            'Mayor versatilidad táctica',
            'Ventaja en jugadas a balón parado',
            'Superior condición física'
        ]
        
        # Retornar 2-3 ventajas aleatorias
        num_ventajas = np.random.randint(2, 4)
        return np.random.choice(ventajas_posibles, size=num_ventajas, replace=False).tolist()
