"""
Script para realizar simulaciones Monte Carlo de partidos de fútbol.
Permite realizar múltiples simulaciones para obtener distribuciones de probabilidad
más robustas y generar visualizaciones de esas distribuciones.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import json

from analisis.futuro import AnalisisFuturo
from analisis.simulador import SimuladorPartidos
from analisis.entidades import GestorEquipos
from utils.data_loader import DataLoader

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Simulación Monte Carlo de partidos de fútbol')
    parser.add_argument('--local', required=True, help='Nombre del equipo local')
    parser.add_argument('--visitante', required=True, help='Nombre del equipo visitante')
    parser.add_argument('--fecha', help='Fecha del partido (YYYY-MM-DD)')
    parser.add_argument('--n', type=int, default=1000, help='Número de simulaciones Monte Carlo')
    parser.add_argument('--eventos', action='store_true', help='Simular eventos minuto a minuto')
    parser.add_argument('--visualizar', action='store_true', help='Generar visualizaciones')
    parser.add_argument('--detalle', action='store_true', help='Nivel de detalle avanzado en simulación')
    parser.add_argument('--timeline', action='store_true', help='Generar timeline de eventos')
    parser.add_argument('--heatmap', action='store_true', help='Generar heatmap de eventos')
    parser.add_argument('--guardar', action='store_true', help='Guardar resultados y visualizaciones')
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"SIMULACIÓN DE PARTIDO: {args.local} vs {args.visitante}")
    print("=" * 60)
    
    # Preparar fecha
    if args.fecha:
        try:
            fecha = datetime.strptime(args.fecha, '%Y-%m-%d')
        except ValueError:
            print("Formato de fecha incorrecto. Usando fecha actual.")
            fecha = datetime.now()
    else:
        fecha = datetime.now()
    
    print(f"Fecha: {fecha.strftime('%d/%m/%Y')}")
    
    # Inicializar componentes
    analizador = AnalisisFuturo()
    simulador = SimuladorPartidos(analizador)
    gestor_equipos = GestorEquipos()
    
    # Cargar datos de equipos si existen
    jugadores_local = None
    jugadores_visitante = None
    
    try:
        equipo_local_obj = gestor_equipos.cargar_equipo(args.local)
        equipo_visitante_obj = gestor_equipos.cargar_equipo(args.visitante)
        
        if equipo_local_obj:
            print(f"Equipo local cargado: {equipo_local_obj.nombre}")
            jugadores_local = [
                {
                    'nombre': jugador.nombre,
                    'posicion': jugador.posicion,
                    'rol': jugador.rol,
                    'habilidad': jugador.habilidad
                }
                for jugador in equipo_local_obj.jugadores
            ]
        
        if equipo_visitante_obj:
            print(f"Equipo visitante cargado: {equipo_visitante_obj.nombre}")
            jugadores_visitante = [
                {
                    'nombre': jugador.nombre,
                    'posicion': jugador.posicion,
                    'rol': jugador.rol,
                    'habilidad': jugador.habilidad
                }
                for jugador in equipo_visitante_obj.jugadores
            ]
    except Exception as e:
        print(f"No se pudieron cargar los datos de los equipos: {e}")
    
    print("-" * 60)
    
    # Simulación Monte Carlo
    if not args.eventos:
        print(f"Ejecutando {args.n} simulaciones Monte Carlo...")
        resultados = simulador.simular_partido_monte_carlo(
            args.local, 
            args.visitante, 
            fecha=fecha, 
            n_simulaciones=args.n
        )
        
        # Mostrar resultados
        print("\nRESULTADOS DE LA SIMULACIÓN:")
        print(f"Probabilidad de victoria {args.local}: {resultados['probabilidades']['victoria_local']:.2%}")
        print(f"Probabilidad de empate: {resultados['probabilidades']['empate']:.2%}")
        print(f"Probabilidad de victoria {args.visitante}: {resultados['probabilidades']['victoria_visitante']:.2%}")
        print(f"Resultado más probable: {resultados['resultado_mas_probable']}")
        
        # Visualizaciones
        if args.visualizar:
            print("\nGenerando visualizaciones...")
            fig = simulador.visualizar_distribucion_resultados(resultados)
            plt.show()
            
            if args.guardar:
                simulador.guardar_resultados(resultados, args.local, args.visitante)
                print("Resultados y visualizaciones guardados.")
    
    # Simulación de eventos
    else:
        print("Simulando partido con eventos minuto a minuto...")
        simulacion = simulador.simular_partido_eventos(
            args.local, 
            args.visitante,
            jugadores_local=jugadores_local,
            jugadores_visitante=jugadores_visitante,
            detalle_avanzado=args.detalle
        )
        
        # Mostrar resultado
        print("\nRESULTADO FINAL:")
        print(f"{args.local} {simulacion['resultado']['local']} - {simulacion['resultado']['visitante']} {args.visitante}")
        
        # Mostrar estadísticas
        print("\nESTADÍSTICAS:")
        print(f"Posesión: {args.local} {simulacion['estadisticas']['posesion']['local']}% - "
              f"{simulacion['estadisticas']['posesion']['visitante']}% {args.visitante}")
        print(f"Tiros: {args.local} {simulacion['estadisticas']['tiros']['local']} - "
              f"{simulacion['estadisticas']['tiros']['visitante']} {args.visitante}")
        print(f"Tiros a puerta: {args.local} {simulacion['estadisticas']['tiros_puerta']['local']} - "
              f"{simulacion['estadisticas']['tiros_puerta']['visitante']} {args.visitante}")
        print(f"Corners: {args.local} {simulacion['estadisticas']['corners']['local']} - "
              f"{simulacion['estadisticas']['corners']['visitante']} {args.visitante}")
        
        # Mostrar tarjetas
        print(f"\nTARJETAS {args.local}:")
        print(f"Amarillas: {simulacion['tarjetas']['local']['amarilla']}")
        print(f"Rojas: {simulacion['tarjetas']['local']['roja']}")
        
        print(f"\nTARJETAS {args.visitante}:")
        print(f"Amarillas: {simulacion['tarjetas']['visitante']['amarilla']}")
        print(f"Rojas: {simulacion['tarjetas']['visitante']['roja']}")
        
        # Mostrar eventos principales
        print("\nEVENTOS PRINCIPALES:")
        for evento in simulacion['eventos']:
            # Solo mostrar eventos significativos
            if evento['tipo'] in ['gol', 'penalti', 'tarjeta_roja', 'final_partido']:
                print(f"Min {evento['minuto']}: {evento['descripcion']}")
        
        # Visualizaciones avanzadas
        if args.timeline:
            print("\nGenerando timeline del partido...")
            fig_timeline = simulador.visualizar_timeline_partido(
                simulacion['eventos'],
                args.local,
                args.visitante,
                simulacion['resultado'],
                guardar=args.guardar
            )
            plt.show()
        
        if args.heatmap:
            print("\nGenerando heatmap de eventos...")
            fig_heatmap = simulador.visualizar_heatmap_eventos(
                simulacion['eventos'],
                simulacion['estadisticas'],
                args.local,
                args.visitante,
                simulacion['resultado'],
                guardar=args.guardar
            )
            plt.show()
        
        # Guardar simulación completa
        if args.guardar:
            ruta_simulacion = os.path.join('data', 'simulaciones', 
                                         f"simulacion_{args.local}_{args.visitante}_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
            os.makedirs(os.path.dirname(ruta_simulacion), exist_ok=True)
            
            # Limpiar tipos de datos no serializables
            simulacion_json = {
                'equipos': simulacion['equipos'],
                'resultado': simulacion['resultado'],
                'estadisticas': simulacion['estadisticas'],
                'tarjetas': simulacion['tarjetas'],
                'eventos': [
                    {k: str(v) if not isinstance(v, (str, int, float, bool, dict, list)) else v 
                     for k, v in evento.items()}
                    for evento in simulacion['eventos']
                ]
            }
            
            with open(ruta_simulacion, 'w', encoding='utf-8') as f:
                json.dump(simulacion_json, f, ensure_ascii=False, indent=2)
            
            print(f"Simulación guardada en: {ruta_simulacion}")

if __name__ == "__main__":
    main()
