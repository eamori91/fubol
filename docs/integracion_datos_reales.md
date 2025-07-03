# Guía de Integración con Datos Reales

Este documento describe el proceso para conectar el sistema de análisis predictivo de fútbol con fuentes de datos reales.

## 1. Introducción

El sistema está diseñado para ser flexible y permitir la integración con diferentes fuentes de datos. Esta guía explica cómo configurar y mantener estas conexiones.

> ⭐ **¡Nuevo!** Se ha implementado un **Adaptador Unificado** para combinar datos de múltiples fuentes gratuitas. Ver sección 4.

## 2. Arquitectura de Integración

### 2.1 Componentes Principales

```
                                 ┌────────────────┐
                                 │   Fuentes de   │
                                 │  Datos Reales  │
                                 └───────┬────────┘
                                         │
                                         │ API/CSV/JSON
                                         ▼
┌───────────────┐          ┌──────────────────────────┐          ┌──────────────┐
│   Adaptador   │◄────────►│  Sistema de Integración  │◄────────►│ Almacén de   │
│   de Datos    │          │      (data_fetcher)      │          │    Datos     │
└───────────────┘          └──────────────────────────┘          └──────────────┘
                                         │
                                         │
                           ┌─────────────┴────────────┐
                           │                          │
                           ▼                          ▼
                  ┌─────────────────┐        ┌────────────────┐
                  │ Motor Predictivo│        │ Visualización  │
                  │     (Flask)     │        │   (Frontend)   │
                  └─────────────────┘        └────────────────┘
```

### 2.2 Flujo de Datos

1. El sistema se conecta a fuentes externas mediante API o archivos
2. Los datos son normalizados por el adaptador
3. Los datos normalizados se almacenan localmente
4. El motor predictivo consume estos datos
5. Los resultados se muestran en la interfaz de usuario

## 3. Fuentes de Datos Recomendadas

### 3.1 APIs Públicas

