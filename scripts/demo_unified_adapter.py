"""
Script de demostración para probar el adaptador de datos unificado.

Este script muestra cómo utilizar el adaptador unificado para obtener datos
de fuentes gratuitas como Football-Data.org, Open Football Data, ESPN, etc.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from tabulate import tabulate
from colorama import init, Fore, Style

# Añadir directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

# Importar el adaptador unificado
from utils.unified_data_adapter import UnifiedDataAdapter

# Inicializar colorama para salida con colores en consola
init()

def print_title(title):
    """Imprime un título formateado"""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{title.center(80)}")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

def print_section(section):
    """Imprime un título de sección"""
    print(f"\n{Fore.GREEN}{'-' * 60}")
    print(f"{section}")
    print(f"{'-' * 60}{Style.RESET_ALL}\n")

def print_error(message):
    """Imprime un mensaje de error"""
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def print_success(message):
    """Imprime un mensaje de éxito"""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def demo_proximos_partidos(adapter):
    """Demostración de obtener próximos partidos"""
    print_section("1. Próximos partidos (7 días)")
    
    try:
        partidos = adapter.obtener_proximos_partidos(dias=7)
        
        if not partidos:
            print_error("No se encontraron partidos próximos.")
            return
        
        # Preparar datos para tabla
        headers = ["Fecha", "Liga", "Local", "Visitante", "Estadio", "Fuente"]
        rows = []
        
        for p in partidos[:10]:  # Mostrar solo los primeros 10
            # Intentar convertir fecha si es string
            fecha = p.get('fecha', '')
            if isinstance(fecha, str):
                try:
                    fecha_dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                    fecha_formateada = fecha_dt.strftime('%d/%m/%Y %H:%M')
                except:
                    fecha_formateada = fecha
            else:
                fecha_formateada = fecha
                
            rows.append([
                fecha_formateada,
                p.get('liga', ''),
                p.get('equipo_local', ''),
                p.get('equipo_visitante', ''),
                p.get('estadio', ''),
                p.get('fuente', '')
            ])
        
        print(tabulate(rows, headers=headers, tablefmt="pretty"))
        print_success(f"Total de partidos encontrados: {len(partidos)}")
        
        # Mostrar ligas disponibles
        ligas = set([p.get('liga') for p in partidos if p.get('liga')])
        if ligas:
            print(f"\nLigas disponibles: {', '.join(ligas)}")
        
    except Exception as e:
        print_error(f"Error al obtener próximos partidos: {e}")

def demo_datos_equipo(adapter):
    """Demostración de obtener datos de un equipo"""
    print_section("2. Datos de un equipo")
    
    equipos_muestra = ["Barcelona", "Real Madrid", "Liverpool", "Manchester United"]
    
    for equipo in equipos_muestra:
        print(f"\nBuscando datos para: {Fore.YELLOW}{equipo}{Style.RESET_ALL}")
        
        try:
            datos = adapter.obtener_datos_equipo(equipo)
            
            if not datos:
                print_error(f"No se encontró información para {equipo}")
                continue
            
            # Mostrar datos básicos del equipo
            print(f"Nombre: {Fore.YELLOW}{datos.get('nombre', '')}{Style.RESET_ALL}")
            print(f"País: {datos.get('pais', '')}")
            print(f"Estadio: {datos.get('estadio', '')}")
            print(f"Liga: {datos.get('liga', '')}")
            
            # Intentar obtener jugadores
            print("\nObteniendo plantilla del equipo...")
            jugadores = adapter.obtener_jugadores_equipo(equipo)
            
            if jugadores:
                # Mostrar algunos jugadores
                headers = ["Nombre", "Posición", "Edad", "País"]
                rows = []
                
                for j in jugadores[:5]:  # Mostrar solo 5 jugadores
                    rows.append([
                        j.get('nombre', ''),
                        j.get('posicion', ''),
                        j.get('edad', ''),
                        j.get('pais', '')
                    ])
                
                print("\nAlgunos jugadores del equipo:")
                print(tabulate(rows, headers=headers, tablefmt="pretty"))
                print(f"Total de jugadores: {len(jugadores)}")
            else:
                print("No se encontraron jugadores para este equipo")
                
        except Exception as e:
            print_error(f"Error al obtener datos de {equipo}: {e}")

def demo_arbitros(adapter):
    """Demostración de obtener datos de árbitros"""
    print_section("3. Datos de árbitros")
    
    try:
        # Obtener lista de árbitros
        arbitros = adapter.obtener_arbitros()
        
        if not arbitros:
            print_error("No se encontraron árbitros.")
            return
        
        print(f"Se encontraron {len(arbitros)} árbitros.")
        
        # Mostrar algunos árbitros
        headers = ["Nombre", "País", "Competición principal"]
        rows = []
        
        for a in arbitros[:10]:  # Mostrar solo 10 árbitros
            rows.append([
                a.get('nombre', ''),
                a.get('pais', ''),
                a.get('competicion_principal', '')
            ])
        
        print("\nÁrbitros disponibles:")
        print(tabulate(rows, headers=headers, tablefmt="pretty"))
        
        # Seleccionar un árbitro para ver sus estadísticas
        if arbitros:
            arbitro_ejemplo = arbitros[0].get('nombre')
            print(f"\nEstadísticas del árbitro: {Fore.YELLOW}{arbitro_ejemplo}{Style.RESET_ALL}")
            
            estadisticas = adapter.obtener_historial_arbitro(arbitro_ejemplo)
            
            if estadisticas:
                print(f"Partidos dirigidos: {estadisticas.get('partidos', 0)}")
                print(f"Tarjetas amarillas por partido: {estadisticas.get('tarjetas_amarillas_promedio', 0)}")
                print(f"Tarjetas rojas por partido: {estadisticas.get('tarjetas_rojas_promedio', 0)}")
                
                # Si hay estadísticas por equipo
                if 'estadisticas_equipo' in estadisticas:
                    est_equipo = estadisticas['estadisticas_equipo']
                    print(f"\nEstadísticas con un equipo específico:")
                    print(f"  Partidos: {est_equipo.get('partidos', 0)}")
                    print(f"  Victorias: {est_equipo.get('victorias', 0)}")
                    print(f"  Empates: {est_equipo.get('empates', 0)}")
                    print(f"  Derrotas: {est_equipo.get('derrotas', 0)}")
                    print(f"  Efectividad: {est_equipo.get('efectividad', 0)}%")
            else:
                print("No se encontraron estadísticas para este árbitro")
                
    except Exception as e:
        print_error(f"Error al obtener datos de árbitros: {e}")

def main():
    """Función principal"""
    print_title("DEMOSTRACIÓN DEL ADAPTADOR UNIFICADO DE DATOS DE FÚTBOL")
    print("Este script muestra cómo obtener datos de fútbol de fuentes gratuitas unificadas")
    
    # Crear instancia del adaptador
    adapter = UnifiedDataAdapter()
    print(f"Adaptador inicializado con {adapter._count_active_sources()} fuentes activas")
    
    # Ejecutar demostraciones
    try:
        demo_proximos_partidos(adapter)
        demo_datos_equipo(adapter)
        demo_arbitros(adapter)
        
        print_title("DEMOSTRACIÓN COMPLETADA")
    except Exception as e:
        print_error(f"Error durante la demostración: {e}")

if __name__ == "__main__":
    main()
