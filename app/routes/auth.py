from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: UserRegistration
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              description: The user's username
            email:
              type: string
              description: The user's email
            password:
              type: string
              description: The user's password
            role:
              type: string
              description: User role (client or admin)
              default: client
    responses:
      201:
        description: User created successfully
      400:
        description: Username or email already exists
    """
    data = request.get_json()
    
    # Verificar si el usuario ya existe
    if User.find_by_username(data['username']):
        return jsonify({'message': 'Username already exists'}), 400
    
    if User.find_by_email(data['email']):
        return jsonify({'message': 'Email already exists'}), 400
    
    # Crear nuevo usuario
    role = data.get('role', 'client')
    if role not in ['client', 'admin']:
        return jsonify({'message': 'Invalid role'}), 400
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=User.generate_hash(data['password']),
        role=role
    )
    
    try:
        new_user.save_to_db()
        return jsonify({'message': 'User created successfully'}), 201
    except:
        return jsonify({'message': 'Something went wrong'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: UserLogin
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: The user's username
            password:
              type: string
              description: The user's password
    responses:
      200:
        description: Login successful
        schema:
          id: AccessToken
          properties:
            access_token:
              type: string
              description: JWT access token
            user_id:
              type: integer
              description: User ID
            role:
              type: string
              description: User role
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    
    # Buscar usuario
    current_user = User.find_by_username(data['username'])
    
    if not current_user:
        return jsonify({'message': 'User not found'}), 404
    
    # Verificar contraseña
    if User.verify_hash(data['password'], current_user.password):
        access_token = create_access_token(identity=current_user.id)
        return jsonify({
            'message': 'Logged in successfully',
            'access_token': access_token,
            'user_id': current_user.id,
            'role': current_user.role
        }), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401