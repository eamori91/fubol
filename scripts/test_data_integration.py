#!/usr/bin/env python
"""
Script para probar la integración entre la aplicación y los datos reales en la base de datos.

Este script prueba:
1. La conexión a la base de datos
2. La obtención de datos a través de DataProvider
3. La integración con DataLoader
4. El uso de esos datos en el flujo de análisis

Uso:
    python test_data_integration.py
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.database import db_manager
    from utils.data_provider import data_provider
    from utils.data_loader import DataLoader
    from analisis.historico import AnalisisHistorico
    from analisis.proximo import AnalisisProximo
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("¿Has instalado todas las dependencias? Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_data_integration')

def test_database_connection():
    """Prueba la conexión a la base de datos."""
    logger.info("\n" + "="*80)
    logger.info("PRUEBA DE CONEXIÓN A BASE DE DATOS")
    logger.info("="*80)
    
    try:
        # Probar una consulta simple
        result = db_manager.execute_query("SELECT 1 as test")
        
        if result and result[0]['test'] == 1:
            logger.info("✅ Conexión exitosa a la base de datos")
            return True
        else:
            logger.error("❌ Fallo al ejecutar consulta de prueba")
            return False
    except Exception as e:
        logger.error(f"❌ Error de conexión: {e}")
        return False

def test_data_provider():
    """Prueba el proveedor de datos reales."""
    logger.info("\n" + "="*80)
    logger.info("PRUEBA DE DATA PROVIDER")
    logger.info("="*80)
    
    try:
        # Probar obtención de ligas
        ligas = data_provider.obtener_ligas()
        if ligas:
            logger.info(f"✅ Obtenidas {len(ligas)} ligas")
            for i, liga in enumerate(ligas[:3]):  # Mostrar solo 3 primeras
                logger.info(f"  {i+1}. {liga['nombre']} ({liga['pais']})")
        else:
            logger.warning("⚠️ No se encontraron ligas en la base de datos")
        
        # Probar obtención de equipos
        equipos = data_provider.obtener_equipos()
        if equipos:
            logger.info(f"✅ Obtenidos {len(equipos)} equipos")
            for i, equipo in enumerate(equipos[:3]):  # Mostrar solo 3 primeros
                logger.info(f"  {i+1}. {equipo['nombre']} ({equipo.get('liga_nombre', 'Sin liga')})")
        else:
            logger.warning("⚠️ No se encontraron equipos en la base de datos")
            
        # Probar búsqueda de equipo
        if equipos:
            equipo_test = equipos[0]['nombre']
            equipo_encontrado = data_provider.buscar_equipo_por_nombre(equipo_test)
            if equipo_encontrado:
                logger.info(f"✅ Equipo '{equipo_test}' encontrado (ID: {equipo_encontrado['id']})")
            else:
                logger.warning(f"⚠️ No se pudo encontrar el equipo '{equipo_test}'")
                
        # Probar obtención de partidos
        partidos = data_provider.obtener_partidos(limite=10)
        if partidos:
            logger.info(f"✅ Obtenidos {len(partidos)} partidos")
            for i, partido in enumerate(partidos[:3]):  # Mostrar solo 3 primeros
                logger.info(f"  {i+1}. {partido['equipo_local']} vs {partido['equipo_visitante']} ({partido.get('fecha', 'Sin fecha')})")
        else:
            logger.warning("⚠️ No se encontraron partidos en la base de datos")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error en prueba de DataProvider: {e}")
        return False

def test_data_loader():
    """Prueba el cargador de datos con la integración real."""
    logger.info("\n" + "="*80)
    logger.info("PRUEBA DE DATA LOADER")
    logger.info("="*80)
    
    try:
        data_loader = DataLoader()
        
        # Verificar si el DataLoader detecta la disponibilidad de datos reales
        logger.info(f"DataLoader configurado para usar datos reales: {data_loader.use_real_data}")
        
        # Probar obtención de ligas
        ligas = data_loader.obtener_ligas()
        if ligas:
            logger.info(f"✅ DataLoader obtuvo {len(ligas)} ligas")
        else:
            logger.warning("⚠️ DataLoader no obtuvo ligas")
            
        # Probar obtención de equipos
        equipos = data_loader.obtener_equipos()
        if equipos:
            logger.info(f"✅ DataLoader obtuvo {len(equipos)} equipos")
        else:
            logger.warning("⚠️ DataLoader no obtuvo equipos")
            
        # Seleccionar un equipo para pruebas si hay equipos disponibles
        equipo_test = None
        if equipos:
            equipo_test = equipos[0]['nombre']
            logger.info(f"Usando equipo '{equipo_test}' para pruebas")
            
        # Probar obtención de partidos históricos
        if equipo_test:
            partidos_hist = data_loader.obtener_partidos_historicos(equipo=equipo_test)
            if not partidos_hist.empty:
                logger.info(f"✅ DataLoader obtuvo {len(partidos_hist)} partidos históricos para {equipo_test}")
                logger.info(f"Columnas disponibles: {partidos_hist.columns.tolist()}")
                if len(partidos_hist) > 0:
                    logger.info("Ejemplo de datos:")
                    logger.info(partidos_hist.head(2))
            else:
                logger.warning(f"⚠️ DataLoader no obtuvo partidos históricos para {equipo_test}")
                
        # Probar obtención de partidos próximos
        partidos_prox = data_loader.obtener_partidos_proximos(dias=30)
        if not partidos_prox.empty:
            logger.info(f"✅ DataLoader obtuvo {len(partidos_prox)} partidos próximos")
        else:
            logger.warning("⚠️ DataLoader no obtuvo partidos próximos")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error en prueba de DataLoader: {e}")
        return False

def test_analysis_integration():
    """Prueba la integración con módulos de análisis."""
    logger.info("\n" + "="*80)
    logger.info("PRUEBA DE INTEGRACIÓN CON ANÁLISIS")
    logger.info("="*80)
    
    try:
        data_loader = DataLoader()
        analisis_historico = AnalisisHistorico()
        analisis_proximo = AnalisisProximo()
        
        # Obtener equipos disponibles
        equipos = data_loader.obtener_equipos()
        if not equipos:
            logger.warning("⚠️ No hay equipos disponibles para realizar prueba de análisis")
            return False
            
        # Seleccionar un equipo para prueba
        equipo_test = equipos[0]['nombre']
        logger.info(f"Usando equipo '{equipo_test}' para pruebas de análisis")
        
        # Obtener partidos históricos
        partidos_hist = data_loader.obtener_partidos_historicos(equipo=equipo_test)
        if partidos_hist.empty:
            logger.warning(f"⚠️ No hay partidos históricos para {equipo_test}")
            return False
            
        # Realizar análisis histórico
        analisis_historico.datos = partidos_hist
        try:
            resultados = analisis_historico.analizar_equipo_local(equipo_test)
            if resultados:
                logger.info("✅ Análisis histórico completado")
                for k, v in resultados.items():
                    if k != 'ultimos_partidos':  # No mostrar lista completa
                        logger.info(f"  {k}: {v}")
            else:
                logger.warning("⚠️ El análisis histórico no produjo resultados")
        except Exception as e:
            logger.error(f"❌ Error en análisis histórico: {e}")
            
        # Probar análisis próximo partido (si hay datos)
        try:
            partidos_prox = data_loader.obtener_partidos_proximos(dias=30, equipo=equipo_test)
            if not partidos_prox.empty:
                proximo_rival = partidos_prox.iloc[0]['equipo_visitante'] if partidos_prox.iloc[0]['equipo_local'] == equipo_test else partidos_prox.iloc[0]['equipo_local']
                
                analisis_proximo.datos = partidos_hist
                resultados_prox = analisis_proximo.analizar_proximo_partido(equipo_test, proximo_rival)
                
                if resultados_prox:
                    logger.info("✅ Análisis de próximo partido completado")
                    logger.info(f"  Próximo rival: {proximo_rival}")
                    for k, v in resultados_prox.items():
                        if isinstance(v, (int, float, str, bool)) or v is None:  # Solo mostrar valores simples
                            logger.info(f"  {k}: {v}")
                else:
                    logger.warning("⚠️ El análisis de próximo partido no produjo resultados")
            else:
                logger.warning(f"⚠️ No hay partidos próximos para {equipo_test}")
        except Exception as e:
            logger.error(f"❌ Error en análisis próximo: {e}")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error general en prueba de análisis: {e}")
        return False

def main():
    """Función principal del script."""
    logger.info("Iniciando pruebas de integración con datos reales")
    
    # Probar conexión a base de datos
    if not test_database_connection():
        logger.error("No se pudo conectar a la base de datos. Abortando pruebas.")
        return
    
    # Probar proveedor de datos
    test_data_provider()
    
    # Probar cargador de datos
    test_data_loader()
    
    # Probar integración con análisis
    test_analysis_integration()
    
    logger.info("\nPruebas de integración completadas.")

if __name__ == '__main__':
    main()
