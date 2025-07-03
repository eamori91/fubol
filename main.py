"""
Analizador Deportivo de Fútbol
Herramienta para analizar partidos pasados, próximos y futuros.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from flask import Flask, render_template, request

from analisis.historico import AnalisisHistorico
from analisis.proximo import AnalisisProximo
from analisis.futuro import AnalisisFuturo
from utils.data_loader import DataLoader
from utils.visualizacion import Visualizador

def main():
    print("Analizador Deportivo de Fútbol")
    print("1. Análisis de partidos históricos")
    print("2. Análisis de partidos próximos (1 semana)")
    print("3. Análisis predictivo de partidos futuros (>2 semanas)")
    print("4. Salir")
    
    opcion = input("Seleccione una opción: ")
    
    if opcion == "1":
        print("Análisis histórico seleccionado")
        analisis = AnalisisHistorico()
        # Implementar flujo de análisis histórico
    elif opcion == "2":
        print("Análisis de partidos próximos seleccionado")
        analisis = AnalisisProximo()
        # Implementar flujo de análisis próximo
    elif opcion == "3":
        print("Análisis predictivo seleccionado")
        analisis = AnalisisFuturo()
        # Implementar flujo de análisis futuro
    elif opcion == "4":
        print("Saliendo...")
        return
    else:
        print("Opción no válida")

if __name__ == "__main__":
    main()