- **Football-Data.org**: Ofrece datos de las principales ligas europeas
  - Documentación: [https://www.football-data.org/documentation/api](https://www.football-data.org/documentation/api)
  - Endpoints útiles: equipos, partidos, clasificaciones

- **API-Football**: Datos detallados de partidos, estadísticas y predicciones
  - Documentación: [https://www.api-football.com/documentation](https://www.api-football.com/documentation)
  - Requiere clave API (plan gratuito disponible con limitaciones)

### 3.2 Datasets Abiertos

- **European Soccer Database**: Base de datos SQLite con +25,000 partidos
  - Disponible en: [Kaggle - European Soccer Database](https://www.kaggle.com/hugomathien/soccer)

- **StatsBomb Open Data**: Datos de eventos detallados de partidos
  - Repositorio: [GitHub - StatsBomb/open-data](https://github.com/statsbomb/open-data)

### 3.3 Feeds de Datos Comerciales

- Opta Sports
- StatsBomb
- Wyscout
- InStat

## 4. Adaptador Unificado de Fuentes Gratuitas

Se ha implementado un adaptador que unifica datos de múltiples fuentes gratuitas para ofrecer información completa sin necesidad de suscripciones de pago.

### 4.1 Fuentes Soportadas

| Fuente | Tipo | Límites | Información Disponible |
|--------|------|---------|------------------------|
| **Football-Data.org** | API REST | 10 llamadas/min (plan gratuito) | Próximos partidos, equipos, jugadores |
| **Open Football Data** | Repositorio JSON | Sin límite | Datos históricos de ligas y resultados |
| **ESPN FC** | Web Scraping | Limitado por política de uso | Equipos, jugadores, calendario |
| **World Football Data** | Archivos CSV | Sin límite | Datos históricos extensivos |

### 4.2 Configuración

El adaptador se configura mediante variables de entorno en el archivo `.env`:

```properties
# Football-Data.org (GRATUITO con límite)
FOOTBALL_DATA_API_KEY=tu_clave_aquí
FOOTBALL_DATA_API_ENABLED=true

# Open Football Data (GRATUITO - sin key)
USE_OPEN_FOOTBALL_DATA=true
OPEN_FOOTBALL_DATA_URL=https://github.com/openfootball/football.json

# ESPN FC Data (GRATUITO - scraping web)
USE_ESPN_DATA=true
ESPN_BASE_URL=https://www.espn.com/soccer

# World Football Data (GRATUITO - archivos CSV)
USE_WORLD_FOOTBALL=true
WORLD_FOOTBALL_URL=https://www.football-data.co.uk/data.php

# Activación del sistema unificado
USE_UNIFIED_DATA=true
```

### 4.3 Utilización del Adaptador Unificado

#### Desde Python

```python
from utils.unified_data_adapter import UnifiedDataAdapter

# Inicializar el adaptador
adapter = UnifiedDataAdapter()

# Obtener próximos partidos
partidos = adapter.obtener_proximos_partidos(dias=7, liga="LaLiga")

# Obtener datos de un equipo
equipo = adapter.obtener_datos_equipo("Barcelona")

# Obtener historial de un árbitro
historial = adapter.obtener_historial_arbitro("Gil Manzano", equipo="Real Madrid")
```

#### Desde la API REST

```
GET /api/datos-unificados/proximos-partidos?dias=7&liga=LaLiga
GET /api/datos-unificados/equipo/Barcelona
GET /api/datos-unificados/arbitro/Gil%20Manzano?equipo=Real%20Madrid
```

### 4.4 Características del Adaptador

- **Caché Automática**: Los datos se almacenan temporalmente para reducir llamadas repetidas
- **Deduplicación**: Elimina datos duplicados de diferentes fuentes
- **Fallback Automático**: Si una fuente falla, intenta con otra
- **Normalización**: Todos los datos se convierten a un formato estándar
- **Complemento de Datos**: Cuando los datos no están disponibles en ninguna fuente, genera simulaciones realistas

### 4.5 Ventajas de este Enfoque

- **Costo Cero**: Utiliza exclusivamente fuentes gratuitas
- **Robustez**: No depende de una única fuente de datos
- **Completitud**: Combina lo mejor de cada fuente para ofrecer datos más completos
- **Adaptabilidad**: Fácil de extender para soportar nuevas fuentes

### 4.6 Demostración

Para probar el adaptador unificado, ejecute:

```bash
python scripts/demo_unified_adapter.py
```

Este script muestra cómo obtener próximos partidos, información de equipos y estadísticas de árbitros.

## 5. Requisitos de Integración

### 5.1 Formato de Datos

El sistema requiere los siguientes datos mínimos:

#### Equipos
```json
{
  "id": "string",
  "nombre": "string",
  "liga": "string",
  "pais": "string",
  "estadio": "string",
  "fundacion": "number",
  "entrenador": "string"
}
```

#### Jugadores
```json
{
  "id": "string",
  "nombre": "string",
  "equipo_id": "string",
  "posicion": "string",
  "edad": "number",
  "nacionalidad": "string",
  "estadisticas": {
    "goles": "number",
    "asistencias": "number",
    "partidos_jugados": "number"
  }
}
```

#### Partidos
```json
{
  "id": "string",
  "fecha": "string (ISO-8601)",
  "equipo_local_id": "string",
  "equipo_visitante_id": "string",
  "goles_local": "number",
  "goles_visitante": "number",
  "temporada": "string",
  "liga": "string",
  "estadisticas": {
    "posesion_local": "number",
    "posesion_visitante": "number",
    "tiros_local": "number",
    "tiros_visitante": "number",
    "corners_local": "number",
    "corners_visitante": "number"
  }
}
```

### 5.2 Frecuencia de Actualización

- Datos históricos: Carga inicial y actualizaciones semanales
- Datos de partidos próximos: Actualización diaria
- Resultados recientes: Actualización diaria o en tiempo real
- Estadísticas de jugadores: Actualización semanal

## 6. Implementación Técnica

### 6.1 Configuración de conexiones

Editar el archivo `config.py` para añadir credenciales de API:

```python
# Configuración de fuentes de datos
DATA_SOURCES = {
    "football_data_org": {
        "api_key": "TU_API_KEY_AQUÍ",
        "base_url": "https://api.football-data.org/v2/",
        "enabled": True
    },
    "api_football": {
        "api_key": "TU_API_KEY_AQUÍ",
        "base_url": "https://v3.football.api-sports.io/",
        "enabled": False
    }
}
```

### 6.2 Actualizar los adaptadores de datos

Los adaptadores de datos se encuentran en `utils/data_fetcher.py`. Para implementar un nuevo adaptador:

1. Crear una clase que herede de `BaseDataFetcher`
2. Implementar los métodos requeridos:
   - `fetch_teams()`
   - `fetch_players()`
   - `fetch_matches()`
3. Registrar el nuevo adaptador en `config.py`

### 6.3 Programar actualizaciones automáticas

Utilizar un programador de tareas (cron en Linux, Task Scheduler en Windows) para ejecutar:

```bash
python update_data.py --source=api_football --data=matches
```

## 7. Endpoints de Integración

El sistema proporciona endpoints específicos para gestionar la integración:

- `GET /api/integracion/configuracion`: Muestra la configuración actual
- `POST /api/integracion/test-conexion`: Prueba una conexión con fuente externa
- `POST /api/integracion/importar-datos`: Importa datos desde una fuente
- `GET /api/integracion/estado`: Muestra el estado de las integraciones

## 8. Consideraciones Prácticas

### 8.1 Manejo de Errores

- Implementar reintentos para fallos de conexión
- Validar datos antes de importar
- Mantener un registro de errores en `logs/integration_errors.log`

### 8.2 Almacenamiento

Los datos se almacenan en:

- `data/equipos/`: Información de equipos (JSON)
- `data/jugadores/`: Información de jugadores (JSON)
- `cache/partidos_historicos.csv`: Datos históricos de partidos
- `cache/partidos_generados.csv`: Datos simulados (cuando no hay datos reales)

### 8.3 Respaldo

- Programar respaldos automáticos antes de cada actualización
- Los respaldos se guardan en `data/backups/` con marca de tiempo

## 9. Pruebas y Monitoreo

### 9.1 Validación

Ejecutar el script de validación para asegurar la integridad de los datos:

```bash
python validar_datos.py
```

### 9.2 Monitoreo

- El estado de las integraciones se muestra en `/admin/integraciones`
- Los logs se encuentran en `logs/integration.log`

## 10. Contacto y Soporte

Para más información sobre la integración con datos reales, contactar a:

- Equipo de Desarrollo: soporte@analytic-futbol.com
- Documentación API: [docs/api_docs.md](api_docs.md)
