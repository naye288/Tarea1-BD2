from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models.reservation import Reservation
from app.models.restaurant import Restaurant
from app.models.user import User

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    Create a new reservation
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: ReservationCreate
          required:
            - date
            - time
            - guests
            - restaurant_id
          properties:
            date:
              type: string
              format: date
              description: Reservation date (YYYY-MM-DD)
            time:
              type: string
              format: time
              description: Reservation time (HH:MM)
            guests:
              type: integer
              description: Number of guests
            notes:
              type: string
              description: Additional notes
            restaurant_id:
              type: integer
              description: Restaurant ID
    responses:
      201:
        description: Reservation created successfully
      400:
        description: Invalid data
      404:
        description: Restaurant not found
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    # Validar campos requeridos
    required_fields = ['date', 'time', 'guests', 'restaurant_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Verificar que el restaurante existe
    restaurant = Restaurant.query.get(data['restaurant_id'])
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Crear nueva reserva
    new_reservation = Reservation(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        time=datetime.strptime(data['time'], '%H:%M').time(),
        guests=data['guests'],
        notes=data.get('notes', ''),
        user_id=current_user_id,
        restaurant_id=data['restaurant_id'],
        status='pending'
    )
    
    try:
        new_reservation.save_to_db()
        return jsonify({
            'message': 'Reservation created successfully',
            'id': new_reservation.id
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@reservations_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_reservation(id):
    """
    Get reservation details
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Reservation ID
    responses:
      200:
        description: Reservation details
      403:
        description: Permission denied
      404:
        description: Reservation not found
    """
    current_user_id = get_jwt_identity()
    reservation = Reservation.query.get(id)
    
    if not reservation:
        return jsonify({'message': 'Reservation not found'}), 404
    
    # Verificar permisos - solo el usuario que hizo la reserva o el admin del restaurante puede verla
    current_user = User.query.get(current_user_id)
    restaurant = Restaurant.query.get(reservation.restaurant_id)
    
    if (reservation.user_id != current_user_id and 
        restaurant.admin_id != current_user_id and 
        current_user.role != 'admin'):
        return jsonify({'message': 'Permission denied'}), 403
    
    return jsonify({
        'id': reservation.id,
        'date': str(reservation.date),
        'time': str(reservation.time),
        'guests': reservation.guests,
        'status': reservation.status,
        'notes': reservation.notes,
        'user_id': reservation.user_id,
        'restaurant_id': reservation.restaurant_id,
        'created_at': str(reservation.created_at),
        'updated_at': str(reservation.updated_at)
    }), 200

@reservations_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def cancel_reservation(id):
    """
    Cancel a reservation
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Reservation ID
    responses:
      200:
        description: Reservation cancelled successfully
      403:
        description: Permission denied
      404:
        description: Reservation not found
    """
    current_user_id = get_jwt_identity()
    reservation = Reservation.query.get(id)
    
    if not reservation:
        return jsonify({'message': 'Reservation not found'}), 404
    
    # Verificar permisos - solo el usuario que hizo la reserva puede cancelarla
    if reservation.user_id != current_user_id:
        current_user = User.query.get(current_user_id)
        restaurant = Restaurant.query.get(reservation.restaurant_id)
        
        if current_user.role != 'admin' and restaurant.admin_id != current_user_id:
            return jsonify({'message': 'Permission denied'}), 403
    
    # Cambiar estado a 'cancelled' en lugar de eliminar
    reservation.status = 'cancelled'
    
    try:
        reservation.save_to_db()
        return jsonify({'message': 'Reservation cancelled successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@reservations_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_reservations():
    """
    Get all reservations for the authenticated user
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    responses:
      200:
        description: List of user reservations
    """
    current_user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(user_id=current_user_id).all()
    result = []
    
    for reservation in reservations:
        result.append({
            'id': reservation.id,
            'date': str(reservation.date),
            'time': str(reservation.time),
            'guests': reservation.guests,
            'status': reservation.status,
            'notes': reservation.notes,
            'restaurant_id': reservation.restaurant_id,
            'created_at': str(reservation.created_at),
            'updated_at': str(reservation.updated_at)
        })
    
    return jsonify(result), 200

@reservations_bp.route('/restaurant/<int:restaurant_id>', methods=['GET'])
@jwt_required()
def get_restaurant_reservations(restaurant_id):
    """
    Get all reservations for a restaurant
    ---
    tags:
      - Reservations
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
        description: List of restaurant reservations
      403:
        description: Permission denied
      404:
        description: Restaurant not found
    """
    current_user_id = get_jwt_identity()
    restaurant = Restaurant.query.get(restaurant_id)
    
    if not restaurant:
        return jsonify({'message': 'Restaurant not found'}), 404
    
    # Verificar permisos - solo el admin del restaurante puede ver todas las reservas
    current_user = User.query.get(current_user_id)
    if restaurant.admin_id != current_user_id and current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    reservations = Reservation.query.filter_by(restaurant_id=restaurant_id).all()
    result = []
    
    for reservation in reservations:
        result.append({
            'id': reservation.id,
            'date': str(reservation.date),
            'time': str(reservation.time),
            'guests': reservation.guests,
            'status': reservation.status,
            'notes': reservation.notes,
            'user_id': reservation.user_id,
            'created_at': str(reservation.created_at),
            'updated_at': str(reservation.updated_at)
        })
    
    return jsonify(result), 200