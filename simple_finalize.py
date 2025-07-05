import
os
sys
logging
importlib
json
from
pathlib
import
Path
print('Creando directorio de configuración...')
Path('config').mkdir(exist_ok=True)
print('Creando directorio de caché...')
Path('data/cache').mkdir(parents=True, exist_ok=True)
print('Creando directorio de logs...')
Path('logs').mkdir(exist_ok=True)
print('Optimizaciones finalizadas correctamente')
print('Para iniciar la aplicación ejecute: python app.py')
