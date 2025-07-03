"""
Extensión del módulo futuro.py con métodos adicionales para simulación
"""

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
