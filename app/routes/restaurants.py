from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.restaurant import Restaurant
from app.models.user import User

restaurants_bp = Blueprint('restaurants', __name__)

@restaurants_bp.route('', methods=['POST'])
@jwt_required()
def create_restaurant():
    print(f"Headers: {request.headers}")
    print(f"Is JSON: {request.is_json}")
    print(f"JSON: {request.get_json()}")

    if not request.is_json:
        return jsonify({'message': 'Request must be application/json'}), 400

    data = request.get_json()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.role != 'admin':
        return jsonify({'message': 'Admin privileges required'}), 403

    required_fields = ['name', 'address', 'phone', 'open_time', 'close_time']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'message': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    try:
        open_time = datetime.strptime(data['open_time'], '%H:%M').time()
        close_time = datetime.strptime(data['close_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'message': 'Invalid time format. Use HH:MM'}), 400

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
        return jsonify({'message': 'Restaurant created successfully', 'id': new_restaurant.id}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@restaurants_bp.route('', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    result = [r.serialize() for r in restaurants]
    return jsonify(result), 200


@restaurants_bp.route('/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    return jsonify(restaurant.serialize()), 200


@restaurants_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_restaurant(id):
    if not request.is_json:
        return jsonify({'message': 'Request must be application/json'}), 400

    current_user_id = get_jwt_identity()
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404

    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()

    if 'name' in data:
        restaurant.name = data['name']
    if 'address' in data:
        restaurant.address = data['address']
    if 'phone' in data:
        restaurant.phone = data['phone']
    if 'description' in data:
        restaurant.description = data['description']
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
    current_user_id = get_jwt_identity()
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404

    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    try:
        restaurant.delete_from_db()
        return jsonify({'message': 'Restaurant deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
