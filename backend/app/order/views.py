from flask import Blueprint, request, jsonify
from .models import Order, OrderItem, OrderStatus
from app import db

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    new_order = Order(customer_id=data['customer_id'], status=OrderStatus.PENDING)
    db.session.add(new_order)
    db.session.commit()
    
    for item in data['items']:
        order_item = OrderItem(order_id=new_order.id, product_id=item['product_id'], quantity=item['quantity'])
        db.session.add(order_item)
    
    db.session.commit()
    return jsonify({'message': 'Order created successfully', 'order_id': new_order.id}), 201

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict()), 200

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    order = Order.query.get_or_404(order_id)
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify({'message': 'Order updated successfully'}), 200

@order_bp.route('/orders', methods=['GET'])
def list_orders():
    orders = Order.query.all()
    return jsonify([order.to_dict() for order in orders]), 200