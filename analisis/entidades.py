"""
Módulo que implementa clases para representar equipos y jugadores con sus características.
Permite un modelado más detallado para simulaciones y análisis avanzados.
"""

import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import defaultdict

class Jugador:
    def __init__(self, id=None, nombre=None, equipo=None, posicion=None, edad=None, nacionalidad=None):
        """
        Inicializa un objeto jugador con sus atributos básicos.
        
        Args:
            id: Identificador único del jugador
            nombre: Nombre completo del jugador
            equipo: Equipo actual del jugador
            posicion: Posición principal del jugador (por ejemplo, "delantero", "centrocampista", etc.)
            edad: Edad del jugador
            nacionalidad: País de origen del jugador
        """
        self.id = id
        self.nombre = nombre
        self.equipo = equipo
        self.posicion = posicion
        self.edad = edad
        self.nacionalidad = nacionalidad
        self.habilidades = {}  # dict con valores de 0-100
        self.estado_fisico = 100  # valor dinámico (0-100)
        self.historia_rendimiento = []  # lista para almacenar rendimiento en partidos
        self.estadisticas = {}  # estadísticas acumuladas (goles, asistencias, etc.)
    
    def establecer_habilidades(self, habilidades):
        """
        Establece las habilidades del jugador.
        
        Args:
            habilidades: Diccionario con habilidades y sus valores (0-100)
        """
        # Validar valores
        for nombre, valor in habilidades.items():
            if not 0 <= valor <= 100:
                raise ValueError(f"El valor de habilidad debe estar entre 0 y 100: {nombre}={valor}")
                
        self.habilidades = habilidades
    
    def actualizar_estadisticas(self, partido_stats):
        """
        Actualiza las estadísticas del jugador con datos de un partido.
        
        Args:
            partido_stats: Diccionario con estadísticas del partido
        """
        # Acumular estadísticas
        for key, value in partido_stats.items():
            if key in self.estadisticas:
                self.estadisticas[key] += value
            else:
                self.estadisticas[key] = value
        
        # Añadir a historial de rendimiento
        self.historia_rendimiento.append({
            'fecha': partido_stats.get('fecha', datetime.now()),
            'rival': partido_stats.get('rival', 'Desconocido'),
            'datos': partido_stats
        })
    
    def actualizar_estado_fisico(self, nuevo_valor=None, delta=None):
        """
        Actualiza el estado físico del jugador.
        
        Args:
            nuevo_valor: Valor absoluto del estado físico (0-100)
            delta: Cambio relativo en el estado físico
        """
        if nuevo_valor is not None:
            self.estado_fisico = max(0, min(100, nuevo_valor))
        elif delta is not None:
            self.estado_fisico = max(0, min(100, self.estado_fisico + delta))
    
    def calcular_impacto_partido(self, es_local=True, rival=None):
        """
        Calcula el impacto esperado del jugador en un partido.
        
        Args:
            es_local: Si el partido es como local o visitante
            rival: Equipo rival (opcional)
            
        Returns:
            Valor numérico que representa el impacto esperado
        """
        # Si no hay habilidades definidas, retornar valor base
        if not self.habilidades:
            return 50.0 * (self.estado_fisico / 100)
            
        # Calcular promedio de habilidades relevantes según posición
        if self.posicion == "delantero":
            habilidades_clave = ['remate', 'definicion', 'velocidad', 'regate']
        elif self.posicion == "centrocampista":
            habilidades_clave = ['pase', 'vision', 'resistencia', 'control']
        elif self.posicion == "defensa":
            habilidades_clave = ['marcaje', 'entrada', 'fuerza', 'anticipacion']
        elif self.posicion == "portero":
            habilidades_clave = ['reflejos', 'posicionamiento', 'salidas', 'manos']
        else:
            habilidades_clave = list(self.habilidades.keys())
        
        # Extraer solo habilidades que existen en el jugador
        habilidades_disponibles = [h for h in habilidades_clave if h in self.habilidades]
        
        if not habilidades_disponibles:
            habilidades_disponibles = list(self.habilidades.keys())
            
        if not habilidades_disponibles:
            return 50.0 * (self.estado_fisico / 100)
        
        # Calcular valor base de impacto
        valor_base = sum(self.habilidades[h] for h in habilidades_disponibles) / len(habilidades_disponibles)
        
        # Factores de ajuste
        factor_local = 1.1 if es_local else 0.9  # Ventaja/desventaja por jugar local/visitante
        factor_fisico = self.estado_fisico / 100  # Ajuste por estado físico
        
        # Ajuste por edad (rendimiento óptimo entre 25-29 años)
        factor_edad = 1.0
        if self.edad:
            if self.edad < 21:
                factor_edad = 0.9
            elif self.edad > 33:
                factor_edad = 0.85
        
        # Cálculo final
        impacto = valor_base * factor_local * factor_fisico * factor_edad
        
        return impacto
    
    def to_dict(self):
        """Convierte el jugador a diccionario para serialización"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'equipo': self.equipo,
            'posicion': self.posicion,
            'edad': self.edad,
            'nacionalidad': self.nacionalidad,
            'habilidades': self.habilidades,
            'estado_fisico': self.estado_fisico,
            'estadisticas': self.estadisticas
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea un jugador a partir de un diccionario"""
        jugador = cls(
            id=data.get('id'),
            nombre=data.get('nombre'),
            equipo=data.get('equipo'),
            posicion=data.get('posicion'),
            edad=data.get('edad'),
            nacionalidad=data.get('nacionalidad')
        )
        
        if 'habilidades' in data:
            jugador.habilidades = data['habilidades']
            
        if 'estado_fisico' in data:
            jugador.estado_fisico = data['estado_fisico']
            
        if 'estadisticas' in data:
            jugador.estadisticas = data['estadisticas']
            
        return jugador


