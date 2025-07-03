"""
Script de depuración para la aplicación Flask.

Este script inicia la aplicación en modo debug con configuraciones
específicas para facilitar la depuración de errores.
"""

import os
import sys
import logging
from werkzeug.serving import run_simple

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('logs', 'debug.log'))
    ]
)

# Asegurarse de que exista el directorio de logs
os.makedirs('logs', exist_ok=True)

# Importar la aplicación después de configurar el logging
try:
    from app import app
    print("✅ Aplicación importada correctamente")
except Exception as e:
    print(f"❌ Error al importar la aplicación: {e}")
    sys.exit(1)

def main():
    """Función principal para ejecutar la aplicación en modo depuración"""
    try:
        # Verificar si hay errores comunes
        check_common_issues()
        
        # Configurar la aplicación para depuración
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
        
        # Añadir funciones a Jinja
        setup_jinja_env()
        
        host = '127.0.0.1'
        port = 5000
        
        print(f"\n📊 Iniciando servidor de depuración en http://{host}:{port}")
        print("🔍 Modo de depuración: ACTIVADO")
        print("🔄 Recarga automática: ACTIVADA")
        print("⚠️ Presiona CTRL+C para detener\n")
        
        # Ejecutar la aplicación
        run_simple(
            hostname=host,
            port=port,
            application=app,
            use_reloader=True,
            use_debugger=True,
            use_evalex=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        logging.error(f"Error al iniciar el servidor: {e}", exc_info=True)

def check_common_issues():
    """Verifica problemas comunes que podrían causar errores"""
    # Verificar que existen las plantillas
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        print(f"❌ El directorio de plantillas no existe: {templates_dir}")
    else:
        print(f"✅ Directorio de plantillas encontrado: {templates_dir}")
        
        # Verificar archivos de plantilla específicos
        for template in ['base.html', 'index.html', 'explorar_db.html']:
            template_path = os.path.join(templates_dir, template)
            if not os.path.exists(template_path):
                print(f"⚠️ Plantilla no encontrada: {template}")
            else:
                print(f"✅ Plantilla encontrada: {template}")
    
    # Verificar directorio de base de datos
    db_dir = os.path.join(os.path.dirname(__file__), 'data', 'database')
    if not os.path.exists(db_dir):
        print(f"⚠️ El directorio de base de datos no existe: {db_dir}")
        print("   Se creará automáticamente al acceder a la base de datos.")
    
    # Verificar archivo .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        print(f"⚠️ Archivo .env no encontrado: {env_path}")

def setup_jinja_env():
    """Configura el entorno Jinja2 para añadir funciones útiles"""
    # Añadir funciones globales a Jinja
    app.jinja_env.globals.update(max=max)
    app.jinja_env.globals.update(min=min)
    app.jinja_env.globals.update(len=len)
    app.jinja_env.globals.update(enumerate=enumerate)
    app.jinja_env.globals.update(zip=zip)
    app.jinja_env.globals.update(list=list)
    app.jinja_env.globals.update(dict=dict)
    app.jinja_env.globals.update(str=str)
    app.jinja_env.globals.update(int=int)
    app.jinja_env.globals.update(float=float)
    
    print("✅ Funciones globales añadidas al entorno Jinja")

if __name__ == "__main__":
    main()
