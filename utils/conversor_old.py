"""
Herramienta para convertir datos entre formatos (CSV, JSON)
Compatible con el formato estándar de open-football y otros datasets públicos.
"""

import os
import pandas as pd
import json
import argparse
import csv
from datetime import datetime
import sys

class CSVtoJSON:
    """Clase para convertir datos CSV a formato JSON estándar"""
    
    def __init__(self):
        """Inicializa el conversor"""
        self.formato_estandar = {
            "name": "",
            "matches": []
        }
    
    def convertir_archivo(self, ruta_csv, ruta_salida=None, nombre_dataset=None):
        """
        Convierte un archivo CSV a formato JSON estándar.
        
        Args:
            ruta_csv: Ruta al archivo CSV de entrada
            ruta_salida: Ruta donde guardar el archivo JSON (opcional)
            nombre_dataset: Nombre para el conjunto de datos (opcional)
        
        Returns:
            Datos en formato JSON (dict)
        """
        try:
            # Cargar datos CSV
            df = pd.read_csv(ruta_csv)
            return self.convertir_dataframe(df, nombre_dataset, ruta_salida)
            
        except Exception as e:
            print(f"Error al convertir archivo CSV: {e}")
            return None
    
    def convertir_dataframe(self, df, nombre_dataset=None, ruta_salida=None):
        """
        Convierte un DataFrame a formato JSON estándar.
        
        Args:
            df: DataFrame de pandas
            nombre_dataset: Nombre para el conjunto de datos (opcional)
            ruta_salida: Ruta donde guardar el archivo JSON (opcional)
        
        Returns:
            Datos en formato JSON (dict)
        """
        try:
            # Crear estructura base
            datos_json = {
                "name": nombre_dataset or "Dataset Convertido",
                "matches": []
            }
            
            # Convertir cada fila
            for _, fila in df.iterrows():
                partido = self._convertir_fila_a_partido(fila)
                if partido:
                    datos_json["matches"].append(partido)
            
            # Guardar si se especifica ruta
            if ruta_salida:
                self._guardar_json(datos_json, ruta_salida)
            
            return datos_json
            
        except Exception as e:
            print(f"Error al convertir DataFrame: {e}")
            return None
    
    def _convertir_fila_a_partido(self, fila):
        """Convierte una fila del DataFrame a formato de partido JSON"""
        try:
            # Verificar columnas mínimas requeridas
            if 'equipo_local' not in fila or 'equipo_visitante' not in fila:
                return None
            
            # Crear estructura básica del partido
            partido = {
                "team1": fila['equipo_local'],
                "team2": fila['equipo_visitante']
            }
            
            # Añadir fecha si está disponible
            if 'fecha' in fila and pd.notna(fila['fecha']):
                try:
                    fecha = pd.to_datetime(fila['fecha'])
                    partido["date"] = fecha.strftime("%Y-%m-%d")
                except:
                    partido["date"] = str(fila['fecha'])
            
            # Añadir resultado si está disponible
            if 'goles_local' in fila and 'goles_visitante' in fila:
                if pd.notna(fila['goles_local']) and pd.notna(fila['goles_visitante']):
                    partido["score"] = {
                        "ft": [int(fila['goles_local']), int(fila['goles_visitante'])]
                    }
            
            # Añadir información adicional si existe
            campos_adicionales = {
                'liga': 'league',
                'temporada': 'season',
                'jornada': 'round',
                'arbitro': 'referee',
                'estadio': 'stadium'
            }
            
            for campo_csv, campo_json in campos_adicionales.items():
                if campo_csv in fila and pd.notna(fila[campo_csv]):
                    partido[campo_json] = str(fila[campo_csv])
            
            return partido
            
        except Exception as e:
            print(f"Error al convertir fila: {e}")
            return None
    
    def _guardar_json(self, datos, ruta_salida):
        """Guarda los datos JSON en un archivo"""
        try:
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            print(f"Archivo JSON guardado en: {ruta_salida}")
            
        except Exception as e:
            print(f"Error al guardar archivo JSON: {e}")

