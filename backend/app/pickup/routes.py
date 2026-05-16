from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.pickup.views import (
    create_pickup_task, start_pickup, add_pickup_item,
    complete_pickup, get_pickup,
)
from app.models.pickup import PickupItem

pickup_bp = Blueprint('pickup', __name__)


@pickup_bp.route('/orders/<int:order_id>/pickup', methods=['POST'])
@jwt_required()
def create_pickup(order_id):
    data = request.get_json() or {}
    result, status_code = create_pickup_task(order_id, data)
    return jsonify(result), status_code


@pickup_bp.route('/pickups/<int:pickup_id>', methods=['GET'])
@jwt_required()
def get_pickup_route(pickup_id):
    result, status_code = get_pickup(pickup_id)
    return jsonify(result), status_code


@pickup_bp.route('/pickups/<int:pickup_id>/start', methods=['POST'])
@jwt_required()
def start_pickup_route(pickup_id):
    result, status_code = start_pickup(pickup_id)
    return jsonify(result), status_code


@pickup_bp.route('/pickups/<int:pickup_id>/items', methods=['POST'])
@jwt_required()
def add_item(pickup_id):
    """
    Scan a garment barcode to add it to the pickup and assign a permanent tag.
    If the barcode is new, a ReusableItemTag is created (one-time, stays with garment forever).
    If the barcode already exists, it is reused.
    """
    data = request.get_json() or {}
    result, status_code = add_pickup_item(pickup_id, data)
    return jsonify(result), status_code


@pickup_bp.route('/pickups/<int:pickup_id>/items', methods=['GET'])
@jwt_required()
def list_items(pickup_id):
    items = PickupItem.query.filter_by(pickup_id=pickup_id).all()
    return jsonify([i.to_dict() for i in items]), 200


@pickup_bp.route('/pickups/<int:pickup_id>/complete', methods=['POST'])
@jwt_required()
def complete_pickup_route(pickup_id):
    data = request.get_json() or {}
    result, status_code = complete_pickup(pickup_id, bag_count=data.get('bag_count'))
    return jsonify(result), status_code
