#!/usr/bin/env python
'''
Script para iniciar la aplicación con optimizaciones.
'''
import os
import sys
import logging

# Configurar variables de entorno
os.environ['OPTIMIZE_CACHE'] = 'true'
os.environ['OPTIMIZE_HTTP'] = 'true'
os.environ['OPTIMIZE_DB'] = 'true'
os.environ['OPTIMIZE_LOGGING'] = 'true'
os.environ['OPTIMIZE_ANALYTICS'] = 'true'

print("Iniciando aplicación con optimizaciones...")
from app import app

if __name__ == "__main__":
    app.run(debug=False, port=5000, threaded=True)
