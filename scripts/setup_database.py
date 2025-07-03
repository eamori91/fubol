#!/usr/bin/env python
"""
Script para inicializar y actualizar el esquema de la base de datos.

Este script crea las tablas necesarias para almacenar equipos, jugadores, partidos y
otras entidades del sistema de análisis y predicción de fútbol.

Uso:
    python setup_database.py [--db_type TYPE] [--reset]

Argumentos:
    --db_type TYPE    Tipo de base de datos a utilizar (sqlite, postgresql, mysql)
    --reset           Eliminar y volver a crear todas las tablas
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any
import json

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, sessionmaker
except ImportError:
    print("ERROR: SQLAlchemy no está instalado. Instala con 'pip install sqlalchemy'")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'database_setup.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('setup_database')

# Definir base declarativa para los modelos
Base = declarative_base()

# Definir modelos
class Liga(Base):
    __tablename__ = 'ligas'
    
    id = sa.Column(sa.Integer, primary_key=True)
    codigo = sa.Column(sa.String(10), unique=True, index=True)
    nombre = sa.Column(sa.String(100), nullable=False)
    pais = sa.Column(sa.String(100))
    temporada_actual = sa.Column(sa.String(20))
    fecha_creacion = sa.Column(sa.DateTime, server_default=sa.func.now())
    fecha_actualizacion = sa.Column(sa.DateTime, onupdate=sa.func.now())
    
    # Relaciones
    equipos = relationship("Equipo", back_populates="liga")
    partidos = relationship("Partido", back_populates="liga")
    
    def __repr__(self):
        return f"<Liga(nombre='{self.nombre}', pais='{self.pais}')>"


class Equipo(Base):
    __tablename__ = 'equipos'
    
    id = sa.Column(sa.Integer, primary_key=True)
    id_externo = sa.Column(sa.String(50), unique=True, index=True)
    nombre = sa.Column(sa.String(100), nullable=False)
    nombre_corto = sa.Column(sa.String(50))
    liga_id = sa.Column(sa.Integer, sa.ForeignKey('ligas.id'), nullable=True)
    pais = sa.Column(sa.String(100))
    fundacion = sa.Column(sa.Integer)
    estadio = sa.Column(sa.String(100))
    escudo_url = sa.Column(sa.String(255))
    fuente = sa.Column(sa.String(50))
    fecha_creacion = sa.Column(sa.DateTime, server_default=sa.func.now())
    fecha_actualizacion = sa.Column(sa.DateTime, onupdate=sa.func.now())
    
    # Relaciones
    liga = relationship("Liga", back_populates="equipos")
    jugadores = relationship("Jugador", back_populates="equipo")
    partidos_local = relationship("Partido", foreign_keys="Partido.equipo_local_id", back_populates="equipo_local")
    partidos_visitante = relationship("Partido", foreign_keys="Partido.equipo_visitante_id", back_populates="equipo_visitante")
    
    def __repr__(self):
        return f"<Equipo(nombre='{self.nombre}', liga='{self.liga_id}')>"


class Jugador(Base):
    __tablename__ = 'jugadores'
    
    id = sa.Column(sa.Integer, primary_key=True)
    id_externo = sa.Column(sa.String(50), unique=True, index=True)
    nombre = sa.Column(sa.String(100), nullable=False)
    apellido = sa.Column(sa.String(100))
    equipo_id = sa.Column(sa.Integer, sa.ForeignKey('equipos.id'), nullable=True)
    posicion = sa.Column(sa.String(50))
    nacionalidad = sa.Column(sa.String(100))
    fecha_nacimiento = sa.Column(sa.Date)
    altura = sa.Column(sa.Integer)
    peso = sa.Column(sa.Integer)
    dorsal = sa.Column(sa.Integer)
    foto_url = sa.Column(sa.String(255))
    fuente = sa.Column(sa.String(50))
    fecha_creacion = sa.Column(sa.DateTime, server_default=sa.func.now())
    fecha_actualizacion = sa.Column(sa.DateTime, onupdate=sa.func.now())
    
    # Relaciones
    equipo = relationship("Equipo", back_populates="jugadores")
    estadisticas = relationship("EstadisticasJugador", back_populates="jugador")
    
    def __repr__(self):
        return f"<Jugador(nombre='{self.nombre}', equipo='{self.equipo_id}')>"


class Partido(Base):
    __tablename__ = 'partidos'
    
    id = sa.Column(sa.Integer, primary_key=True)
    id_externo = sa.Column(sa.String(50), index=True)
    liga_id = sa.Column(sa.Integer, sa.ForeignKey('ligas.id'))
    temporada = sa.Column(sa.String(20))
    fecha = sa.Column(sa.DateTime, nullable=False)
    jornada = sa.Column(sa.Integer)
    equipo_local_id = sa.Column(sa.Integer, sa.ForeignKey('equipos.id'))
    equipo_visitante_id = sa.Column(sa.Integer, sa.ForeignKey('equipos.id'))
    goles_local = sa.Column(sa.Integer)
    goles_visitante = sa.Column(sa.Integer)
    estado = sa.Column(sa.String(20))  # SCHEDULED, LIVE, FINISHED, POSTPONED, etc.
    resultado_primer_tiempo_local = sa.Column(sa.Integer)
    resultado_primer_tiempo_visitante = sa.Column(sa.Integer)
    estadio = sa.Column(sa.String(100))
    arbitro = sa.Column(sa.String(100))
    fuente = sa.Column(sa.String(50))
    fecha_creacion = sa.Column(sa.DateTime, server_default=sa.func.now())
    fecha_actualizacion = sa.Column(sa.DateTime, onupdate=sa.func.now())
    
    # Relaciones
    liga = relationship("Liga", back_populates="partidos")
    equipo_local = relationship("Equipo", foreign_keys=[equipo_local_id], back_populates="partidos_local")
    equipo_visitante = relationship("Equipo", foreign_keys=[equipo_visitante_id], back_populates="partidos_visitante")
    eventos = relationship("EventoPartido", back_populates="partido")
    predicciones = relationship("Prediccion", back_populates="partido")
    
    def __repr__(self):
        return f"<Partido(local='{self.equipo_local_id}', visitante='{self.equipo_visitante_id}', fecha='{self.fecha}')>"


class EventoPartido(Base):
    __tablename__ = 'eventos_partido'
    
    id = sa.Column(sa.Integer, primary_key=True)
    partido_id = sa.Column(sa.Integer, sa.ForeignKey('partidos.id'), nullable=False)
    minuto = sa.Column(sa.Integer)
    tipo = sa.Column(sa.String(50))  # GOL, TARJETA_AMARILLA, TARJETA_ROJA, CAMBIO, etc.
    equipo_id = sa.Column(sa.Integer, sa.ForeignKey('equipos.id'))
    jugador_id = sa.Column(sa.Integer, sa.ForeignKey('jugadores.id'))
    jugador2_id = sa.Column(sa.Integer, sa.ForeignKey('jugadores.id'))  # Para asistencias o cambios
    detalle = sa.Column(sa.Text)
    fuente = sa.Column(sa.String(50))
    fecha_creacion = sa.Column(sa.DateTime, server_default=sa.func.now())
    
    # Relaciones
    partido = relationship("Partido", back_populates="eventos")
    equipo = relationship("Equipo")
    jugador = relationship("Jugador", foreign_keys=[jugador_id])
    jugador2 = relationship("Jugador", foreign_keys=[jugador2_id])
    
    def __repr__(self):
        return f"<EventoPartido(partido='{self.partido_id}', tipo='{self.tipo}', minuto='{self.minuto}')>"


class EstadisticasJugador(Base):
    __tablename__ = 'estadisticas_jugador'
    
    id = sa.Column(sa.Integer, primary_key=True)
    jugador_id = sa.Column(sa.Integer, sa.ForeignKey('jugadores.id'), nullable=False)
    temporada = sa.Column(sa.String(20), nullable=False)
    partidos_jugados = sa.Column(sa.Integer, default=0)
    minutos_jugados = sa.Column(sa.Integer, default=0)
    goles = sa.Column(sa.Integer, default=0)
    asistencias = sa.Column(sa.Integer, default=0)
    tarjetas_amarillas = sa.Column(sa.Integer, default=0)
    tarjetas_rojas = sa.Column(sa.Integer, default=0)
    valoracion_media = sa.Column(sa.Float)
    fuente = sa.Column(sa.String(50))
    fecha_actualizacion = sa.Column(sa.DateTime, onupdate=sa.func.now())
    
    # Relaciones
    jugador = relationship("Jugador", back_populates="estadisticas")
    
    __table_args__ = (
        sa.UniqueConstraint('jugador_id', 'temporada', name='uix_jugador_temporada'),
    )
    
    def __repr__(self):
        return f"<EstadisticasJugador(jugador='{self.jugador_id}', temporada='{self.temporada}')>"


class Prediccion(Base):
    __tablename__ = 'predicciones'
    
    id = sa.Column(sa.Integer, primary_key=True)
    partido_id = sa.Column(sa.Integer, sa.ForeignKey('partidos.id'), nullable=False)
    modelo = sa.Column(sa.String(50))  # TRADICIONAL, DEEP_LEARNING, etc.
    probabilidad_local = sa.Column(sa.Float)
    probabilidad_empate = sa.Column(sa.Float)
    probabilidad_visitante = sa.Column(sa.Float)
    prediccion_goles_local = sa.Column(sa.Float)
    prediccion_goles_visitante = sa.Column(sa.Float)
    fecha_prediccion = sa.Column(sa.DateTime, server_default=sa.func.now())
    
    # Relaciones
    partido = relationship("Partido", back_populates="predicciones")
    
    def __repr__(self):
        return f"<Prediccion(partido='{self.partido_id}', modelo='{self.modelo}')>"


def get_connection_url(db_type: str) -> str:
    """
    Obtiene la URL de conexión a la base de datos.
    
    Args:
        db_type: Tipo de base de datos (sqlite, postgresql, mysql)
        
    Returns:
        URL de conexión
    """
    if db_type == 'sqlite':
        db_path = os.path.join('data', 'database', 'football.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"
        
    elif db_type == 'postgresql':
        # Leer configuración
        config_file = os.path.join('config', 'database.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                db_config = json.load(f)
                
            # Construir URL
            user = db_config.get('user', 'postgres')
            password = db_config.get('password', '')
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', '5432')
            database = db_config.get('database', 'football_analytics')
            
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            # Valores por defecto
            return "postgresql://postgres:postgres@localhost:5432/football_analytics"
            
    elif db_type == 'mysql':
        # Leer configuración
        config_file = os.path.join('config', 'database.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                db_config = json.load(f)
                
            # Construir URL
            user = db_config.get('user', 'root')
            password = db_config.get('password', '')
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', '3306')
            database = db_config.get('database', 'football_analytics')
            
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        else:
            # Valores por defecto
            return "mysql+pymysql://root:root@localhost:3306/football_analytics"
    else:
        raise ValueError(f"Tipo de base de datos no soportado: {db_type}")

def create_tables(engine: sa.engine.Engine) -> None:
    """
    Crea todas las tablas en la base de datos.
    
    Args:
        engine: Motor de conexión SQLAlchemy
    """
    logger.info("Creando tablas...")
    Base.metadata.create_all(engine)
    logger.info("Tablas creadas correctamente.")

def drop_tables(engine: sa.engine.Engine) -> None:
    """
    Elimina todas las tablas de la base de datos.
    
    Args:
        engine: Motor de conexión SQLAlchemy
    """
    logger.info("Eliminando tablas existentes...")
    Base.metadata.drop_all(engine)
    logger.info("Tablas eliminadas correctamente.")

def insert_initial_data(session: sa.orm.Session) -> None:
    """
    Inserta datos iniciales en la base de datos.
    
    Args:
        session: Sesión de SQLAlchemy
    """
    logger.info("Insertando datos iniciales...")
    
    # Ligas principales
    ligas = [
        Liga(codigo='PD', nombre='Primera División', pais='España', temporada_actual='2023-24'),
        Liga(codigo='PL', nombre='Premier League', pais='Inglaterra', temporada_actual='2023-24'),
        Liga(codigo='BL1', nombre='Bundesliga', pais='Alemania', temporada_actual='2023-24'),
        Liga(codigo='SA', nombre='Serie A', pais='Italia', temporada_actual='2023-24'),
        Liga(codigo='FL1', nombre='Ligue 1', pais='Francia', temporada_actual='2023-24')
    ]
    
    session.add_all(ligas)
    session.commit()
    
    logger.info(f"Se han insertado {len(ligas)} ligas.")

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Configura la base de datos para el sistema')
    parser.add_argument('--db_type', choices=['sqlite', 'postgresql', 'mysql'],
                        default='sqlite', help='Tipo de base de datos a utilizar')
    parser.add_argument('--reset', action='store_true', 
                        help='Eliminar y volver a crear todas las tablas')
    return parser.parse_args()

def main():
    """Función principal del script."""
    args = parse_args()
    
    try:
        # Obtener URL de conexión
        connection_url = get_connection_url(args.db_type)
        logger.info(f"Conectando a la base de datos: {connection_url.split('@')[-1]}")
        
        # Crear motor de conexión
        engine = sa.create_engine(connection_url)
        
        # Si se solicita resetear, eliminar tablas existentes
        if args.reset:
            drop_tables(engine)
        
        # Crear tablas
        create_tables(engine)
        
        # Insertar datos iniciales
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            insert_initial_data(session)
        except Exception as e:
            logger.error(f"Error al insertar datos iniciales: {e}")
        finally:
            session.close()
            
        logger.info("Configuración de la base de datos completada correctamente.")
        
    except Exception as e:
        logger.error(f"Error al configurar la base de datos: {e}")

if __name__ == '__main__':
    main()
