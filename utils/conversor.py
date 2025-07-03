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

def main():
    """Función principal para ejecución desde línea de comandos"""
    parser = argparse.ArgumentParser(description='Conversor de datos entre CSV y JSON')
    parser.add_argument('--entrada', required=True, help='Archivo de entrada')
    parser.add_argument('--salida', help='Archivo de salida (opcional)')
    parser.add_argument('--formato', choices=['csv-json', 'json-csv'], required=True,
                       help='Formato de conversión')
    parser.add_argument('--nombre', help='Nombre del dataset (para CSV a JSON)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.entrada):
        print(f"Error: El archivo {args.entrada} no existe")
        sys.exit(1)
    
    try:
        if args.formato == 'csv-json':
            print(f"Convirtiendo CSV a JSON: {args.entrada}")
            resultado = csv_a_json(args.entrada, args.salida, args.nombre)
            
            if resultado:
                print(f"Conversión exitosa. {len(resultado['matches'])} partidos convertidos.")
            else:
                print("Error en la conversión")
                sys.exit(1)
                
        elif args.formato == 'json-csv':
            print(f"Convirtiendo JSON a CSV: {args.entrada}")
            resultado = json_a_csv(args.entrada, args.salida)
            
            if resultado is not None:
                print(f"Conversión exitosa. {len(resultado)} partidos convertidos.")
            else:
                print("Error en la conversión")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error durante la conversión: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
