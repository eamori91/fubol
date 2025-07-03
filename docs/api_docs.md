# Documentación de la API del Analizador Deportivo de Fútbol

Esta documentación describe los endpoints disponibles en la API pública del Analizador Deportivo de Fútbol.

## Base URL

```
/api
```

## Endpoints para integración con datos reales

### Configuración de integración

```
GET /integracion/configuracion
```

Devuelve información sobre cómo configurar la integración con fuentes de datos externas.

**Ejemplo de respuesta:**
```json
{
  "version_api": "1.0.0",
  "formatos_soportados": ["json", "csv"],
  "endpoints_principales": {
    "equipos": "/api/equipos",
    "jugadores": "/api/jugadores",
    "predicciones": "/api/predicciones/{equipo_local}/{equipo_visitante}"
  },
  "frecuencia_actualizacion": "diaria",
  "fuentes_datos_recomendadas": [
    {"nombre": "API-Football", "url": "https://www.api-football.com/"},
    {"nombre": "Football-Data.org", "url": "https://www.football-data.org/"}
  ],
  "estructura_datos_requerida": {
    "equipo": ["id", "nombre", "liga", "pais"],
    "jugador": ["id", "nombre", "equipo_id", "posicion", "estadisticas"],
    "partido": ["id", "fecha", "equipo_local_id", "equipo_visitante_id", "resultado_local", "resultado_visitante"]
  }
}
```

### Probar conexión con fuente externa

```
POST /integracion/test-conexion
```

Permite probar la conexión con una fuente de datos externa.

**Cuerpo de la petición:**
```json
{
  "tipo": "api",
  "url": "https://api.football-data.org/v2/",
  "api_key": "YOUR_API_KEY",
  "formato": "json"
}
```

**Ejemplo de respuesta:**
```json
{
  "estado": "exitoso",
  "mensaje": "Conexión establecida correctamente",
  "detalles": {
    "latencia": "120ms",
    "formato_correcto": true,
    "campos_validados": true,
    "timestamp": "2023-07-01T14:35:12Z"
  }
}
```

### Importar datos externos

```
POST /integracion/importar-datos
```

Importa datos desde una fuente externa.

**Cuerpo de la petición:**
```json
{
  "tipo": "equipos",
  "fuente": "api-football",
  "datos": [
    {
      "id": "EQ0001",
      "nombre": "FC Barcelona",
      "liga": "La Liga",
      "pais": "España"
    }
  ]
}
```

**Ejemplo de respuesta:**
```json
{
  "estado": "exitoso",
  "mensaje": "Datos importados correctamente",
  "estadisticas": {
    "total_procesados": 1,
    "nuevos_registros": 1,
    "actualizados": 0
  }
}
```

## Endpoints regulares

### Predicciones

#### Predecir resultado de partido

```
GET /prediccion?local={equipo_local}&visitante={equipo_visitante}&fecha={YYYY-MM-DD}
```

Devuelve la predicción para un partido específico.

**Parámetros:**
- `local`: Nombre del equipo local
- `visitante`: Nombre del equipo visitante
- `fecha`: (Opcional) Fecha del partido en formato YYYY-MM-DD

**Ejemplo de respuesta:**
```json
{
  "prediccion": {
    "probabilidades": {
      "victoria_local": 0.65,
      "empate": 0.20,
      "victoria_visitante": 0.15
    },
    "resultado_probable": "2-1",
    "goles_esperados": {
      "local": 2.3,
      "visitante": 0.9
    }
  },
  "equipos": {
    "local": "Barcelona",
    "visitante": "Real Madrid"
  },
  "fecha": "2025-07-15",
  "factores_clave": [
    "Buen rendimiento local reciente",
    "Lesión de jugador clave visitante",
    "Victoria en último enfrentamiento directo"
  ]
}
```

#### Predecir con características personalizadas

```
POST /prediccion/personalizada
```

Permite realizar predicciones con características personalizadas.

