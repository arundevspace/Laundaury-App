from flask import Blueprint, request, jsonify
from .models import StockItem, StockMovement
from app import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory/items', methods=['GET'])
def get_stock_items():
    items = StockItem.query.all()
    return jsonify([item.to_dict() for item in items]), 200

@inventory_bp.route('/inventory/items', methods=['POST'])
def add_stock_item():
    data = request.json
    new_item = StockItem(name=data['name'], quantity=data['quantity'])
    db.session.add(new_item)
    db.session.commit()
    return jsonify(new_item.to_dict()), 201

@inventory_bp.route('/inventory/items/<int:item_id>', methods=['PUT'])
def update_stock_item(item_id):
    data = request.json
    item = StockItem.query.get_or_404(item_id)
    item.name = data['name']
    item.quantity = data['quantity']
    db.session.commit()
    return jsonify(item.to_dict()), 200

@inventory_bp.route('/inventory/items/<int:item_id>', methods=['DELETE'])
def delete_stock_item(item_id):
    item = StockItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted'}), 204

@inventory_bp.route('/inventory/movements', methods=['POST'])
def record_stock_movement():
    data = request.json
    movement = StockMovement(item_id=data['item_id'], quantity=data['quantity'], movement_type=data['movement_type'])
    db.session.add(movement)
    db.session.commit()
    return jsonify(movement.to_dict()), 201