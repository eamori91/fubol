# Sistema Integrado de Análisis Predictivo de Fútbol

Herramienta avanzada e integrada para el análisis comprehensivo de partidos de fútbol que combina análisis estadístico tradicional, simulaciones Monte Carlo, modelos de deep learning, gestión detallada de equipos y jugadores, y una API pública completa.

## 🚀 Características principales

### Análisis Predictivo Multicapa
- **Análisis de partidos históricos**: Estudio profundo de patrones y tendencias
- **Análisis de partidos próximos**: Predicción para partidos de la próxima semana
- **Análisis predictivo avanzado**: Predicción para partidos futuros con múltiples modelos
- **Modelos de Deep Learning**: Redes neuronales para predicciones más precisas
- **Comparativa de modelos**: Consenso entre diferentes enfoques predictivos

### Simulaciones Avanzadas
- **Simulación Monte Carlo**: Miles de simulaciones para robustez estadística
- **Simulación de eventos**: Partidos minuto a minuto con eventos detallados
- **Distribuciones de probabilidad**: Análisis estadístico completo de resultados
- **Visualizaciones interactivas**: Gráficos avanzados de distribuciones y tendencias

### Gestión de Equipos y Jugadores
- **Modelo de datos detallado**: Equipos con jugadores, estadísticas y habilidades
- **Análisis de plantillas**: Cálculo de fuerza y rendimiento de equipos
- **Historial de jugadores**: Seguimiento individual y colectivo
- **Análisis de estilos de juego**: Caracterización de equipos y estrategias

### API Pública Completa
- **Endpoints RESTful**: Acceso programático a todas las funcionalidades
- **Formato de datos estandarizado**: Compatible con open-football y otros estándares
- **Conversión de formatos**: CSV ↔ JSON automática
- **Documentación interactiva**: API autodocumentada
- **Rate limiting y seguridad**: Control de acceso y uso

### Integración de Datos Externos
- **Actualización automática**: Datos desde fuentes públicas (football-data.org, espn.com, etc.)
- **Formatos abiertos**: Compatibilidad con datasets públicos
- **Cache inteligente**: Optimización de rendimiento y uso de recursos

### Unificación de Fuentes de Datos Gratuitas
- **Adaptador Unificado**: Integración de múltiples fuentes gratuitas
- **ESPN API**: Integración con la API no oficial de ESPN para datos actualizados
- **Próximos Partidos**: Calendario completo de partidos futuros
- **Datos Históricos**: Información de equipos y resultados pasados
- **Información de Árbitros**: Estadísticas y tendencias de árbitros
- **Normalización de Datos**: Formato unificado para todas las fuentes

## 🛠 Tecnologías utilizadas

### Core
- **Python 3.8+**: Lenguaje principal
- **pandas & numpy**: Procesamiento y análisis de datos
- **scikit-learn**: Modelos de machine learning tradicionales
- **TensorFlow/Keras**: Modelos de deep learning
- **Flask**: API y aplicación web

### Análisis y Visualización
- **matplotlib & seaborn**: Visualizaciones estáticas
- **plotly**: Visualizaciones interactivas
- **scipy & statsmodels**: Análisis estadístico avanzado
- **shap**: Explicabilidad de modelos

### Optimización y Performance
- **XGBoost**: Modelos de gradient boosting
- **Optuna**: Optimización de hiperparámetros
- **joblib**: Paralelización y persistencia
- **Redis**: Cache distribuido (opcional)

## 📦 Instalación y configuración

### Requisitos del sistema
```bash
Python 3.8+
pip 21.0+
4GB RAM mínimo (8GB recomendado)
2GB espacio en disco
```

### Instalación rápida
```bash
# 1. Clonar el repositorio
git clone https://github.com/yourusername/fubol-analyzer.git
cd fubol-analyzer

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar entorno (opcional)
cp .env.example .env
# Editar .env con sus configuraciones

# 5. Inicializar sistema
python sistema_integrado.py --modo inicializar
```

### Configuración avanzada
```bash
# Variables de entorno importantes
export ENVIRONMENT=development  # development, production, testing
export FOOTBALL_DATA_API_KEY=your_api_key_here
export SECRET_KEY=your_secret_key_here
export FLASK_ENV=development
```

## 🎯 Uso del sistema

### Modo interactivo (recomendado para nuevos usuarios)
```bash
python sistema_integrado.py --modo interactivo
```

### Análisis completo de un partido
```bash
python sistema_integrado.py --modo analisis --local "Real Madrid" --visitante "Barcelona" --guardar
```

### Simulación Monte Carlo
```bash
python simular_partido.py --local "Real Madrid" --visitante "Barcelona" --n 1000 --visualizar
```

### Gestión de equipos
```bash
python gestionar_equipos.py --generar --equipos 20 --visualizar
```

### Aplicación web
```bash
python app.py
# Navegar a http://localhost:5000
```

### API REST
```bash
# Iniciar servidor API
python app.py

# Ejemplos de uso de la API
curl "http://localhost:5000/api/predicciones/Real%20Madrid/Barcelona?simular=true"
curl "http://localhost:5000/api/equipos/Real%20Madrid"
curl "http://localhost:5000/api/metricas"
```

## 📈 API Endpoints

