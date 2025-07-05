#!/usr/bin/env python
"""
Script de pruebas para verificar que las optimizaciones funcionen correctamente.
Ejecuta este script después de aplicar las optimizaciones para validar el rendimiento.
"""

import os
import sys
import time
import logging
import unittest
from pathlib import Path
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pruebas_optimizacion')

class OptimizationTests(unittest.TestCase):
    """Pruebas para verificar las optimizaciones"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para las pruebas"""
        # Verificar que los módulos de optimización existan
        cls.optimization_modules = [
            "utils/cache_manager.py",
            "utils/http_optimizer.py",
            "utils/db_optimizer.py",
            "utils/log_manager.py",
            "utils/analytics_optimizer.py",
            "utils/config_manager.py"
        ]
        
        # Importar los módulos de optimización si existen
        sys.path.insert(0, os.path.abspath("."))
        
        # Intentar importar los módulos
        cls.modules_imported = {}
        for module_path in cls.optimization_modules:
            module_name = os.path.basename(module_path).replace(".py", "")
            try:
                module = __import__(f"utils.{module_name}", fromlist=["*"])
                cls.modules_imported[module_name] = module
                logger.info(f"Módulo {module_name} importado correctamente")
            except ImportError as e:
                logger.warning(f"No se pudo importar {module_name}: {e}")
                cls.modules_imported[module_name] = None
    
    def test_modules_exist(self):
        """Verifica que los módulos de optimización existan"""
        for module_path in self.optimization_modules:
            self.assertTrue(
                os.path.exists(module_path),
                f"El módulo {module_path} no existe"
            )
    
    def test_cache_manager(self):
        """Prueba el gestor de caché"""
        if not self.modules_imported.get("cache_manager"):
            self.skipTest("Módulo cache_manager no disponible")
            
        cache_manager_module = self.modules_imported["cache_manager"]
        cache_manager = cache_manager_module.CacheManager(cache_dir="data/cache")
        
        # Prueba de almacenamiento en memoria
        key = "test_key"
        data = {"test": "data", "value": 123}
        
        cache_manager.set(key, data)
        retrieved_data = cache_manager.get(key)
        
        self.assertEqual(data, retrieved_data, "Los datos recuperados no coinciden con los guardados")
        
        # Prueba de expiración
        cache_manager.set(key + "_expire", data, expiry=1)
        time.sleep(1.5)  # Esperar a que expire
        expired_data = cache_manager.get(key + "_expire")
        
        self.assertIsNone(expired_data, "Los datos no expiraron correctamente")
    
    def test_config_manager(self):
        """Prueba el gestor de configuración"""
        if not self.modules_imported.get("config_manager"):
            self.skipTest("Módulo config_manager no disponible")
            
        config_manager_module = self.modules_imported["config_manager"]
        
        # Crear un archivo de configuración temporal para la prueba
        config_dir = Path("config_test")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "test_config.json"
        test_config = {
            "app": {
                "name": "TestApp",
                "version": "1.0.0"
            },
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }
        
        with open(config_file, "w") as f:
            json.dump(test_config, f)
        
        # Probar el gestor de configuración
        config_manager = config_manager_module.ConfigManager(
            config_dir=str(config_dir),
            main_config_file="test_config.json"
        )
        
        # Verificar que se cargue correctamente la configuración
        self.assertEqual(
            config_manager.get("app.name"),
            "TestApp",
            "No se pudo leer la configuración correctamente"
        )
        
        # Verificar valor por defecto
        self.assertEqual(
            config_manager.get("app.missing", default="DefaultValue"),
            "DefaultValue",
            "El valor por defecto no funciona correctamente"
        )
        
        # Limpiar
        config_file.unlink()
        config_dir.rmdir()
    
    def test_http_optimizer(self):
        """Prueba el optimizador HTTP"""
        if not self.modules_imported.get("http_optimizer"):
            self.skipTest("Módulo http_optimizer no disponible")
            
        http_optimizer_module = self.modules_imported["http_optimizer"]
        http_optimizer = http_optimizer_module.HTTPOptimizer()
        
        # Probar sesión reutilizable
        session = http_optimizer.session
        self.assertIsNotNone(session, "La sesión HTTP no se inicializó")
        
        # Probar petición con retry
        try:
            response = http_optimizer.fetch_with_retry("https://httpbin.org/get")
            self.assertEqual(response.status_code, 200, "La petición HTTP no fue exitosa")
        except Exception as e:
            self.fail(f"La petición HTTP falló con error: {e}")
            
        # Probar peticiones paralelas
        urls = ["https://httpbin.org/get", "https://httpbin.org/get?q=1", "https://httpbin.org/get?q=2"]
        
        try:
            def fetch_url(url):
                response = requests.get(url)
                return response.status_code
                
            results = http_optimizer.fetch_parallel([
                (fetch_url, [url]) for url in urls
            ])
            
            self.assertEqual(len(results), len(urls), "No se completaron todas las peticiones paralelas")
            for result in results:
                self.assertEqual(result, 200, "Una petición paralela no fue exitosa")
        except Exception as e:
            self.fail(f"Las peticiones paralelas fallaron con error: {e}")
    
    def test_performance_comparison(self):
        """Compara el rendimiento antes y después de las optimizaciones"""
        logger.info("Ejecutando comparación de rendimiento...")
        
        # Simular una función sin optimización
        def unoptimized_function(iterations=1000):
            start_time = time.time()
            result = 0
            for i in range(iterations):
                result += i
            elapsed = time.time() - start_time
            return elapsed
        
        # Simular una función con optimización (paralelizada)
        def optimized_function(iterations=1000):
            start_time = time.time()
            chunks = 10
            chunk_size = iterations // chunks
            
            def process_chunk(start, end):
                result = 0
                for i in range(start, end):
                    result += i
                return result
            
            with ThreadPoolExecutor(max_workers=chunks) as executor:
                futures = [
                    executor.submit(process_chunk, i*chunk_size, (i+1)*chunk_size)
                    for i in range(chunks)
                ]
                results = [future.result() for future in futures]
                
            elapsed = time.time() - start_time
            return elapsed
        
        # Ejecutar pruebas de rendimiento
        iterations = [10000, 100000, 1000000]
        unoptimized_times = []
        optimized_times = []
        
        for iteration in iterations:
            logger.info(f"Probando con {iteration} iteraciones...")
            
            unopt_time = unoptimized_function(iteration)
            unoptimized_times.append(unopt_time)
            
            opt_time = optimized_function(iteration)
            optimized_times.append(opt_time)
            
            improvement = (unopt_time - opt_time) / unopt_time * 100
            logger.info(f"Mejora: {improvement:.2f}%")
        
        # Crear gráfica de comparación
        x = np.arange(len(iterations))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        rects1 = ax.bar(x - width/2, unoptimized_times, width, label='Sin optimizar')
        rects2 = ax.bar(x + width/2, optimized_times, width, label='Optimizado')
        
        ax.set_ylabel('Tiempo (segundos)')
        ax.set_title('Comparación de rendimiento')
        ax.set_xticks(x)
        ax.set_xticklabels([f"{it/1000}K" for it in iterations])
        ax.legend()
        
        # Añadir etiquetas con porcentajes de mejora
        for i in range(len(iterations)):
            improvement = (unoptimized_times[i] - optimized_times[i]) / unoptimized_times[i] * 100
            ax.annotate(f"{improvement:.1f}%", 
                       xy=(i, min(unoptimized_times[i], optimized_times[i])/2),
                       xytext=(0, 0),
                       textcoords="offset points",
                       ha='center', va='bottom')
        
        # Guardar gráfica
        plt.tight_layout()
        plt.savefig('performance_comparison.png')
        logger.info("Gráfica guardada en 'performance_comparison.png'")
        
        # Verificar que hay mejora de rendimiento
        for i in range(len(iterations)):
            self.assertLess(
                optimized_times[i],
                unoptimized_times[i],
                f"No hay mejora de rendimiento para {iterations[i]} iteraciones"
            )

def run_tests():
    """Ejecuta las pruebas de optimización"""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

def main():
    """Función principal"""
    logger.info("Iniciando pruebas de optimización")
    run_tests()
    logger.info("Pruebas de optimización completadas")

if __name__ == "__main__":
    main()
