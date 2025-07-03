# Integración con Datos Reales - Plan de Implementación

## 1. Fuentes de Datos Recomendadas

Para integrar este sistema con datos reales de fútbol, recomendamos las siguientes fuentes:

### 1.1. APIs de Fútbol
- **[API-Football](https://www.api-football.com/)**: Ofrece datos detallados de partidos, equipos, jugadores y estadísticas de más de 800 ligas.
- **[Football-Data.org](https://www.football-data.org/)**: API gratuita (con límites) que proporciona resultados, calendarios y clasificaciones.
- **[SportsDataIO](https://sportsdata.io/soccer-api)**: API con múltiples endpoints para datos detallados de fútbol.

### 1.2. Datasets Abiertos
- **[European Soccer Database](https://www.kaggle.com/datasets/hugomathien/soccer)**: Base de datos SQLite con información de +25,000 partidos.
- **[StatsBomb Open Data](https://github.com/statsbomb/open-data)**: Datos de eventos detallados de algunos partidos y competiciones.
- **[World Football](https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017)**: Resultados de partidos internacionales desde 1872.

## 2. Arquitectura de Integración

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Fuentes de Datos│     │    Adaptador    │     │   Sistema de    │
│    Externas     │────▶│  (data_fetcher) │────▶│  Almacenamiento │
└─────────────────┘     └─────────────────┘     └─────────┬───────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │◀────│  API REST Flask │◀────│    Modelos      │
│  (Interfaz Web) │     │   (endpoints)   │     │   Predictivos   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 3. Pasos para la Integración

### 3.1. Preparar el Sistema de Almacenamiento
1. **Base de Datos**: Implementar una base de datos SQL o NoSQL (recomendado PostgreSQL o MongoDB).
2. **Esquema de Datos**:
   - Tablas/Colecciones para: Equipos, Jugadores, Partidos, Estadísticas, Predicciones
3. **Sistema de Caché**:
   - Implementar Redis para almacenar en caché resultados de API y predicciones frecuentes

### 3.2. Implementar Adaptadores de Datos
1. **Crear clases adaptadoras** en `utils/data_fetcher.py` para cada fuente de datos:
   ```python
   class FootballDataOrgFetcher:
       def __init__(self, api_key):
           self.api_key = api_key
           self.base_url = "https://api.football-data.org/v4/"
           
       def fetch_teams(self, league_code):
           # Implementación
           
       def fetch_matches(self, date_from, date_to):
           # Implementación
   ```

2. **Implementar transformadores** para convertir datos externos al formato interno:
   ```python
   class DataTransformer:
       def transform_match(self, external_format):
           # Convertir formato externo al formato interno
           
       def transform_team(self, external_format):
           # Convertir formato externo al formato interno
   ```

### 3.3. Configuración del Sistema
1. Crear un archivo `config.py` con la configuración de las fuentes de datos:
   ```python
   DATA_SOURCES = {
       "football_data_org": {
           "api_key": "TU_API_KEY",
           "base_url": "https://api.football-data.org/v4/",
           "enabled": True
       },
       "api_football": {
           "api_key": "TU_API_KEY",
           "base_url": "https://v3.football.api-sports.io/",
           "enabled": False
       }
   }
   
   DATABASE = {
       "type": "postgresql",  # o "mongodb", "sqlite"
       "host": "localhost",
       "port": 5432,
       "user": "username",
       "password": "password",
       "database": "football_analytics"
   }
   ```

### 3.4. Implementar Tareas Programadas
1. Crear scripts para actualización automática en `scripts/`:
   - `update_teams.py`: Actualiza información de equipos
   - `update_players.py`: Actualiza información de jugadores
   - `update_matches.py`: Actualiza resultados de partidos
   - `train_models.py`: Reentrenar modelos con nuevos datos

2. Configurar Cron Jobs o Windows Task Scheduler:
   ```bash
   # Actualizar partidos diariamente
   0 3 * * * /usr/bin/python /ruta/a/update_matches.py
   
   # Actualizar equipos/jugadores semanalmente
   0 4 * * 1 /usr/bin/python /ruta/a/update_teams.py
   0 5 * * 1 /usr/bin/python /ruta/a/update_players.py
   
   # Reentrenar modelos mensualmente
   0 2 1 * * /usr/bin/python /ruta/a/train_models.py
   ```

### 3.5. Modificar la Interfaz para Usar Datos Reales
1. Actualizar endpoints de API para obtener datos desde la base de datos en lugar de simulaciones:
   ```python
   @app.route('/api/equipos', methods=['GET'])
   def api_equipos():
       try:
           # Conexión a base de datos
           conn = get_db_connection()
           cursor = conn.cursor()
           
           # Consulta SQL
           cursor.execute("SELECT id, nombre, liga, pais FROM equipos ORDER BY nombre")
           equipos = cursor.fetchall()
           
           # Convertir a formato JSON
           resultado = [
               {"id": eq[0], "nombre": eq[1], "liga": eq[2], "pais": eq[3]}
               for eq in equipos
           ]
           
           return jsonify(resultado)
       except Exception as e:
           return jsonify({"error": str(e)}), 500
   ```

2. Actualizar frontend para manejar datos reales:
   - Implementar paginación para grandes conjuntos de datos
   - Añadir filtros por liga, temporada, equipo, etc.
   - Implementar sistema de búsqueda avanzada

## 4. Plan de Implementación

### 4.1. Fase 1: Preparación (1-2 semanas)
- Configurar base de datos
- Implementar clases adaptadoras básicas
- Definir esquemas de datos

### 4.2. Fase 2: Obtención de Datos (2-3 semanas)
- Implementar scripts de actualización
- Obtener datos históricos
- Realizar transformaciones necesarias

### 4.3. Fase 3: Adaptación de Modelos (2 semanas)
- Adaptar modelos predictivos para usar datos reales
- Reentrenar modelos
- Evaluar rendimiento

### 4.4. Fase 4: Integración Frontend (1-2 semanas)
- Actualizar endpoints de API
- Modificar frontend para consumir datos reales
- Implementar mejoras de UX

### 4.5. Fase 5: Pruebas y Optimización (1 semana)
- Realizar pruebas exhaustivas
- Optimizar rendimiento
- Implementar monitoreo

## 5. Monitoreo y Mantenimiento

### 5.1. Monitoreo de Datos
- Implementar sistema de alertas para detectar anomalías en datos
- Verificar integridad de datos regularmente
- Monitorear uso de API (límites de peticiones)

### 5.2. Mantenimiento de Modelos
- Evaluar regularmente rendimiento de modelos
- Reentrenar con nuevos datos
- Actualizar características y algoritmos según sea necesario

### 5.3. Escalabilidad
- Preparar sistema para manejar más ligas/competiciones
- Implementar estrategias de caché para mejorar rendimiento
- Considerar migrar a infraestructura cloud para mayor escalabilidad

## 6. Evaluación del Éxito

### 6.1. Métricas de Éxito
- **Precisión de Predicciones**: Comparar con predicciones basadas en simulación
- **Velocidad de Carga**: Tiempos de respuesta menores a 500ms
- **Cobertura de Datos**: Número de ligas, equipos y partidos disponibles
- **Actualidad de Datos**: Tiempo entre evento real y actualización en el sistema

### 6.2. Plan de Contingencia
- Mantener sistema de simulación como respaldo
- Implementar múltiples fuentes de datos para redundancia
- Crear sistema de caché para funcionar offline en caso de fallo de API

## 7. Herramientas Recomendadas

### 7.1. Desarrollo
- **Gestión de Datos**: PostgreSQL, MongoDB, Redis
- **ORM/ODM**: SQLAlchemy (SQL), Mongoengine (MongoDB)
- **Cliente API**: Requests, aiohttp (para async)
- **Procesamiento**: Pandas, NumPy
- **Visualización**: Matplotlib, Seaborn, Plotly

### 7.2. Despliegue y Operaciones
- **Contenedorización**: Docker
- **Orquestación**: Docker Compose o Kubernetes (para sistemas más grandes)
- **CI/CD**: GitHub Actions, Jenkins
- **Monitoreo**: Prometheus, Grafana

## 8. Próximos Pasos Inmediatos

1. **Configurar entorno de desarrollo**:
   ```bash
   pip install sqlalchemy psycopg2-binary requests pandas redis
   ```

2. **Crear estructura inicial de base de datos**:
   ```python
   # models.py
   from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy.orm import relationship
   
   Base = declarative_base()
   
   class Equipo(Base):
       __tablename__ = 'equipos'
       
       id = Column(Integer, primary_key=True)
       nombre = Column(String)
       liga = Column(String)
       pais = Column(String)
       
       jugadores = relationship("Jugador", back_populates="equipo")
   
   class Jugador(Base):
       __tablename__ = 'jugadores'
       
       id = Column(Integer, primary_key=True)
       nombre = Column(String)
       equipo_id = Column(Integer, ForeignKey('equipos.id'))
       posicion = Column(String)
       
       equipo = relationship("Equipo", back_populates="jugadores")
   ```

3. **Crear primer adaptador para API externa**:
   ```python
   # data_fetcher.py
   import requests
   import pandas as pd
   
   class FootballDataAPI:
       def __init__(self, api_key):
           self.api_key = api_key
           self.headers = {'X-Auth-Token': api_key}
           self.base_url = 'https://api.football-data.org/v4/'
           
       def get_competitions(self):
           url = f"{self.base_url}competitions"
           response = requests.get(url, headers=self.headers)
           return response.json()
   ```

4. **Realizar prueba de concepto**:
   ```python
   # test_integration.py
   from data_fetcher import FootballDataAPI
   
   api = FootballDataAPI(api_key="TU_API_KEY")
   competitions = api.get_competitions()
   
   print(f"Ligas disponibles: {len(competitions['competitions'])}")
   for comp in competitions['competitions'][:5]:
       print(f"- {comp['name']} ({comp['code']})")
   ```

5. **Implementar primer script de actualización automática**:
   ```python
   # update_competitions.py
   from data_fetcher import FootballDataAPI
   from models import Competicion
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   
   # Configurar base de datos
   engine = create_engine('postgresql://usuario:password@localhost/football')
   Session = sessionmaker(bind=engine)
   session = Session()
   
   # Actualizar competiciones
   api = FootballDataAPI(api_key="TU_API_KEY")
   competitions = api.get_competitions()
   
   for comp in competitions['competitions']:
       competicion = session.query(Competicion).filter_by(code=comp['code']).first()
       if competicion:
           # Actualizar competición existente
           competicion.nombre = comp['name']
       else:
           # Crear nueva competición
           nueva_competicion = Competicion(
               code=comp['code'],
               nombre=comp['name'],
               pais=comp.get('area', {}).get('name', 'Desconocido')
           )
           session.add(nueva_competicion)
   
   # Guardar cambios
   session.commit()
   print("Competiciones actualizadas correctamente")
   ```

6. **Configurar sistema de monitoreo básico**:
   ```python
   # monitor.py
   import logging
   import time
   import requests
   
   logging.basicConfig(filename='api_monitor.log', level=logging.INFO,
                      format='%(asctime)s - %(levelname)s - %(message)s')
   
   def check_api_status(url, headers=None):
       try:
           start_time = time.time()
           response = requests.get(url, headers=headers)
           elapsed = time.time() - start_time
           
           if response.status_code == 200:
               logging.info(f"API OK - Status: {response.status_code} - Time: {elapsed:.2f}s")
               return True
           else:
               logging.error(f"API Error - Status: {response.status_code}")
               return False
       except Exception as e:
           logging.error(f"API Connection Error: {str(e)}")
           return False
   
   if __name__ == "__main__":
       api_key = "TU_API_KEY"
       url = "https://api.football-data.org/v4/competitions"
       headers = {'X-Auth-Token': api_key}
       
       check_api_status(url, headers)
   ```
