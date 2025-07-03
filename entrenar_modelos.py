"""
Script para entrenar modelos predictivos avanzados para partidos futuros.
Incluye técnicas avanzadas como XGBoost, stacking y optimización de hiperparámetros.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import joblib

from analisis.futuro import AnalisisFuturo
from utils.data_loader import DataLoader

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Entrenamiento de modelos predictivos para fútbol')
    parser.add_argument('--optimizar', action='store_true', help='Realizar optimización de hiperparámetros')
    parser.add_argument('--visualizar', action='store_true', help='Generar visualizaciones de importancia de características')
    parser.add_argument('--generar-datos', action='store_true', help='Generar datos sintéticos para entrenamiento')
    parser.add_argument('--evaluar', action='store_true', help='Evaluar modelos después del entrenamiento')
    args = parser.parse_args()
    
    print("=" * 60)
    print("ENTRENAMIENTO DE MODELOS PREDICTIVOS AVANZADOS PARA FÚTBOL")
    print("=" * 60)
    
    # Inicializar el analizador y el cargador de datos
    analizador = AnalisisFuturo()
    data_loader = DataLoader()
    
    # Verificar si existen datos históricos
    ruta_datos = os.path.join('cache', 'partidos_historicos.csv')
    
    if os.path.exists(ruta_datos) and not args.generar_datos:
        print(f"Cargando datos históricos desde {ruta_datos}...")
        datos = data_loader.cargar_datos_csv(ruta_datos)
    else:
        print("No se encontraron datos históricos o se solicitó generación. Generando datos de ejemplo...")
        datos = analizador.generar_datos_ejemplo()
    
    if datos is None or datos.empty:
        print("Error: No se pudieron obtener datos para el entrenamiento.")
        return
    
    print(f"Se cargaron {len(datos)} partidos para entrenamiento.")
    
    # Cargar los datos en el analizador
    analizador.datos = datos
    
    # Entrenar modelos con búsqueda de hiperparámetros (si se solicita)
    busqueda_hiperparametros = args.optimizar
    if busqueda_hiperparametros:
        print("\n🔍 Se realizará optimización de hiperparámetros (esto puede tardar varios minutos)...")
    else:
        print("\n🔧 Se utilizarán modelos ensemble con parámetros predeterminados...")
    
    print("\n🔄 Iniciando entrenamiento de modelos...")
    analizador.entrenar_modelos(busqueda_hiperparametros=busqueda_hiperparametros)
    
    # Analizar importancia de características
    print("\n📊 Analizando importancia de características...")
    
    # Depuración - Verificar feature_names
    if hasattr(analizador, 'feature_names'):
        if analizador.feature_names is None:
            print("No hay nombres de características disponibles")
        else:
            print(f"Nombres de características disponibles: {len(analizador.feature_names)}")
            # Verificar si la dimensión coincide con las características usadas para entrenar
            if len(analizador.feature_names) != 77:
                print(f"ADVERTENCIA: Las dimensiones de feature_names ({len(analizador.feature_names)}) no coinciden con las características reportadas (77)")
            # Intentar cargar nombres de características desde archivo
            try:
                feature_path = os.path.join('data', 'modelos', 'feature_names.txt')
                if os.path.exists(feature_path):
                    with open(feature_path, 'r') as f:
                        analizador.feature_names = [line.strip() for line in f.readlines()]
                    print(f"Nombres de características cargados desde archivo: {len(analizador.feature_names)}")
            except Exception as e:
                print(f"Error al cargar nombres de características: {e}")
    else:
        print("El analizador no tiene atributo feature_names")
        
    importancia = analizador.analizar_importancia_caracteristicas()
    
    # Guardar resultados de importancia
    if importancia:
        importancia_dir = os.path.join('data', 'importancia')
        os.makedirs(importancia_dir, exist_ok=True)
        
        for modelo, df in importancia.items():
            if isinstance(df, pd.DataFrame):
                ruta_csv = os.path.join(importancia_dir, f'importancia_{modelo}.csv')
                df.to_csv(ruta_csv, index=False)
                print(f"Resultados de importancia guardados en {ruta_csv}")
    
    # Realizar evaluación si se solicita
    if args.evaluar:
        print("\n🧪 Realizando evaluación de modelos con datos de prueba...")
        # Cargamos los modelos para asegurarnos de evaluar los modelos guardados
        analizador.cargar_modelos()
        
        # Realizamos predicciones de ejemplo
        equipos = datos['equipo_local'].unique()
        
        if len(equipos) >= 4:
            # Evaluamos con varias combinaciones de equipos
            pares_equipos = [
                (equipos[0], equipos[1]),
                (equipos[2], equipos[3]),
                (equipos[1], equipos[0])  # Invertimos para probar diferentes roles
            ]
        else:
            pares_equipos = [
                ("FC Barcelona", "Real Madrid"),
                ("Atlético Madrid", "Sevilla FC")
            ]
        
        # Diferentes fechas para probar
        fechas = [
            datetime(2025, 10, 15),  # Temporada regular
            datetime(2025, 5, 20),   # Final de temporada
            datetime(2025, 12, 24)   # Período navideño
        ]
        
        # Realizar predicciones para diferentes combinaciones
        print("\nPredicciones de ejemplo:")
        
        for equipo_local, equipo_visitante in pares_equipos:
            for fecha in fechas[:1]:  # Limitamos a una fecha por brevedad
                prediccion = analizador.predecir_partido_futuro(equipo_local, equipo_visitante, fecha)
                
                if prediccion:
                    print(f"\n📝 Predicción para {equipo_local} vs {equipo_visitante} ({fecha.strftime('%Y-%m-%d')}):")
                    print(f"   Resultado más probable: {prediccion['resultado_predicho']}")
                    print(f"   Probabilidades: Victoria local: {prediccion['probabilidades']['victoria_local']:.1%}, "
                        f"Empate: {prediccion['probabilidades']['empate']:.1%}, "
                        f"Victoria visitante: {prediccion['probabilidades']['victoria_visitante']:.1%}")
                    print(f"   Goles predichos: {prediccion['goles_predichos']['local']} - {prediccion['goles_predichos']['visitante']}")
                    print("   Factores clave:")
                    for factor in prediccion['factores_clave']:
                        print(f"   - {factor}")
    
    print("\n✅ Entrenamiento y evaluación completados.")
    print("🔐 Los modelos han sido guardados y están listos para su uso.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error durante el entrenamiento: {e}")
        import traceback
        traceback.print_exc()
