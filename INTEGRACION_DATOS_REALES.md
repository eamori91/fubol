# Integración con Datos Reales

Este directorio contiene la implementación de la integración con datos reales de fútbol, siguiendo el plan detallado en `docs/plan_integracion_datos_reales.md`.

## Estructura de Integración

La integración se ha implementado siguiendo esta arquitectura:

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

## Componentes Principales

### Adaptadores de Datos
- `utils/football_data_api.py`: Adaptador para Football-Data.org
- `utils/api_football.py`: Adaptador para API-Football

### Base de Datos
- Basada en SQLAlchemy con soporte para SQLite, PostgreSQL y MySQL
- Esquema definido en `scripts/setup_database.py`
- Configuración en `config/database.json`

### Proveedores de Datos
- `utils/data_provider.py`: Interfaz para acceder a datos reales desde la base de datos
- `utils/data_loader.py`: Integración con el sistema existente para consumir datos reales

### Scripts de Actualización
- `scripts/update_database.py`: Actualiza la base de datos con información de APIs externas
- `scripts/test_data_integration.py`: Prueba la integración entre componentes
- `scripts/run_integration.py`: Script principal para ejecutar toda la integración

## Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura las siguientes variables:

```bash
# API Keys
FOOTBALL_DATA_API_KEY=tu_clave_api_football_data_aqui
API_FOOTBALL_KEY=tu_clave_api_football_aqui
API_FOOTBALL_HOST=v3.football.api-sports.io
```

### Base de Datos

La configuración de la base de datos se encuentra en `config/database.json`. 
Por defecto, utiliza SQLite, pero puedes configurar PostgreSQL o MySQL.

## Uso

### Configuración Inicial

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   - En Linux/macOS: `source load_env.sh`
   - En Windows: `.\load_env.ps1`

3. **Configurar la base de datos**:
   ```bash
   python scripts/setup_database.py
   ```

### Ejecutar Integración

Para ejecutar todo el proceso de integración:

```bash
python scripts/run_integration.py
```

Este comando realiza:
1. Configuración de la base de datos
2. Actualización de datos desde APIs externas
3. Pruebas de integración
4. Demostración de funcionalidades

### Ejecución Individual de Componentes

- **Actualizar base de datos**:
  ```bash
  python scripts/update_database.py --source football-data --data teams
  ```

- **Probar integración con datos reales**:
  ```bash
  python scripts/test_data_integration.py
  ```

- **Ejecutar demostración**:
  ```bash
  python scripts/demo_integracion.py
  ```

- **Ejecutar aplicación web**:
  ```bash
  python app.py
  ```

## APIs Soportadas

### Football-Data.org
- **Uso gratuito**: 10 peticiones/minuto
- **Documentación**: [https://www.football-data.org/documentation/api](https://www.football-data.org/documentation/api)
- **Endpoints implementados**: Competiciones, Equipos, Jugadores, Partidos, Clasificaciones

### API-Football
- **Plan gratuito**: 100 peticiones/día
- **Documentación**: [https://www.api-football.com/documentation](https://www.api-football.com/documentation)
- **Endpoints implementados**: Ligas, Equipos, Jugadores, Partidos, Clasificaciones

## Modelo de Datos

Se ha implementado un esquema de base de datos con las siguientes entidades:

- **Ligas**: Competiciones deportivas
- **Equipos**: Clubes que participan en las ligas
- **Jugadores**: Deportistas vinculados a equipos
- **Partidos**: Encuentros entre equipos con resultados y estadísticas
- **Eventos de Partidos**: Goles, tarjetas y otros eventos
- **Estadísticas de Jugadores**: Rendimiento individual por temporada
- **Predicciones**: Resultados de modelos predictivos

## Próximos Pasos

- Mejorar la integración con frontend para visualizar datos reales
- Implementar actualización automática programada
- Implementar caché con Redis para mejorar rendimiento
- Ampliar cobertura de pruebas automatizadas
- Integrar con nuevas fuentes de datos
