from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy.dialects import registry
from app.models import db
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.restaurants import restaurants_bp
from app.routes.menus import menus_bp
from app.routes.reservations import reservations_bp
from app.routes.orders import orders_bp

from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Forzar a SQLAlchemy a usar psycopg
    registry.register("postgresql.psycopg", "psycopg.sqlalchemy", "PsycopgDialect")
    engine = create_engine('postgresql+psycopg2://postgres:postgres@db:5432/restaurant_api')
    db_session = scoped_session(sessionmaker(bind=engine))
    db.metadata.bind = engine
    db.session = db_session

    # Inicializar otras extensiones
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    CORS(app)
    
    # Configuración de Swagger para documentación de API
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "API de Reserva Inteligente de Restaurantes",
            "description": "API REST para gestión de reservas en restaurantes",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        },
        "security": [
            {
                "Bearer": []
            }
        ]
    })
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(restaurants_bp, url_prefix='/restaurants')
    app.register_blueprint(menus_bp, url_prefix='/menus')
    app.register_blueprint(reservations_bp, url_prefix='/reservations')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    
    @app.route('/')
    def home():
        return {"message": "API de Reserva Inteligente de Restaurantes"}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=3200, debug=True)
