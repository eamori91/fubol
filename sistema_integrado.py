"""
Script principal para el Sistema Integrado de Análisis Predictivo de Fútbol.
Coordina todas las funcionalidades del sistema incluyendo:
- Análisis predictivo tradicional
- Simulaciones Monte Carlo
- Modelos de deep learning
- Gestión de equipos y jugadores
- API pública
- Actualización automática de datos
- Unificación de fuentes gratuitas
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Importar todos los módulos del sistema
from analisis.futuro import AnalisisFuturo
from analisis.simulador import SimuladorPartidos
from analisis.entidades import GestorEquipos
from utils.data_loader import DataLoader
from utils.data_fetcher import DataFetcher
from utils.visualizacion import Visualizador
from utils.conversor import CSVtoJSON
from utils.unified_data_adapter import UnifiedDataAdapter

# Importar deep learning si está disponible
try:
    from analisis.deep_learning import DeepLearningPredictor
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False

class SistemaIntegrado:
    """Clase principal que coordina todo el sistema integrado"""
    
    def __init__(self):
        """Inicializa todos los componentes del sistema"""
        print("Inicializando Sistema Integrado de Análisis Predictivo de Fútbol...")
        
        # Componentes principales
        self.analizador = AnalisisFuturo()
        self.simulador = SimuladorPartidos(self.analizador)
        self.gestor_equipos = GestorEquipos()
        self.data_loader = DataLoader()
        self.data_fetcher = DataFetcher()
        self.visualizador = Visualizador()
        self.conversor = CSVtoJSON()
        self.unified_adapter = UnifiedDataAdapter()  # Nuevo adaptador unificado
        
        # Deep learning si está disponible
        if DEEP_LEARNING_AVAILABLE:
            self.deep_learning = DeepLearningPredictor()
            print("✓ Modelos de Deep Learning disponibles")
        else:
            self.deep_learning = None
            print("⚠ Modelos de Deep Learning no disponibles")
        
        # Directorios
        self.resultados_dir = os.path.join('data', 'resultados_integrados')
        os.makedirs(self.resultados_dir, exist_ok=True)
        
        print("✓ Sistema inicializado correctamente")
        
        # Verificar fuentes de datos disponibles
        fuentes_activas = self.unified_adapter._count_active_sources()
        print(f"✓ Adaptador unificado inicializado con {fuentes_activas} fuentes de datos gratuitas activas")
    
    def cargar_datos(self):
        """Carga todos los datos necesarios"""
        print("\nCargando datos del sistema...")
        
        # Cargar datos históricos
        ruta_datos = os.path.join('cache', 'partidos_historicos.csv')
        if os.path.exists(ruta_datos):
            self.analizador.datos = self.data_loader.cargar_datos_csv(ruta_datos)
            print(f"✓ Datos históricos cargados: {len(self.analizador.datos)} partidos")
        else:
            print("⚠ No se encontraron datos históricos, generando datos de ejemplo...")
            self.analizador.datos = self.analizador.generar_datos_ejemplo()
        
        # Cargar modelos predictivos
        self.analizador.cargar_modelos()
        print("✓ Modelos predictivos cargados")
        
        # Cargar datos de equipos
        self.gestor_equipos.cargar_datos()
        print(f"✓ Datos de equipos cargados: {len(self.gestor_equipos.equipos)} equipos")
        
        # Cargar modelos de deep learning si están disponibles
        if self.deep_learning:
            try:
                self.deep_learning.cargar_modelos()
                print("✓ Modelos de Deep Learning cargados")
            except Exception as e:
                print(f"⚠ Error al cargar modelos de Deep Learning: {e}")
    
    def actualizar_datos_externos(self, fuente='football-data', liga=None, temporada=None):
        """Actualiza datos desde fuentes externas"""
        print(f"\nActualizando datos desde fuente externa: {fuente}")
        
        try:
            resultado = self.data_fetcher.actualizar_datos(
                fuente=fuente,
                liga=liga,
                temporada=temporada,
                forzar_actualizacion=True
            )
            
            if resultado['exito']:
                # Recargar datos
                self.analizador.datos = self.data_loader.cargar_datos_csv(resultado['archivo'])
                print(f"✓ Datos actualizados: {resultado['partidos_nuevos']} partidos nuevos")
                return True
            else:
                print(f"✗ Error al actualizar datos: {resultado['error']}")
                return False
                
        except Exception as e:
            print(f"✗ Error durante la actualización: {e}")
            return False
    
    def analisis_completo(self, equipo_local, equipo_visitante, fecha=None):
        """Realiza un análisis completo usando todos los métodos disponibles"""
        if fecha is None:
            fecha = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"ANÁLISIS COMPLETO: {equipo_local} vs {equipo_visitante}")
        print(f"Fecha: {fecha.strftime('%d/%m/%Y')}")
        print(f"{'='*60}")
        
        resultados = {
            'partido': {
                'equipo_local': equipo_local,
                'equipo_visitante': equipo_visitante,
                'fecha': fecha.strftime('%Y-%m-%d')
            },
            'analisis': {}
        }
        
        # 1. Predicción tradicional
        print("\n1. ANÁLISIS PREDICTIVO TRADICIONAL")
        print("-" * 40)
        try:
            prediccion_tradicional = self.analizador.predecir_partido_futuro(
                equipo_local, equipo_visitante, fecha
            )
            
            if prediccion_tradicional:
                resultados['analisis']['tradicional'] = prediccion_tradicional
                print(f"Victoria {equipo_local}: {prediccion_tradicional['probabilidades']['victoria_local']:.2%}")
                print(f"Empate: {prediccion_tradicional['probabilidades']['empate']:.2%}")
                print(f"Victoria {equipo_visitante}: {prediccion_tradicional['probabilidades']['victoria_visitante']:.2%}")
                print(f"Resultado probable: {prediccion_tradicional['resultado_probable']}")
            else:
                print("✗ No se pudo generar predicción tradicional")
                
        except Exception as e:
            print(f"✗ Error en predicción tradicional: {e}")
        
        # 2. Simulación Monte Carlo
        print("\n2. SIMULACIÓN MONTE CARLO")
        print("-" * 40)
        try:
            simulacion = self.simulador.simular_partido_monte_carlo(
                equipo_local, equipo_visitante, fecha, n_simulaciones=1000
            )
            
            if simulacion:
                resultados['analisis']['simulacion_monte_carlo'] = simulacion
                print(f"Victoria {equipo_local}: {simulacion['probabilidades']['victoria_local']:.2%}")
                print(f"Empate: {simulacion['probabilidades']['empate']:.2%}")
                print(f"Victoria {equipo_visitante}: {simulacion['probabilidades']['victoria_visitante']:.2%}")
                print(f"Resultado más probable: {simulacion['resultado_mas_probable']}")
                print(f"Simulaciones realizadas: {simulacion['n_simulaciones']}")
            else:
                print("✗ No se pudo realizar simulación Monte Carlo")
                
        except Exception as e:
            print(f"✗ Error en simulación Monte Carlo: {e}")
        
        # 3. Deep Learning (si está disponible)
        if self.deep_learning:
            print("\n3. PREDICCIÓN CON DEEP LEARNING")
            print("-" * 40)
            try:
                prediccion_dl = self.deep_learning.predecir_partido(
                    equipo_local, equipo_visitante, fecha
                )
                
                if prediccion_dl:
                    resultados['analisis']['deep_learning'] = prediccion_dl
                    print(f"Victoria {equipo_local}: {prediccion_dl['probabilidades']['victoria_local']:.2%}")
                    print(f"Empate: {prediccion_dl['probabilidades']['empate']:.2%}")
                    print(f"Victoria {equipo_visitante}: {prediccion_dl['probabilidades']['victoria_visitante']:.2%}")
                    print(f"Confianza del modelo: {prediccion_dl.get('confianza', 'N/A')}")
                else:
                    print("✗ No se pudo generar predicción con Deep Learning")
                    
            except Exception as e:
                print(f"✗ Error en predicción Deep Learning: {e}")
        
        # 4. Análisis de equipos
        print("\n4. ANÁLISIS DE EQUIPOS")
        print("-" * 40)
        try:
            equipo_local_obj = self.gestor_equipos.obtener_equipo_por_nombre(equipo_local)
            equipo_visitante_obj = self.gestor_equipos.obtener_equipo_por_nombre(equipo_visitante)
            
            if equipo_local_obj and equipo_visitante_obj:
                fuerza_local = equipo_local_obj.calcular_fuerza_plantilla()
                fuerza_visitante = equipo_visitante_obj.calcular_fuerza_plantilla()
                
                resultados['analisis']['equipos'] = {
                    'local': {
                        'nombre': equipo_local_obj.nombre,
                        'fuerza_plantilla': fuerza_local,
                        'jugadores': len(equipo_local_obj.jugadores)
                    },
                    'visitante': {
                        'nombre': equipo_visitante_obj.nombre,
                        'fuerza_plantilla': fuerza_visitante,
                        'jugadores': len(equipo_visitante_obj.jugadores)
                    }
                }
                
                print(f"Fuerza plantilla {equipo_local}: {fuerza_local:.1f}")
                print(f"Fuerza plantilla {equipo_visitante}: {fuerza_visitante:.1f}")
                print(f"Ventaja: {equipo_local if fuerza_local > fuerza_visitante else equipo_visitante}")
            else:
                print("⚠ No se encontraron datos detallados de los equipos")
                
        except Exception as e:
            print(f"✗ Error en análisis de equipos: {e}")
        
        # 5. Resumen y consenso
        print("\n5. RESUMEN Y CONSENSO")
        print("-" * 40)
        self._generar_consenso(resultados)
        
        return resultados
    
    def _generar_consenso(self, resultados):
        """Genera un consenso basado en todos los análisis realizados"""
        try:
            probabilidades = []
            
            # Recopilar probabilidades de todos los métodos
            for metodo, analisis in resultados['analisis'].items():
                if 'probabilidades' in analisis:
                    probabilidades.append(analisis['probabilidades'])
            
            if not probabilidades:
                print("No hay suficientes datos para generar consenso")
                return
            
            # Calcular promedio ponderado
            consenso = {
                'victoria_local': np.mean([p['victoria_local'] for p in probabilidades]),
                'empate': np.mean([p['empate'] for p in probabilidades]),
                'victoria_visitante': np.mean([p['victoria_visitante'] for p in probabilidades])
            }
            
            # Determinar resultado más probable
            max_prob = max(consenso.values())
            if consenso['victoria_local'] == max_prob:
                resultado_consenso = f"Victoria {resultados['partido']['equipo_local']}"
            elif consenso['empate'] == max_prob:
                resultado_consenso = "Empate"
            else:
                resultado_consenso = f"Victoria {resultados['partido']['equipo_visitante']}"
            
            resultados['consenso'] = {
                'probabilidades': consenso,
                'resultado_probable': resultado_consenso,
                'metodos_utilizados': len(probabilidades)
            }
            
            print(f"CONSENSO ({len(probabilidades)} métodos):")
            print(f"Victoria {resultados['partido']['equipo_local']}: {consenso['victoria_local']:.2%}")
            print(f"Empate: {consenso['empate']:.2%}")
            print(f"Victoria {resultados['partido']['equipo_visitante']}: {consenso['victoria_visitante']:.2%}")
            print(f"Resultado más probable: {resultado_consenso}")
            
        except Exception as e:
            print(f"✗ Error al generar consenso: {e}")
    
    def entrenar_todos_los_modelos(self, optimizar=False):
        """Entrena todos los modelos disponibles"""
        print("\nEntrenando todos los modelos...")
        
        resultados_entrenamiento = {}
        
        # Entrenar modelos tradicionales
        print("\n1. ENTRENANDO MODELOS TRADICIONALES")
        print("-" * 40)
        try:
            resultado_tradicional = self.analizador.entrenar_modelos(
                optimizar_hiperparametros=optimizar
            )
            resultados_entrenamiento['tradicional'] = resultado_tradicional
            print("✓ Modelos tradicionales entrenados")
            
        except Exception as e:
            print(f"✗ Error entrenando modelos tradicionales: {e}")
            resultados_entrenamiento['tradicional'] = {'error': str(e)}
        
        # Entrenar modelos de deep learning
        if self.deep_learning:
            print("\n2. ENTRENANDO MODELOS DE DEEP LEARNING")
            print("-" * 40)
            try:
                resultado_dl = self.deep_learning.entrenar_modelo(self.analizador.datos)
                resultados_entrenamiento['deep_learning'] = resultado_dl
                print("✓ Modelos de Deep Learning entrenados")
                
            except Exception as e:
                print(f"✗ Error entrenando modelos Deep Learning: {e}")
                resultados_entrenamiento['deep_learning'] = {'error': str(e)}
        
        return resultados_entrenamiento
    
    def generar_reporte_completo(self, equipo_local, equipo_visitante, fecha=None, guardar=True):
        """Genera un reporte completo del análisis"""
        # Realizar análisis completo
        resultados = self.analisis_completo(equipo_local, equipo_visitante, fecha)
        
        # Generar visualizaciones
        if guardar:
            print("\nGenerando visualizaciones...")
            try:
                # Guardar resultados en JSON
                fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                archivo_resultados = os.path.join(
                    self.resultados_dir, 
                    f'analisis_completo_{equipo_local}_vs_{equipo_visitante}_{fecha_str}.json'
                )
                
                with open(archivo_resultados, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"✓ Resultados guardados en: {archivo_resultados}")
                
                # Generar visualizaciones si hay simulación Monte Carlo
                if 'simulacion_monte_carlo' in resultados['analisis']:
                    fig = self.simulador.visualizar_distribucion_resultados(
                        resultados['analisis']['simulacion_monte_carlo']
                    )
                    if fig:
                        archivo_grafico = os.path.join(
                            self.resultados_dir,
                            f'distribucion_{equipo_local}_vs_{equipo_visitante}_{fecha_str}.png'
                        )
                        fig.savefig(archivo_grafico, dpi=300, bbox_inches='tight')
                        print(f"✓ Gráfico guardado en: {archivo_grafico}")
                
            except Exception as e:
                print(f"✗ Error al guardar resultados: {e}")
        
        return resultados
    
    def ejecutar_modo_interactivo(self):
        """Ejecuta el sistema en modo interactivo"""
        print("\n" + "="*60)
        print("MODO INTERACTIVO - Sistema Integrado de Análisis de Fútbol")
        print("="*60)
        
        while True:
            print("\nOpciones disponibles:")
            print("1. Análisis completo de un partido")
            print("2. Actualizar datos externos")
            print("3. Entrenar modelos")
            print("4. Simular partido con eventos")
            print("5. Gestionar equipos")
            print("6. Ver métricas del sistema")
            print("0. Salir")
            
            try:
                opcion = input("\nSelecciona una opción: ").strip()
                
                if opcion == '0':
                    print("¡Hasta luego!")
                    break
                elif opcion == '1':
                    self._opcion_analisis_completo()
                elif opcion == '2':
                    self._opcion_actualizar_datos()
                elif opcion == '3':
                    self._opcion_entrenar_modelos()
                elif opcion == '4':
                    self._opcion_simular_eventos()
                elif opcion == '5':
                    self._opcion_gestionar_equipos()
                elif opcion == '6':
                    self._opcion_metricas_sistema()
                else:
                    print("Opción no válida")
                    
            except KeyboardInterrupt:
                print("\n¡Hasta luego!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _opcion_analisis_completo(self):
        """Opción interactiva para análisis completo"""
        print("\n--- ANÁLISIS COMPLETO ---")
        equipo_local = input("Equipo local: ").strip()
        equipo_visitante = input("Equipo visitante: ").strip()
        fecha_str = input("Fecha (YYYY-MM-DD, vacío para hoy): ").strip()
        
        fecha = None
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            except ValueError:
                print("Formato de fecha incorrecto, usando fecha actual")
                fecha = datetime.now()
        
        guardar = input("¿Guardar resultados? (s/n): ").strip().lower() == 's'
        
        self.generar_reporte_completo(equipo_local, equipo_visitante, fecha, guardar)
    
    def _opcion_actualizar_datos(self):
        """Opción interactiva para actualizar datos"""
        print("\n--- ACTUALIZAR DATOS ---")
        fuente = input("Fuente (football-data): ").strip() or 'football-data'
        liga = input("Liga (opcional): ").strip() or None
        temporada = input("Temporada (opcional): ").strip() or None
        
        self.actualizar_datos_externos(fuente, liga, temporada)
    
    def _opcion_entrenar_modelos(self):
        """Opción interactiva para entrenar modelos"""
        print("\n--- ENTRENAR MODELOS ---")
        optimizar = input("¿Optimizar hiperparámetros? (s/n): ").strip().lower() == 's'
        
        self.entrenar_todos_los_modelos(optimizar)
    
    def _opcion_simular_eventos(self):
        """Opción interactiva para simular eventos"""
        print("\n--- SIMULAR EVENTOS ---")
        equipo_local = input("Equipo local: ").strip()
        equipo_visitante = input("Equipo visitante: ").strip()
        
        try:
            simulacion = self.simulador.simular_partido_eventos(equipo_local, equipo_visitante)
            
            print(f"\nResultado: {equipo_local} {simulacion['resultado']['local']}"
                  f" - {simulacion['resultado']['visitante']} {equipo_visitante}")
            print("\nEventos principales:")
            
            for evento in simulacion['eventos'][:10]:  # Mostrar primeros 10 eventos
                print(f"  {evento['minuto']}' - {evento['tipo']}: {evento.get('descripcion', '')}")
                
        except Exception as e:
            print(f"Error en simulación: {e}")
    
    def _opcion_gestionar_equipos(self):
        """Opción interactiva para gestionar equipos"""
        print("\n--- GESTIONAR EQUIPOS ---")
        print(f"Equipos registrados: {len(self.gestor_equipos.equipos)}")
        
        for nombre, equipo in list(self.gestor_equipos.equipos.items())[:5]:
            print(f"  - {nombre} ({len(equipo.jugadores)} jugadores)")
        
        if len(self.gestor_equipos.equipos) > 5:
            print(f"  ... y {len(self.gestor_equipos.equipos) - 5} más")
    
    def _opcion_metricas_sistema(self):
        """Opción interactiva para ver métricas del sistema"""
        print("\n--- MÉTRICAS DEL SISTEMA ---")
        print(f"Partidos históricos: {len(self.analizador.datos) if self.analizador.datos is not None else 0}")
        print(f"Equipos registrados: {len(self.gestor_equipos.equipos)}")
        print(f"Modelos tradicionales: {'✓' if self.analizador.modelo_resultado is not None else '✗'}")
        print(f"Deep Learning: {'✓' if self.deep_learning else '✗'}")
        print(f"Fuentes de datos unificadas: {self.unified_adapter._count_active_sources()}")
        print(f"Jugadores en plantilla: {sum(len(equipo.jugadores) for equipo in self.gestor_equipos.equipos.values())}")

    def obtener_proximos_partidos_unificados(self, dias=7, liga=None):
        """
        Obtiene los próximos partidos utilizando el adaptador unificado
        
        Args:
            dias: Número de días hacia adelante para buscar
            liga: Liga específica para filtrar (opcional)
            
        Returns:
            Lista de partidos próximos desde fuentes gratuitas
        """
        print(f"\nObteniendo próximos partidos unificados para {dias} días...")
        
        try:
            partidos = self.unified_adapter.obtener_proximos_partidos(dias=dias, liga=liga)
            print(f"✓ Se obtuvieron {len(partidos)} partidos")
            
            # Mostrar ligas disponibles
            ligas = set([p.get('liga') for p in partidos if p.get('liga')])
            if ligas:
                print(f"✓ Ligas disponibles: {', '.join(ligas)}")
            
            return partidos
        except Exception as e:
            print(f"⚠ Error al obtener próximos partidos: {e}")
            return []
    
    def obtener_datos_equipo_unificados(self, nombre_equipo):
        """
        Obtiene datos de un equipo utilizando el adaptador unificado
        
        Args:
            nombre_equipo: Nombre del equipo a buscar
            
        Returns:
            Diccionario con información del equipo y su plantilla
        """
        print(f"\nObteniendo datos unificados para el equipo: {nombre_equipo}")
        
        try:
            # Obtener datos básicos del equipo
            datos_equipo = self.unified_adapter.obtener_datos_equipo(nombre_equipo)
            
            if not datos_equipo:
                print(f"⚠ No se encontró información para el equipo: {nombre_equipo}")
                return None
                
            print(f"✓ Datos básicos del equipo obtenidos")
            
            # Obtener jugadores
            jugadores = self.unified_adapter.obtener_jugadores_equipo(nombre_equipo)
            
            if jugadores:
                print(f"✓ Se obtuvieron {len(jugadores)} jugadores")
                datos_equipo['jugadores'] = jugadores
            else:
                print("⚠ No se encontraron jugadores para este equipo")
            
            return datos_equipo
        except Exception as e:
            print(f"⚠ Error al obtener datos del equipo: {e}")
            return None
    
    def obtener_arbitros_unificados(self):
        """
        Obtiene lista de árbitros utilizando el adaptador unificado
        
        Returns:
            Lista de árbitros disponibles
        """
        print("\nObteniendo lista de árbitros disponibles...")
        
        try:
            arbitros = self.unified_adapter.obtener_arbitros()
            print(f"✓ Se obtuvieron {len(arbitros)} árbitros")
            return arbitros
        except Exception as e:
            print(f"⚠ Error al obtener árbitros: {e}")
            return []
    
    def obtener_historial_arbitro_unificado(self, nombre_arbitro, equipo=None):
        """
        Obtiene estadísticas de un árbitro utilizando el adaptador unificado
        
        Args:
            nombre_arbitro: Nombre del árbitro
            equipo: Nombre del equipo para filtrar (opcional)
            
        Returns:
            Diccionario con estadísticas del árbitro
        """
        print(f"\nObteniendo historial para el árbitro: {nombre_arbitro}")
        
        if equipo:
            print(f"Filtrando por equipo: {equipo}")
            
        try:
            estadisticas = self.unified_adapter.obtener_historial_arbitro(nombre_arbitro, equipo)
            
            if not estadisticas:
                print(f"⚠ No se encontró información para el árbitro: {nombre_arbitro}")
                return None
                
            print(f"✓ Estadísticas del árbitro obtenidas: {estadisticas.get('partidos', 0)} partidos dirigidos")
            
            return estadisticas
        except Exception as e:
            print(f"⚠ Error al obtener historial del árbitro: {e}")
            return None

def main():
    """Función principal del sistema integrado"""
    parser = argparse.ArgumentParser(description='Sistema Integrado de Análisis Predictivo de Fútbol')
    parser.add_argument('--modo', choices=['interactivo', 'analisis', 'actualizar', 'entrenar'], 
                       default='interactivo', help='Modo de operación')
    parser.add_argument('--local', help='Equipo local')
    parser.add_argument('--visitante', help='Equipo visitante')
    parser.add_argument('--fecha', help='Fecha del partido (YYYY-MM-DD)')
    parser.add_argument('--optimizar', action='store_true', help='Optimizar hiperparámetros durante entrenamiento')
    parser.add_argument('--guardar', action='store_true', help='Guardar resultados y visualizaciones')
    
    args = parser.parse_args()
    
    # Inicializar sistema
    sistema = SistemaIntegrado()
    sistema.cargar_datos()
    
    if args.modo == 'interactivo':
        sistema.ejecutar_modo_interactivo()
    
    elif args.modo == 'analisis':
        if not args.local or not args.visitante:
            print("Error: Se requieren --local y --visitante para el modo análisis")
            sys.exit(1)
        
        fecha = None
        if args.fecha:
            try:
                fecha = datetime.strptime(args.fecha, '%Y-%m-%d')
            except ValueError:
                print("Formato de fecha incorrecto")
                sys.exit(1)
        
        sistema.generar_reporte_completo(args.local, args.visitante, fecha, args.guardar)
    
    elif args.modo == 'actualizar':
        sistema.actualizar_datos_externos()
    
    elif args.modo == 'entrenar':
        sistema.entrenar_todos_los_modelos(args.optimizar)

if __name__ == '__main__':
    main()
