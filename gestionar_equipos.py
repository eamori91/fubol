"""
Script para gestionar equipos y jugadores, generar datos de ejemplo
y realizar análisis predictivos con datos detallados.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import json

from analisis.entidades import GestorEquipos, Equipo, Jugador
from analisis.futuro import AnalisisFuturo
from utils.data_loader import DataLoader

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Gestión de equipos y jugadores para análisis de fútbol')
    parser.add_argument('--generar', action='store_true', help='Generar equipos y jugadores de ejemplo')
    parser.add_argument('--equipos', type=int, default=10, help='Número de equipos a generar')
    parser.add_argument('--predecir', action='store_true', help='Realizar predicciones con datos de equipos')
    parser.add_argument('--local', help='Nombre del equipo local para predicción')
    parser.add_argument('--visitante', help='Nombre del equipo visitante para predicción')
    parser.add_argument('--visualizar', action='store_true', help='Visualizar datos de equipos')
    args = parser.parse_args()
    
    print("=" * 60)
    print("SISTEMA DE GESTIÓN DE EQUIPOS Y JUGADORES")
    print("=" * 60)
    
    # Inicializar componentes
    gestor = GestorEquipos()
    data_loader = DataLoader()
    
    # Generar equipos de ejemplo si se solicita
    if args.generar:
        print(f"\n🏭 Generando {args.equipos} equipos de ejemplo con sus jugadores...")
        equipos = gestor.generar_equipos_ejemplo(args.equipos)
        
        print(f"✅ Se generaron {len(equipos)} equipos con sus jugadores")
        print(f"📊 Total de jugadores generados: {len(gestor.jugadores)}")
        print(f"\nEquipos generados:")
        
        for equipo in equipos:
            print(f"- {equipo.nombre} ({equipo.liga}, {equipo.pais}): {len(equipo.jugadores)} jugadores")
        
        print("\n💾 Datos guardados correctamente en el directorio 'data/equipos'")
    else:
        # Intentar cargar datos existentes
        print("\n📂 Cargando datos de equipos y jugadores...")
        if gestor.cargar_datos():
            print(f"✅ Se cargaron {len(gestor.equipos)} equipos y {len(gestor.jugadores)} jugadores")
        else:
            print("❌ No se pudieron cargar datos de equipos y jugadores")
            print("   Ejecute el script con '--generar' para crear datos de ejemplo")
    
    # Realizar predicciones si se solicita
    if args.predecir:
        if not args.local or not args.visitante:
            print("\n❌ Debe especificar los nombres de los equipos local y visitante para la predicción")
            print("   Ejemplo: --predecir --local \"Equipo 1\" --visitante \"Equipo 2\"")
            return
        
        print(f"\n🔮 Realizando predicción para: {args.local} vs {args.visitante}")
        
        # Obtener equipos por nombre
        equipo_local = gestor.obtener_equipo_por_nombre(args.local)
        equipo_visitante = gestor.obtener_equipo_por_nombre(args.visitante)
        
        if not equipo_local:
            print(f"❌ No se encontró el equipo local: {args.local}")
            return
        
        if not equipo_visitante:
            print(f"❌ No se encontró el equipo visitante: {args.visitante}")
            return
        
        # Cargar analizador futuro para predicciones
        analizador = AnalisisFuturo()
        
        # Cargar datos históricos para el analizador
        ruta_datos = os.path.join('cache', 'partidos_historicos.csv')
        if os.path.exists(ruta_datos):
            datos = data_loader.cargar_datos_csv(ruta_datos)
            analizador.datos = datos
        else:
            print("❌ No se encontraron datos históricos. Generando datos de ejemplo...")
            analizador.datos = analizador.generar_datos_ejemplo()
        
        # Cargar modelos entrenados
        print("📊 Cargando modelos predictivos...")
        if not analizador.cargar_modelos():
            print("❌ No se pudieron cargar los modelos. Por favor, entrene los modelos primero.")
            return
        
        # Realizar predicción base
        fecha = datetime.now()
        print(f"📅 Predicción para fecha: {fecha.strftime('%Y-%m-%d')}")
        
        prediccion_base = analizador.predecir_partido_futuro(
            equipo_local.nombre, 
            equipo_visitante.nombre, 
            fecha
        )
        
        if not prediccion_base:
            print("❌ No se pudo realizar la predicción base")
            return
        
        print("\n📊 Predicción base:")
        print(f"   Resultado más probable: {prediccion_base['resultado_predicho']}")
        print(f"   Probabilidades: Victoria local: {prediccion_base['probabilidades']['victoria_local']:.1%}, " +
              f"Empate: {prediccion_base['probabilidades']['empate']:.1%}, " +
              f"Victoria visitante: {prediccion_base['probabilidades']['victoria_visitante']:.1%}")
        print(f"   Goles predichos: {prediccion_base['goles_predichos']['local']} - " +
             f"{prediccion_base['goles_predichos']['visitante']}")
        
        # Calcular fuerzas de los equipos basadas en jugadores
        print("\n💪 Análisis de fuerzas de equipos:")
        
        fuerza_local = equipo_local.calcular_fuerza_actual(equipo_visitante, es_local=True)
        fuerza_visitante = equipo_visitante.calcular_fuerza_actual(equipo_local, es_local=False)
        
        print(f"   {equipo_local.nombre}: {fuerza_local:.2f}")
        print(f"   {equipo_visitante.nombre}: {fuerza_visitante:.2f}")
        
        # Ajustar predicción según fuerzas calculadas
        ratio_fuerzas = fuerza_local / fuerza_visitante if fuerza_visitante > 0 else 1.0
        print(f"   Ratio de fuerzas (local/visitante): {ratio_fuerzas:.2f}")
        
        # Ajustar probabilidades según fuerzas
        factor_ajuste = min(1.5, max(0.5, ratio_fuerzas))
        
        prediccion_ajustada = prediccion_base.copy()
        prediccion_ajustada['probabilidades'] = prediccion_base['probabilidades'].copy()
        
        prediccion_ajustada['probabilidades']['victoria_local'] *= factor_ajuste
        prediccion_ajustada['probabilidades']['victoria_visitante'] /= factor_ajuste
        
        # Normalizar probabilidades
        total = sum(prediccion_ajustada['probabilidades'].values())
        for k in prediccion_ajustada['probabilidades']:
            prediccion_ajustada['probabilidades'][k] /= total
        
        # Ajustar resultado más probable
        max_prob = max(prediccion_ajustada['probabilidades'].items(), key=lambda x: x[1])
        prediccion_ajustada['resultado_predicho'] = max_prob[0]
        
        # Ajustar predicción de goles
        goles_local_ajustados = prediccion_base['goles_predichos']['local'] * (ratio_fuerzas ** 0.5)
        goles_visitante_ajustados = prediccion_base['goles_predichos']['visitante'] / (ratio_fuerzas ** 0.5)
        
        prediccion_ajustada['goles_predichos'] = {
            'local': round(goles_local_ajustados, 1),
            'visitante': round(goles_visitante_ajustados, 1)
        }
        
        print("\n📈 Predicción ajustada con datos de jugadores:")
        print(f"   Resultado más probable: {prediccion_ajustada['resultado_predicho']}")
        print(f"   Probabilidades: Victoria local: {prediccion_ajustada['probabilidades']['victoria_local']:.1%}, " +
              f"Empate: {prediccion_ajustada['probabilidades']['empate']:.1%}, " +
              f"Victoria visitante: {prediccion_ajustada['probabilidades']['victoria_visitante']:.1%}")
        print(f"   Goles predichos: {prediccion_ajustada['goles_predichos']['local']} - " +
             f"{prediccion_ajustada['goles_predichos']['visitante']}")
        
        # Identificar jugadores clave para el partido
        print("\n🌟 Jugadores clave:")
        
        # Ordenar jugadores por impacto esperado en el partido
        jugadores_local = sorted(equipo_local.jugadores, 
                                key=lambda j: j.calcular_impacto_partido(True, equipo_visitante),
                                reverse=True)
        
        jugadores_visitante = sorted(equipo_visitante.jugadores,
                                    key=lambda j: j.calcular_impacto_partido(False, equipo_local),
                                    reverse=True)
        
        # Mostrar los 3 jugadores más importantes de cada equipo
        print(f"   {equipo_local.nombre}:")
        for i, jugador in enumerate(jugadores_local[:3], 1):
            impacto = jugador.calcular_impacto_partido(True, equipo_visitante)
            print(f"     {i}. {jugador.nombre} ({jugador.posicion}): {impacto:.2f}")
        
        print(f"   {equipo_visitante.nombre}:")
        for i, jugador in enumerate(jugadores_visitante[:3], 1):
            impacto = jugador.calcular_impacto_partido(False, equipo_local)
            print(f"     {i}. {jugador.nombre} ({jugador.posicion}): {impacto:.2f}")
    
    # Visualizar datos de equipos si se solicita
    if args.visualizar and gestor.equipos:
        print("\n📊 Visualizando datos de equipos...")
        
        # Obtener datos para visualización
        nombres_equipos = []
        puntos_equipos = []
        estilos_juego = {}
        
        for equipo in gestor.equipos.values():
            nombres_equipos.append(equipo.nombre)
            
            # Calcular puntos
            stats = equipo.estadisticas.get('temporada_actual', {})
            puntos = stats.get('puntos', 0)
            puntos_equipos.append(puntos)
            
            # Recopilar datos de estilo de juego
            for estilo, valor in equipo.estilo_juego.items():
                if estilo not in estilos_juego:
                    estilos_juego[estilo] = []
                estilos_juego[estilo].append(valor)
        
        # Crear directorio para visualizaciones
        vis_dir = os.path.join('data', 'visualizaciones')
        os.makedirs(vis_dir, exist_ok=True)
        
        # Visualizar puntos por equipo
        plt.figure(figsize=(12, 6))
        plt.bar(nombres_equipos, puntos_equipos)
        plt.title('Puntos por Equipo')
        plt.xlabel('Equipo')
        plt.ylabel('Puntos')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(vis_dir, 'puntos_equipos.png'))
        
        # Visualizar distribución de estilos de juego
        plt.figure(figsize=(12, 6))
        for estilo, valores in estilos_juego.items():
            plt.hist(valores, alpha=0.6, label=estilo, bins=10)
        plt.title('Distribución de Estilos de Juego')
        plt.xlabel('Valor')
        plt.ylabel('Frecuencia')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(vis_dir, 'estilos_juego.png'))
        
        print(f"✅ Visualizaciones guardadas en el directorio '{vis_dir}'")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
