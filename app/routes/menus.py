from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.menu import Menu
from app.models.restaurant import Restaurant
from app.models.user import User

menus_bp = Blueprint('menus', __name__)

@menus_bp.route('', methods=['POST'])
@jwt_required()
def create_menu():
    """
    Create a new menu item
    ---
    tags:
      - Menus
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: MenuCreate
          required:
            - name
            - price
            - category
            - restaurant_id
          properties:
            name:
              type: string
              description: Menu item name
            description:
              type: string
              description: Menu item description
            price:
              type: number
              description: Menu item price
            category:
              type: string
              description: Menu category (e.g. appetizer, main, dessert)
            restaurant_id:
              type: integer
              description: Restaurant ID
    responses:
      201:
        description: Menu item created successfully
      400:
        description: Invalid data
      403:
        description: Permission denied
      404:
        description: Restaurant not found
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Validar campos requeridos
    required_fields = ['name', 'price', 'category', 'restaurant_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Verificar que el restaurante existe
    restaurant = Restaurant.query.get(data['restaurant_id'])
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Verificar que el usuario es admin o el administrador del restaurante
    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    # Crear nuevo menú
    new_menu = Menu(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        category=data['category'],
        restaurant_id=data['restaurant_id']
    )
    
    try:
        new_menu.save_to_db()
        return jsonify({
            'message': 'Menu item created successfully',
            'id': new_menu.id
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@menus_bp.route('/<int:id>', methods=['GET'])
def get_menu(id):
    """
    Get menu item details
    ---
    tags:
      - Menus
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Menu ID
    responses:
      200:
        description: Menu item details
      404:
        description: Menu item not found
    """
    menu = Menu.query.get(id)
    
    if not menu:
        return jsonify({'message': 'Menu item not found'}), 404
    
    return jsonify({
        'id': menu.id,
        'name': menu.name,
        'description': menu.description,
        'price': menu.price,
        'category': menu.category,
        'restaurant_id': menu.restaurant_id,
        'created_at': str(menu.created_at),
        'updated_at': str(menu.updated_at)
    }), 200

@menus_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_menu(id):
    """
    Update menu item
    ---
    tags:
      - Menus
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Menu ID
      - in: body
        name: body
        schema:
          id: MenuUpdate
          properties:
            name:
              type: string
              description: Menu item name
            description:
              type: string
              description: Menu item description
            price:
              type: number
              description: Menu item price
            category:
              type: string
              description: Menu category
    responses:
      200:
        description: Menu item updated successfully
      403:
        description: Permission denied
      404:
        description: Menu item not found
    """
    current_user_id = get_jwt_identity()
    menu = Menu.query.get(id)
    
    if not menu:
        return jsonify({'message': 'Menu item not found'}), 404
    
    # Verificar que el usuario es admin o el administrador del restaurante
    restaurant = Restaurant.query.get(menu.restaurant_id)
    current_user = User.query.get(current_user_id)
    
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Actualizar campos
    if 'name' in data:
        menu.name = data['name']
    if 'description' in data:
        menu.description = data['description']
    if 'price' in data:
        menu.price = data['price']
    if 'category' in data:
        menu.category = data['category']
    
    try:
        menu.save_to_db()
        return jsonify({'message': 'Menu item updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@menus_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_menu(id):
    """
    Delete menu item
    ---
    tags:
      - Menus
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Menu ID
    responses:
      200:
        description: Menu item deleted successfully
      403:
        description: Permission denied
      404:
        description: Menu item not found
    """
    current_user_id = get_jwt_identity()
    menu = Menu.query.get(id)
    
    if not menu:
        return jsonify({'message': 'Menu item not found'}), 404
    
    # Verificar que el usuario es admin o el administrador del restaurante
    restaurant = Restaurant.query.get(menu.restaurant_id)
    current_user = User.query.get(current_user_id)
    
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    try:
        menu.delete_from_db()
        return jsonify({'message': 'Menu item deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@menus_bp.route('/restaurant/<int:restaurant_id>', methods=['GET'])
def get_restaurant_menus(restaurant_id):
    """
    Get all menu items for a restaurant
    ---
    tags:
      - Menus
    parameters:
      - name: restaurant_id
        in: path
        type: integer
        required: true
        description: Restaurant ID
    responses:
      200:
        description: List of menu items
      404:
        description: Restaurant not found
    """
    # Verificar que el restaurante existe
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    menus = Menu.query.filter_by(restaurant_id=restaurant_id).all()
    result = []
    
    for menu in menus:
        result.append({
            'id': menu.id,
            'name': menu.name,
            'description': menu.description,
            'price': menu.price,
            'category': menu.category,
            'restaurant_id': menu.restaurant_id,
            'created_at': str(menu.created_at),
            'updated_at': str(menu.updated_at)
        })
    
    return jsonify(result), 200