"""
Módulo para análisis predictivo de partidos futuros (>2 semanas).
Utiliza modelos predictivos considerando la historia larga y corta del equipo.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
import joblib
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingClassifier, GradientBoostingRegressor, StackingClassifier, VotingClassifier, VotingRegressor
from sklearn.linear_model import LogisticRegression, Ridge, ElasticNet, Lasso
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, TimeSeriesSplit, KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, mean_squared_error, f1_score, classification_report, confusion_matrix, precision_recall_curve, roc_curve, auc
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PowerTransformer, RobustScaler, QuantileTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import SelectFromModel, RFE, mutual_info_classif, mutual_info_regression, RFECV
import xgboost as xgb
import optuna
import warnings
import shap
from sklearn.exceptions import ConvergenceWarning

# Suprimir advertencias no críticas
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

class AnalisisFuturo:
    def __init__(self):
        self.datos = None
        self.modelo_resultado = None
        self.modelo_goles_local = None
        self.modelo_goles_visitante = None
        self.scaler = None
        self.encoder = None
        self.feature_names = None
        self.modelos_dir = os.path.join('data', 'modelos')
        os.makedirs(self.modelos_dir, exist_ok=True)
    
    def cargar_datos(self, ruta_archivo):
        """Carga datos históricos para entrenar modelos predictivos"""
        try:
            self.datos = pd.read_csv(ruta_archivo)
            return True
        except Exception as e:
            print(f"Error al cargar datos: {e}")
            return False
    
    def preparar_caracteristicas(self):
        """Prepara características avanzadas para los modelos predictivos"""
        if self.datos is None:
            print("No hay datos disponibles")
            return None, None, None, None
        
        # Creamos una copia para trabajar
        datos = self.datos.copy()
        
        # 1. Procesar datos y agregar variables derivadas
        
        # Convertir fecha a datetime
        datos['fecha'] = pd.to_datetime(datos['fecha'])
        
        # Crear variable para resultado (usaremos como target)
        datos['resultado'] = 'empate'  # valor por defecto
        datos.loc[datos['goles_local'] > datos['goles_visitante'], 'resultado'] = 'victoria_local'
        datos.loc[datos['goles_local'] < datos['goles_visitante'], 'resultado'] = 'victoria_visitante'
        
        # 2. Crear características históricas para cada equipo
        
        # Ordenar por fecha para cálculos históricos correctos
        datos = datos.sort_values('fecha')
        
        # Listas para almacenar nuestras filas de características procesadas
        filas_features = []
        resultados = []
        goles_local_list = []
        goles_visitante_list = []
        
        # Procesamos cada partido a partir de cierta fecha (permitimos acumular datos históricos)
        fecha_inicio_modelado = datos['fecha'].min() + pd.Timedelta(days=60)  # Empezamos después de acumular 2 meses de datos
        
        for idx, partido in datos[datos['fecha'] >= fecha_inicio_modelado].iterrows():
            # Fecha límite para datos históricos (todo antes del partido actual)
            fecha_limite = partido['fecha'] - pd.Timedelta(days=1)
            datos_historicos = datos[datos['fecha'] <= fecha_limite]
            
            # Extraemos características para equipo local
            features_local = self._calcular_features_equipo(
                datos_historicos, 
                partido['equipo_local'],
                partido['equipo_visitante'],
                partido['fecha'],
                es_local=True
            )
            
            # Extraemos características para equipo visitante
            features_visitante = self._calcular_features_equipo(
                datos_historicos,
                partido['equipo_visitante'],
                partido['equipo_local'],
                partido['fecha'],
                es_local=False
            )
            
            # Otras características del partido
            features_partido = {
                'mes': partido['fecha'].month,
                'dia_semana': partido['fecha'].dayofweek,
                'liga': partido['liga'],
                'temporada': partido['temporada']
            }
            
            # Combinamos todas las características
            features_combinadas = {**features_local, **features_visitante, **features_partido}
            filas_features.append(features_combinadas)
            
            # Guardamos los valores objetivo
            resultados.append(partido['resultado'])
            goles_local_list.append(partido['goles_local'])
            goles_visitante_list.append(partido['goles_visitante'])
        
        # Convertimos a DataFrame
        df_features = pd.DataFrame(filas_features)
        
        # Almacenamos los nombres de las características para uso futuro
        self.feature_names = df_features.columns.tolist()
        
        # 3. Preparar para entrenamiento (separar numéricos y categóricos)
        numeric_features = df_features.select_dtypes(include=['int64', 'float64']).columns
        categorical_features = df_features.select_dtypes(include=['object', 'category']).columns
        
        # Definimos el preprocesador
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])
        
        # Guardamos el preprocesador
        self.preprocessor = preprocessor
        
        return df_features, resultados, goles_local_list, goles_visitante_list
    
    def _calcular_features_equipo(self, datos_historicos, equipo, rival, fecha_partido, es_local=True):
        """Calcula características avanzadas para un equipo específico"""
        # Filtros para diferentes vistas de los datos
        datos_equipo = datos_historicos[(datos_historicos['equipo_local'] == equipo) | 
                                       (datos_historicos['equipo_visitante'] == equipo)]
        
        datos_local = datos_historicos[datos_historicos['equipo_local'] == equipo]
        datos_visitante = datos_historicos[datos_historicos['equipo_visitante'] == equipo]
        
        # Enfrentamientos directos
        enfrentamientos = datos_historicos[
            ((datos_historicos['equipo_local'] == equipo) & (datos_historicos['equipo_visitante'] == rival)) |
            ((datos_historicos['equipo_local'] == rival) & (datos_historicos['equipo_visitante'] == equipo))
        ]
        
        # Datos recientes (últimos 5 partidos)
        datos_recientes = datos_equipo.sort_values('fecha').tail(5)
        
        # Datos de los últimos 10 partidos para análisis de forma
        datos_ultimos10 = datos_equipo.sort_values('fecha').tail(10)
        
        # Datos última temporada
        temporada = self._obtener_temporada(fecha_partido)
        datos_temporada = datos_equipo[datos_equipo['temporada'] == temporada]
        
        # Datos de los últimos 30 días para análisis de cansancio
        fecha_30_dias = pd.to_datetime(fecha_partido) - timedelta(days=30)
        datos_mes = datos_equipo[datos_equipo['fecha'] >= fecha_30_dias]
        
        # Prefijo para las características
        prefijo = 'local_' if es_local else 'visitante_'
        
        # Características generales
        features = {}
        
        # 1. Rendimiento general
        if not datos_equipo.empty:
            # Promedio de goles
            if es_local:
                gf_total = datos_local['goles_local'].sum() + datos_visitante['goles_visitante'].sum()
                gc_total = datos_local['goles_visitante'].sum() + datos_visitante['goles_local'].sum()
            else:
                gf_total = datos_visitante['goles_visitante'].sum() + datos_local['goles_local'].sum()
                gc_total = datos_visitante['goles_local'].sum() + datos_local['goles_visitante'].sum()
            
            features[f'{prefijo}promedio_goles_favor'] = gf_total / len(datos_equipo)
            features[f'{prefijo}promedio_goles_contra'] = gc_total / len(datos_equipo)
            
            # NUEVA: Eficiencia ofensiva y defensiva (media móvil)
            if len(datos_ultimos10) > 0:
                goles_favor_10 = 0
                goles_contra_10 = 0
                
                for _, partido in datos_ultimos10.iterrows():
                    if partido['equipo_local'] == equipo:
                        goles_favor_10 += partido['goles_local']
                        goles_contra_10 += partido['goles_visitante']
                    else:
                        goles_favor_10 += partido['goles_visitante']
                        goles_contra_10 += partido['goles_local']
                
                features[f'{prefijo}eficiencia_ofensiva'] = goles_favor_10 / len(datos_ultimos10)
                features[f'{prefijo}eficiencia_defensiva'] = goles_contra_10 / len(datos_ultimos10)
                
                # NUEVA: Tendencia de goles (comparando últimos 5 con los 5 anteriores)
                if len(datos_ultimos10) >= 10:
                    ultimos5 = datos_ultimos10.tail(5)
                    anteriores5 = datos_ultimos10.head(5)
                    
                    gf_ultimos5 = 0
                    gf_anteriores5 = 0
                    
                    for _, partido in ultimos5.iterrows():
                        if partido['equipo_local'] == equipo:
                            gf_ultimos5 += partido['goles_local']
                        else:
                            gf_ultimos5 += partido['goles_visitante']
                            
                    for _, partido in anteriores5.iterrows():
                        if partido['equipo_local'] == equipo:
                            gf_anteriores5 += partido['goles_local']
                        else:
                            gf_anteriores5 += partido['goles_visitante']
                            
                    features[f'{prefijo}tendencia_goles'] = (gf_ultimos5 - gf_anteriores5) / 5
                else:
                    features[f'{prefijo}tendencia_goles'] = 0
            else:
                features[f'{prefijo}eficiencia_ofensiva'] = features[f'{prefijo}promedio_goles_favor']
                features[f'{prefijo}eficiencia_defensiva'] = features[f'{prefijo}promedio_goles_contra']
                features[f'{prefijo}tendencia_goles'] = 0
            
            # NUEVA: Factor de cansancio (partidos en los últimos 30 días)
            features[f'{prefijo}factor_cansancio'] = len(datos_mes) / 6  # Normalizado (6 partidos por mes sería un valor alto)
            
            # Forma (victorias, empates, derrotas en últimos 5 partidos)
            victorias = 0
            empates = 0
            derrotas = 0
            
            for _, partido in datos_recientes.iterrows():
                if partido['equipo_local'] == equipo:
                    if partido['goles_local'] > partido['goles_visitante']:
                        victorias += 1
                    elif partido['goles_local'] == partido['goles_visitante']:
                        empates += 1
                    else:
                        derrotas += 1
                else:
                    if partido['goles_visitante'] > partido['goles_local']:
                        victorias += 1
                    elif partido['goles_visitante'] == partido['goles_local']:
                        empates += 1
                    else:
                        derrotas += 1
            
            features[f'{prefijo}victorias_recientes'] = victorias
            features[f'{prefijo}empates_recientes'] = empates
            features[f'{prefijo}derrotas_recientes'] = derrotas
            features[f'{prefijo}puntos_recientes'] = victorias * 3 + empates
            
            # NUEVA: Consistencia (variabilidad en los resultados)
            if len(datos_recientes) >= 3:
                resultados = []
                for _, partido in datos_recientes.iterrows():
                    if partido['equipo_local'] == equipo:
                        if partido['goles_local'] > partido['goles_visitante']:
                            resultados.append(3)  # victoria
                        elif partido['goles_local'] == partido['goles_visitante']:
                            resultados.append(1)  # empate
                        else:
                            resultados.append(0)  # derrota
                    else:
                        if partido['goles_visitante'] > partido['goles_local']:
                            resultados.append(3)  # victoria
                        elif partido['goles_visitante'] == partido['goles_local']:
                            resultados.append(1)  # empate
                        else:
                            resultados.append(0)  # derrota
                
                features[f'{prefijo}consistencia'] = np.std(resultados) if len(resultados) > 1 else 1
            else:
                features[f'{prefijo}consistencia'] = 1  # valor neutral
            
            # Estadísticas de la temporada actual
            if not datos_temporada.empty:
                partidos_temporada = len(datos_temporada)
                features[f'{prefijo}partidos_temporada'] = partidos_temporada
                
                # Calcular victorias, empates, derrotas en temporada
                victorias_temp = 0
                empates_temp = 0
                derrotas_temp = 0
                
                for _, partido in datos_temporada.iterrows():
                    if partido['equipo_local'] == equipo:
                        if partido['goles_local'] > partido['goles_visitante']:
                            victorias_temp += 1
                        elif partido['goles_local'] == partido['goles_visitante']:
                            empates_temp += 1
                        else:
                            derrotas_temp += 1
                    else:
                        if partido['goles_visitante'] > partido['goles_local']:
                            victorias_temp += 1
                        elif partido['goles_visitante'] == partido['goles_local']:
                            empates_temp += 1
                        else:
                            derrotas_temp += 1
                
                features[f'{prefijo}victorias_temporada'] = victorias_temp
                features[f'{prefijo}empates_temporada'] = empates_temp
                features[f'{prefijo}derrotas_temporada'] = derrotas_temp
                features[f'{prefijo}puntos_temporada'] = victorias_temp * 3 + empates_temp
                
                if partidos_temporada > 0:
                    features[f'{prefijo}puntos_por_partido'] = (victorias_temp * 3 + empates_temp) / partidos_temporada
                    
                # NUEVA: Evolución durante la temporada
                if partidos_temporada >= 10:
                    # Dividir la temporada en dos mitades
                    mitad = len(datos_temporada) // 2
                    primera_mitad = datos_temporada.sort_values('fecha').head(mitad)
                    segunda_mitad = datos_temporada.sort_values('fecha').tail(mitad)
                    
                    # Calcular puntos en cada mitad
                    puntos_primera = 0
                    puntos_segunda = 0
                    
                    for _, partido in primera_mitad.iterrows():
                        if partido['equipo_local'] == equipo:
                            if partido['goles_local'] > partido['goles_visitante']:
                                puntos_primera += 3
                            elif partido['goles_local'] == partido['goles_visitante']:
                                puntos_primera += 1
                        else:
                            if partido['goles_visitante'] > partido['goles_local']:
                                puntos_primera += 3
                            elif partido['goles_visitante'] == partido['goles_local']:
                                puntos_primera += 1
                    
                    for _, partido in segunda_mitad.iterrows():
                        if partido['equipo_local'] == equipo:
                            if partido['goles_local'] > partido['goles_visitante']:
                                puntos_segunda += 3
                            elif partido['goles_local'] == partido['goles_visitante']:
                                puntos_segunda += 1
                        else:
                            if partido['goles_visitante'] > partido['goles_local']:
                                puntos_segunda += 3
                            elif partido['goles_visitante'] == partido['goles_local']:
                                puntos_segunda += 1
                    
                    # Normalizar por número de partidos
                    puntos_primera = puntos_primera / len(primera_mitad) if len(primera_mitad) > 0 else 0
                    puntos_segunda = puntos_segunda / len(segunda_mitad) if len(segunda_mitad) > 0 else 0
                    
                    # Calcular evolución (diferencia entre segunda y primera mitad)
                    features[f'{prefijo}evolucion_temporada'] = puntos_segunda - puntos_primera
                else:
                    features[f'{prefijo}evolucion_temporada'] = 0
            else:
                # Valores por defecto si no hay datos de temporada
                features[f'{prefijo}partidos_temporada'] = 0
                features[f'{prefijo}victorias_temporada'] = 0
                features[f'{prefijo}empates_temporada'] = 0
                features[f'{prefijo}derrotas_temporada'] = 0
                features[f'{prefijo}puntos_temporada'] = 0
                features[f'{prefijo}puntos_por_partido'] = 0
                features[f'{prefijo}evolucion_temporada'] = 0
        
        # 2. Estadísticas específicas del rol (local/visitante)
        datos_rol = datos_local if es_local else datos_visitante
        
        if not datos_rol.empty:
            # Campo de goles según el rol
            campo_goles_favor = 'goles_local' if es_local else 'goles_visitante'
            campo_goles_contra = 'goles_visitante' if es_local else 'goles_local'
            
            features[f'{prefijo}promedio_goles_favor_rol'] = datos_rol[campo_goles_favor].mean()
            features[f'{prefijo}promedio_goles_contra_rol'] = datos_rol[campo_goles_contra].mean()
            
            # Otras estadísticas de rendimiento según el rol
            victorias_rol = sum(datos_rol[campo_goles_favor] > datos_rol[campo_goles_contra])
            empates_rol = sum(datos_rol[campo_goles_favor] == datos_rol[campo_goles_contra])
            derrotas_rol = sum(datos_rol[campo_goles_favor] < datos_rol[campo_goles_contra])
            
            features[f'{prefijo}victorias_rol'] = victorias_rol
            features[f'{prefijo}empates_rol'] = empates_rol
            features[f'{prefijo}derrotas_rol'] = derrotas_rol
            
            if len(datos_rol) > 0:
                features[f'{prefijo}porcentaje_victorias_rol'] = victorias_rol / len(datos_rol)
                
                # NUEVA: "Home Field Advantage" o ventaja de localía
                if es_local:
                    # Calculamos la diferencia de rendimiento entre local y visitante
                    if not datos_visitante.empty:
                        victorias_visit = sum(datos_visitante['goles_visitante'] > datos_visitante['goles_local'])
                        prop_victorias_visit = victorias_visit / len(datos_visitante) if len(datos_visitante) > 0 else 0
                        
                        # La ventaja de localía es la diferencia entre el % de victorias como local vs visitante
                        features[f'{prefijo}home_advantage'] = (victorias_rol / len(datos_rol)) - prop_victorias_visit
                    else:
                        features[f'{prefijo}home_advantage'] = 0.1  # valor predeterminado si no hay datos
                else:
                    features[f'{prefijo}home_advantage'] = 0  # no aplica para visitante
            else:
                features[f'{prefijo}porcentaje_victorias_rol'] = 0
                features[f'{prefijo}home_advantage'] = 0.1 if es_local else 0
        else:
            # Valores por defecto si no hay datos en ese rol
            features[f'{prefijo}promedio_goles_favor_rol'] = 0
            features[f'{prefijo}promedio_goles_contra_rol'] = 0
            features[f'{prefijo}victorias_rol'] = 0
            features[f'{prefijo}empates_rol'] = 0
            features[f'{prefijo}derrotas_rol'] = 0
            features[f'{prefijo}porcentaje_victorias_rol'] = 0
            features[f'{prefijo}home_advantage'] = 0.1 if es_local else 0
        
        # 3. Enfrentamientos directos con el rival
        if not enfrentamientos.empty:
            victorias_vs = 0
            empates_vs = 0
            derrotas_vs = 0
            
            # NUEVA: Factor recencia para enfrentamientos (los más recientes pesan más)
            enfrentamientos_ordenados = enfrentamientos.sort_values('fecha')
            goles_vs_rival = []
            goles_rival_vs = []
            fechas = []
            
            for _, partido in enfrentamientos_ordenados.iterrows():
                if partido['equipo_local'] == equipo:
                    if partido['goles_local'] > partido['goles_visitante']:
                        victorias_vs += 1
                    elif partido['goles_local'] == partido['goles_visitante']:
                        empates_vs += 1
                    else:
                        derrotas_vs += 1
                    
                    goles_vs_rival.append(partido['goles_local'])
                    goles_rival_vs.append(partido['goles_visitante'])
                else:
                    if partido['goles_visitante'] > partido['goles_local']:
                        victorias_vs += 1
                    elif partido['goles_visitante'] == partido['goles_local']:
                        empates_vs += 1
                    else:
                        derrotas_vs += 1
                    
                    goles_vs_rival.append(partido['goles_visitante'])
                    goles_rival_vs.append(partido['goles_local'])
                
                fechas.append(partido['fecha'])
            
            features[f'{prefijo}victorias_vs_rival'] = victorias_vs
            features[f'{prefijo}empates_vs_rival'] = empates_vs
            features[f'{prefijo}derrotas_vs_rival'] = derrotas_vs
            
            # NUEVA: Ponderación de enfrentamientos recientes (los últimos son más importantes)
            if len(goles_vs_rival) >= 3:
                # Calculamos pesos por recencia (más peso a los más recientes)
                dias_desde_ultimo = [(fecha_partido - fecha).days for fecha in fechas]
                pesos = [1 / (max(d, 1) ** 0.5) for d in dias_desde_ultimo]  # pesos inversamente proporcionales a la raíz del tiempo
                
                # Normalizamos pesos para que sumen 1
                suma_pesos = sum(pesos)
                if suma_pesos > 0:
                    pesos_norm = [p / suma_pesos for p in pesos]
                    
                    # Calculamos promedio ponderado de goles
                    goles_favor_ponderados = sum(g * p for g, p in zip(goles_vs_rival, pesos_norm))
                    goles_contra_ponderados = sum(g * p for g, p in zip(goles_rival_vs, pesos_norm))
                    
                    features[f'{prefijo}goles_favor_ponderados_vs_rival'] = goles_favor_ponderados
                    features[f'{prefijo}goles_contra_ponderados_vs_rival'] = goles_contra_ponderados
                else:
                    features[f'{prefijo}goles_favor_ponderados_vs_rival'] = np.mean(goles_vs_rival)
                    features[f'{prefijo}goles_contra_ponderados_vs_rival'] = np.mean(goles_rival_vs)
            else:
                features[f'{prefijo}goles_favor_ponderados_vs_rival'] = np.mean(goles_vs_rival) if goles_vs_rival else 0
                features[f'{prefijo}goles_contra_ponderados_vs_rival'] = np.mean(goles_rival_vs) if goles_rival_vs else 0
        else:
            features[f'{prefijo}victorias_vs_rival'] = 0
            features[f'{prefijo}empates_vs_rival'] = 0
            features[f'{prefijo}derrotas_vs_rival'] = 0
            features[f'{prefijo}goles_favor_ponderados_vs_rival'] = 0
            features[f'{prefijo}goles_contra_ponderados_vs_rival'] = 0
        
        # 4. Estadísticas avanzadas
        if not datos_equipo.empty:
            # Posesión promedio
            if 'posesion_local' in datos_equipo.columns and 'posesion_visitante' in datos_equipo.columns:
                posesiones = []
                for _, partido in datos_equipo.iterrows():
                    if partido['equipo_local'] == equipo:
                        posesiones.append(partido['posesion_local'])
                    else:
                        posesiones.append(partido['posesion_visitante'])
                
                features[f'{prefijo}posesion_promedio'] = np.mean(posesiones) if posesiones else 0
            else:
                features[f'{prefijo}posesion_promedio'] = 0
                
            # Tiros a puerta promedio
            if 'tiros_puerta_local' in datos_equipo.columns and 'tiros_puerta_visitante' in datos_equipo.columns:
                tiros = []
                for _, partido in datos_equipo.iterrows():
                    if partido['equipo_local'] == equipo:
                        tiros.append(partido['tiros_puerta_local'])
                    else:
                        tiros.append(partido['tiros_puerta_visitante'])
                
                features[f'{prefijo}tiros_puerta_promedio'] = np.mean(tiros) if tiros else 0
            else:
                features[f'{prefijo}tiros_puerta_promedio'] = 0
            
            # NUEVA: Estilo de juego (a partir de estadísticas como posesión y tiros)
            if ('posesion_local' in datos_equipo.columns and 
                'posesion_visitante' in datos_equipo.columns and 
                'tiros_puerta_local' in datos_equipo.columns and 
                'tiros_puerta_visitante' in datos_equipo.columns):
                
                posesiones = []
                tiros = []
                goles = []
                
                for _, partido in datos_equipo.iterrows():
                    if partido['equipo_local'] == equipo:
                        posesiones.append(partido['posesion_local'])
                        tiros.append(partido['tiros_puerta_local'])
                        goles.append(partido['goles_local'])
                    else:
                        posesiones.append(partido['posesion_visitante'])
                        tiros.append(partido['tiros_puerta_visitante'])
                        goles.append(partido['goles_visitante'])
                
                if tiros and posesiones and goles:
                    # Eficiencia de tiro (goles por tiro)
                    eficiencia_tiro = sum(goles) / max(sum(tiros), 1)
                    
                    # Índice de posesión (0-1)
                    indice_posesion = np.mean(posesiones) / 100 if posesiones else 0.5
                    
                    # Índice de directo vs posesión (valores bajos = más directo, valores altos = más posesional)
                    # Fórmula: ratio de posesión / ratio de eficiencia de tiro normalizado
                    indice_estilo = indice_posesion / max(eficiencia_tiro * 10, 0.1)
                    
                    features[f'{prefijo}indice_estilo'] = indice_estilo
                    features[f'{prefijo}eficiencia_tiro'] = eficiencia_tiro
                else:
                    features[f'{prefijo}indice_estilo'] = 0.5  # neutral
                    features[f'{prefijo}eficiencia_tiro'] = 0.1  # valor promedio típico
            else:
                features[f'{prefijo}indice_estilo'] = 0.5
                features[f'{prefijo}eficiencia_tiro'] = 0.1
        
        # 5. Factor momentum (tendencia reciente, últimos 3 partidos)
        if len(datos_recientes) >= 3:
            ultimos_tres = datos_recientes.tail(3)
            puntos_ultimos_tres = 0
            
            for _, partido in ultimos_tres.iterrows():
                if partido['equipo_local'] == equipo:
                    if partido['goles_local'] > partido['goles_visitante']:
                        puntos_ultimos_tres += 3
                    elif partido['goles_local'] == partido['goles_visitante']:
                        puntos_ultimos_tres += 1
                else:
                    if partido['goles_visitante'] > partido['goles_local']:
                        puntos_ultimos_tres += 3
                    elif partido['goles_visitante'] == partido['goles_local']:
                        puntos_ultimos_tres += 1
            
            features[f'{prefijo}momentum'] = puntos_ultimos_tres / 9  # normalizado entre 0 y 1
            
            # NUEVA: Momentum exponencial (los partidos más recientes pesan exponencialmente más)
            if len(datos_recientes) >= 5:
                resultados_recientes = []
                for _, partido in datos_recientes.iterrows():
                    if partido['equipo_local'] == equipo:
                        if partido['goles_local'] > partido['goles_visitante']:
                            resultados_recientes.append(3)  # victoria
                        elif partido['goles_local'] == partido['goles_visitante']:
                            resultados_recientes.append(1)  # empate
                        else:
                            resultados_recientes.append(0)  # derrota
                    else:
                        if partido['goles_visitante'] > partido['goles_local']:
                            resultados_recientes.append(3)  # victoria
                        elif partido['goles_visitante'] == partido['goles_local']:
                            resultados_recientes.append(1)  # empate
                        else:
                            resultados_recientes.append(0)  # derrota
                
                # Pesos exponenciales (el más reciente pesa más)
                pesos = [0.5, 0.25, 0.125, 0.075, 0.05]  # Deben sumar 1
                pesos = pesos[:len(resultados_recientes)]
                
                # Calcular momentum exponencial
                momentum_exp = sum(r * p for r, p in zip(reversed(resultados_recientes), pesos[:len(resultados_recientes)]))
                
                # Normalizar a rango 0-1 (considerando que el máximo posible es 3)
                momentum_exp_norm = momentum_exp / 3
                
                features[f'{prefijo}momentum_exp'] = momentum_exp_norm
            else:
                features[f'{prefijo}momentum_exp'] = features[f'{prefijo}momentum']  # usar el mismo valor si no hay suficientes partidos
        else:
            features[f'{prefijo}momentum'] = 0.5  # valor neutral por defecto
            features[f'{prefijo}momentum_exp'] = 0.5
        
        return features
        
    def _obtener_temporada(self, fecha):
        """Determina la temporada para una fecha dada"""
        anyo = fecha.year
        mes = fecha.month
        
        if mes >= 8:  # Asumimos que la temporada comienza en agosto
            return f"{anyo}-{anyo+1}"
        else:
            return f"{anyo-1}-{anyo}"
    
    def entrenar_modelos(self, busqueda_hiperparametros=False):
        """Entrena modelos predictivos avanzados para resultados y goles"""
        # Preparar datos y características
        features, resultados, goles_local_list, goles_visitante_list = self.preparar_caracteristicas()
        
        if features is None or len(features) == 0:
            print("No se pudieron preparar las características para el entrenamiento")
            return False
        
        # Convertir a array numpy para entrenamiento
        X = features
        y_resultado = np.array(resultados)
        y_goles_local = np.array(goles_local_list)
        y_goles_visitante = np.array(goles_visitante_list)
        
        # Dividir datos en entrenamiento y prueba
        X_train, X_test, y_res_train, y_res_test = train_test_split(
            X, y_resultado, test_size=0.2, random_state=42, stratify=y_resultado
        )
        
        # Usamos los mismos índices para la división de los otros targets
        train_indices = X_train.index
        test_indices = X_test.index
        
        y_gl_train = y_goles_local[train_indices]
        y_gl_test = y_goles_local[test_indices]
        y_gv_train = y_goles_visitante[train_indices]
        y_gv_test = y_goles_visitante[test_indices]
        
        # Aplicar preprocesamiento con técnicas más avanzadas
        numeric_features = X_train.select_dtypes(include=['int64', 'float64']).columns
        categorical_features = X_train.select_dtypes(include=['object', 'category']).columns
        
        # Preprocesamiento mejorado: KNNImputer para valores numéricos faltantes
        # y RobustScaler para ser más resistente a outliers
        numeric_transformer = Pipeline(steps=[
            ('imputer', KNNImputer(n_neighbors=5)),
            ('scaler', RobustScaler())  # Menos sensible a outliers que StandardScaler
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ],
            remainder='passthrough'  # Pasar cualquier columna no especificada sin cambios
        )
        
        # Crear pipeline para preprocesamiento
        preprocessor_pipeline = Pipeline(steps=[('preprocessor', self.preprocessor)])
        preprocessor_pipeline.fit(X_train)
        
        # Transformar los datos
        X_train_processed = preprocessor_pipeline.transform(X_train)
        X_test_processed = preprocessor_pipeline.transform(X_test)
        
        # Guardar el preprocesador
        joblib.dump(preprocessor_pipeline, os.path.join(self.modelos_dir, 'preprocessor.pkl'))
        
        print(f"Características para entrenamiento: {X_train_processed.shape[1]}")
        
        # =====================================================================
        # 1. Modelo para predecir resultado (victoria_local, empate, victoria_visitante)
        # =====================================================================
        
        if busqueda_hiperparametros:
            print("\n1. Optimizando hiperparámetros para modelo de resultado con Optuna...")
            
            # Definimos una función objetivo para Optuna
            def objetivo_resultado(trial):
                # Parámetros para XGBoost
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                    'gamma': trial.suggest_float('gamma', 0, 10),
                    'random_state': 42
                }
                
                # Crear validación cruzada estratificada
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                
                # Evaluar usando validación cruzada
                scores = []
                for train_idx, val_idx in cv.split(X_train_processed, y_res_train):
                    X_cv_train, X_cv_val = X_train_processed[train_idx], X_train_processed[val_idx]
                    y_cv_train, y_cv_val = y_res_train[train_idx], y_res_train[val_idx]
                    
                    # Entrenar XGBoost
                    model = xgb.XGBClassifier(**params)
                    model.fit(X_cv_train, y_cv_train)
                    
                    # Evaluar
                    y_pred = model.predict(X_cv_val)
                    f1 = f1_score(y_cv_val, y_pred, average='weighted')
                    scores.append(f1)
                
                # Devolver la media de los scores
                return np.mean(scores)
            
            # Crear un estudio Optuna y optimizar
            try:
                study = optuna.create_study(direction='maximize')
                study.optimize(objetivo_resultado, n_trials=20)  # Ajustar número de pruebas según tiempo disponible
                
                print(f"Mejores hiperparámetros encontrados: {study.best_params}")
                
                # Usar los mejores parámetros para entrenar el modelo final
                best_params = study.best_params
                self.modelo_resultado = xgb.XGBClassifier(**best_params)
            except Exception as e:
                print(f"Error en la optimización de hiperparámetros: {e}")
                # En caso de error, usar modelo con parámetros predeterminados
                self.modelo_resultado = xgb.XGBClassifier(
                    n_estimators=300,
                    max_depth=6,
                    learning_rate=0.05,
                    random_state=42
                )
        else:
            # Si no se buscan hiperparámetros, usar un conjunto de modelos en un Stacking
            print("\n1. Creando modelo de ensemble para resultado...")
            
            # Definir modelos base
            estimadores_base = [
                ('xgb', xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)),
                ('rf', RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42))
            ]
            
            # Crear modelo de stacking con LogisticRegression como meta-estimador
            self.modelo_resultado = StackingClassifier(
                estimators=estimadores_base,
                final_estimator=LogisticRegression(max_iter=1000, random_state=42),
                cv=5,
                stack_method='predict_proba'
            )
        
        # Entrenar el modelo
        print("Entrenando modelo de resultado...")
        self.modelo_resultado.fit(X_train_processed, y_res_train)
        
        # =====================================================================
        # 2. Modelo para predecir goles locales
        # =====================================================================
        
        if busqueda_hiperparametros:
            print("\n2. Optimizando hiperparámetros para modelo de goles locales con Optuna...")
            
            # Definimos una función objetivo para Optuna
            def objetivo_goles_local(trial):
                # Parámetros para XGBoost
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                    'gamma': trial.suggest_float('gamma', 0, 10),
                    'random_state': 42
                }
                
                # Crear validación cruzada para regresión
                cv = KFold(n_splits=5, shuffle=True, random_state=42)
                
                # Evaluar usando validación cruzada
                scores = []
                for train_idx, val_idx in cv.split(X_train_processed):
                    X_cv_train, X_cv_val = X_train_processed[train_idx], X_train_processed[val_idx]
                    y_cv_train, y_cv_val = y_gl_train[train_idx], y_gl_train[val_idx]
                    
                    # Entrenar XGBoost
                    model = xgb.XGBRegressor(**params)
                    model.fit(X_cv_train, y_cv_train)
                    
                    # Evaluar
                    y_pred = model.predict(X_cv_val)
                    mse = mean_squared_error(y_cv_val, y_pred)
                    scores.append(-mse)  # Negativo porque queremos maximizar (minimizar el MSE)
                
                # Devolver la media de los scores
                return np.mean(scores)
            
            # Crear un estudio Optuna y optimizar
            try:
                study_gl = optuna.create_study(direction='maximize')
                study_gl.optimize(objetivo_goles_local, n_trials=20)
                
                print(f"Mejores hiperparámetros encontrados: {study_gl.best_params}")
                
                # Usar los mejores parámetros para entrenar el modelo final
                best_params_gl = study_gl.best_params
                self.modelo_goles_local = xgb.XGBRegressor(**best_params_gl)
            except Exception as e:
                print(f"Error en la optimización de hiperparámetros: {e}")
                # En caso de error, usar modelo con parámetros predeterminados
                self.modelo_goles_local = xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=42
                )
        else:
            # Si no se buscan hiperparámetros, usar un conjunto de modelos en un VotingRegressor
            print("\n2. Creando modelo de ensemble para goles locales...")
            
            # Definir modelos base
            estimadores_base_reg = [
                ('xgb', xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42)),
                ('gb', GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)),
                ('rf', RandomForestRegressor(n_estimators=200, max_depth=None, random_state=42)),
                ('ridge', Ridge(alpha=1.0, random_state=42))
            ]
            
            # Crear modelo de votación con pesos
            self.modelo_goles_local = VotingRegressor(
                estimators=estimadores_base_reg,
                weights=[0.4, 0.3, 0.2, 0.1]  # Dar más peso a XGBoost y GradientBoosting
            )
        
        # Entrenar el modelo
        print("Entrenando modelo de goles locales...")
        self.modelo_goles_local.fit(X_train_processed, y_gl_train)
        
        # =====================================================================
        # 3. Modelo para predecir goles visitantes
        # =====================================================================
        
        if busqueda_hiperparametros:
            print("\n3. Optimizando hiperparámetros para modelo de goles visitantes con Optuna...")
            
            # Definimos una función objetivo para Optuna
            def objetivo_goles_visitante(trial):
                # Parámetros para XGBoost
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                    'gamma': trial.suggest_float('gamma', 0, 10),
                    'random_state': 42
                }
                
                # Crear validación cruzada para regresión
                cv = KFold(n_splits=5, shuffle=True, random_state=42)
                
                # Evaluar usando validación cruzada
                scores = []
                for train_idx, val_idx in cv.split(X_train_processed):
                    X_cv_train, X_cv_val = X_train_processed[train_idx], X_train_processed[val_idx]
                    y_cv_train, y_cv_val = y_gv_train[train_idx], y_gv_train[val_idx]
                    
                    # Entrenar XGBoost
                    model = xgb.XGBRegressor(**params)
                    model.fit(X_cv_train, y_cv_train)
                    
                    # Evaluar
                    y_pred = model.predict(X_cv_val)
                    mse = mean_squared_error(y_cv_val, y_pred)
                    scores.append(-mse)  # Negativo porque queremos maximizar (minimizar el MSE)
                
                # Devolver la media de los scores
                return np.mean(scores)
            
            # Crear un estudio Optuna y optimizar
            try:
                study_gv = optuna.create_study(direction='maximize')
                study_gv.optimize(objetivo_goles_visitante, n_trials=20)
                
                print(f"Mejores hiperparámetros encontrados: {study_gv.best_params}")
                
                # Usar los mejores parámetros para entrenar el modelo final
                best_params_gv = study_gv.best_params
                self.modelo_goles_visitante = xgb.XGBRegressor(**best_params_gv)
            except Exception as e:
                print(f"Error en la optimización de hiperparámetros: {e}")
                # En caso de error, usar modelo con parámetros predeterminados
                self.modelo_goles_visitante = xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.05,
                    random_state=42
                )
        else:
            # Usar el mismo enfoque de ensemble para goles visitantes
            print("\n3. Creando modelo de ensemble para goles visitantes...")
            self.modelo_goles_visitante = VotingRegressor(
                estimators=estimadores_base_reg,
                weights=[0.4, 0.3, 0.2, 0.1]
            )
        
        # Entrenar el modelo
        print("Entrenando modelo de goles visitantes...")
        self.modelo_goles_visitante.fit(X_train_processed, y_gv_train)
        
        # =====================================================================
        # Evaluar modelos
        # =====================================================================
        print("\nEvaluando modelos:")
        
        # Modelo de resultado
        res_pred = self.modelo_resultado.predict(X_test_processed)
        accuracy = accuracy_score(y_res_test, res_pred)
        f1 = f1_score(y_res_test, res_pred, average='weighted')
        
        print(f"Modelo de resultado - Precisión: {accuracy:.4f}, F1-score: {f1:.4f}")
        print("\nMatriz de confusión:")
        print(confusion_matrix(y_res_test, res_pred))
        print("\nInforme de clasificación:")
        print(classification_report(y_res_test, res_pred))
        
        # Modelos de goles
        gl_pred = self.modelo_goles_local.predict(X_test_processed)
        gv_pred = self.modelo_goles_visitante.predict(X_test_processed)
        
        rmse_gl = np.sqrt(mean_squared_error(y_gl_test, gl_pred))
        rmse_gv = np.sqrt(mean_squared_error(y_gv_test, gv_pred))
        
        print(f"Modelo de goles local - RMSE: {rmse_gl:.4f}")
        print(f"Modelo de goles visitante - RMSE: {rmse_gv:.4f}")
        
        # =====================================================================
        # Análisis de importancia de características
        # =====================================================================
        print("\nAnalizando importancia de características...")
        
        # Intentar obtener importancia de características (varía según el tipo de modelo)
        try:
            # Para modelo de resultado (dependiendo del tipo)
            if hasattr(self.modelo_resultado, 'feature_importances_'):
                # Para Random Forest, GradientBoosting, XGBoost
                importancia_resultado = self.modelo_resultado.feature_importances_
            elif hasattr(self.modelo_resultado, 'coef_'):
                # Para modelos lineales
                importancia_resultado = np.abs(self.modelo_resultado.coef_).mean(axis=0)
            elif hasattr(self.modelo_resultado, 'estimators_') and hasattr(self.modelo_resultado, 'final_estimator_'):
                # Para StackingClassifier, usar el primer estimador base
                importancia_resultado = self.modelo_resultado.estimators_[0][1].feature_importances_
            else:
                print("No se pudo obtener la importancia de características para el modelo de resultado")
                importancia_resultado = None
            
            # Guardamos la importancia para uso posterior
            if importancia_resultado is not None:
                joblib.dump(importancia_resultado, os.path.join(self.modelos_dir, 'importancia_resultado.pkl'))
                
                # Si hay suficientes muestras, intentamos análisis SHAP para el primer modelo en caso de ensemble
                try:
                    if len(X_test) > 50:
                        # Limitamos a un subconjunto de muestras para evitar cálculos muy pesados
                        X_shap = X_test_processed[:50]
                        
                        # Si es un modelo de ensemble, usamos el primer estimador base para SHAP
                        if hasattr(self.modelo_resultado, 'estimators_'):
                            model_for_shap = self.modelo_resultado.estimators_[0][1]
                        else:
                            model_for_shap = self.modelo_resultado
                        
                        # Calcular valores SHAP
                        explainer = shap.Explainer(model_for_shap, X_shap)
                        shap_values = explainer(X_shap)
                        
                        # Guardar valores SHAP para uso posterior
                        joblib.dump(shap_values, os.path.join(self.modelos_dir, 'shap_values_resultado.pkl'))
                        print("Valores SHAP calculados y guardados para el modelo de resultado")
                except Exception as e:
                    print(f"Error al calcular valores SHAP: {e}")
            
        except Exception as e:
            print(f"Error al analizar importancia de características: {e}")
        
        # =====================================================================
        # Guardar modelos
        # =====================================================================
        print("\nGuardando modelos...")
        joblib.dump(self.modelo_resultado, os.path.join(self.modelos_dir, 'modelo_resultado.pkl'))
        joblib.dump(self.modelo_goles_local, os.path.join(self.modelos_dir, 'modelo_goles_local.pkl'))
        joblib.dump(self.modelo_goles_visitante, os.path.join(self.modelos_dir, 'modelo_goles_visitante.pkl'))
        
        # Guardar lista de características
        if hasattr(self, 'feature_names') and self.feature_names is not None:
            with open(os.path.join(self.modelos_dir, 'feature_names.txt'), 'w') as f:
                for feature in self.feature_names:
                    f.write(f"{feature}\n")
        
        print("Modelos guardados exitosamente.")
        return True
    
    def cargar_modelos(self):
        """Carga modelos previamente entrenados desde archivos"""
        try:
            # Comprobar si existen los archivos de los modelos
            ruta_modelo_resultado = os.path.join(self.modelos_dir, 'modelo_resultado.pkl')
            ruta_modelo_gl = os.path.join(self.modelos_dir, 'modelo_goles_local.pkl')
            ruta_modelo_gv = os.path.join(self.modelos_dir, 'modelo_goles_visitante.pkl')
            ruta_preprocessor = os.path.join(self.modelos_dir, 'preprocessor.pkl')
            ruta_features = os.path.join(self.modelos_dir, 'feature_names.txt')
            
            if (os.path.exists(ruta_modelo_resultado) and 
                os.path.exists(ruta_modelo_gl) and 
                os.path.exists(ruta_modelo_gv) and
                os.path.exists(ruta_preprocessor) and
                os.path.exists(ruta_features)):
                
                print("Cargando modelos previamente entrenados...")
                
                # Cargar modelos
                self.modelo_resultado = joblib.load(ruta_modelo_resultado)
                self.modelo_goles_local = joblib.load(ruta_modelo_gl)
                self.modelo_goles_visitante = joblib.load(ruta_modelo_gv)
                
                # Cargar preprocesador
                preprocessor_pipeline = joblib.load(ruta_preprocessor)
                self.preprocessor = preprocessor_pipeline.named_steps['preprocessor']
                
                # Cargar nombres de características
                self.feature_names = []
                with open(ruta_features, 'r') as f:
                    self.feature_names = [line.strip() for line in f]
                
                print("Modelos cargados exitosamente.")
                return True
            else:
                print("No se encontraron todos los archivos de modelo necesarios.")
                return False
        except Exception as e:
            print(f"Error al cargar los modelos: {e}")
            return False
            
    def generar_features_para_prediccion(self, datos_historicos, equipo_local, equipo_visitante, fecha_partido):
        """Genera un dataframe con las características para un partido futuro"""
        # Convertir fecha a datetime si es string
        if isinstance(fecha_partido, str):
            fecha_partido = pd.to_datetime(fecha_partido)
            
        # Crear características para equipo local
        features_local = self._calcular_features_equipo(
            datos_historicos,
            equipo_local,
            equipo_visitante,
            fecha_partido,
            es_local=True
        )
        
        # Crear características para equipo visitante
        features_visitante = self._calcular_features_equipo(
            datos_historicos,
            equipo_visitante,
            equipo_local,
            fecha_partido,
            es_local=False
        )
        
        # Otras características del partido
        features_partido = {
            'mes': fecha_partido.month,
            'dia_semana': fecha_partido.weekday(),
            'liga': 'LaLiga',  # Podría ser un parámetro o inferirse
            'temporada': self._obtener_temporada(fecha_partido)
        }
        
        # Combinar todas las características
        features_combinadas = {**features_local, **features_visitante, **features_partido}
        
        # Convertir a DataFrame
        df_features = pd.DataFrame([features_combinadas])
        
        return df_features

    def predecir_partido_futuro(self, equipo_local, equipo_visitante, fecha_partido):
        """Predice el resultado de un partido futuro utilizando modelos avanzados"""
        # Verificar que los modelos estén cargados
        if self.modelo_resultado is None or self.modelo_goles_local is None or self.modelo_goles_visitante is None:
            modelos_cargados = self.cargar_modelos()
            if not modelos_cargados:
                print("Los modelos no están entrenados ni se pudieron cargar. Ejecute entrenar_modelos() primero.")
                return None
                
        try:
            # Cargar datos históricos para generar características
            datos_historicos = None
            if self.datos is not None:
                # Asegurar que las fechas están en formato datetime
                if 'fecha' in self.datos.columns:
                    self.datos['fecha'] = pd.to_datetime(self.datos['fecha'], errors='coerce')
                datos_historicos = self.datos[self.datos['fecha'] < fecha_partido]
            else:
                # Intentar cargar desde el caché
                ruta_cache = os.path.join('cache', 'partidos_historicos.csv')
                if os.path.exists(ruta_cache):
                    datos_historicos = pd.read_csv(ruta_cache)
                    if 'fecha' in datos_historicos.columns:
                        datos_historicos['fecha'] = pd.to_datetime(datos_historicos['fecha'], errors='coerce')
                    datos_historicos['fecha'] = pd.to_datetime(datos_historicos['fecha'])
                    datos_historicos = datos_historicos[datos_historicos['fecha'] < fecha_partido]
                    
            if datos_historicos is None or datos_historicos.empty:
                print("No hay datos históricos suficientes para generar predicciones.")
                return None
                
            # Generar características para el partido específico
            df_features = self.generar_features_para_prediccion(
                datos_historicos, equipo_local, equipo_visitante, fecha_partido
            )
            
            # Aplicar preprocesamiento
            X_processed = self.preprocessor.transform(df_features)
            
            # Predecir resultado
            resultado_id = self.modelo_resultado.predict(X_processed)[0]
            prob_resultado = self.modelo_resultado.predict_proba(X_processed)[0]
            
            # Mapear ID de resultado a texto
            if resultado_id == 'victoria_local':
                resultado_texto = 'Victoria Local'
            elif resultado_id == 'empate':
                resultado_texto = 'Empate'
            else:  # victoria_visitante
                resultado_texto = 'Victoria Visitante'
            
            # Predecir goles (con control de valores negativos)
            goles_local_pred = self.modelo_goles_local.predict(X_processed)[0]
            goles_visitante_pred = self.modelo_goles_visitante.predict(X_processed)[0]
            
            # Redondear y asegurar valores no negativos
            goles_local = max(0, round(goles_local_pred))
            goles_visitante = max(0, round(goles_visitante_pred))
            
            # Identificar factores importantes que influyeron en la predicción
            factores_clave = self._identificar_factores_clave(df_features, equipo_local, equipo_visitante)
            
            # Crear diccionario de predicción
            prediccion = {
                'equipo_local': equipo_local,
                'equipo_visitante': equipo_visitante,
                'fecha': fecha_partido,
                'resultado_predicho': resultado_texto,
                'probabilidades': {
                    'victoria_local': float(prob_resultado[0]) if len(prob_resultado) >= 1 else 0.33,
                    'empate': float(prob_resultado[1]) if len(prob_resultado) >= 2 else 0.33,
                    'victoria_visitante': float(prob_resultado[2]) if len(prob_resultado) >= 3 else 0.33
                },
                'goles_predichos': {
                    'local': int(goles_local),
                    'visitante': int(goles_visitante)
                },
                'factores_clave': factores_clave
            }
            
            return prediccion
            
        except Exception as e:
            print(f"Error al predecir resultado: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _identificar_factores_clave(self, df_features, equipo_local, equipo_visitante):
        """Identifica los factores clave que influyen en la predicción utilizando análisis avanzado"""
        factores = []
        importancia_por_grupo = {}
        
        try:
            # 0. Si no tenemos características para interpretar, regresamos mensaje genérico
            if not hasattr(self, 'feature_names') or self.feature_names is None or len(self.feature_names) == 0:
                return ["No hay suficiente información para identificar factores clave"]
            
            # 1. Inicializar diccionario de importancias con valores por defecto para todas las características
            importancia_caracteristicas = {feature: 0.0 for feature in self.feature_names}
            
            # Seguridad para verificar si el modelo existe
            if self.modelo_resultado is None:
                print("No hay modelo de resultado disponible para identificar factores clave")
                return ["No hay suficientes datos para identificar factores clave"]
                
            # 1.1 Intentar cargar importancia guardada en archivo
            ruta_importancia = os.path.join(self.modelos_dir, 'importancia_resultado.pkl')
            if os.path.exists(ruta_importancia):
                try:
                    importancia_guardada = joblib.load(ruta_importancia)
                    if isinstance(importancia_guardada, dict):
                        # Si ya es un diccionario, usarlo directamente
                        importancia_caracteristicas = importancia_guardada
                    elif isinstance(importancia_guardada, (np.ndarray, list)) and len(importancia_guardada) == len(self.feature_names):
                        # Si es un array o lista, convertir a diccionario
                        for i, feature in enumerate(self.feature_names):
                            importancia_caracteristicas[feature] = importancia_guardada[i]
                    print("Importancia de características cargada desde archivo")
                except Exception as e:
                    print(f"Error al cargar importancia guardada: {e}")
            
            # 1.2. Verificar si importancia_caracteristicas está vacío o todos son ceros
            if not importancia_caracteristicas or all(v == 0 for v in importancia_caracteristicas.values()):
                # Si no hay importancias válidas, usamos valores aleatorios para features conocidas
                print("No se encontró información de importancia válida. Usando valores simples.")
                for feature in self.feature_names:
                    # Asignar valores más altos a características importantes conocidas
                    if 'momentum' in feature or 'victorias_recientes' in feature or 'promedio_goles' in feature:
                        importancia_caracteristicas[feature] = 0.8
                    elif 'puntos_temporada' in feature or 'racha' in feature:
                        importancia_caracteristicas[feature] = 0.6
                    else:
                        importancia_caracteristicas[feature] = 0.3
            
            # 1.2. Si tenemos valores SHAP calculados, combinarlos con feature importance
            ruta_shap = os.path.join(self.modelos_dir, 'shap_values_resultado.pkl')
            if os.path.exists(ruta_shap):
                try:
                    shap_values = joblib.load(ruta_shap)
                    # Usar los valores SHAP para identificar características importantes
                    if hasattr(self, 'feature_names') and self.feature_names is not None:
                        shap_mean = np.abs(shap_values.values).mean(axis=0)
                        importancia_shap = dict(zip(self.feature_names, shap_mean))
                        
                        # Combinar con la importancia del modelo (60% SHAP, 40% feature importance)
                        for feature, imp in importancia_shap.items():
                            if feature in importancia_caracteristicas:
                                importancia_caracteristicas[feature] = importancia_caracteristicas[feature] * 0.4 + imp * 0.6
                            else:
                                importancia_caracteristicas[feature] = imp
                except Exception as e:
                    print(f"Error al cargar valores SHAP: {e}")
            
            # 2. Agrupar características por categorías para mejor interpretación
            categorias_caracteristicas = {
                'rendimiento_reciente': ['victorias_recientes', 'derrotas_recientes', 'empates_recientes', 'promedio_puntos_recientes', 'racha_actual'],
                'ofensiva': ['promedio_goles_favor', 'max_goles_anotados', 'partidos_anotando'],
                'defensiva': ['promedio_goles_contra', 'min_goles_recibidos', 'partidos_imbatido'],
                'enfrentamiento_directo': ['victorias_vs_rival', 'derrotas_vs_rival', 'empates_vs_rival', 'racha_vs_rival'],
                'forma': ['momentum', 'momentum_exp', 'tendencia_puntos'],
                'cansancio': ['partidos_ultimo_mes', 'dias_desde_ultimo_partido'],
                'contexto': ['mes', 'dia_semana', 'temporada'],
                'eficiencia': ['eficiencia_ofensiva', 'eficiencia_defensiva', 'aprovechamiento_ocasiones'],
                'home_advantage': ['rendimiento_local', 'rendimiento_visitante']
            }
            
            # Agrupar importancia por categorías
            for feature, importancia in importancia_caracteristicas.items():
                asignada = False
                for categoria, patrones in categorias_caracteristicas.items():
                    for patron in patrones:
                        if patron in feature:
                            if categoria not in importancia_por_grupo:
                                importancia_por_grupo[categoria] = 0
                            importancia_por_grupo[categoria] += importancia
                            asignada = True
                            break
                    if asignada:
                        break
                
                if not asignada:
                    if 'otros' not in importancia_por_grupo:
                        importancia_por_grupo['otros'] = 0
                    importancia_por_grupo['otros'] += importancia
            
            # 3. Seleccionar top características individuales por importancia
            factores_individuales = sorted(importancia_caracteristicas.items(), key=lambda x: x[1], reverse=True)
            top_factores = [f[0] for f in factores_individuales[:8]]  # Ampliamos a 8 factores para tener más contexto
            
            # 4. Generar mensajes interpretativos mejorados para los factores clave
            mensajes_factores = []
            rival_map = {equipo_local: equipo_visitante, equipo_visitante: equipo_local}
            
            for factor in top_factores:
                # Determinar equipo y rival
                if 'local_' in factor:
                    prefijo = 'local_'
                    equipo = equipo_local
                    rival = equipo_visitante
                elif 'visitante_' in factor:
                    prefijo = 'visitante_'
                    equipo = equipo_visitante
                    rival = equipo_local
                else:
                    prefijo = ''
                    equipo = None
                    rival = None
                
                # Factor sin el prefijo local/visitante
                factor_base = factor.replace(f"{prefijo}", "")
                total_importancia = sum(importancia_caracteristicas.values())
                importancia_rel = importancia_caracteristicas[factor] / max(total_importancia, 0.0001) * 100
                
                # Generar mensaje descriptivo según el factor
                mensaje = None
                
                # Rendimiento reciente
                if 'victorias_recientes' in factor:
                    mensaje = f"Racha positiva de {equipo} ({prefijo.replace('_', '')}): Factor de alta influencia ({importancia_rel:.1f}%)"
                elif 'derrotas_recientes' in factor:
                    mensaje = f"Racha negativa de {equipo} ({prefijo.replace('_', '')}): Factor de alerta ({importancia_rel:.1f}%)"
                elif 'promedio_puntos_recientes' in factor:
                    mensaje = f"Rendimiento reciente de {equipo}: Factor significativo ({importancia_rel:.1f}%)"
                elif 'racha_actual' in factor:
                    mensaje = f"Momento actual de {equipo}: Factor decisivo ({importancia_rel:.1f}%)"
                
                # Ofensiva
                elif 'promedio_goles_favor' in factor:
                    mensaje = f"Capacidad ofensiva de {equipo}: Factor determinante ({importancia_rel:.1f}%)"
                elif 'max_goles_anotados' in factor:
                    mensaje = f"Potencial ofensivo máximo de {equipo}: Factor relevante ({importancia_rel:.1f}%)"
                elif 'partidos_anotando' in factor:
                    mensaje = f"Consistencia ofensiva de {equipo}: Factor importante ({importancia_rel:.1f}%)"
                
                # Defensiva
                elif 'promedio_goles_contra' in factor:
                    mensaje = f"Solidez defensiva de {equipo}: Factor crucial ({importancia_rel:.1f}%)"
                elif 'partidos_imbatido' in factor:
                    mensaje = f"Fortaleza defensiva de {equipo}: Factor destacable ({importancia_rel:.1f}%)"
                
                # Enfrentamientos directos
                elif 'victorias_vs_rival' in factor:
                    mensaje = f"Historial favorable de {equipo} contra {rival}: Factor psicológico importante ({importancia_rel:.1f}%)"
                elif 'derrotas_vs_rival' in factor:
                    mensaje = f"Historial desfavorable de {equipo} contra {rival}: Factor a considerar ({importancia_rel:.1f}%)"
                elif 'racha_vs_rival' in factor:
                    mensaje = f"Tendencia reciente en enfrentamientos {equipo} vs {rival}: Factor relevante ({importancia_rel:.1f}%)"
                
                # Forma y momentum
                elif 'momentum' in factor:
                    mensaje = f"Dinámica actual de {equipo}: Factor clave ({importancia_rel:.1f}%)"
                elif 'momentum_exp' in factor:
                    mensaje = f"Impulso creciente de {equipo}: Factor determinante ({importancia_rel:.1f}%)"
                elif 'tendencia_puntos' in factor:
                    mensaje = f"Evolución reciente de {equipo}: Factor significativo ({importancia_rel:.1f}%)"
                
                # Cansancio
                elif 'partidos_ultimo_mes' in factor:
                    mensaje = f"Carga de partidos de {equipo}: Factor físico importante ({importancia_rel:.1f}%)"
                elif 'dias_desde_ultimo_partido' in factor:
                    mensaje = f"Descanso/recuperación de {equipo}: Factor relevante ({importancia_rel:.1f}%)"
                
                # Eficiencia
                elif 'eficiencia_ofensiva' in factor:
                    mensaje = f"Efectividad en ataque de {equipo}: Factor decisivo ({importancia_rel:.1f}%)"
                elif 'eficiencia_defensiva' in factor:
                    mensaje = f"Solidez en defensa de {equipo}: Factor destacado ({importancia_rel:.1f}%)"
                
                # Ventaja local
                elif 'rendimiento_local' in factor:
                    mensaje = f"Fortaleza como local de {equipo_local}: Factor determinante ({importancia_rel:.1f}%)"
                elif 'rendimiento_visitante' in factor:
                    mensaje = f"Desempeño como visitante de {equipo_visitante}: Factor significativo ({importancia_rel:.1f}%)"
                
                # Contexto
                elif factor in ['mes', 'dia_semana', 'temporada', 'liga']:
                    mensaje = f"Contexto del partido ({factor}): Factor situacional ({importancia_rel:.1f}%)"
                
                # Para cualquier otro factor no categorizado
                else:
                    mensaje = f"Factor '{factor_base}' para {equipo if equipo else 'el partido'}: Influencia de {importancia_rel:.1f}%"
                
                if mensaje:
                    mensajes_factores.append(mensaje)
            
            # 5. Añadir resumen de categorías más importantes
            categorias_ordenadas = sorted(importancia_por_grupo.items(), key=lambda x: x[1], reverse=True)
            
            mensajes_categorias = []
            categoria_map = {
                'rendimiento_reciente': "el rendimiento reciente",
                'ofensiva': "la capacidad ofensiva",
                'defensiva': "la solidez defensiva",
                'enfrentamiento_directo': "el historial de enfrentamientos directos",
                'forma': "el momentum y la dinámica actual",
                'cansancio': "el estado físico y descanso",
                'contexto': "factores contextuales (temporada, fecha)",
                'eficiencia': "la eficiencia en ataque y defensa",
                'home_advantage': "la ventaja de jugar en casa/fuera"
            }
            
            # Añadir las tres categorías más importantes
            for i, (categoria, importancia) in enumerate(categorias_ordenadas[:3]):
                total_grupo = sum(importancia_por_grupo.values())
                peso_rel = importancia / max(total_grupo, 0.0001) * 100
                if categoria in categoria_map:
                    if i == 0:
                        mensajes_categorias.append(f"El factor más determinante para este partido es {categoria_map[categoria]} ({peso_rel:.1f}%)")
                    else:
                        mensajes_categorias.append(f"También es relevante {categoria_map[categoria]} ({peso_rel:.1f}%)")
            
            # Combinar mensajes de categorías y factores individuales
            factores = mensajes_categorias + mensajes_factores
        
        except Exception as e:
            print(f"Error al identificar factores clave: {e}")
            import traceback
            traceback.print_exc()
        
        return factores
    
    def generar_datos_ejemplo(self, ruta_salida=None):
        """
        Genera datos de ejemplo para entrenar los modelos si no hay datos reales disponibles.
        Esto permite tener modelos funcionales para demostración incluso sin datos históricos completos.
        """
        if ruta_salida is None:
            ruta_salida = os.path.join('cache', 'partidos_generados.csv')
        
        print(f"Generando datos de ejemplo para entrenamiento en {ruta_salida}...")
        
        # Lista de equipos de ejemplo
        equipos = [
            "FC Barcelona", "Real Madrid", "Atlético Madrid", "Sevilla FC",
            "Valencia CF", "Villarreal", "Athletic Bilbao", "Real Sociedad",
            "Real Betis", "Getafe CF", "Espanyol", "Celta de Vigo"
        ]
        
        # Fechas para generar partidos (2 temporadas)
        fecha_inicio = datetime(2023, 8, 1)
        fecha_fin = datetime(2025, 5, 31)
        
        # Generar partidos
        partidos = []
        
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            # Determinar temporada
            if fecha_actual.month >= 8:
                temporada = f"{fecha_actual.year}-{fecha_actual.year + 1}"
            else:
                temporada = f"{fecha_actual.year - 1}-{fecha_actual.year}"
            
            # Generar algunos partidos para esta fecha
            for _ in range(3):  # 3 partidos por fecha
                # Seleccionar equipos diferentes aleatoriamente
                equipos_seleccionados = np.random.choice(equipos, 2, replace=False)
                equipo_local = equipos_seleccionados[0]
                equipo_visitante = equipos_seleccionados[1]
                
                # Generar estadísticas del partido
                # Las probabilidades se sesgan para favorecer ligeramente al local
                if np.random.random() < 0.45:  # victoria local
                    goles_local = np.random.choice([1, 2, 3, 4, 5], p=[0.2, 0.4, 0.25, 0.1, 0.05])
                    goles_visitante = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
                    if goles_local <= goles_visitante:
                        goles_visitante = goles_local - 1
                elif np.random.random() < 0.75:  # empate
                    goles = np.random.choice([0, 1, 2, 3], p=[0.3, 0.4, 0.2, 0.1])
                    goles_local = goles
                    goles_visitante = goles
                else:  # victoria visitante
                    goles_visitante = np.random.choice([1, 2, 3, 4], p=[0.4, 0.4, 0.15, 0.05])
                    goles_local = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
                    if goles_local >= goles_visitante:
                        goles_local = goles_visitante - 1
                
                # Generar otras estadísticas realistas
                posesion_local = np.random.randint(35, 66)
                posesion_visitante = 100 - posesion_local
                
                tiros_puerta_local = goles_local + np.random.randint(1, 8)
                tiros_puerta_visitante = goles_visitante + np.random.randint(1, 6)
                
                faltas_local = np.random.randint(5, 16)
                faltas_visitante = np.random.randint(5, 16)
                
                corners_local = np.random.randint(2, 10)
                corners_visitante = np.random.randint(1, 8)
                
                tarjetas_amarillas_local = np.random.randint(0, 6)
                tarjetas_amarillas_visitante = np.random.randint(0, 6)
                
                tarjetas_rojas_local = np.random.binomial(1, 0.05)  # 5% de probabilidad de tarjeta roja
                tarjetas_rojas_visitante = np.random.binomial(1, 0.05)
                
                # Crear el registro del partido
                partido = {
                    'fecha': fecha_actual.strftime('%Y-%m-%d'),
                    'temporada': temporada,
                    'liga': 'LaLiga',
                    'equipo_local': equipo_local,
                    'equipo_visitante': equipo_visitante,
                    'goles_local': goles_local,
                    'goles_visitante': goles_visitante,
                    'posesion_local': posesion_local,
                    'posesion_visitante': posesion_visitante,
                    'tiros_puerta_local': tiros_puerta_local,
                    'tiros_puerta_visitante': tiros_puerta_visitante,
                    'faltas_local': faltas_local,
                    'faltas_visitante': faltas_visitante,
                    'corners_local': corners_local,
                    'corners_visitante': corners_visitante,
                    'tarjetas_amarillas_local': tarjetas_amarillas_local,
                    'tarjetas_amarillas_visitante': tarjetas_amarillas_visitante,
                    'tarjetas_rojas_local': tarjetas_rojas_local,
                    'tarjetas_rojas_visitante': tarjetas_rojas_visitante
                }
                
                partidos.append(partido)
            
            # Avanzar 7 días
            fecha_actual += timedelta(days=7)
        
        # Convertir a DataFrame y guardar
        df_partidos = pd.DataFrame(partidos)
        df_partidos.to_csv(ruta_salida, index=False)
        
        print(f"Generados {len(df_partidos)} partidos de ejemplo y guardados en {ruta_salida}")
        return df_partidos
    
    def analizar_importancia_caracteristicas(self):
        """Analiza y visualiza la importancia de las características en los modelos"""
        if self.modelo_resultado is None:
            print("No hay modelos entrenados para analizar.")
            modelos_cargados = self.cargar_modelos()
            if not modelos_cargados:
                return None
        
        # Intentar cargar importancia de características guardadas
        importancia_resultado = None
        importancia_goles_local = None
        importancia_goles_visitante = None
        
        # Intentar cargar desde archivos
        try:
            ruta_importancia_resultado = os.path.join(self.modelos_dir, 'importancia_resultado.pkl')
            if os.path.exists(ruta_importancia_resultado):
                importancia_resultado = joblib.load(ruta_importancia_resultado)
                print("Importancia de modelo de resultado cargada desde archivo")
        except Exception as e:
            print(f"Error al cargar importancia de resultado: {e}")
            
        try:
            ruta_importancia_gl = os.path.join(self.modelos_dir, 'importancia_goles_local.pkl')
            if os.path.exists(ruta_importancia_gl):
                importancia_goles_local = joblib.load(ruta_importancia_gl)
                print("Importancia de modelo de goles local cargada desde archivo")
        except Exception as e:
            print(f"Error al cargar importancia de goles local: {e}")
            
        try:
            ruta_importancia_gv = os.path.join(self.modelos_dir, 'importancia_goles_visitante.pkl')
            if os.path.exists(ruta_importancia_gv):
                importancia_goles_visitante = joblib.load(ruta_importancia_gv)
                print("Importancia de modelo de goles visitante cargada desde archivo")
        except Exception as e:
            print(f"Error al cargar importancia de goles visitante: {e}")
        
        # Si no hay datos de importancia disponibles, intenta extraerlos de los modelos
        # Intentamos obtener importancias usando métodos alternativos
        def extraer_importancia_segura(modelo, nombre_modelo):
            """Extraer importancia de características de forma segura con múltiples métodos"""
            if modelo is None:
                return None
            
            importancia = None
            
            # Método 1: Probar feature_importances_ directo
            try:
                if hasattr(modelo, 'feature_importances_'):
                    return modelo.feature_importances_
            except:
                pass
                
            # Método 2: Para modelos XGBoost
            try:
                if hasattr(modelo, 'get_booster') and callable(getattr(modelo, 'get_booster', None)):
                    # Para XGBoost podemos obtener importancia mediante get_score
                    importancia_dict = modelo.get_booster().get_score(importance_type='weight')
                    if importancia_dict:
                        # Convertir a lista ordenada por índice de característica
                        importancia_array = []
                        # Intentamos extraer los índices numéricos (f0, f1, etc.)
                        # Si tenemos feature_names, usarlos para ordenar
                        if self.feature_names is not None:
                            for i in range(len(self.feature_names)):
                                key = f'f{i}'
                                if key in importancia_dict:
                                    importancia_array.append(importancia_dict[key])
                                else:
                                    importancia_array.append(0.0)
                        else:
                            # Si no tenemos feature_names, usar el max índice de las claves
                            max_feature_idx = 0
                            for key in importancia_dict.keys():
                                if key.startswith('f'):
                                    try:
                                        idx = int(key[1:])
                                        max_feature_idx = max(max_feature_idx, idx)
                                    except:
                                        pass
                            
                            # Crear array con tamaño apropiado
                            importancia_array = [0.0] * (max_feature_idx + 1)
                            for key, value in importancia_dict.items():
                                if key.startswith('f'):
                                    try:
                                        idx = int(key[1:])
                                        importancia_array[idx] = value
                                    except:
                                        pass
                        if importancia_array:
                            return np.array(importancia_array)
            except Exception as e:
                print(f"Error al obtener importancia XGBoost para {nombre_modelo}: {e}")
            
            # Método 3: Para modelos de ensemble (con comprobaciones explícitas de tipo)
            try:
                if hasattr(modelo, 'estimators_'):
                    estimadores = getattr(modelo, 'estimators_')
                    # Verificamos que sea una lista o iterable
                    if isinstance(estimadores, (list, tuple)) and len(estimadores) > 0:
                        # Tomamos el primer estimador con comprobación de seguridad
                        try:
                            primer_estimador = estimadores[0]
                            # Si es una tupla (nombre, estimador), extraemos el estimador
                            if isinstance(primer_estimador, tuple) and len(primer_estimador) == 2:
                                primer_estimador = primer_estimador[1]
                            
                            # Verificamos que el estimador sea un objeto antes de acceder a atributos
                            if primer_estimador is not None and hasattr(primer_estimador, 'feature_importances_'):
                                return getattr(primer_estimador, 'feature_importances_')
                        except Exception as e:
                            print(f"Error al acceder al primer estimador: {e}")
            except Exception as e:
                print(f"Error al obtener importancia de ensemble para {nombre_modelo}: {e}")
                
            # Método 4: Para modelos lineales
            try:
                if hasattr(modelo, 'coef_'):
                    coefs = modelo.coef_
                    if hasattr(coefs, 'ndim'):
                        return np.abs(coefs).mean(axis=0) if coefs.ndim > 1 else np.abs(coefs)
            except Exception as e:
                print(f"Error al obtener coeficientes para {nombre_modelo}: {e}")
                
            # Si nada funciona, regresamos None
            return None
            
        # Aplicar la función segura para cada modelo
        if importancia_resultado is None and self.modelo_resultado is not None:
            importancia_resultado = extraer_importancia_segura(self.modelo_resultado, "modelo de resultado")
                
        if importancia_goles_local is None and self.modelo_goles_local is not None:
            importancia_goles_local = extraer_importancia_segura(self.modelo_goles_local, "modelo de goles local")
                
        if importancia_goles_visitante is None and self.modelo_goles_visitante is not None:
            importancia_goles_visitante = extraer_importancia_segura(self.modelo_goles_visitante, "modelo de goles visitante")
                
        # Si no hay importancia disponible, salir
        if importancia_resultado is None and importancia_goles_local is None and importancia_goles_visitante is None:
            print("No hay información de importancia de características disponible para ningún modelo.")
            return None
        
        # Si tenemos los nombres de las características
        dataframes = []
        
        if hasattr(self, 'feature_names') and self.feature_names is not None:
            # Crear DataFrames solo para modelos con importancia disponible
            # Función para crear nombres de características genéricos
            def generar_nombres_features(num_features):
                return [f'feature_{i}' for i in range(num_features)]
            
            # Función para manejar dimensiones no coincidentes
            def crear_dataframe_importancia(nombre_modelo, importancia_array):
                if importancia_array is None:
                    return None
                
                # Si las dimensiones coinciden, usamos los nombres existentes
                if self.feature_names is not None and len(importancia_array) == len(self.feature_names):
                    nombres = self.feature_names
                else:
                    # Si no coinciden, generamos nombres genéricos
                    print(f"Usando nombres de características genéricos para {nombre_modelo}. " +
                          f"Features requeridas: {len(importancia_array)}, Disponibles: {len(self.feature_names) if self.feature_names is not None else 0}")
                    nombres = generar_nombres_features(len(importancia_array))
                
                # Crear DataFrame y ordenar por importancia
                df = pd.DataFrame({
                    'caracteristica': nombres,
                    'importancia': importancia_array
                }).sort_values('importancia', ascending=False)
                
                return df
            
            # Crear DataFrames para cada modelo
            if importancia_resultado is not None:
                df_resultado = crear_dataframe_importancia('resultado', importancia_resultado)
                if df_resultado is not None:
                    dataframes.append(('resultado', df_resultado))
            
            if importancia_goles_local is not None:
                df_goles_local = crear_dataframe_importancia('goles_local', importancia_goles_local)
                if df_goles_local is not None:
                    dataframes.append(('goles_local', df_goles_local))
            
            if importancia_goles_visitante is not None:
                df_goles_visitante = crear_dataframe_importancia('goles_visitante', importancia_goles_visitante)
                if df_goles_visitante is not None:
                    dataframes.append(('goles_visitante', df_goles_visitante))
            
            # Si no hay DataFrames válidos, terminar
            if not dataframes:
                print("No se pudo crear ningún DataFrame de importancia de características.")
                return None
            
            # Mostrar las 10 características más importantes para cada modelo
            for modelo_nombre, df in dataframes:
                print(f"\nTop 10 características más importantes para predecir {modelo_nombre}:")
                print(df.head(10))
            
            # Crear visualizaciones si matplotlib está disponible
            try:
                import matplotlib.pyplot as plt
                
                # Crear visualización para cada modelo disponible
                for modelo_nombre, df in dataframes:
                    plt.figure(figsize=(12, 8))
                    plt.barh(df.head(10)['caracteristica'], df.head(10)['importancia'])
                    
                    # Título personalizado según el modelo
                    if modelo_nombre == 'resultado':
                        titulo = 'Top 10 características importantes - Predicción de resultado'
                    elif modelo_nombre == 'goles_local':
                        titulo = 'Top 10 características importantes - Predicción de goles locales'
                    elif modelo_nombre == 'goles_visitante':
                        titulo = 'Top 10 características importantes - Predicción de goles visitantes'
                    else:
                        titulo = f'Top 10 características importantes - {modelo_nombre}'
                    
                    plt.title(titulo)
                    plt.xlabel('Importancia')
                    plt.tight_layout()
                    plt.savefig(os.path.join(self.modelos_dir, f'importancia_{modelo_nombre}.png'))
                
                print("Visualizaciones guardadas en el directorio de modelos.")
                
            except Exception as e:
                print(f"No se pudieron crear visualizaciones: {e}")
            
            # Convertir lista de tuplas a diccionario para retornar
            return {nombre: df for nombre, df in dataframes} if dataframes else None
        else:
            print("No se dispone de nombres de características.")
            return {
                'resultado': importancia_resultado,
                'goles_local': importancia_goles_local,
                'goles_visitante': importancia_goles_visitante
            }
    
    def obtener_caracteristicas_partido(self, equipo_local, equipo_visitante, fecha):
        """
        Obtiene las características de un partido sin realizar la predicción.
        Útil para simulaciones Monte Carlo que necesitan modificar características.
        
        Args:
            equipo_local: Nombre del equipo local
            equipo_visitante: Nombre del equipo visitante
            fecha: Fecha del partido (datetime)
            
        Returns:
            DataFrame con las características del partido
        """
        if self.datos is None:
            print("No hay datos disponibles para extraer características")
            return None
        
        try:
            # Extraemos características para el partido específico
            fecha_limite = fecha - timedelta(days=1)
            datos_historicos = self.datos[self.datos['fecha'] <= fecha_limite].copy()
            
            if datos_historicos.empty:
                print("No hay suficientes datos históricos para extraer características")
                return None
            
            # Extraemos características para ambos equipos
            features_local = self._calcular_features_equipo(
                datos_historicos, 
                equipo_local,
                equipo_visitante,
                fecha,
                es_local=True
            )
            
            features_visitante = self._calcular_features_equipo(
                datos_historicos, 
                equipo_visitante,
                equipo_local,
                fecha,
                es_local=False
            )
            
            # Combinamos todas las características
            caracteristicas = pd.concat([features_local, features_visitante], axis=1)
            
            # Aseguramos que los nombres de las columnas sean únicos
            caracteristicas.columns = [f"{col}_{i}" if col in caracteristicas.columns[:i] else col 
                                      for i, col in enumerate(caracteristicas.columns)]
            
            return pd.DataFrame([caracteristicas.iloc[0]])
            
        except Exception as e:
            print(f"Error al obtener características del partido: {e}")
            return None
    
    def predecir_con_caracteristicas(self, caracteristicas):
        """
        Realiza una predicción utilizando características ya extraídas.
        Útil para simulaciones que modifican características.
        
        Args:
            caracteristicas: DataFrame con características preprocesadas
            
        Returns:
            Diccionario con resultados de la predicción
        """
        if self.modelo_resultado is None or self.modelo_goles_local is None or self.modelo_goles_visitante is None:
            print("Los modelos no están cargados")
            if not self.cargar_modelos():
                return None
        
        try:
            # Predecir resultado (victoria local, empate, victoria visitante)
            resultado_predicho = self.modelo_resultado.predict(caracteristicas)[0]
            
            # Predecir número de goles
            goles_local_pred = max(0, self.modelo_goles_local.predict(caracteristicas)[0])
            goles_visitante_pred = max(0, self.modelo_goles_visitante.predict(caracteristicas)[0])
            
            # Si tenemos un clasificador que devuelve probabilidades, las extraemos
            probabilidades = {}
            try:
                probs = self.modelo_resultado.predict_proba(caracteristicas)[0]
                clases = self.modelo_resultado.classes_
                for i, clase in enumerate(clases):
                    probabilidades[clase] = probs[i]
            except:
                # Si no hay probabilidades, asignamos valores estimados
                if resultado_predicho == 'victoria_local':
                    probabilidades = {'victoria_local': 0.6, 'empate': 0.25, 'victoria_visitante': 0.15}
                elif resultado_predicho == 'empate':
                    probabilidades = {'victoria_local': 0.25, 'empate': 0.5, 'victoria_visitante': 0.25}
                else:
                    probabilidades = {'victoria_local': 0.15, 'empate': 0.25, 'victoria_visitante': 0.6}
            
            # Construir respuesta
            prediccion = {
                'resultado_predicho': resultado_predicho,
                'probabilidades': probabilidades,
                'goles_predichos': {
                    'local': round(goles_local_pred, 1),
                    'visitante': round(goles_visitante_pred, 1)
                }
            }
            
            return prediccion
            
        except Exception as e:
            print(f"Error al predecir con características: {e}")
            return None