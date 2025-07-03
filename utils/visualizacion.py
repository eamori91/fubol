"""
Módulo para visualizar datos y resultados del análisis deportivo.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class Visualizador:
    def __init__(self, estilo='darkgrid'):
        """Inicializa el visualizador con un estilo específico"""
        sns.set_style(estilo)
        self.paleta = sns.color_palette("muted")
        
    def grafico_rendimiento_equipo(self, datos, equipo, temporada=None, titulo=None):
        """
        Crea un gráfico de líneas mostrando el rendimiento de un equipo a lo largo del tiempo
        
        Args:
            datos: DataFrame con los datos de partidos
            equipo: Nombre del equipo a analizar
            temporada: Temporada específica (opcional)
            titulo: Título personalizado para el gráfico (opcional)
        """
        if not isinstance(datos, pd.DataFrame) or datos.empty:
            print("No hay datos disponibles para visualizar")
            return
            
        # Filtrar datos por equipo y temporada
        df = datos[(datos['equipo_local'] == equipo) | (datos['equipo_visitante'] == equipo)].copy()
        if temporada:
            df = df[df['temporada'] == temporada]
            
        if df.empty:
            print(f"No hay datos para el equipo {equipo}")
            return
            
        # Calcular puntos por partido
        df['puntos'] = 0
        for idx, row in df.iterrows():
            if row['equipo_local'] == equipo:
                if row['goles_local'] > row['goles_visitante']:
                    df.loc[idx, 'puntos'] = 3
                elif row['goles_local'] == row['goles_visitante']:
                    df.loc[idx, 'puntos'] = 1
            else:  # Es visitante
                if row['goles_visitante'] > row['goles_local']:
                    df.loc[idx, 'puntos'] = 3
                elif row['goles_local'] == row['goles_visitante']:
                    df.loc[idx, 'puntos'] = 1
        
        # Ordenar por fecha
        df = df.sort_values('fecha')
        
        # Calcular puntos acumulados
        df['puntos_acumulados'] = df['puntos'].cumsum()
        
        # Crear el gráfico
        plt.figure(figsize=(12, 6))
        plt.plot(df['fecha'], df['puntos_acumulados'], marker='o', linewidth=2, color=self.paleta[0])
        
        if not titulo:
            titulo = f"Rendimiento de {equipo}" + (f" - Temporada {temporada}" if temporada else "")
        
        plt.title(titulo, fontsize=15)
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel('Puntos acumulados', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()
    
    def comparativa_equipos(self, datos, equipos, metricas, temporada=None):
        """
        Crea un gráfico de barras comparando estadísticas de varios equipos
        
        Args:
            datos: DataFrame con los datos
            equipos: Lista de nombres de equipos a comparar
            metricas: Lista de métricas a comparar ('goles_favor', 'goles_contra', etc)
            temporada: Temporada específica (opcional)
        """
        if not isinstance(datos, pd.DataFrame) or datos.empty:
            print("No hay datos disponibles para visualizar")
            return
            
        # Filtrar por temporada si se especifica
        df = datos.copy()
        if temporada:
            df = df[df['temporada'] == temporada]
        
        # Preparar datos para la visualización
        resultados = []
        for equipo in equipos:
            datos_equipo = {}
            datos_equipo['equipo'] = equipo
            
            for metrica in metricas:
                # Lógica para calcular la métrica específica para el equipo
                # Ejemplo simplificado:
                valor = df[df['equipo'] == equipo][metrica].mean() if metrica in df.columns else 0
                datos_equipo[metrica] = valor
                
            resultados.append(datos_equipo)
            
        # Convertir a DataFrame
        df_resultados = pd.DataFrame(resultados)
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Configurar ancho de barras
        bar_width = 0.8 / len(metricas)
        positions = np.arange(len(equipos))
        
        # Dibujar barras para cada métrica
        for i, metrica in enumerate(metricas):
            offset = bar_width * i - bar_width * (len(metricas) - 1) / 2
            ax.bar(positions + offset, df_resultados[metrica], 
                   width=bar_width, label=metrica, color=self.paleta[i % len(self.paleta)])
        
        # Configurar etiquetas y leyenda
        ax.set_xticks(positions)
        ax.set_xticklabels(equipos, rotation=45, ha='right')
        ax.legend()
        
        plt.title('Comparativa de equipos', fontsize=15)
        plt.tight_layout()
        
        return fig
    
    def mapa_calor_correlacion(self, datos, variables, titulo="Correlación entre variables"):
        """
        Crea un mapa de calor mostrando la correlación entre variables
        
        Args:
            datos: DataFrame con los datos
            variables: Lista de variables a incluir en la correlación
            titulo: Título del gráfico
        """
        if not isinstance(datos, pd.DataFrame) or datos.empty:
            print("No hay datos disponibles para visualizar")
            return
            
        # Filtrar solo las variables de interés
        df = datos[variables].copy()
        
        # Calcular matriz de correlación
        corr_matrix = df.corr()
        
        # Crear mapa de calor
        plt.figure(figsize=(10, 8))
        heatmap = sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', linewidths=0.5, fmt=".2f", vmin=-1, vmax=1)
        
        plt.title(titulo, fontsize=15)
        plt.tight_layout()
        
        return plt.gcf()
    
    def grafico_prediccion_resultado(self, predicciones, titulo="Probabilidad de resultados"):
        """
        Crea un gráfico de pie mostrando la probabilidad de cada resultado
        
        Args:
            predicciones: Diccionario con probabilidades {'victoria_local': 0.5, 'empate': 0.3, 'victoria_visitante': 0.2}
            titulo: Título del gráfico
        """
        # Verificar datos
        if not isinstance(predicciones, dict) or not all(k in predicciones for k in ['victoria_local', 'empate', 'victoria_visitante']):
            print("Formato de predicciones incorrecto")
            return
            
        # Extraer datos
        labels = ['Victoria Local', 'Empate', 'Victoria Visitante']
        sizes = [predicciones['victoria_local'], predicciones['empate'], predicciones['victoria_visitante']]
        
        # Crear gráfico
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.paleta[:3],
                wedgeprops={'edgecolor': 'white', 'linewidth': 1})
        
        plt.title(titulo, fontsize=15)
        plt.axis('equal')  # Para asegurar que se vea circular
        
        return plt.gcf()