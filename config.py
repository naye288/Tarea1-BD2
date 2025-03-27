import os
from datetime import timedelta

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:postgres@db:5432/restaurant_api'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Configuración general
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret'
    DEBUG = os.environ.get('FLASK_DEBUG') or True

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@db:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False