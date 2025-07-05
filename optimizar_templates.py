"""
Actualizador de plantillas Flask para integrar las optimizaciones.
Este módulo modifica las plantillas para aprovechar las optimizaciones.
"""

import os
import re
from pathlib import Path
import logging
import shutil
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('templates_updater')

def backup_template(template_path):
    """
    Crea una copia de seguridad de la plantilla antes de modificarla
    
    Args:
        template_path: Ruta de la plantilla a respaldar
    
    Returns:
        Ruta del archivo de respaldo
    """
    backup_dir = Path("backups/templates")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    template_path = Path(template_path)
    backup_path = backup_dir / f"{template_path.name}.{timestamp}.bak"
    
    shutil.copy2(template_path, backup_path)
    logger.info(f"Plantilla respaldada: {backup_path}")
    
    return backup_path

def update_base_template():
    """Actualiza la plantilla base con optimizaciones"""
    template_path = Path("templates/base.html")
    backup_template(template_path)
    
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Añadir preload y preconnect para optimizar la carga
    head_tag = r'</head>'
    optimized_head = (
        '    <!-- Optimizaciones de rendimiento -->\n'
        '    <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '    <link rel="preload" href="{{ url_for(\'static\', filename=\'css/styles.css\') }}" as="style">\n'
        '    <link rel="preload" href="{{ url_for(\'static\', filename=\'js/main.js\') }}" as="script">\n'
        '</head>'
    )
    content = content.replace(head_tag, optimized_head)
    
    # Añadir Service Worker para soporte offline y carga optimizada
    body_end = r'</body>'
    sw_script = (
        '    <!-- Service Worker para optimización y soporte offline -->\n'
        '    <script>\n'
        '        if ("serviceWorker" in navigator) {\n'
        '            window.addEventListener("load", function() {\n'
        '                navigator.serviceWorker.register("{{ url_for(\'static\', filename=\'sw.js\') }}")\n'
        '                    .then(reg => console.log("Service Worker registrado"))\n'
        '                    .catch(err => console.error("Error al registrar Service Worker:", err));\n'
        '            });\n'
        '        }\n'
        '    </script>\n'
        '</body>'
    )
    content = content.replace(body_end, sw_script)
    
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Plantilla base actualizada con optimizaciones: {template_path}")

def update_dashboard_template():
    """Actualiza la plantilla de dashboard con lazy loading y otras optimizaciones"""
    template_path = Path("templates/dashboard_mejorado.html")
    
    if not template_path.exists():
        logger.warning(f"Plantilla no encontrada: {template_path}")
        return
        
    backup_template(template_path)
    
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Añadir lazy loading a las imágenes
    img_pattern = r'<img src='
    lazy_img = r'<img loading="lazy" src='
    content = content.replace(img_pattern, lazy_img)
    
    # Añadir atributos de tamaño a gráficos para evitar layout shifts
    chart_pattern = r'<canvas id="([^"]+)"([^>]*)></canvas>'
    sized_chart = r'<canvas id="\1"\2 width="100%" height="300"></canvas>'
    content = re.sub(chart_pattern, sized_chart, content)
    
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Plantilla de dashboard actualizada: {template_path}")

def update_all_templates():
    """Actualiza todas las plantillas relevantes"""
    templates_dir = Path("templates")
    
    # Actualizar plantilla base primero
    update_base_template()
    
    # Actualizar plantillas específicas
    update_dashboard_template()
    
    # Recorrer todas las plantillas para optimizaciones básicas
    for template_path in templates_dir.glob("*.html"):
        # Excluir las que ya se han actualizado
        if template_path.name in ["base.html", "dashboard_mejorado.html"]:
            continue
            
        logger.info(f"Actualizando plantilla: {template_path.name}")
        backup_template(template_path)
        
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Añadir lazy loading a imágenes
        content = content.replace('<img src=', '<img loading="lazy" src=')
        
        # Añadir atributos de rendimiento a scripts
        content = content.replace('<script src=', '<script defer src=')
        
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Plantilla actualizada: {template_path}")

def create_service_worker():
    """Crea un Service Worker para optimización y soporte offline"""
    sw_dir = Path("static")
    sw_path = sw_dir / "sw.js"
    
    sw_content = """/**
 * Service Worker para optimización y soporte offline
 * Caché de recursos estáticos y estrategia offline-first
 */

const CACHE_NAME = 'fubol-cache-v1';
const ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/js/main.js',
    '/static/images/logo.png',
    '/index',
    '/historico',
    '/proximo',
    '/futuro'
];

// Instalación del Service Worker y caché de recursos
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caché abierta');
                return cache.addAll(ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Limpieza de cachés antiguas
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

// Estrategia de caché: Network first, fallback to cache
self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clonar la respuesta para almacenarla en caché
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(cache => {
                        // Solo cachear GET requests
                        if (event.request.method === 'GET') {
                            cache.put(event.request, responseClone);
                        }
                    });
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
"""
    
    # Crear directorio si no existe
    sw_dir.mkdir(exist_ok=True)
    
    with open(sw_path, "w", encoding="utf-8") as f:
        f.write(sw_content)
    
    logger.info(f"Service Worker creado: {sw_path}")

def create_manifest():
    """Crea un Web App Manifest para PWA"""
    manifest_path = Path("static/manifest.json")
    
    manifest_content = {
        "name": "Sistema de Análisis de Fútbol",
        "short_name": "Fubol",
        "description": "Sistema avanzado de análisis de fútbol",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#4285f4",
        "icons": [
            {
                "src": "/static/images/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    # Crear directorio si no existe
    manifest_path.parent.mkdir(exist_ok=True)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        import json
        json.dump(manifest_content, f, indent=4)
    
    logger.info(f"Manifest creado: {manifest_path}")

def main():
    """Función principal para actualizar todas las plantillas"""
    logger.info("Iniciando actualización de plantillas")
    
    # Actualizar plantillas
    update_all_templates()
    
    # Crear Service Worker
    create_service_worker()
    
    # Crear Web App Manifest
    create_manifest()
    
    logger.info("Actualización de plantillas completada")

if __name__ == "__main__":
    main()