**Cuerpo de la solicitud (JSON):**
```json
{
  "features": {
    "media_goles_local": 2.3,
    "media_goles_visitante": 1.1,
    "forma_local": 0.8,
    "forma_visitante": 0.6,
    "momentum_local": 0.75,
    "momentum_visitante": 0.65,
    "posesion_media_local": 58.2,
    "posesion_media_visitante": 52.6
  }
}
```

**Ejemplo de respuesta:**
```json
{
  "prediccion": {
    "goles_local": 2.4,
    "goles_visitante": 0.9,
    "probabilidad_empate": 0.22,
    "probabilidad_local": 0.68,
    "probabilidad_visitante": 0.1
  }
}
```

#### Predecir con Deep Learning

```
GET /prediccion/deep?local={equipo_local}&visitante={equipo_visitante}&fecha={YYYY-MM-DD}
```

Realiza predicciones utilizando modelos de deep learning.

**Parámetros:**
- `local`: Nombre del equipo local
- `visitante`: Nombre del equipo visitante
- `fecha`: (Opcional) Fecha del partido en formato YYYY-MM-DD

**Ejemplo de respuesta:**
```json
{
  "prediccion": {
    "probabilidades": {
      "victoria_local": 0.68,
      "empate": 0.22,
      "victoria_visitante": 0.10
    },
    "resultado_probable": "2-0",
    "goles_esperados": {
      "local": 2.1,
      "visitante": 0.7
    }
  },
  "modelo": "deep_learning",
  "tipo_modelo": "LSTM",
  "confianza": 0.89
}
```

### Simulaciones

#### Simular partido (Monte Carlo)

```
GET /simulacion/monte-carlo?local={equipo_local}&visitante={equipo_visitante}&n={numero_simulaciones}
```

Ejecuta simulaciones Monte Carlo para un partido.

**Parámetros:**
- `local`: Nombre del equipo local
- `visitante`: Nombre del equipo visitante
- `n`: (Opcional) Número de simulaciones (predeterminado: 1000)

**Ejemplo de respuesta:**
```json
{
  "equipos": {
    "local": "Barcelona",
    "visitante": "Real Madrid"
  },
  "resultado_mas_probable": "2-1",
  "probabilidades": {
    "victoria_local": 0.62,
    "empate": 0.23,
    "victoria_visitante": 0.15
  },
  "distribucion_goles": {
    "local": {
      "0": 0.12,
      "1": 0.28,
      "2": 0.35,
      "3": 0.18,
      "4": 0.05,
      "5+": 0.02
    },
    "visitante": {
      "0": 0.31,
      "1": 0.42,
      "2": 0.19,
      "3": 0.06,
      "4": 0.02,
      "5+": 0.00
    }
  },
  "resultados_mas_comunes": [
    {"resultado": "2-1", "probabilidad": 0.22},
    {"resultado": "1-1", "probabilidad": 0.18},
    {"resultado": "2-0", "probabilidad": 0.15},
    {"resultado": "1-0", "probabilidad": 0.12},
    {"resultado": "3-1", "probabilidad": 0.08}
  ],
  "n_simulaciones": 1000
}
```

#### Simular partido (Eventos)

```
GET /simulacion/eventos?local={equipo_local}&visitante={equipo_visitante}&detalle={nivel_detalle}
```

Ejecuta una simulación detallada de eventos minuto a minuto.

**Parámetros:**
- `local`: Nombre del equipo local
- `visitante`: Nombre del equipo visitante
- `detalle`: (Opcional) Nivel de detalle (1-3, default: 1)

