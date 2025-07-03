# Mejoras en Modelos Predictivos para Analizador Deportivo de Fútbol

Este documento describe las mejoras implementadas en los modelos predictivos para el análisis de partidos futuros en la herramienta de Analizador Deportivo de Fútbol.

## Características Implementadas

### 1. Variables Predictivas Avanzadas

Se han implementado numerosas características avanzadas para mejorar la precisión predictiva:

#### Variables Estadísticas
- **Estadísticas históricos de equipos**:
  - Promedio de goles a favor y en contra
  - Rendimiento como local/visitante
  - Victorias, empates y derrotas recientes

- **Enfrentamientos directos**:
  - Historial entre los equipos
  - Resultados de encuentros anteriores
  - Tendencia de goles en enfrentamientos previos
  - **NUEVO**: Sistema de ponderación por recencia de enfrentamientos

- **Variables de temporada**:
  - Desempeño en la temporada actual
  - Puntos por partido
  - Racha reciente (últimos 5 partidos)
  - **NUEVO**: Evolución durante la temporada (comparación primera/segunda mitad)

#### Nuevas Variables de Rendimiento
- **Factor momentum**:
  - Rendimiento ponderado de los últimos 3 partidos
  - Tendencia ascendente o descendente
  - **NUEVO**: Momentum exponencial (más peso a partidos más recientes)

- **Estadísticas avanzadas**:
  - Posesión promedio
  - Tiros a puerta
  - Tendencias defensivas y ofensivas
  - **NUEVO**: Eficiencia ofensiva y defensiva
  - **NUEVO**: Tendencia de goles (comparando períodos)
  - **NUEVO**: Factor de cansancio (partidos en los últimos 30 días)
  - **NUEVO**: Índice de consistencia (variabilidad en resultados)
  - **NUEVO**: Home field advantage mejorado
  - **NUEVO**: Índice de estilo de juego (posesión vs. directo)
  - **NUEVO**: Eficiencia de tiro (goles por tiro)

### 2. Modelos de Machine Learning Avanzados

Se han implementado algoritmos de última generación:

#### Modelos Predictivos Mejorados
- **XGBoost**:
  - Mayor precisión y capacidad de capturar relaciones complejas
  - Mejor rendimiento con características no lineales
  - Implementación optimizada para entrenamientos rápidos

- **Modelos de Ensemble**:
  - **NUEVO**: StackingClassifier para predicción de resultados
  - **NUEVO**: VotingRegressor para predicción de goles
  - Combinación de múltiples algoritmos para mayor robustez

#### Optimización y Validación
- **Optimización avanzada de hiperparámetros**:
  - **NUEVO**: Integración de Optuna para búsqueda eficiente
  - Exploración automática del espacio de hiperparámetros
  - Optimización basada en métricas relevantes (F1-score, RMSE)

- **Validación cruzada avanzada**:
  - Estratificada para mantener distribución de resultados
  - K-Fold para evaluación robusta de modelos regresores

### 3. Técnicas de Ingeniería de Características

- **Preprocesamiento robusto**:
  - **NUEVO**: KNNImputer para valores faltantes
  - **NUEVO**: RobustScaler resistente a outliers
  - Codificación one-hot para variables categóricas

- **Selección y Análisis de Características**:
  - Análisis de importancia para identificar las variables más predictivas
  - **NUEVO**: Soporte para análisis SHAP
  - Visualización de las características más influyentes

### 4. Explicabilidad e Interpretación

- **Factores clave mejorados**:
  - Identificación inteligente de factores relevantes para cada predicción
  - **NUEVO**: Factores más específicos basados en el contexto del partido
  - **NUEVO**: Análisis comparativo de estilos de juego entre equipos

- **Visualizaciones avanzadas**:
  - **NUEVO**: Exportación de importancia de características
  - Gráficos de barras para variables más influyentes
  - Capacidad de analizar la evolución de predicciones

## Cómo entrenar los modelos

Para entrenar los modelos mejorados, ejecute el siguiente comando:

```bash
python entrenar_modelos.py [opciones]
```

Opciones disponibles:
- `--optimizar`: Realiza búsqueda de hiperparámetros con Optuna
- `--visualizar`: Genera visualizaciones adicionales de importancia
- `--generar-datos`: Fuerza la generación de datos sintéticos nuevos
- `--evaluar`: Realiza una evaluación completa después del entrenamiento

Este script:
1. Cargará los datos históricos o generará datos sintéticos
2. Extraerá las características avanzadas
3. Entrenará modelos predictivos (con optimización opcional)
4. Evaluará su rendimiento
5. Guardará los modelos entrenados para uso futuro

## Próximas mejoras planificadas

- **Integración de datos externos**: Incorporación de información sobre lesiones de jugadores, clima, etc.
- **Modelos de deep learning**: Exploración de redes neuronales para patrones más complejos
- **Actualización continua**: Reentrenamiento automático con nuevos datos
- **Explicabilidad avanzada**: Expansión de herramientas SHAP para interpretación
- **Análisis de jugadores clave**: Inclusión de estadísticas individuales de jugadores

## Requisitos

Para utilizar estas mejoras, asegúrese de tener instaladas las siguientes bibliotecas:

```
pandas==2.1.0
numpy==1.24.3
scikit-learn==1.3.0
matplotlib==3.7.2
seaborn==0.12.2
flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
xgboost==2.0.0
optuna==3.3.0
shap==0.43.0
joblib==1.3.2
```

Instale los requisitos con:

```bash
pip install -r requirements.txt
```