class Equipo:
    def __init__(self, id=None, nombre=None, liga=None, pais=None):
        """
        Inicializa un objeto equipo con sus atributos básicos.
        
        Args:
            id: Identificador único del equipo
            nombre: Nombre del equipo
            liga: Liga a la que pertenece el equipo
            pais: País del equipo
        """
        self.id = id
        self.nombre = nombre
        self.liga = liga
        self.pais = pais
        self.jugadores = []  # lista de objetos Jugador
        self.titulares = []  # IDs de jugadores titulares
        self.estilo_juego = {}  # dict con valores de estilo (0-100)
        self.historia_partidos = []  # lista para almacenar resultados de partidos
        self.estadisticas = {
            'temporada_actual': {},
            'historico': {}
        }
    
    def establecer_estilo_juego(self, estilo):
        """
        Establece el estilo de juego del equipo.
        
        Args:
            estilo: Diccionario con atributos de estilo y sus valores (0-100)
        """
        # Validar valores
        for nombre, valor in estilo.items():
            if not 0 <= valor <= 100:
                raise ValueError(f"El valor de estilo debe estar entre 0 y 100: {nombre}={valor}")
                
        self.estilo_juego = estilo
    
    def agregar_jugador(self, jugador):
        """
        Añade un jugador al equipo.
        
        Args:
            jugador: Objeto Jugador a añadir
        """
        # Actualizar equipo del jugador
        jugador.equipo = self.nombre
        self.jugadores.append(jugador)
    
    def establecer_titulares(self, jugadores_ids):
        """
        Establece los jugadores titulares del equipo.
        
        Args:
            jugadores_ids: Lista con los IDs de los jugadores titulares
        """
        # Verificar que todos los IDs corresponden a jugadores del equipo
        ids_equipo = set(j.id for j in self.jugadores)
        for id_jugador in jugadores_ids:
            if id_jugador not in ids_equipo:
                raise ValueError(f"El jugador con ID {id_jugador} no pertenece a este equipo")
        
        self.titulares = jugadores_ids
    
    def obtener_jugadores_titulares(self):
        """
        Obtiene la lista de objetos Jugador que son titulares.
        
        Returns:
            Lista de objetos Jugador titulares
        """
        return [j for j in self.jugadores if j.id in self.titulares]
    
    def registrar_partido(self, datos_partido):
        """
        Registra un partido en el historial del equipo.
        
        Args:
            datos_partido: Diccionario con datos del partido
        """
        self.historia_partidos.append(datos_partido)
        
        # Actualizar estadísticas
        temporada = datos_partido.get('temporada', 'actual')
        
        # Inicializar estadísticas si no existen
        if temporada not in self.estadisticas:
            self.estadisticas[temporada] = {}
        
        # Actualizar estadísticas básicas
        stats = self.estadisticas[temporada]
        
        # Incrementar partidos jugados
        stats['partidos'] = stats.get('partidos', 0) + 1
        
        # Determinar resultado
        es_local = datos_partido.get('es_local', True)
        goles_favor = datos_partido.get('goles_favor', 0)
        goles_contra = datos_partido.get('goles_contra', 0)
        
        if goles_favor > goles_contra:
            stats['victorias'] = stats.get('victorias', 0) + 1
            stats['puntos'] = stats.get('puntos', 0) + 3
        elif goles_favor == goles_contra:
            stats['empates'] = stats.get('empates', 0) + 1
            stats['puntos'] = stats.get('puntos', 0) + 1
        else:
            stats['derrotas'] = stats.get('derrotas', 0) + 1
        
        # Actualizar estadísticas de goles
        stats['goles_favor'] = stats.get('goles_favor', 0) + goles_favor
        stats['goles_contra'] = stats.get('goles_contra', 0) + goles_contra
        
        # Estadísticas como local/visitante
        if es_local:
            stats['partidos_local'] = stats.get('partidos_local', 0) + 1
            if goles_favor > goles_contra:
                stats['victorias_local'] = stats.get('victorias_local', 0) + 1
            elif goles_favor == goles_contra:
                stats['empates_local'] = stats.get('empates_local', 0) + 1
            else:
                stats['derrotas_local'] = stats.get('derrotas_local', 0) + 1
        else:
            stats['partidos_visitante'] = stats.get('partidos_visitante', 0) + 1
            if goles_favor > goles_contra:
                stats['victorias_visitante'] = stats.get('victorias_visitante', 0) + 1
            elif goles_favor == goles_contra:
                stats['empates_visitante'] = stats.get('empates_visitante', 0) + 1
            else:
                stats['derrotas_visitante'] = stats.get('derrotas_visitante', 0) + 1
    
    def obtener_rendimiento_reciente(self, n_partidos=5):
        """
        Calcula el rendimiento reciente del equipo.
        
        Args:
            n_partidos: Número de partidos recientes a considerar
            
        Returns:
            Diccionario con estadísticas de rendimiento reciente
        """
        # Si no hay suficientes partidos, usar todos los disponibles
        partidos = self.historia_partidos[-n_partidos:] if self.historia_partidos else []
        
        if not partidos:
            return {
                'puntos_promedio': 0,
                'efectividad': 0,
                'racha': 'neutral',
                'goles_favor': 0,
                'goles_contra': 0
            }
        
        # Calcular estadísticas
        victorias = sum(1 for p in partidos if p.get('goles_favor', 0) > p.get('goles_contra', 0))
        empates = sum(1 for p in partidos if p.get('goles_favor', 0) == p.get('goles_contra', 0))
        derrotas = sum(1 for p in partidos if p.get('goles_favor', 0) < p.get('goles_contra', 0))
        
        puntos = victorias * 3 + empates
        puntos_posibles = len(partidos) * 3
        efectividad = (puntos / puntos_posibles) * 100 if puntos_posibles > 0 else 0
        
        goles_favor = sum(p.get('goles_favor', 0) for p in partidos)
        goles_contra = sum(p.get('goles_contra', 0) for p in partidos)
        
        # Determinar racha
        if len(partidos) >= 3:
            ultimos_3 = partidos[-3:]
            resultados = []
            
            for p in ultimos_3:
                if p.get('goles_favor', 0) > p.get('goles_contra', 0):
                    resultados.append('V')
                elif p.get('goles_favor', 0) == p.get('goles_contra', 0):
                    resultados.append('E')
                else:
                    resultados.append('D')
            
            if resultados.count('V') >= 2:
                racha = 'positiva'
            elif resultados.count('D') >= 2:
                racha = 'negativa'
            else:
                racha = 'neutral'
        else:
            racha = 'neutral'
        
        return {
            'puntos_promedio': puntos / len(partidos) if partidos else 0,
            'efectividad': efectividad,
            'racha': racha,
            'goles_favor': goles_favor,
            'goles_contra': goles_contra,
            'diferencia_goles': goles_favor - goles_contra
        }
    
    def calcular_fuerza_actual(self, rival=None, es_local=True):
        """
        Calcula la fuerza actual del equipo para un partido específico.
        
        Args:
            rival: Objeto Equipo rival (opcional)
            es_local: Si el partido es como local o visitante
            
        Returns:
            Valor numérico que representa la fuerza actual
        """
        # 1. Fuerza base calculada desde los jugadores titulares
        if self.titulares:
            jugadores_titulares = self.obtener_jugadores_titulares()
            fuerza_jugadores = sum(j.calcular_impacto_partido(es_local, rival) for j in jugadores_titulares)
            fuerza_base = fuerza_jugadores / len(jugadores_titulares) if jugadores_titulares else 50
        else:
            # Si no hay titulares definidos, usar los mejores 11 jugadores
            jugadores_ordenados = sorted(self.jugadores, 
                                        key=lambda j: j.calcular_impacto_partido(es_local, rival),
                                        reverse=True)
            mejores_jugadores = jugadores_ordenados[:11] if len(jugadores_ordenados) >= 11 else jugadores_ordenados
            fuerza_jugadores = sum(j.calcular_impacto_partido(es_local, rival) for j in mejores_jugadores)
            fuerza_base = fuerza_jugadores / len(mejores_jugadores) if mejores_jugadores else 50
        
        # 2. Ajustes por rendimiento reciente
        rendimiento = self.obtener_rendimiento_reciente(5)
        factor_rendimiento = 1.0
        
        if rendimiento['racha'] == 'positiva':
            factor_rendimiento = 1.15
        elif rendimiento['racha'] == 'negativa':
            factor_rendimiento = 0.85
        
        # 3. Ajuste por localía
        factor_local = 1.1 if es_local else 0.9
        
        # 4. Ajuste por estilo de juego y compatibilidad con el rival
        factor_estilo = 1.0
        if rival and self.estilo_juego and rival.estilo_juego:
            # Ejemplos de compatibilidad de estilos:
            # - Posesión alta vs. Presión alta: desventaja para posesión
            # - Juego directo vs. Defensa alta: ventaja para juego directo
            if self.estilo_juego.get('posesion', 50) > 70 and rival.estilo_juego.get('presion', 50) > 70:
                factor_estilo = 0.9
            elif self.estilo_juego.get('juego_directo', 50) > 70 and rival.estilo_juego.get('defensa_alta', 50) > 70:
                factor_estilo = 1.1
        
        # Cálculo final
        fuerza_ajustada = fuerza_base * factor_rendimiento * factor_local * factor_estilo
        
        return fuerza_ajustada
    
    def to_dict(self):
        """Convierte el equipo a diccionario para serialización"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'liga': self.liga,
            'pais': self.pais,
            'estilo_juego': self.estilo_juego,
            'titulares': self.titulares,
            'estadisticas': self.estadisticas,
            'jugadores': [j.to_dict() for j in self.jugadores]
        }
    
    @classmethod
    def from_dict(cls, data, cargar_jugadores=True):
        """Crea un equipo a partir de un diccionario"""
        equipo = cls(
            id=data.get('id'),
            nombre=data.get('nombre'),
            liga=data.get('liga'),
            pais=data.get('pais')
        )
        
        if 'estilo_juego' in data:
            equipo.estilo_juego = data['estilo_juego']
            
        if 'titulares' in data:
            equipo.titulares = data['titulares']
            
        if 'estadisticas' in data:
            equipo.estadisticas = data['estadisticas']
            
        if cargar_jugadores and 'jugadores' in data:
            for j_data in data['jugadores']:
                jugador = Jugador.from_dict(j_data)
                equipo.agregar_jugador(jugador)
                
        return equipo


class GestorEquipos:
    def __init__(self):
        """Inicializa el gestor de equipos y jugadores"""
        self.equipos = {}  # dict con id_equipo -> objeto Equipo
        self.jugadores = {}  # dict con id_jugador -> objeto Jugador
        self.datos_dir = os.path.join('data', 'equipos')
        os.makedirs(self.datos_dir, exist_ok=True)
    
    def agregar_equipo(self, equipo):
        """
        Agrega un equipo al gestor.
        
        Args:
            equipo: Objeto Equipo a agregar
        """
        if equipo.id is None:
            equipo.id = self._generar_id_equipo()
        
        self.equipos[equipo.id] = equipo
        
        # Agregar jugadores del equipo al registro
        for jugador in equipo.jugadores:
            self.agregar_jugador(jugador)
    
    def agregar_jugador(self, jugador):
        """
        Agrega un jugador al gestor.
        
        Args:
            jugador: Objeto Jugador a agregar
        """
        if jugador.id is None:
            jugador.id = self._generar_id_jugador()
        
        self.jugadores[jugador.id] = jugador
    
    def obtener_equipo_por_nombre(self, nombre):
        """
        Busca un equipo por su nombre.
        
        Args:
            nombre: Nombre del equipo a buscar
            
        Returns:
            Objeto Equipo o None si no se encuentra
        """
        for equipo in self.equipos.values():
            if equipo.nombre.lower() == nombre.lower():
                return equipo
        return None
    
    def obtener_jugador_por_nombre(self, nombre):
        """
        Busca un jugador por su nombre.
        
        Args:
            nombre: Nombre del jugador a buscar
            
        Returns:
            Objeto Jugador o None si no se encuentra
        """
        for jugador in self.jugadores.values():
            if jugador.nombre and jugador.nombre.lower() == nombre.lower():
                return jugador
        return None
    
    def guardar_datos(self):
        """
        Guarda todos los datos de equipos y jugadores en archivos JSON.
        
        Returns:
            True si se guardaron correctamente, False en caso contrario
        """
        try:
            # Crear directorio para equipos
            equipos_dir = os.path.join(self.datos_dir, 'equipos')
            os.makedirs(equipos_dir, exist_ok=True)
            
            # Guardar cada equipo en un archivo separado
            for equipo_id, equipo in self.equipos.items():
                ruta = os.path.join(equipos_dir, f"{equipo_id}.json")
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump(equipo.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Crear directorio para jugadores
            jugadores_dir = os.path.join(self.datos_dir, 'jugadores')
            os.makedirs(jugadores_dir, exist_ok=True)
            
            # Guardar cada jugador en un archivo separado
            for jugador_id, jugador in self.jugadores.items():
                ruta = os.path.join(jugadores_dir, f"{jugador_id}.json")
                with open(ruta, 'w', encoding='utf-8') as f:
                    json.dump(jugador.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Guardar índice de equipos
            indice_equipos = {
                equipo_id: {
                    'nombre': equipo.nombre,
                    'liga': equipo.liga,
                    'pais': equipo.pais
                } for equipo_id, equipo in self.equipos.items()
            }
            
            with open(os.path.join(self.datos_dir, 'indice_equipos.json'), 'w', encoding='utf-8') as f:
                json.dump(indice_equipos, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error al guardar datos: {e}")
            return False
    
    def cargar_datos(self):
        """
        Carga todos los datos de equipos y jugadores desde archivos JSON.
        
        Returns:
            True si se cargaron correctamente, False en caso contrario
        """
        try:
            # Limpiar datos actuales
            self.equipos = {}
            self.jugadores = {}
            
            # Cargar jugadores primero
            jugadores_dir = os.path.join(self.datos_dir, 'jugadores')
            if os.path.exists(jugadores_dir):
                for archivo in os.listdir(jugadores_dir):
                    if archivo.endswith('.json'):
                        ruta = os.path.join(jugadores_dir, archivo)
                        with open(ruta, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            jugador = Jugador.from_dict(data)
                            self.jugadores[jugador.id] = jugador
            
            # Cargar equipos después
            equipos_dir = os.path.join(self.datos_dir, 'equipos')
            if os.path.exists(equipos_dir):
                for archivo in os.listdir(equipos_dir):
                    if archivo.endswith('.json'):
                        ruta = os.path.join(equipos_dir, archivo)
                        with open(ruta, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # No cargar jugadores del JSON, ya que los tenemos en memoria
                            equipo = Equipo.from_dict(data, cargar_jugadores=False)
                            
                            # Asignar jugadores existentes al equipo
                            for j_data in data.get('jugadores', []):
                                j_id = j_data.get('id')
                                if j_id in self.jugadores:
                                    equipo.jugadores.append(self.jugadores[j_id])
                            
                            self.equipos[equipo.id] = equipo
            
            return True
        except Exception as e:
            print(f"Error al cargar datos: {e}")
            return False
    
    def generar_equipo_ejemplo(self, nombre="Equipo Ejemplo", liga="Liga Ejemplo", pais="País"):
        """
        Genera un equipo de ejemplo con jugadores.
        
        Args:
            nombre: Nombre del equipo
            liga: Liga del equipo
            pais: País del equipo
            
        Returns:
            Objeto Equipo generado
        """
        equipo = Equipo(nombre=nombre, liga=liga, pais=pais)
        
        # Definir estilo de juego aleatorio
        equipo.establecer_estilo_juego({
            'posesion': np.random.randint(30, 90),
            'presion': np.random.randint(30, 90),
            'defensa_alta': np.random.randint(30, 90),
            'juego_directo': np.random.randint(30, 90),
            'contraataque': np.random.randint(30, 90),
            'agresividad': np.random.randint(30, 90)
        })
        
        # Generar jugadores
        posiciones = ['portero', 'defensa', 'centrocampista', 'delantero']
        cantidad_por_posicion = {
            'portero': 3,
            'defensa': 8,
            'centrocampista': 8,
            'delantero': 6
        }
        
        nombres_base = ["Nombre", "Apellido"]
        titulares_ids = []
        
        for posicion, cantidad in cantidad_por_posicion.items():
            for i in range(cantidad):
                nombre = f"{nombres_base[0]}{i+1} {nombres_base[1]}{i+1}"
                jugador = Jugador(
                    nombre=nombre,
                    equipo=nombre,
                    posicion=posicion,
                    edad=np.random.randint(18, 38),
                    nacionalidad=pais
                )
                
                # Generar habilidades aleatorias según posición
                habilidades = {}
                
                # Habilidades comunes a todas las posiciones
                habilidades['resistencia'] = np.random.randint(50, 90)
                habilidades['velocidad'] = np.random.randint(50, 90)
                habilidades['fuerza'] = np.random.randint(50, 90)
                habilidades['control'] = np.random.randint(50, 90)
                
                # Habilidades específicas según posición
                if posicion == 'portero':
                    habilidades['reflejos'] = np.random.randint(60, 95)
                    habilidades['posicionamiento'] = np.random.randint(60, 95)
                    habilidades['salidas'] = np.random.randint(60, 95)
                    habilidades['manos'] = np.random.randint(60, 95)
                elif posicion == 'defensa':
                    habilidades['marcaje'] = np.random.randint(60, 95)
                    habilidades['entrada'] = np.random.randint(60, 95)
                    habilidades['anticipacion'] = np.random.randint(60, 95)
                    habilidades['cabeza'] = np.random.randint(60, 95)
                elif posicion == 'centrocampista':
                    habilidades['pase'] = np.random.randint(60, 95)
                    habilidades['vision'] = np.random.randint(60, 95)
                    habilidades['tecnica'] = np.random.randint(60, 95)
                    habilidades['creatividad'] = np.random.randint(60, 95)
                elif posicion == 'delantero':
                    habilidades['remate'] = np.random.randint(60, 95)
                    habilidades['definicion'] = np.random.randint(60, 95)
                    habilidades['regate'] = np.random.randint(60, 95)
                    habilidades['oportunismo'] = np.random.randint(60, 95)
                
                jugador.establecer_habilidades(habilidades)
                
                # Añadir algunas estadísticas básicas
                jugador.estadisticas = {
                    'partidos': np.random.randint(0, 30),
                    'minutos': np.random.randint(0, 2700),
                    'goles': np.random.randint(0, 15) if posicion != 'portero' else 0,
                    'asistencias': np.random.randint(0, 10) if posicion != 'portero' else 0,
                    'tarjetas_amarillas': np.random.randint(0, 8),
                    'tarjetas_rojas': np.random.randint(0, 2)
                }
                
                # Añadir jugador al equipo
                equipo.agregar_jugador(jugador)
                
                # Los primeros de cada posición serán titulares
                if (posicion == 'portero' and i == 0) or \
                   (posicion == 'defensa' and i < 4) or \
                   (posicion == 'centrocampista' and i < 3) or \
                   (posicion == 'delantero' and i < 3):
                    titulares_ids.append(jugador.id)
        
        # Establecer titulares
        equipo.establecer_titulares(titulares_ids)
        
        # Generar historial de partidos
        for i in range(10):
            rival = f"Rival {i+1}"
            fecha = datetime.now() - timedelta(days=30-i*3)
            es_local = i % 2 == 0
            goles_favor = np.random.randint(0, 5)
            goles_contra = np.random.randint(0, 5)
            
            equipo.registrar_partido({
                'fecha': fecha,
                'rival': rival,
                'es_local': es_local,
                'goles_favor': goles_favor,
                'goles_contra': goles_contra,
                'temporada': 'actual'
            })
        
        return equipo
    
    def generar_equipos_ejemplo(self, n_equipos=10):
        """
        Genera varios equipos de ejemplo.
        
        Args:
            n_equipos: Número de equipos a generar
            
        Returns:
            Lista de equipos generados
        """
        equipos = []
        ligas = ["Liga A", "Liga B", "Liga C"]
        paises = ["País A", "País B", "País C", "País D"]
        
        for i in range(n_equipos):
            nombre = f"Equipo {i+1}"
            liga = np.random.choice(ligas)
            pais = np.random.choice(paises)
            
            equipo = self.generar_equipo_ejemplo(nombre, liga, pais)
            self.agregar_equipo(equipo)
            equipos.append(equipo)
        
        # Guardar datos generados
        self.guardar_datos()
        
        return equipos
    
    def _generar_id_equipo(self):
        """Genera un ID único para un equipo"""
        return f"EQ{len(self.equipos) + 1:04d}"
    
    def _generar_id_jugador(self):
        """Genera un ID único para un jugador"""
        return f"JG{len(self.jugadores) + 1:06d}"