class JSONtoCSV:
    """Clase para convertir datos JSON a formato CSV"""
    
    def __init__(self):
        """Inicializa el conversor"""
        pass
    
    def convertir_archivo(self, ruta_json, ruta_salida=None):
        """
        Convierte un archivo JSON a formato CSV.
        
        Args:
            ruta_json: Ruta al archivo JSON de entrada
            ruta_salida: Ruta donde guardar el archivo CSV (opcional)
        
        Returns:
            DataFrame de pandas
        """
        try:
            # Cargar datos JSON
            with open(ruta_json, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            return self.convertir_datos(datos, ruta_salida)
            
        except Exception as e:
            print(f"Error al convertir archivo JSON: {e}")
            return None
    
    def convertir_datos(self, datos_json, ruta_salida=None):
        """
        Convierte datos JSON a formato CSV.
        
        Args:
            datos_json: Datos en formato JSON (dict)
            ruta_salida: Ruta donde guardar el archivo CSV (opcional)
        
        Returns:
            DataFrame de pandas
        """
        try:
            # Extraer partidos
            partidos = datos_json.get('matches', [])
            if not partidos:
                print("No se encontraron partidos en los datos JSON")
                return None
            
            # Convertir a lista de diccionarios
            filas = []
            for partido in partidos:
                fila = self._convertir_partido_a_fila(partido)
                if fila:
                    filas.append(fila)
            
            if not filas:
                print("No se pudieron convertir los partidos")
                return None
            
            # Crear DataFrame
            df = pd.DataFrame(filas)
            
            # Guardar si se especifica ruta
            if ruta_salida:
                df.to_csv(ruta_salida, index=False, encoding='utf-8')
                print(f"Archivo CSV guardado en: {ruta_salida}")
            
            return df
            
        except Exception as e:
            print(f"Error al convertir datos JSON: {e}")
            return None
    
    def _convertir_partido_a_fila(self, partido):
        """Convierte un partido JSON a fila de CSV"""
        try:
            fila = {
                'equipo_local': partido.get('team1', ''),
                'equipo_visitante': partido.get('team2', '')
            }
            
            # Añadir fecha
            if 'date' in partido:
                fila['fecha'] = partido['date']
            
            # Añadir resultado
            if 'score' in partido and 'ft' in partido['score']:
                goles = partido['score']['ft']
                if len(goles) >= 2:
                    fila['goles_local'] = goles[0]
                    fila['goles_visitante'] = goles[1]
            
            # Añadir campos adicionales
            campos_adicionales = {
                'league': 'liga',
                'season': 'temporada',
                'round': 'jornada',
                'referee': 'arbitro',
                'stadium': 'estadio'
            }
            
            for campo_json, campo_csv in campos_adicionales.items():
                if campo_json in partido:
                    fila[campo_csv] = partido[campo_json]
            
            return fila
            
        except Exception as e:
            print(f"Error al convertir partido: {e}")
            return None

# Funciones de compatibilidad hacia atrás
def csv_a_json(ruta_csv, ruta_salida=None, nombre_dataset=None):
    """Función de compatibilidad para conversión CSV a JSON"""
    conversor = CSVtoJSON()
    return conversor.convertir_archivo(ruta_csv, ruta_salida, nombre_dataset)

def json_a_csv(ruta_json, ruta_salida=None):
    """Función de compatibilidad para conversión JSON a CSV"""
    conversor = JSONtoCSV()
    return conversor.convertir_archivo(ruta_json, ruta_salida)
                    print(f"Advertencia: No se pudo convertir fecha '{fila['fecha']}' para {fila['equipo_local']} vs {fila['equipo_visitante']}")
            
            # Añadir resultado si está disponible
            if 'goles_local' in fila and 'goles_visitante' in fila:
                try:
                    goles_local = int(fila['goles_local'])
                    goles_visitante = int(fila['goles_visitante'])
                    partido["score"] = {"ft": [goles_local, goles_visitante]}
                except:
                    print(f"Advertencia: No se pudieron convertir goles para {fila['equipo_local']} vs {fila['equipo_visitante']}")
            
            # Añadir información de competición/ronda si está disponible
            if 'competicion' in fila:
                partido["competition"] = fila['competicion']
            if 'jornada' in fila:
                partido["round"] = f"Jornada {fila['jornada']}"
            elif 'fase' in fila:
                partido["round"] = fila['fase']
            
            # Añadir predicción si está disponible
            if 'prob_local' in fila and 'prob_empate' in fila and 'prob_visitante' in fila:
                try:
                    partido["prediction"] = {
                        "probabilities": {
                            "home_win": float(fila['prob_local']),
                            "draw": float(fila['prob_empate']),
                            "away_win": float(fila['prob_visitante'])
                        }
                    }
                except:
                    pass
            
            partidos.append(partido)
        
        # Crear estructura final del JSON
        json_data = {
            "name": nombre_dataset or os.path.basename(ruta_csv).split('.')[0],
            "matches": partidos
        }
        
        # Guardar archivo JSON si se especificó ruta
        if ruta_salida:
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"Archivo JSON guardado en {ruta_salida}")
        
        return json_data
    
    except Exception as e:
        print(f"Error al convertir CSV a JSON: {e}")
        return None

