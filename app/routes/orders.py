from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.models.menu import Menu
from app.models.user import User

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create a new order
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: OrderCreate
          required:
            - pickup_time
            - restaurant_id
            - items
          properties:
            pickup_time:
              type: string
              format: datetime
              description: Pickup time (YYYY-MM-DD HH:MM)
            notes:
              type: string
              description: Additional notes
            restaurant_id:
              type: integer
              description: Restaurant ID
            items:
              type: array
              description: List of menu items to order
              items:
                type: object
                required:
                  - menu_id
                  - quantity
                properties:
                  menu_id:
                    type: integer
                    description: Menu item ID
                  quantity:
                    type: integer
                    description: Quantity to order
    responses:
      201:
        description: Order created successfully
      400:
        description: Invalid data
      404:
        description: Restaurant or menu item not found
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Valida los campos requeridos
    required_fields = ['pickup_time', 'restaurant_id', 'items']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Ve si el restaurante existe
    restaurant = Restaurant.query.get(data['restaurant_id'])
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Valida items
    if not isinstance(data['items'], list) or len(data['items']) == 0:
        return jsonify({'message': 'Order must include at least one item'}), 400
    
    # Calcula el total y verifica los items del menu
    total = 0
    for item in data['items']:
        if 'menu_id' not in item or 'quantity' not in item:
            return jsonify({'message': 'Each item must have menu_id and quantity'}), 400
        
        menu_item = Menu.query.get(item['menu_id'])
        if not menu_item:
            return jsonify({'message': f'Menu item {item["menu_id"]} not found'}), 404
        
        if menu_item.restaurant_id != data['restaurant_id']:
            return jsonify({'message': f'Menu item {item["menu_id"]} does not belong to this restaurant'}), 400
        
        total += menu_item.price * item['quantity']
    
    # Parsea el tiempo de recogida
    try:
        pickup_time = datetime.strptime(data['pickup_time'], '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({'message': 'Invalid pickup_time format. Use YYYY-MM-DD HH:MM'}), 400
    
    # Crea nueva orden
    new_order = Order(
        status='pending',
        pickup_time=pickup_time,
        total=total,
        notes=data.get('notes', ''),
        user_id=current_user_id,
        restaurant_id=data['restaurant_id']
    )
    
    try:
        new_order.save_to_db()
        
        # Crea nuevos items en la orden
        for item in data['items']:
            menu_item = Menu.query.get(item['menu_id'])
            order_item = OrderItem(
                quantity=item['quantity'],
                price=menu_item.price,
                order_id=new_order.id,
                menu_id=item['menu_id']
            )
            order_item.save_to_db()
        
        return jsonify({
            'message': 'Order created successfully',
            'id': new_order.id,
            'total': total
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@orders_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    """
    Get order details
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Order ID
    responses:
      200:
        description: Order details
      403:
        description: Permission denied
      404:
        description: Order not found
    """
    current_user_id = get_jwt_identity()
    order = Order.query.get(id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Ve los permisos - solo el admin de restaurante o admin pueden verlo
    current_user = User.query.get(current_user_id)
    restaurant = Restaurant.query.get(order.restaurant_id)
    
    if (order.user_id != current_user_id and 
        restaurant.admin_id != current_user_id and 
        current_user.role != 'admin'):
        return jsonify({'message': 'Permission denied'}), 403
    
    # Get order items
    items = []
    for item in order.items:
        menu_item = Menu.query.get(item.menu_id)
        items.append({
            'id': item.id,
            'menu_id': item.menu_id,
            'name': menu_item.name,
            'quantity': item.quantity,
            'price': item.price,
            'subtotal': item.price * item.quantity
        })
    
    return jsonify({
        'id': order.id,
        'status': order.status,
        'pickup_time': str(order.pickup_time),
        'total': order.total,
        'notes': order.notes,
        'user_id': order.user_id,
        'restaurant_id': order.restaurant_id,
        'items': items,
        'created_at': str(order.created_at),
        'updated_at': str(order.updated_at)
    }), 200

@orders_bp.route('/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(id):
    """
    Update order status
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Order ID
      - in: body
        name: body
        schema:
          id: OrderStatusUpdate
          required:
            - status
          properties:
            status:
              type: string
              description: New order status (pending, confirmed, ready, delivered)
    responses:
      200:
        description: Order status updated successfully
      400:
        description: Invalid status
      403:
        description: Permission denied
      404:
        description: Order not found
    """
    current_user_id = get_jwt_identity()
    order = Order.query.get(id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Solo admins del restaurante pueden actualizar la orden
    restaurant = Restaurant.query.get(order.restaurant_id)
    current_user = User.query.get(current_user_id)
    
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'message': 'Status field is required'}), 400
    
    valid_statuses = ['pending', 'confirmed', 'ready', 'delivered']
    if data['status'] not in valid_statuses:
        return jsonify({'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    order.status = data['status']
    
    try:
        order.save_to_db()
        return jsonify({'message': 'Order status updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@orders_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_orders():
    """
    Get all orders for the authenticated user
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    responses:
      200:
        description: List of user orders
    """
    current_user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=current_user_id).all()
    result = []
    
    for order in orders:
        result.append({
            'id': order.id,
            'status': order.status,
            'pickup_time': str(order.pickup_time),
            'total': order.total,
            'restaurant_id': order.restaurant_id,
            'created_at': str(order.created_at)
        })
    
    return jsonify(result), 200

@orders_bp.route('/restaurant/<int:restaurant_id>', methods=['GET'])
@jwt_required()
def get_restaurant_orders(restaurant_id):
    """
    Get all orders for a restaurant
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: restaurant_id
        in: path
        type: integer
        required: true
        description: Restaurant ID
    responses:
      200:
        description: List of restaurant orders
      403:
        description: Permission denied
      404:
        description: Restaurant not found
    """
    current_user_id = get_jwt_identity()
    restaurant = Restaurant.query.get(restaurant_id)
    
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Check permissions - only restaurant admin can see all orders
    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    orders = Order.query.filter_by(restaurant_id=restaurant_id).all()
    result = []
    
    for order in orders:
        result.append({
            'id': order.id,
            'status': order.status,
            'pickup_time': str(order.pickup_time),
            'total': order.total,
            'user_id': order.user_id,
            'created_at': str(order.created_at)
        })
    
    return jsonify(result), 200