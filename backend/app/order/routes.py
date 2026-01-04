from flask import Blueprint, request, jsonify
from app.models import Order, OrderItem, OrderStatus
from .views import create_order, update_order, get_order, get_all_orders

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['POST'])
def create_order_route():
    data = request.get_json()
    order = create_order(data)
    return jsonify(order), 201

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
def update_order_route(order_id):
    data = request.get_json()
    order = update_order(order_id, data)
    return jsonify(order), 200

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order_route(order_id):
    order = get_order(order_id)
    return jsonify(order), 200

@order_bp.route('/orders', methods=['GET'])
def get_all_orders_route():
    orders = get_all_orders()
    return jsonify(orders), 200