def json_a_csv(ruta_json, ruta_salida=None):
    """
    Convierte un archivo JSON en formato estándar a CSV.
    
    Args:
        ruta_json: Ruta al archivo JSON de entrada
        ruta_salida: Ruta donde guardar el archivo CSV (opcional)
    
    Returns:
        DataFrame con los datos
    """
    try:
        # Cargar datos JSON
        with open(ruta_json, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Extraer partidos
        if 'matches' not in json_data:
            print("Error: El archivo JSON no contiene una lista de partidos ('matches').")
            return None
        
        partidos = json_data['matches']
        
        # Convertir a lista de diccionarios para DataFrame
        filas = []
        
        for partido in partidos:
            fila = {}
            
            # Datos básicos
            fila['equipo_local'] = partido.get('team1', '')
            fila['equipo_visitante'] = partido.get('team2', '')
            
            # Fecha
            if 'date' in partido:
                fila['fecha'] = partido['date']
            
            # Información de competición/ronda
            if 'competition' in partido:
                fila['competicion'] = partido['competition']
            if 'round' in partido:
                fila['jornada'] = partido['round']
            
            # Resultado
            if 'score' in partido and 'ft' in partido['score'] and len(partido['score']['ft']) >= 2:
                fila['goles_local'] = partido['score']['ft'][0]
                fila['goles_visitante'] = partido['score']['ft'][1]
            
            # Predicción
            if 'prediction' in partido and 'probabilities' in partido['prediction']:
                prob = partido['prediction']['probabilities']
                fila['prob_local'] = prob.get('home_win', '')
                fila['prob_empate'] = prob.get('draw', '')
                fila['prob_visitante'] = prob.get('away_win', '')
            
            if 'prediction' in partido and 'score' in partido['prediction'] and len(partido['prediction']['score']) >= 2:
                fila['pred_goles_local'] = partido['prediction']['score'][0]
                fila['pred_goles_visitante'] = partido['prediction']['score'][1]
            
            filas.append(fila)
        
        # Crear DataFrame
        df = pd.DataFrame(filas)
        
        # Guardar CSV si se especificó ruta
        if ruta_salida:
            df.to_csv(ruta_salida, index=False)
            print(f"Archivo CSV guardado en {ruta_salida}")
        
        return df
    
    except Exception as e:
        print(f"Error al convertir JSON a CSV: {e}")
        return None

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Conversor entre formatos CSV y JSON para datos de fútbol')
    parser.add_argument('archivo_entrada', help='Archivo de entrada a convertir')
    parser.add_argument('-o', '--output', help='Ruta del archivo de salida')
    parser.add_argument('-n', '--nombre', help='Nombre para el conjunto de datos (solo para conversión CSV a JSON)')
    parser.add_argument('--formato', choices=['auto', 'csv2json', 'json2csv'], default='auto',
                       help='Formato de conversión (por defecto: auto)')
    args = parser.parse_args()
    
    # Determinar rutas
    ruta_entrada = args.archivo_entrada
    
    if not os.path.exists(ruta_entrada):
        print(f"Error: No se encontró el archivo {ruta_entrada}")
        sys.exit(1)
    
    # Determinar formato de conversión si es automático
    formato = args.formato
    if formato == 'auto':
        if ruta_entrada.lower().endswith('.csv'):
            formato = 'csv2json'
        elif ruta_entrada.lower().endswith('.json'):
            formato = 'json2csv'
        else:
            print("Error: No se pudo determinar el formato automáticamente. Utilice --formato")
            sys.exit(1)
    
    # Determinar ruta de salida si no se especificó
    ruta_salida = args.output
    if not ruta_salida:
        base = os.path.basename(ruta_entrada).split('.')[0]
        if formato == 'csv2json':
            ruta_salida = f"{base}.json"
        else:
            ruta_salida = f"{base}.csv"
    
    # Realizar conversión
    if formato == 'csv2json':
        csv_a_json(ruta_entrada, ruta_salida, args.nombre)
    else:
        json_a_csv(ruta_entrada, ruta_salida)

if __name__ == "__main__":
    main()
