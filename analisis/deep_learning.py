"""
Módulo para integrar modelos de Deep Learning para análisis predictivo de fútbol.
Implementa interfaces para redes neuronales en TensorFlow/Keras.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import joblib
import json

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model, Model
    from tensorflow.keras.layers import Dense, Dropout, LSTM, GRU, Bidirectional, Input, Concatenate
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("TensorFlow no está instalado. Modelos de deep learning no disponibles.")
    TENSORFLOW_AVAILABLE = False

class DeepLearningPredictor:
    def __init__(self):
        """
        Inicializa el predictor de Deep Learning para partidos de fútbol.
        """
        self.models_dir = os.path.join('data', 'modelos', 'deep_learning')
        os.makedirs(self.models_dir, exist_ok=True)
        self.modelo_goles_local = None
        self.modelo_goles_visitante = None
        self.modelo_resultado = None
        self.modelo_secuencial = None  # Para análisis de secuencias (LSTM/GRU)
        self.feature_scaler = None
    
    def disponible(self):
        """
        Verifica si TensorFlow está disponible para usar modelos de deep learning.
        
        Returns:
            bool: True si TensorFlow está disponible, False en caso contrario.
        """
        return TENSORFLOW_AVAILABLE
    
    def crear_modelo_goles(self, input_shape):
        """
        Crea un modelo de red neuronal para predecir goles.
        
        Args:
            input_shape: Forma de entrada para el modelo
            
        Returns:
            Modelo de Keras compilado
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se puede crear el modelo.")
            return None
        
        model = Sequential([
            Dense(64, activation='relu', input_shape=(input_shape,)),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')  # Regresión para número de goles
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return model
    
    def crear_modelo_resultado(self, input_shape):
        """
        Crea un modelo de red neuronal para predecir el resultado (victoria local, empate, victoria visitante).
        
        Args:
            input_shape: Forma de entrada para el modelo
            
        Returns:
            Modelo de Keras compilado
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se puede crear el modelo.")
            return None
        
        model = Sequential([
            Dense(64, activation='relu', input_shape=(input_shape,)),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')  # Clasificación multiclase (local, empate, visitante)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def crear_modelo_secuencial(self, seq_length, n_features):
        """
        Crea un modelo secuencial con LSTM para analizar series temporales de partidos.
        
        Args:
            seq_length: Longitud de la secuencia (número de partidos anteriores)
            n_features: Número de características por partido
            
        Returns:
            Modelo de Keras compilado
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se puede crear el modelo.")
            return None
        
        model = Sequential([
            LSTM(64, input_shape=(seq_length, n_features), return_sequences=True),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')  # Clasificación multiclase (local, empate, visitante)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def entrenar_modelos(self, X_train, y_train_goles_local, y_train_goles_visitante, y_train_resultado, 
                         X_val=None, y_val_goles_local=None, y_val_goles_visitante=None, y_val_resultado=None,
                         epochs=100, batch_size=32, verbose=1):
        """
        Entrena los modelos de deep learning con los datos proporcionados.
        
        Args:
            X_train: Características de entrenamiento
            y_train_goles_local: Goles locales (entrenamiento)
            y_train_goles_visitante: Goles visitantes (entrenamiento)
            y_train_resultado: Resultados codificados one-hot (entrenamiento)
            X_val: Características de validación (opcional)
            y_val_goles_local: Goles locales (validación)
            y_val_goles_visitante: Goles visitantes (validación)
            y_val_resultado: Resultados codificados one-hot (validación)
            epochs: Número de épocas de entrenamiento
            batch_size: Tamaño del lote para entrenamiento
            verbose: Nivel de detalle en la salida durante el entrenamiento
            
        Returns:
            Dict con historiales de entrenamiento
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se pueden entrenar los modelos.")
            return None
        
        # Crear modelos
        input_shape = X_train.shape[1]
        self.modelo_goles_local = self.crear_modelo_goles(input_shape)
        self.modelo_goles_visitante = self.crear_modelo_goles(input_shape)
        self.modelo_resultado = self.crear_modelo_resultado(input_shape)
        
        # Callbacks para early stopping y checkpoint
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ModelCheckpoint(
                os.path.join(self.models_dir, 'mejor_modelo_{epoch:02d}.h5'),
                save_best_only=True
            )
        ]
        
        # Configurar datos de validación
        validation_data = {}
        if X_val is not None:
            validation_data['goles_local'] = (X_val, y_val_goles_local)
            validation_data['goles_visitante'] = (X_val, y_val_goles_visitante)
            validation_data['resultado'] = (X_val, y_val_resultado)
        
        # Entrenar modelos
        historiales = {}
        
        print("Entrenando modelo de goles local...")
        history_local = self.modelo_goles_local.fit(
            X_train, y_train_goles_local,
            validation_data=validation_data.get('goles_local'),
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=callbacks
        )
        historiales['goles_local'] = history_local.history
        
        print("Entrenando modelo de goles visitante...")
        history_visitante = self.modelo_goles_visitante.fit(
            X_train, y_train_goles_visitante,
            validation_data=validation_data.get('goles_visitante'),
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=callbacks
        )
        historiales['goles_visitante'] = history_visitante.history
        
        print("Entrenando modelo de resultado...")
        history_resultado = self.modelo_resultado.fit(
            X_train, y_train_resultado,
            validation_data=validation_data.get('resultado'),
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=callbacks
        )
        historiales['resultado'] = history_resultado.history
        
        # Guardar modelos
        self.guardar_modelos()
        
        return historiales
    
    def entrenar_modelo_secuencial(self, X_train_seq, y_train, X_val_seq=None, y_val=None, 
                                   epochs=100, batch_size=32, verbose=1):
        """
        Entrena un modelo secuencial con datos de series temporales.
        
        Args:
            X_train_seq: Secuencias de características (forma: [samples, sequence_length, features])
            y_train: Etiquetas de entrenamiento
            X_val_seq: Secuencias de validación (opcional)
            y_val: Etiquetas de validación (opcional)
            epochs: Número de épocas
            batch_size: Tamaño del lote
            verbose: Nivel de verbosidad
            
        Returns:
            Historial de entrenamiento
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se puede entrenar el modelo secuencial.")
            return None
        
        # Crear modelo
        seq_length, n_features = X_train_seq.shape[1], X_train_seq.shape[2]
        self.modelo_secuencial = self.crear_modelo_secuencial(seq_length, n_features)
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ModelCheckpoint(
                os.path.join(self.models_dir, 'mejor_modelo_secuencial_{epoch:02d}.h5'),
                save_best_only=True
            )
        ]
        
        # Configurar datos de validación
        validation_data = None
        if X_val_seq is not None and y_val is not None:
            validation_data = (X_val_seq, y_val)
        
        # Entrenar modelo
        print("Entrenando modelo secuencial...")
        history = self.modelo_secuencial.fit(
            X_train_seq, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            callbacks=callbacks
        )
        
        # Guardar modelo
        self.modelo_secuencial.save(os.path.join(self.models_dir, 'modelo_secuencial.h5'))
        
        return history.history
    
    def guardar_modelos(self):
        """
        Guarda los modelos entrenados en disco.
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se pueden guardar los modelos.")
            return
        
        if self.modelo_goles_local:
            self.modelo_goles_local.save(os.path.join(self.models_dir, 'modelo_goles_local.h5'))
            
        if self.modelo_goles_visitante:
            self.modelo_goles_visitante.save(os.path.join(self.models_dir, 'modelo_goles_visitante.h5'))
            
        if self.modelo_resultado:
            self.modelo_resultado.save(os.path.join(self.models_dir, 'modelo_resultado.h5'))
        
        print(f"Modelos guardados en {self.models_dir}")
    
    def cargar_modelos(self):
        """
        Carga los modelos guardados desde disco.
        
        Returns:
            bool: True si se cargaron los modelos correctamente, False en caso contrario
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se pueden cargar los modelos.")
            return False
        
        try:
            modelo_goles_local_path = os.path.join(self.models_dir, 'modelo_goles_local.h5')
            modelo_goles_visitante_path = os.path.join(self.models_dir, 'modelo_goles_visitante.h5')
            modelo_resultado_path = os.path.join(self.models_dir, 'modelo_resultado.h5')
            modelo_secuencial_path = os.path.join(self.models_dir, 'modelo_secuencial.h5')
            
            if os.path.exists(modelo_goles_local_path):
                self.modelo_goles_local = load_model(modelo_goles_local_path)
            
            if os.path.exists(modelo_goles_visitante_path):
                self.modelo_goles_visitante = load_model(modelo_goles_visitante_path)
            
            if os.path.exists(modelo_resultado_path):
                self.modelo_resultado = load_model(modelo_resultado_path)
                
            if os.path.exists(modelo_secuencial_path):
                self.modelo_secuencial = load_model(modelo_secuencial_path)
                
            # Cargar scaler si existe
            scaler_path = os.path.join(self.models_dir, 'feature_scaler.pkl')
            if os.path.exists(scaler_path):
                self.feature_scaler = joblib.load(scaler_path)
                
            return True
        except Exception as e:
            print(f"Error al cargar los modelos: {e}")
            return False
    
    def predecir(self, X):
        """
        Realiza predicciones con los modelos de deep learning.
        
        Args:
            X: Características para predecir
            
        Returns:
            Dict con predicciones de goles y resultado
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se pueden hacer predicciones.")
            return None
        
        if self.modelo_goles_local is None or self.modelo_goles_visitante is None or self.modelo_resultado is None:
            print("Los modelos no están cargados. Cargue los modelos primero.")
            return None
        
        # Aplicar scaler si existe
        if self.feature_scaler is not None:
            X_scaled = self.feature_scaler.transform(X)
        else:
            X_scaled = X
        
        # Hacer predicciones
        goles_local_pred = self.modelo_goles_local.predict(X_scaled)
        goles_visitante_pred = self.modelo_goles_visitante.predict(X_scaled)
        resultado_probs = self.modelo_resultado.predict(X_scaled)
        
        # Redondear goles a enteros no negativos
        goles_local = max(0, round(float(goles_local_pred[0][0])))
        goles_visitante = max(0, round(float(goles_visitante_pred[0][0])))
        
        # Interpretar resultado (victoria local, empate, victoria visitante)
        resultado_idx = np.argmax(resultado_probs[0])
        resultados = ['local', 'empate', 'visitante']
        resultado = resultados[resultado_idx]
        
        # Estructura de resultado
        prediccion = {
            'goles': {
                'local': int(goles_local),
                'visitante': int(goles_visitante)
            },
            'resultado': resultado,
            'probabilidades': {
                'victoria_local': float(resultado_probs[0][0]),
                'empate': float(resultado_probs[0][1]),
                'victoria_visitante': float(resultado_probs[0][2])
            }
        }
        
        return prediccion
    
    def predecir_secuencia(self, X_seq):
        """
        Realiza predicciones usando el modelo secuencial.
        
        Args:
            X_seq: Secuencia de características (forma: [1, sequence_length, features])
            
        Returns:
            Predicción de resultado
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no está disponible. No se pueden hacer predicciones.")
            return None
        
        if self.modelo_secuencial is None:
            print("El modelo secuencial no está cargado. Cargue el modelo primero.")
            return None
        
        # Hacer predicción
        resultado_probs = self.modelo_secuencial.predict(X_seq)
        
        # Interpretar resultado
        resultado_idx = np.argmax(resultado_probs[0])
        resultados = ['local', 'empate', 'visitante']
        resultado = resultados[resultado_idx]
        
        # Estructura de resultado
        prediccion = {
            'resultado': resultado,
            'probabilidades': {
                'victoria_local': float(resultado_probs[0][0]),
                'empate': float(resultado_probs[0][1]),
                'victoria_visitante': float(resultado_probs[0][2])
            }
        }
        
        return prediccion
    
    def visualizar_historico_entrenamiento(self, historiales, guardar=False):
        """
        Visualiza el histórico de entrenamiento de los modelos.
        
        Args:
            historiales: Dict con los historiales de entrenamiento
            guardar: Si True, guarda las figuras en disco
            
        Returns:
            Lista de figuras generadas
        """
        if not historiales:
            print("No hay historiales de entrenamiento para visualizar.")
            return None
        
        figuras = []
        
        # Función auxiliar para crear gráficos
        def crear_grafico_metrica(historia, titulo, metrica, val_metrica=None):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(historia[metrica], label=f'Entrenamiento')
            if val_metrica in historia:
                ax.plot(historia[val_metrica], label=f'Validación')
            ax.set_title(titulo)
            ax.set_xlabel('Época')
            ax.set_ylabel(metrica)
            ax.legend()
            ax.grid(True)
            return fig
        
        # Gráficos para modelo de goles local
        if 'goles_local' in historiales:
            hist = historiales['goles_local']
            fig_loss = crear_grafico_metrica(hist, 'Pérdida - Modelo Goles Local', 'loss', 'val_loss')
            fig_mae = crear_grafico_metrica(hist, 'Error Absoluto Medio - Modelo Goles Local', 'mae', 'val_mae')
            figuras.extend([fig_loss, fig_mae])
            
            if guardar:
                fig_loss.savefig(os.path.join(self.models_dir, 'history_loss_goles_local.png'))
                fig_mae.savefig(os.path.join(self.models_dir, 'history_mae_goles_local.png'))
        
        # Gráficos para modelo de goles visitante
        if 'goles_visitante' in historiales:
            hist = historiales['goles_visitante']
            fig_loss = crear_grafico_metrica(hist, 'Pérdida - Modelo Goles Visitante', 'loss', 'val_loss')
            fig_mae = crear_grafico_metrica(hist, 'Error Absoluto Medio - Modelo Goles Visitante', 'mae', 'val_mae')
            figuras.extend([fig_loss, fig_mae])
            
            if guardar:
                fig_loss.savefig(os.path.join(self.models_dir, 'history_loss_goles_visitante.png'))
                fig_mae.savefig(os.path.join(self.models_dir, 'history_mae_goles_visitante.png'))
        
        # Gráficos para modelo de resultado
        if 'resultado' in historiales:
            hist = historiales['resultado']
            fig_loss = crear_grafico_metrica(hist, 'Pérdida - Modelo Resultado', 'loss', 'val_loss')
            fig_acc = crear_grafico_metrica(hist, 'Precisión - Modelo Resultado', 'accuracy', 'val_accuracy')
            figuras.extend([fig_loss, fig_acc])
            
            if guardar:
                fig_loss.savefig(os.path.join(self.models_dir, 'history_loss_resultado.png'))
                fig_acc.savefig(os.path.join(self.models_dir, 'history_accuracy_resultado.png'))
        
        return figuras
