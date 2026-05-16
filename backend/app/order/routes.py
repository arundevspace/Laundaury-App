from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.order.views import create_order, get_order, get_all_orders, update_order_status

order_bp = Blueprint('order', __name__)


@order_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order_route():
    data = request.get_json() or {}
    created_by = int(get_jwt_identity())
    result, status_code = create_order(data, created_by)
    return jsonify(result), status_code


@order_bp.route('/orders', methods=['GET'])
@jwt_required()
def list_orders():
    customer_id = request.args.get('customer_id', type=int)
    status = request.args.get('status')
    result, status_code = get_all_orders(customer_id=customer_id, status=status)
    return jsonify(result), status_code


@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_route(order_id):
    result, status_code = get_order(order_id)
    return jsonify(result), status_code


@order_bp.route('/orders/<int:order_id>/status', methods=['PATCH'])
@jwt_required()
def update_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status', '').upper()
    result, status_code = update_order_status(order_id, new_status)
    return jsonify(result), status_code
