from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.restaurant import Restaurant
from app.models.user import User
from app.middleware.auth_middleware import admin_required

restaurants_bp = Blueprint('restaurants', __name__)

@restaurants_bp.route('', methods=['POST'])
@jwt_required()
def create_restaurant():
    """
    Register a new restaurant
    ---
    tags:
      - Restaurants
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: RestaurantCreate
          required:
            - name
            - address
            - phone
            - open_time
            - close_time
          properties:
            name:
              type: string
              description: Restaurant name
            address:
              type: string
              description: Restaurant address
            phone:
              type: string
              description: Restaurant phone number
            description:
              type: string
              description: Restaurant description
            open_time:
              type: string
              format: time
              description: Opening time (HH:MM)
            close_time:
              type: string
              format: time
              description: Closing time (HH:MM)
    responses:
      201:
        description: Restaurant created successfully
      400:
        description: Invalid data
      403:
        description: Admin privileges required
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Check if user is admin
    current_user = User.query.get(current_user_id)
    if current_user.role != 'admin':
        return jsonify({'message': 'Admin privileges required'}), 403
    
    # Validate required fields
    required_fields = ['name', 'address', 'phone', 'open_time', 'close_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Parse time fields
    from datetime import datetime
    try:
        open_time = datetime.strptime(data['open_time'], '%H:%M').time()
        close_time = datetime.strptime(data['close_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'message': 'Invalid time format. Use HH:MM'}), 400
    
    # Create new restaurant
    new_restaurant = Restaurant(
        name=data['name'],
        address=data['address'],
        phone=data['phone'],
        description=data.get('description', ''),
        open_time=open_time,
        close_time=close_time,
        admin_id=current_user_id
    )
    
    try:
        new_restaurant.save_to_db()
        return jsonify({
            'message': 'Restaurant created successfully',
            'id': new_restaurant.id
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@restaurants_bp.route('', methods=['GET'])
def get_restaurants():
    """
    Get list of restaurants
    ---
    tags:
      - Restaurants
    responses:
      200:
        description: List of restaurants
    """
    restaurants = Restaurant.query.all()
    result = []
    
    for restaurant in restaurants:
        result.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'description': restaurant.description,
            'open_time': str(restaurant.open_time),
            'close_time': str(restaurant.close_time),
            'admin_id': restaurant.admin_id
        })
    
    return jsonify(result), 200

@restaurants_bp.route('/<int:id>', methods=['GET'])
def get_restaurant(id):
    """
    Get restaurant details
    ---
    tags:
      - Restaurants
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Restaurant ID
    responses:
      200:
        description: Restaurant details
      404:
        description: Restaurant not found
    """
    restaurant = Restaurant.query.get(id)
    
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    return jsonify({
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address,
        'phone': restaurant.phone,
        'description': restaurant.description,
        'open_time': str(restaurant.open_time),
        'close_time': str(restaurant.close_time),
        'admin_id': restaurant.admin_id,
        'created_at': str(restaurant.created_at),
        'updated_at': str(restaurant.updated_at)
    }), 200

@restaurants_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_restaurant(id):
    """
    Update restaurant information
    ---
    tags:
      - Restaurants
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Restaurant ID
      - in: body
        name: body
        schema:
          id: RestaurantUpdate
          properties:
            name:
              type: string
              description: Restaurant name
            address:
              type: string
              description: Restaurant address
            phone:
              type: string
              description: Restaurant phone number
            description:
              type: string
              description: Restaurant description
            open_time:
              type: string
              format: time
              description: Opening time (HH:MM)
            close_time:
              type: string
              format: time
              description: Closing time (HH:MM)
    responses:
      200:
        description: Restaurant updated successfully
      403:
        description: Permission denied
      404:
        description: Restaurant not found
    """
    current_user_id = get_jwt_identity()
    restaurant = Restaurant.query.get(id)
    
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Check if user is admin or restaurant admin
    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        restaurant.name = data['name']
    if 'address' in data:
        restaurant.address = data['address']
    if 'phone' in data:
        restaurant.phone = data['phone']
    if 'description' in data:
        restaurant.description = data['description']
    
    # Parse time fields if provided
    from datetime import datetime
    if 'open_time' in data:
        try:
            restaurant.open_time = datetime.strptime(data['open_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'message': 'Invalid open_time format. Use HH:MM'}), 400
    
    if 'close_time' in data:
        try:
            restaurant.close_time = datetime.strptime(data['close_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'message': 'Invalid close_time format. Use HH:MM'}), 400
    
    try:
        restaurant.save_to_db()
        return jsonify({'message': 'Restaurant updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@restaurants_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_restaurant(id):
    """
    Delete a restaurant
    ---
    tags:
      - Restaurants
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Restaurant ID
    responses:
      200:
        description: Restaurant deleted successfully
      403:
        description: Permission denied
      404:
        description: Restaurant not found
    """
    current_user_id = get_jwt_identity()
    restaurant = Restaurant.query.get(id)
    
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Check if user is admin or restaurant admin
    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    try:
        restaurant.delete_from_db()
        return jsonify({'message': 'Restaurant deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500