**Ejemplo de respuesta:**
```json
{
  "equipos": {
    "local": "Barcelona",
    "visitante": "Real Madrid"
  },
  "resultado": {
    "local": 2,
    "visitante": 1
  },
  "eventos": [
    {
      "minuto": 23,
      "tipo": "gol",
      "equipo": "local",
      "jugador": "Lewandowski",
      "descripcion": "Gol de Barcelona. Lewandowski marca tras un centro desde la banda derecha."
    },
    {
      "minuto": 39,
      "tipo": "tarjeta_amarilla",
      "equipo": "visitante",
      "jugador": "Carvajal",
      "descripcion": "Tarjeta amarilla para Carvajal por una entrada dura."
    },
    {
      "minuto": 56,
      "tipo": "gol",
      "equipo": "visitante",
      "jugador": "Vinicius",
      "descripcion": "Gol de Real Madrid. Vinicius empata con un disparo desde fuera del área."
    },
    {
      "minuto": 78,
      "tipo": "gol",
      "equipo": "local",
      "jugador": "Pedri",
      "descripcion": "Gol de Barcelona. Pedri marca el gol de la victoria."
    },
    {
      "minuto": 90,
      "tipo": "final_partido",
      "descripcion": "Final del partido. Barcelona 2-1 Real Madrid"
    }
  ],
  "estadisticas": {
    "posesion": {
      "local": 58,
      "visitante": 42
    },
    "tiros": {
      "local": 14,
      "visitante": 8
    },
    "tiros_puerta": {
      "local": 6,
      "visitante": 3
    },
    "corners": {
      "local": 7,
      "visitante": 3
    }
  },
  "tarjetas": {
    "local": {
      "amarilla": 2,
      "roja": 0
    },
    "visitante": {
      "amarilla": 3,
      "roja": 0
    }
  }
}
```

### Equipos y Jugadores

#### Obtener información de equipos

```
GET /equipos?nombre={nombre_equipo}
```

Obtiene información detallada de un equipo.

**Parámetros:**
- `nombre`: (Opcional) Nombre del equipo a consultar. Si no se proporciona, devuelve la lista de equipos disponibles.

**Ejemplo de respuesta (lista de equipos):**
```json
{
  "equipos": [
    {
      "id": "BAR",
      "nombre": "Barcelona",
      "liga": "La Liga"
    },
    {
      "id": "RMA",
      "nombre": "Real Madrid",
      "liga": "La Liga"
    }
  ]
}
```

**Ejemplo de respuesta (equipo específico):**
```json
{
  "equipo": {
    "id": "BAR",
    "nombre": "Barcelona",
    "liga": "La Liga",
    "estadio": "Camp Nou",
    "fundacion": 1899,
    "entrenador": "Xavi Hernández",
    "fuerza": {
      "ataque": 88,
      "medio_campo": 85,
      "defensa": 82,
      "global": 85
    },
    "estadisticas": {
      "partidos_jugados": 38,
      "victorias": 24,
      "empates": 8,
      "derrotas": 6,
      "goles_favor": 68,
      "goles_contra": 27,
      "puntos": 80
    },
    "forma": ["V", "V", "E", "V", "D"]
  },
  "jugadores": [
    {
      "id": "LEW01",
      "nombre": "Robert Lewandowski",
      "posicion": "Delantero",
      "rol": "Goleador",
      "edad": 36,
      "nacionalidad": "Polonia",
      "estadisticas": {
        "partidos": 36,
        "goles": 23,
        "asistencias": 7,
        "minutos": 3120
      },
      "habilidades": {
        "finalizacion": 90,
        "pases": 82,
        "velocidad": 78
      }
    }
  ]
}
```

#### Obtener jugadores

```
GET /jugadores?equipo={nombre_equipo}&id={id_jugador}
```

Obtiene información de jugadores.

**Parámetros:**
- `equipo`: (Opcional) Nombre del equipo para filtrar jugadores
- `id`: (Opcional) ID del jugador específico a consultar