La API REST proporciona acceso programático a todas las funcionalidades:

### Predicciones
- `GET /api/predicciones/{local}/{visitante}` - Predicción tradicional
- `GET /api/predicciones/deep-learning/{local}/{visitante}` - Predicción con deep learning
- `GET /api/predicciones/comparacion/{local}/{visitante}` - Comparar múltiples modelos

### Simulaciones
- `GET /api/simulaciones/eventos/{local}/{visitante}` - Simulación de eventos

### Equipos y datos
- `GET /api/equipos/{nombre}` - Datos de un equipo
- `GET /api/partidos/historico` - Historial de partidos
- `POST /api/datos/actualizar` - Actualizar datos externos

### Sistema
- `GET /api/metricas` - Métricas del sistema
- `POST /api/modelos/entrenar` - Reentrenar modelos
- `POST /api/convertir` - Convertir formatos de datos

### Documentación
- `GET /api/` - Documentación interactiva de la API

## 🎛 Configuración avanzada

### Modelos predictivos
```python
# config.py
MODELO_TRADICIONAL = {
    'n_estimators': 100,
    'max_depth': 10,
    'random_state': 42
}

MODELO_DEEP_LEARNING = {
    'epochs': 100,
    'batch_size': 32,
    'learning_rate': 0.001
}
```

### Fuentes de datos
```python
FUENTES_DATOS = {
    'football-data': {
        'url_base': 'https://api.football-data.org/v4',
        'api_key': 'YOUR_API_KEY'
    }
}
```

## 🧪 Ejemplos de uso

### Análisis completo en Python
```python
from sistema_integrado import SistemaIntegrado

# Inicializar sistema
sistema = SistemaIntegrado()
sistema.cargar_datos()

# Análisis completo
resultados = sistema.analisis_completo(
    'Real Madrid', 'Barcelona'
)

# Ver consenso
print(f"Resultado probable: {resultados['consenso']['resultado_probable']}")
```

### Simulación Monte Carlo
```python
from analisis.simulador import SimuladorPartidos
from analisis.futuro import AnalisisFuturo

simulador = SimuladorPartidos(AnalisisFuturo())
resultados = simulador.simular_partido_monte_carlo(
    'Real Madrid', 'Barcelona', n_simulaciones=1000
)

print(f"Probabilidades: {resultados['probabilidades']}")
```

### Gestión de equipos
```python
from analisis.entidades import GestorEquipos, Equipo, Jugador

gestor = GestorEquipos()
equipo = Equipo('Mi Equipo', 'Mi Liga', 'España')

# Agregar jugadores
for i in range(11):
    jugador = Jugador(f'player_{i}', f'Jugador {i}', 'Mi Equipo', 'Delantero', 25)
    equipo.agregar_jugador(jugador)

gestor.agregar_equipo(equipo)
fuerza = equipo.calcular_fuerza_plantilla()
```

## 🔬 Testing y validación

### Ejecutar pruebas
```bash
# Prueba rápida (recomendada para desarrollo)
python pruebas_integracion.py --rapida

# Suite completa (para CI/CD)
python pruebas_integracion.py --completa

# Pruebas específicas con pytest
pytest tests/ -v
```

### Métricas de calidad
El sistema incluye métricas automáticas de:
- Precisión de predicciones
- Tiempo de respuesta de API
- Cobertura de datos
- Rendimiento de modelos

## 🚀 Despliegue

### Docker (recomendado)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Despliegue en producción
```bash
# Con gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Con supervisor (recomendado)
# Ver docs/deployment.md para configuración completa
```

## 🤝 Contribución

### Proceso de desarrollo
1. Fork del proyecto
2. Crear branch para feature (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Crear Pull Request

### Estándares de código
- PEP 8 para Python
- Docstrings para todas las funciones públicas
- Type hints donde sea apropiado
- Pruebas para nuevas funcionalidades

### Estructura de commits
```
type(scope): description

feat(api): add new prediction endpoint
fix(simulator): resolve Monte Carlo accuracy issue
docs(readme): update installation instructions
test(integration): add comprehensive system tests
```

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [football-data.org](https://football-data.org) por proporcionar datos abiertos
- [open-football](https://github.com/openfootball) por el formato estándar de datos
- Comunidad de Python y machine learning por las herramientas utilizadas

## 📞 Soporte y contacto

- **Issues**: [GitHub Issues](https://github.com/yourusername/fubol-analyzer/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/yourusername/fubol-analyzer/wiki)
- **Email**: support@fubol-analyzer.com

## 🗺 Roadmap

### Próximas versiones
- **v2.0**: Modelos de deep learning más avanzados (LSTM, Transformers)
- **v2.1**: Integración con más fuentes de datos (transfermarkt, etc.)
- **v2.2**: Dashboard interactivo con Dash/Streamlit
- **v2.3**: Análisis de vídeo con computer vision
- **v3.0**: Predicciones en tiempo real durante partidos

### Características experimentales
- Análisis de sentimiento de redes sociales
- Predicción de lesiones
- Optimización de alineaciones
- Análisis de mercado de fichajes

---

**¿Te resulta útil este proyecto? ⭐ Dale una estrella en GitHub y compártelo con otros aficionados al fútbol y data science!**
