# Tarea1-BD2
Tarea corta 1 
# API de Reserva Inteligente de Restaurantes

Esta API permite la gestión de usuarios, restaurantes, menús, reservas y pedidos para un sistema de reservas de restaurantes inteligente. Está desarrollada con Flask, autenticación JWT y contenedorización con Docker.

## Características

- Autenticación y gestión de sesiones con JWT
- Gestión de usuarios (clientes y administradores)
- Gestión de restaurantes
- Gestión de menús y productos
- Reserva de mesas y pedidos
- Documentación de API con Swagger

## Requisitos

- Docker y Docker Compose
- Python 3.8+

## Instalación

1. Clonar el repositorio:
```
git clone https://github.com/naye288/Tarea1-BD2
cd restaurant-api
```

2. Crear un archivo `.env` (opcional) para configurar variables de entorno:
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/restaurant_api
JWT_SECRET_KEY=your_jwt_secret_key
FLASK_DEBUG=1
```

3. Iniciar los contenedores con Docker Compose:
```
docker-compose up -d
```

4. La API estará disponible en `http://localhost:3200`
5. La documentación Swagger estará disponible en `http://localhost:3200/apidocs/`
6. El servicio Keycloak estará disponible en `http://localhost:8080`

## Estructura del Proyecto

```
restaurant-api/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── middleware/
│   └── utils/
├── tests/
├── app.py
├── config.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Endpoints

La API proporciona los siguientes endpoints:

### Autenticación
- `POST /auth/register` - Registro de un nuevo usuario
- `POST /auth/login` - Inicio de sesión y obtención de JWT

### Usuarios
- `GET /users/me` - Obtener detalles del usuario autenticado
- `PUT /users/:id` - Actualizar información de un usuario
- `DELETE /users/:id` - Eliminar un usuario

### Restaurantes
- `POST /restaurants` - Registrar un restaurante (solo administradores)
- `GET /restaurants` - Listar restaurantes disponibles
- `GET /restaurants/:id` - Obtener detalles de un restaurante específico
- `PUT /restaurants/:id` - Actualizar restaurante

### Menús
- `POST /menus` - Crear un nuevo menú para un restaurante
- `GET /menus/:id` - Obtener detalles de un menú específico
- `PUT /menus/:id` - Actualizar un menú existente
- `DELETE /menus/:id` - Eliminar un menú

### Reservas
- `POST /reservations` - Crear una nueva reserva
- `DELETE /reservations/:id` - Cancelar una reserva

### Pedidos
- `POST /orders` - Realizar un pedido
- `GET /orders/:id` - Obtener detalles de un pedido

## Pruebas Unitarias

Para ejecutar las pruebas unitarias:

```
docker-compose exec api pytest -v
```

Para ejecutar las pruebas con cobertura:

```
docker-compose exec api pytest --cov=app tests/
```

## Desarrollo

1. Para entrar en el contenedor de desarrollo:
```
docker-compose exec api bash
```

2. Para aplicar migraciones de base de datos:
```
docker-compose exec api flask db migrate -m "mensaje de migración"
docker-compose exec api flask db upgrade
```