**Ejemplo de respuesta:**
```json
{
  "jugador": {
    "id": "LEW01",
    "nombre": "Robert Lewandowski",
    "equipo": "Barcelona",
    "posicion": "Delantero",
    "rol": "Goleador",
    "edad": 36,
    "nacionalidad": "Polonia",
    "estadisticas": {
      "partidos": 36,
      "goles": 23,
      "asistencias": 7,
      "minutos": 3120,
      "tarjetas_amarillas": 4,
      "tarjetas_rojas": 0
    },
    "habilidades": {
      "finalizacion": 90,
      "pases": 82,
      "velocidad": 78,
      "regate": 85,
      "defensa": 42,
      "fisica": 80
    },
    "valoracion": 88,
    "lesionado": false,
    "forma": 92
  },
  "historial": [
    {
      "temporada": "2024/25",
      "equipo": "Barcelona",
      "goles": 23,
      "asistencias": 7,
      "partidos": 36
    },
    {
      "temporada": "2023/24",
      "equipo": "Barcelona",
      "goles": 25,
      "asistencias": 6,
      "partidos": 38
    }
  ]
}
```

### Conversión de Formatos

#### Convertir CSV a JSON

```
POST /convertir/csv-json
```

Convierte datos CSV al formato JSON estándar de open-football.

**Parámetros del cuerpo (multipart/form-data):**
- `archivo`: Archivo CSV a convertir

**Ejemplo de respuesta:**
```json
{
  "conversion_id": "conv_123456",
  "formato_original": "csv",
  "formato_final": "json",
  "filas_procesadas": 240,
  "url_descarga": "/api/descargas/conv_123456.json"
}
```

#### Convertir JSON a CSV

```
POST /convertir/json-csv
```

Convierte datos JSON al formato CSV compatible con el sistema.

**Parámetros del cuerpo (multipart/form-data):**
- `archivo`: Archivo JSON a convertir

**Ejemplo de respuesta:**
```json
{
  "conversion_id": "conv_789012",
  "formato_original": "json",
  "formato_final": "csv",
  "filas_procesadas": 240,
  "url_descarga": "/api/descargas/conv_789012.csv"
}
```

### Actualización de Datos

#### Actualizar datos externos

```
GET /actualizar?fuente={nombre_fuente}&dias={dias_atras}
```

Inicia una actualización de datos desde fuentes externas.

**Parámetros:**
- `fuente`: (Opcional) Nombre de la fuente a actualizar (openfootball, football-data). Si no se especifica, actualiza todas.
- `dias`: (Opcional) Número de días hacia atrás para actualizar (default: 30)

**Ejemplo de respuesta:**
```json
{
  "actualizacion_id": "upd_345678",
  "estado": "iniciado",
  "fuentes": ["openfootball", "football-data"],
  "timestamp": "2025-07-02T14:30:45",
  "mensaje": "Actualización iniciada. Use /estado/{actualizacion_id} para verificar el progreso."
}
```

#### Verificar estado de actualización

```
GET /estado/{actualizacion_id}
```

Verifica el estado de una actualización de datos.

**Parámetros:**
- `actualizacion_id`: ID de la actualización a verificar

**Ejemplo de respuesta:**
```json
{
  "actualizacion_id": "upd_345678",
  "estado": "completado",
  "fuentes": {
    "openfootball": {
      "estado": "completado",
      "archivos_procesados": 5,
      "partidos_importados": 1140
    },
    "football-data": {
      "estado": "completado",
      "archivos_procesados": 1,
      "partidos_importados": 240
    }
  },
  "timestamp_inicio": "2025-07-02T14:30:45",
  "timestamp_fin": "2025-07-02T14:32:10",
  "duracion_segundos": 85
}
```

## Códigos de Estado HTTP

- `200 OK`: Solicitud exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Parámetros inválidos
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Paginación

Para endpoints que devuelven múltiples registros, se utiliza paginación con los siguientes parámetros:

- `page`: Número de página (predeterminado: 1)
- `per_page`: Elementos por página (predeterminado: 20, máximo: 100)

## Formato de Fechas

Todas las fechas se proporcionan y se esperan en formato ISO 8601: `YYYY-MM-DD`.

## Limitaciones y Cuotas

- Máximo 100 solicitudes por hora por IP
- Máximo 10 simulaciones Monte Carlo simultáneas
- Tamaño máximo de archivos para conversión: 10MB
