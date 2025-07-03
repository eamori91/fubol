"""
Módulo de Análisis por Posiciones
Analiza el rendimiento de equipos desglosado por posiciones de jugadores
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime, timedelta

class AnalisisPosiciones:
    """Clase para análisis detallado por posiciones de jugadores"""
    
    def __init__(self):
        self.posiciones = {
            'porteros': ['POR'],
            'defensas': ['DFC', 'LI', 'LD', 'DFI', 'DFD'],
            'mediocampistas': ['MCD', 'MC', 'MCO', 'MI', 'MD', 'MOI', 'MOD'],
            'delanteros': ['DC', 'SD', 'EI', 'ED', 'DI', 'DD']
        }
        
        self.metricas_por_posicion = {
            'porteros': ['paradas', 'goles_encajados', 'porterias_cero', 'puntuacion_fifa'],
            'defensas': ['entradas', 'intercepciones', 'despejes', 'duelos_aereos'],
            'mediocampistas': ['pases_completados', 'asistencias', 'recuperaciones', 'km_recorridos'],
            'delanteros': ['goles', 'tiros_puerta', 'regates_exitosos', 'ocasiones_creadas']
        }

    def analizar_linea_defensiva(self, equipo: str, temporada: str = "2024") -> Dict:
        """
        Analiza el rendimiento de la línea defensiva
        
        Args:
            equipo: Nombre del equipo
            temporada: Temporada a analizar
            
        Returns:
            Diccionario con análisis de la defensa
        """
        try:
            # Simular datos de defensa (en producción vendría de base de datos)
            rendimiento_defensivo = {
                'goles_contra_por_partido': np.random.uniform(0.8, 2.2),
                'porterias_cero': np.random.randint(8, 18),
                'entradas_exitosas_porcentaje': np.random.uniform(65, 85),
                'duelos_aereos_ganados': np.random.uniform(55, 75),
                'interceptaciones_por_partido': np.random.uniform(8, 15),
                'linea_defensiva_altura': np.random.uniform(35, 55)  # metros desde portería
            }
            
            # Análisis individual de defensas clave
            defensas_clave = self._simular_defensas_clave()
            
            # Evaluación de parejas centrales
            parejas_centrales = self._analizar_parejas_centrales()
            
            # Análisis de laterales
            rendimiento_laterales = self._analizar_laterales()
            
            return {
                'equipo': equipo,
                'temporada': temporada,
                'metricas_generales': rendimiento_defensivo,
                'defensas_clave': defensas_clave,
                'parejas_centrales': parejas_centrales,
                'laterales': rendimiento_laterales,
                'fortalezas_defensivas': self._identificar_fortalezas_defensivas(rendimiento_defensivo),
                'areas_mejora': self._identificar_areas_mejora_defensivas(rendimiento_defensivo),
                'calificacion_defensa': self._calificar_defensa(rendimiento_defensivo)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis defensivo: {str(e)}'}

    def analizar_medio_campo(self, equipo: str, temporada: str = "2024") -> Dict:
        """
        Analiza el rendimiento del mediocampo
        
        Args:
            equipo: Nombre del equipo
            temporada: Temporada a analizar
            
        Returns:
            Diccionario con análisis del mediocampo
        """
        try:
            rendimiento_medio = {
                'posesion_promedio': np.random.uniform(45, 65),
                'pases_completados_porcentaje': np.random.uniform(78, 92),
                'pases_clave_por_partido': np.random.uniform(8, 20),
                'recuperaciones_por_partido': np.random.uniform(15, 25),
                'distancia_recorrida_km': np.random.uniform(110, 125),
                'intensidad_pressing': np.random.uniform(60, 90)
            }
            
            # Análisis por tipo de mediocampista
            tipos_mediocampistas = self._analizar_tipos_mediocampistas()
            
            # Análisis de distribución
            capacidad_distribucion = self._analizar_distribucion()
            
            # Análisis defensivo del mediocampo
            contribucion_defensiva = self._analizar_contribucion_defensiva_medio()
            
            return {
                'equipo': equipo,
                'temporada': temporada,
                'metricas_generales': rendimiento_medio,
                'tipos_mediocampistas': tipos_mediocampistas,
                'distribucion': capacidad_distribucion,
                'contribucion_defensiva': contribucion_defensiva,
                'creatividad': self._evaluar_creatividad_medio(rendimiento_medio),
                'equilibrio_medio': self._evaluar_equilibrio_medio(rendimiento_medio),
                'calificacion_mediocampo': self._calificar_mediocampo(rendimiento_medio)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis de mediocampo: {str(e)}'}

    def analizar_ataque(self, equipo: str, temporada: str = "2024") -> Dict:
        """
        Analiza el rendimiento ofensivo
        
        Args:
            equipo: Nombre del equipo
            temporada: Temporada a analizar
            
        Returns:
            Diccionario con análisis del ataque
        """
        try:
            rendimiento_ofensivo = {
                'goles_por_partido': np.random.uniform(1.2, 3.2),
                'tiros_por_partido': np.random.uniform(12, 22),
                'tiros_puerta_porcentaje': np.random.uniform(30, 50),
                'conversion_goles_porcentaje': np.random.uniform(8, 18),
                'ocasiones_claras_por_partido': np.random.uniform(3, 8),
                'velocidad_ataque_promedio': np.random.uniform(15, 25)  # km/h
            }
            
            # Análisis de delanteros
            delanteros_rendimiento = self._analizar_delanteros()
            
            # Análisis de bandas
            juego_bandas = self._analizar_juego_bandas()
            
            # Análisis de jugadas a balón parado
            balon_parado = self._analizar_balon_parado()
            
            return {
                'equipo': equipo,
                'temporada': temporada,
                'metricas_generales': rendimiento_ofensivo,
                'delanteros': delanteros_rendimiento,
                'juego_bandas': juego_bandas,
                'balon_parado': balon_parado,
                'eficiencia_ofensiva': self._calcular_eficiencia_ofensiva(rendimiento_ofensivo),
                'variabilidad_ataque': self._evaluar_variabilidad_ataque(),
                'calificacion_ataque': self._calificar_ataque(rendimiento_ofensivo)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis ofensivo: {str(e)}'}

    def comparar_por_posiciones(self, equipo1: str, equipo2: str, temporada: str = "2024") -> Dict:
        """
        Compara dos equipos línea por línea
        
        Args:
            equipo1: Primer equipo
            equipo2: Segundo equipo
            temporada: Temporada a analizar
            
        Returns:
            Diccionario con comparación por posiciones
        """
        try:
            # Obtener análisis de ambos equipos
            defensa1 = self.analizar_linea_defensiva(equipo1, temporada)
            medio1 = self.analizar_medio_campo(equipo1, temporada)
            ataque1 = self.analizar_ataque(equipo1, temporada)
            
            defensa2 = self.analizar_linea_defensiva(equipo2, temporada)
            medio2 = self.analizar_medio_campo(equipo2, temporada)
            ataque2 = self.analizar_ataque(equipo2, temporada)
            
            # Comparaciones por línea
            comparacion = {
                'equipos': [equipo1, equipo2],
                'defensa': self._comparar_defensas(defensa1, defensa2),
                'mediocampo': self._comparar_mediocampos(medio1, medio2),
                'ataque': self._comparar_ataques(ataque1, ataque2),
                'ventajas_por_linea': {
                    equipo1: self._calcular_ventajas_por_linea(defensa1, medio1, ataque1, 
                                                             defensa2, medio2, ataque2),
                    equipo2: self._calcular_ventajas_por_linea(defensa2, medio2, ataque2,
                                                             defensa1, medio1, ataque1)
                },
                'prediccion_areas_clave': self._predecir_areas_clave(defensa1, medio1, ataque1,
                                                                  defensa2, medio2, ataque2)
            }
            
            return comparacion
            
        except Exception as e:
            return {'error': f'Error en comparación por posiciones: {str(e)}'}

    def analizar_impacto_lesiones(self, equipo: str, jugadores_lesionados: List[str]) -> Dict:
        """
        Analiza el impacto de las lesiones en el rendimiento por posiciones
        
        Args:
            equipo: Nombre del equipo
            jugadores_lesionados: Lista de jugadores lesionados
            
        Returns:
            Diccionario con análisis de impacto de lesiones
        """
        try:
            # Simular datos de jugadores y sus posiciones
            impacto_por_posicion = {}
            
            for jugador in jugadores_lesionados:
                # Simular posición y importancia del jugador
                posicion = np.random.choice(['Defensa', 'Mediocampo', 'Delantero'])
                importancia = np.random.choice(['Titular', 'Suplente habitual', 'Reserva'])
                
                impacto_por_posicion[jugador] = {
                    'posicion': posicion,
                    'importancia': importancia,
                    'impacto_estimado': self._calcular_impacto_lesion(posicion, importancia),
                    'reemplazos_disponibles': np.random.randint(1, 4),
                    'reduccion_rendimiento_estimada': np.random.uniform(5, 25)  # porcentaje
                }
            
            return {
                'equipo': equipo,
                'jugadores_afectados': len(jugadores_lesionados),
                'impacto_detallado': impacto_por_posicion,
                'lineas_mas_afectadas': self._identificar_lineas_afectadas(impacto_por_posicion),
                'recomendaciones_tacticas': self._generar_recomendaciones_lesiones(impacto_por_posicion),
                'nivel_gravedad_general': self._evaluar_gravedad_lesiones(impacto_por_posicion)
            }
            
        except Exception as e:
            return {'error': f'Error en análisis de lesiones: {str(e)}'}

    # Métodos auxiliares para análisis defensivo
    def _simular_defensas_clave(self) -> List[Dict]:
        """Simula datos de defensas clave"""
        defensas = []
        nombres = ['Defensa A', 'Defensa B', 'Defensa C', 'Defensa D']
        
        for nombre in nombres:
            defensas.append({
                'nombre': nombre,
                'posicion': np.random.choice(['DFC', 'LI', 'LD']),
                'partidos_jugados': np.random.randint(20, 35),
                'entradas_exitosas': np.random.uniform(70, 90),
                'duelos_aereos_ganados': np.random.uniform(60, 85),
                'goles_evitados': np.random.randint(3, 12),
                'calificacion': np.random.uniform(6.5, 8.5)
            })
        
        return defensas

    def _analizar_parejas_centrales(self) -> Dict:
        """Analiza el rendimiento de las parejas de centrales"""
        return {
            'pareja_titular': {
                'nombres': ['Central A', 'Central B'],
                'partidos_juntos': np.random.randint(15, 30),
                'goles_contra_promedio': np.random.uniform(0.8, 1.8),
                'quimica_pareja': np.random.uniform(7.0, 9.5),
                'complementariedad': np.random.choice(['Excelente', 'Buena', 'Regular'])
            },
            'parejas_alternativas': np.random.randint(2, 5)
        }

    def _analizar_laterales(self) -> Dict:
        """Analiza el rendimiento de los laterales"""
        return {
            'lateral_izquierdo': {
                'nombre': 'Lateral I',
                'contribucion_ofensiva': np.random.uniform(0.2, 0.8),  # goles + asistencias
                'solidez_defensiva': np.random.uniform(6.0, 9.0),
                'centros_exitosos': np.random.uniform(20, 40)  # porcentaje
            },
            'lateral_derecho': {
                'nombre': 'Lateral D',
                'contribucion_ofensiva': np.random.uniform(0.2, 0.8),
                'solidez_defensiva': np.random.uniform(6.0, 9.0),
                'centros_exitosos': np.random.uniform(20, 40)
            }
        }

    # Métodos auxiliares para análisis de mediocampo
    def _analizar_tipos_mediocampistas(self) -> Dict:
        """Analiza los diferentes tipos de mediocampistas"""
        return {
            'mediocampista_defensivo': {
                'recuperaciones_por_partido': np.random.uniform(8, 15),
                'intercepciones': np.random.uniform(4, 8),
                'pases_largos_precision': np.random.uniform(75, 90)
            },
            'mediocampista_creativo': {
                'pases_clave_por_partido': np.random.uniform(3, 8),
                'asistencias_temporada': np.random.randint(5, 15),
                'regates_exitosos': np.random.uniform(60, 85)
            },
            'mediocampista_box_to_box': {
                'km_recorridos': np.random.uniform(11, 13),
                'contribucion_goles': np.random.randint(3, 10),
                'versatilidad': np.random.uniform(7.5, 9.5)
            }
        }

    def _analizar_distribucion(self) -> Dict:
        """Analiza la capacidad de distribución del mediocampo"""
        return {
            'precision_pase_corto': np.random.uniform(88, 95),
            'precision_pase_largo': np.random.uniform(65, 85),
            'velocidad_circulacion': np.random.uniform(2.1, 3.5),  # segundos
            'creatividad_pases': np.random.uniform(6.0, 9.0)
        }

    def _analizar_contribucion_defensiva_medio(self) -> Dict:
        """Analiza la contribución defensiva del mediocampo"""
        return {
            'pressing_coordinado': np.random.uniform(70, 90),
            'recuperaciones_campo_rival': np.random.uniform(25, 45),
            'cobertura_defensas': np.random.uniform(6.5, 8.5),
            'transiciones_defensivas': np.random.uniform(7.0, 9.0)
        }

    # Métodos auxiliares para análisis ofensivo
    def _analizar_delanteros(self) -> Dict:
        """Analiza el rendimiento de los delanteros"""
        return {
            'delantero_centro': {
                'goles_temporada': np.random.randint(8, 25),
                'conversion_oportunidades': np.random.uniform(15, 35),
                'juego_espaldas': np.random.uniform(6.5, 8.5),
                'movimientos_area': np.random.uniform(7.0, 9.0)
            },
            'segundo_delantero': {
                'goles_asistencias': np.random.randint(5, 18),
                'creatividad': np.random.uniform(7.0, 9.0),
                'trabajo_equipo': np.random.uniform(7.5, 9.5),
                'versatilidad_posicional': np.random.uniform(6.0, 8.5)
            }
        }

    def _analizar_juego_bandas(self) -> Dict:
        """Analiza el juego por las bandas"""
        return {
            'banda_izquierda': {
                'centros_por_partido': np.random.uniform(4, 12),
                'precision_centros': np.random.uniform(25, 45),
                'regates_exitosos': np.random.uniform(55, 80),
                'contribucion_goles': np.random.randint(2, 12)
            },
            'banda_derecha': {
                'centros_por_partido': np.random.uniform(4, 12),
                'precision_centros': np.random.uniform(25, 45),
                'regates_exitosos': np.random.uniform(55, 80),
                'contribucion_goles': np.random.randint(2, 12)
            }
        }

    def _analizar_balon_parado(self) -> Dict:
        """Analiza el rendimiento en jugadas a balón parado"""
        return {
            'corners': {
                'goles_de_corner': np.random.randint(3, 12),
                'precision_corners': np.random.uniform(35, 65),
                'variabilidad_corners': np.random.randint(3, 7)
            },
            'tiros_libres': {
                'goles_tiro_libre': np.random.randint(2, 8),
                'precision_tiros_libres': np.random.uniform(15, 35),
                'especialistas': np.random.randint(2, 4)
            },
            'penaltis': {
                'efectividad_penaltis': np.random.uniform(75, 95),
                'lanzador_principal': 'Jugador X'
            }
        }

    # Métodos de evaluación y calificación
    def _identificar_fortalezas_defensivas(self, metricas: Dict) -> List[str]:
        """Identifica las fortalezas defensivas"""
        fortalezas = []
        
        if metricas['goles_contra_por_partido'] < 1.2:
            fortalezas.append('Solidez defensiva excepcional')
        if metricas['porterias_cero'] > 12:
            fortalezas.append('Capacidad de mantener portería a cero')
        if metricas['duelos_aereos_ganados'] > 65:
            fortalezas.append('Dominio en el juego aéreo')
        if metricas['interceptaciones_por_partido'] > 12:
            fortalezas.append('Lectura de juego excepcional')
            
        return fortalezas if fortalezas else ['Defensa equilibrada']

    def _identificar_areas_mejora_defensivas(self, metricas: Dict) -> List[str]:
        """Identifica áreas de mejora defensivas"""
        mejoras = []
        
        if metricas['goles_contra_por_partido'] > 1.8:
            mejoras.append('Reducir goles en contra')
        if metricas['entradas_exitosas_porcentaje'] < 70:
            mejoras.append('Mejorar precisión en entradas')
        if metricas['duelos_aereos_ganados'] < 60:
            mejoras.append('Fortalecer juego aéreo defensivo')
            
        return mejoras if mejoras else ['Defensa sólida sin áreas críticas']

    def _calificar_defensa(self, metricas: Dict) -> float:
        """Califica la defensa de 1 a 10"""
        score = 5.0  # Base
        
        # Ajustes basados en métricas
        score += (2.0 - metricas['goles_contra_por_partido']) * 2
        score += (metricas['porterias_cero'] / 38) * 2  # Asumiendo 38 partidos
        score += (metricas['entradas_exitosas_porcentaje'] - 70) / 10
        
        return max(1.0, min(10.0, score))

    def _calificar_mediocampo(self, metricas: Dict) -> float:
        """Califica el mediocampo de 1 a 10"""
        score = 5.0
        
        score += (metricas['posesion_promedio'] - 50) / 10
        score += (metricas['pases_completados_porcentaje'] - 80) / 5
        score += (metricas['pases_clave_por_partido'] - 10) / 5
        
        return max(1.0, min(10.0, score))

    def _calificar_ataque(self, metricas: Dict) -> float:
        """Califica el ataque de 1 a 10"""
        score = 5.0
        
        score += (metricas['goles_por_partido'] - 1.5) * 2
        score += (metricas['conversion_goles_porcentaje'] - 10) / 2
        score += (metricas['ocasiones_claras_por_partido'] - 4) / 2
        
        return max(1.0, min(10.0, score))

    # Métodos de comparación
    def _comparar_defensas(self, def1: Dict, def2: Dict) -> Dict:
        """Compara dos defensas"""
        return {
            'mejor_en_solidez': self._determinar_mejor_metrica(
                def1['metricas_generales']['goles_contra_por_partido'],
                def2['metricas_generales']['goles_contra_por_partido'],
                menor_es_mejor=True
            ),
            'mejor_en_duelos_aereos': self._determinar_mejor_metrica(
                def1['metricas_generales']['duelos_aereos_ganados'],
                def2['metricas_generales']['duelos_aereos_ganados']
            ),
            'ventaja_significativa': abs(def1['calificacion_defensa'] - def2['calificacion_defensa']) > 1.0
        }

    def _comparar_mediocampos(self, medio1: Dict, medio2: Dict) -> Dict:
        """Compara dos mediocampos"""
        return {
            'mejor_control': self._determinar_mejor_metrica(
                medio1['metricas_generales']['posesion_promedio'],
                medio2['metricas_generales']['posesion_promedio']
            ),
            'mejor_creatividad': self._determinar_mejor_metrica(
                medio1['metricas_generales']['pases_clave_por_partido'],
                medio2['metricas_generales']['pases_clave_por_partido']
            ),
            'ventaja_significativa': abs(medio1['calificacion_mediocampo'] - medio2['calificacion_mediocampo']) > 1.0
        }

    def _comparar_ataques(self, ataque1: Dict, ataque2: Dict) -> Dict:
        """Compara dos ataques"""
        return {
            'mas_goleador': self._determinar_mejor_metrica(
                ataque1['metricas_generales']['goles_por_partido'],
                ataque2['metricas_generales']['goles_por_partido']
            ),
            'mas_eficiente': self._determinar_mejor_metrica(
                ataque1['metricas_generales']['conversion_goles_porcentaje'],
                ataque2['metricas_generales']['conversion_goles_porcentaje']
            ),
            'ventaja_significativa': abs(ataque1['calificacion_ataque'] - ataque2['calificacion_ataque']) > 1.0
        }

    def _determinar_mejor_metrica(self, valor1: float, valor2: float, menor_es_mejor: bool = False) -> str:
        """Determina qué equipo tiene mejor métrica"""
        if menor_es_mejor:
            return 'Equipo 1' if valor1 < valor2 else 'Equipo 2'
        else:
            return 'Equipo 1' if valor1 > valor2 else 'Equipo 2'

    def _calcular_ventajas_por_linea(self, def1: Dict, medio1: Dict, ataque1: Dict,
                                   def2: Dict, medio2: Dict, ataque2: Dict) -> List[str]:
        """Calcula las ventajas de un equipo línea por línea"""
        ventajas = []
        
        if def1['calificacion_defensa'] > def2['calificacion_defensa']:
            ventajas.append('Superioridad defensiva')
        if medio1['calificacion_mediocampo'] > medio2['calificacion_mediocampo']:
            ventajas.append('Dominio en el mediocampo')
        if ataque1['calificacion_ataque'] > ataque2['calificacion_ataque']:
            ventajas.append('Mayor potencial ofensivo')
            
        return ventajas if ventajas else ['Sin ventajas claras por línea']

    def _predecir_areas_clave(self, def1: Dict, medio1: Dict, ataque1: Dict,
                            def2: Dict, medio2: Dict, ataque2: Dict) -> List[str]:
        """Predice las áreas clave del partido"""
        areas_clave = []
        
        # Determinar diferencias significativas
        diff_def = abs(def1['calificacion_defensa'] - def2['calificacion_defensa'])
        diff_medio = abs(medio1['calificacion_mediocampo'] - medio2['calificacion_mediocampo'])
        diff_ataque = abs(ataque1['calificacion_ataque'] - ataque2['calificacion_ataque'])
        
        if diff_def > 1.5:
            areas_clave.append('Batalla defensiva será decisiva')
        if diff_medio > 1.5:
            areas_clave.append('Control del mediocampo clave')
        if diff_ataque > 1.5:
            areas_clave.append('Eficiencia ofensiva determinante')
            
        return areas_clave if areas_clave else ['Partido equilibrado en todas las líneas']

    # Métodos para análisis de lesiones
    def _calcular_impacto_lesion(self, posicion: str, importancia: str) -> str:
        """Calcula el impacto de una lesión"""
        if importancia == 'Titular':
            if posicion == 'Delantero':
                return 'Alto'
            elif posicion == 'Mediocampo':
                return 'Medio-Alto'
            else:
                return 'Medio'
        elif importancia == 'Suplente habitual':
            return 'Medio' if posicion in ['Delantero', 'Mediocampo'] else 'Bajo'
        else:
            return 'Bajo'

    def _identificar_lineas_afectadas(self, impacto: Dict) -> List[str]:
        """Identifica las líneas más afectadas por lesiones"""
        lineas_afectadas = {}
        
        for jugador, datos in impacto.items():
            linea = datos['posicion']
            if linea not in lineas_afectadas:
                lineas_afectadas[linea] = 0
            
            if datos['importancia'] == 'Titular':
                lineas_afectadas[linea] += 3
            elif datos['importancia'] == 'Suplente habitual':
                lineas_afectadas[linea] += 2
            else:
                lineas_afectadas[linea] += 1
        
        # Ordenar por impacto y devolver solo los nombres
        lineas_ordenadas = sorted(lineas_afectadas.items(), key=lambda x: x[1], reverse=True)
        return [linea[0] for linea in lineas_ordenadas]

    def _generar_recomendaciones_lesiones(self, impacto: Dict) -> List[str]:
        """Genera recomendaciones tácticas basadas en lesiones"""
        recomendaciones = []
        
        # Análisis simple basado en posiciones afectadas
        posiciones_afectadas = [datos['posicion'] for datos in impacto.values()]
        
        if posiciones_afectadas.count('Delantero') >= 2:
            recomendaciones.append('Considerar cambio de sistema ofensivo')
        if posiciones_afectadas.count('Mediocampo') >= 2:
            recomendaciones.append('Reforzar control del mediocampo')
        if posiciones_afectadas.count('Defensa') >= 2:
            recomendaciones.append('Adoptar táctica más conservadora')
            
        return recomendaciones if recomendaciones else ['Mantener esquema táctico habitual']

    def _evaluar_gravedad_lesiones(self, impacto: Dict) -> str:
        """Evalúa la gravedad general de las lesiones"""
        score = 0
        
        for datos in impacto.values():
            if datos['importancia'] == 'Titular':
                score += 3
            elif datos['importancia'] == 'Suplente habitual':
                score += 2
            else:
                score += 1
        
        if score >= 8:
            return 'Crítica'
        elif score >= 5:
            return 'Alta'
        elif score >= 3:
            return 'Media'
        else:
            return 'Baja'

    # Métodos de evaluación adicionales
    def _evaluar_creatividad_medio(self, metricas: Dict) -> str:
        """Evalúa la creatividad del mediocampo"""
        score = metricas['pases_clave_por_partido']
        
        if score > 16:
            return 'Muy Alta'
        elif score > 12:
            return 'Alta'
        elif score > 8:
            return 'Media'
        else:
            return 'Baja'

    def _evaluar_equilibrio_medio(self, metricas: Dict) -> str:
        """Evalúa el equilibrio entre ataque y defensa en el mediocampo"""
        # Balance entre contribución ofensiva y defensiva
        balance = (metricas['pases_clave_por_partido'] + metricas['recuperaciones_por_partido']) / 2
        
        if balance > 18:
            return 'Excelente'
        elif balance > 15:
            return 'Bueno'
        elif balance > 12:
            return 'Regular'
        else:
            return 'Deficiente'

    def _calcular_eficiencia_ofensiva(self, metricas: Dict) -> float:
        """Calcula la eficiencia ofensiva general"""
        # Relación entre goles y ocasiones creadas
        if metricas['ocasiones_claras_por_partido'] > 0:
            eficiencia = metricas['goles_por_partido'] / metricas['ocasiones_claras_por_partido']
            return round(eficiencia * 100, 1)  # Porcentaje
        return 0.0

    def _evaluar_variabilidad_ataque(self) -> Dict:
        """Evalúa la variabilidad del ataque"""
        return {
            'fuentes_gol': np.random.randint(3, 8),  # Número de jugadores goleadores
            'tipos_jugada': {
                'juego_elaborado': np.random.uniform(40, 70),
                'contraataque': np.random.uniform(15, 35),
                'balon_parado': np.random.uniform(10, 25),
                'jugadas_individuales': np.random.uniform(5, 20)
            },
            'impredecibilidad': np.random.choice(['Alta', 'Media', 'Baja'])
        }
