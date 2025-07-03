# Integración con ESPN API

Este documento describe la integración del Sistema Integrado de Análisis Predictivo de Fútbol con la API no oficial de ESPN, basada en el repositorio [Public-ESPN-API](https://github.com/eamori91/Public-ESPN-API).

## Introducción

La integración con la API no oficial de ESPN permite obtener datos actualizados de ligas, equipos, jugadores, partidos y estadísticas de fútbol. Al no ser una API oficial, se ha implementado siguiendo las mejores prácticas y consideraciones para evitar problemas de disponibilidad o cambios inesperados.

## Implementación

La integración se ha realizado mediante:

1. **Adaptador dedicado**: Se ha creado un adaptador `ESPNAPI` en `utils/espn_api.py` que implementa la interfaz `BaseDataFetcher`.
2. **Integración en adaptador unificado**: Se ha integrado este adaptador en `UnifiedDataAdapter` para fusionar datos de múltiples fuentes.
3. **Variables de entorno**: Se ha añadido la configuración en `.env` para activar o desactivar esta fuente.

## Endpoints Utilizados

Los principales endpoints de ESPN utilizados son:

### Site API (site.api.espn.com)
- `/apis/site/v2/sports/soccer`: Lista de ligas/deportes
- `/apis/site/v2/sports/soccer/{league}/teams`: Equipos de una liga
- `/apis/site/v2/sports/soccer/teams/{team_id}/roster`: Jugadores de un equipo
- `/apis/site/v2/sports/soccer/{league}/scoreboard`: Partidos (resultados y próximos)
- `/apis/site/v2/sports/soccer/{league}/standings`: Clasificación de una liga

### Core API (sports.core.api.espn.com)
- Implementada la estructura pero no utilizada activamente en esta versión

## Funcionalidades Soportadas

El adaptador ESPN API proporciona las siguientes funcionalidades:

1. **Ligas**: Obtención de ligas disponibles con sus detalles
2. **Equipos**: Obtención de equipos por liga, con detalles como nombre, escudo, etc.
3. **Jugadores**: Obtención de plantillas completas de equipos
4. **Partidos**: Obtención de resultados y próximos partidos por liga
5. **Clasificación**: Obtención de tablas de clasificación por liga
6. **Estadísticas**: Estadísticas básicas de equipos

## Mapeo de Códigos de Liga

El adaptador implementa un mapeo entre los códigos de liga utilizados en el sistema y los utilizados en la API de ESPN:

| Código Sistema | Código ESPN API | Liga                    |
|----------------|----------------|-----------------------|
| PD             | esp.1          | LaLiga (España)        |
| PL             | eng.1          | Premier League (Inglaterra) |
| BL1            | ger.1          | Bundesliga (Alemania)   |
| SA             | ita.1          | Serie A (Italia)        |
| FL1            | fra.1          | Ligue 1 (Francia)       |
| PPL            | por.1          | Primeira Liga (Portugal) |
| DED            | ned.1          | Eredivisie (Países Bajos) |
| UCL            | UEFA.CHAMPIONS | UEFA Champions League   |
| UEL            | UEFA.EUROPA    | UEFA Europa League      |

## Consideraciones

Al utilizar una API no oficial, es importante tener en cuenta:

1. **Cambios sin previo aviso**: ESPN puede cambiar la estructura o disponibilidad de sus endpoints en cualquier momento
2. **Limitaciones de tasa**: No hay documentación oficial sobre límites de tasa, se recomienda no abusar
3. **Confiabilidad**: El sistema está preparado para manejar fallos mediante múltiples fuentes y cacheo inteligente
4. **Uso legítimo**: Esta integración está diseñada solo para uso educacional y no comercial

## Prueba de la Integración

Se ha desarrollado un script de prueba `scripts/test_espn_api.py` para verificar el funcionamiento de la integración. Para ejecutarlo:

```bash
python scripts/test_espn_api.py
```

Este script realiza pruebas de todas las funcionalidades y guarda los resultados en `data/test_espn_api/`.

## Ejemplo de Uso

```python
from utils.espn_api import ESPNAPI

# Inicializar API
api = ESPNAPI()

# Obtener equipos de LaLiga
equipos = api.fetch_teams(league="PD")

# Obtener jugadores de un equipo
jugadores = api.fetch_players(team_id="83")  # Barcelona

# Obtener próximos partidos de Premier League
partidos = api.fetch_matches(league="PL", 
                            date_from="2023-09-01", 
                            date_to="2023-09-30")
```

## Referencias

- [Repositorio Public-ESPN-API](https://github.com/eamori91/Public-ESPN-API)
- [Guía Completa de Endpoints de ESPN](https://github.com/eamori91/Public-ESPN-API/tree/main/README.md)
