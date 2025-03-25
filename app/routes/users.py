from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.middleware.auth_middleware import admin_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user():
    """
    Get authenticated user details
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': str(user.created_at)
    }), 200

@users_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    """
    Update user information
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: User ID
      - in: body
        name: body
        schema:
          id: UserUpdate
          properties:
            email:
              type: string
              description: The user's email
            username:
              type: string
              description: The user's username
    responses:
      200:
        description: User updated successfully
      403:
        description: Permission denied
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Solo el propio usuario o un admin puede actualizar la información
    current_user = User.query.get(current_user_id)
    if current_user.id != id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Actualizar campos
    if 'email' in data:
        # Verificar que el email no exista ya
        if User.find_by_email(data['email']) and User.find_by_email(data['email']).id != id:
            return jsonify({'message': 'Email already exists'}), 400
        user.email = data['email']
    
    if 'username' in data:
        # Verificar que el username no exista ya
        if User.find_by_username(data['username']) and User.find_by_username(data['username']).id != id:
            return jsonify({'message': 'Username already exists'}), 400
        user.username = data['username']
    
    try:
        user.save_to_db()
        return jsonify({'message': 'User updated successfully'}), 200
    except:
        return jsonify({'message': 'Something went wrong'}), 500

@users_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    """
    Delete a user
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User deleted successfully
      403:
        description: Permission denied
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Solo el propio usuario o un admin puede eliminar un usuario
    current_user = User.query.get(current_user_id)
    if current_user.id != id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    try:
        user.delete_from_db()
        return jsonify({'message': 'User deleted successfully'}), 200
    except:
        return jsonify({'message': 'Something went wrong'}), 500