from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.inventory.views import (
    create_inward, scan_inward_item, complete_inward,
    get_inward, list_inwards,
)

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inward', methods=['GET'])
@jwt_required()
def list_inwards_route():
    warehouse_id = request.args.get('warehouse_id', type=int)
    completed = request.args.get('completed')
    if completed is not None:
        completed = completed.lower() == 'true'
    result, status_code = list_inwards(warehouse_id=warehouse_id, completed=completed)
    return jsonify(result), status_code


@inventory_bp.route('/inward', methods=['POST'])
@jwt_required()
def create_inward_route():
    """
    Open an inward session once pickup bags arrive at the warehouse.
    Requires pickup_id (must be COMPLETED) and warehouse_id.
    """
    data = request.get_json() or {}
    operator_id = int(get_jwt_identity())
    result, status_code = create_inward(data, operator_id)
    return jsonify(result), status_code


@inventory_bp.route('/inward/<int:inward_id>', methods=['GET'])
@jwt_required()
def get_inward_route(inward_id):
    result, status_code = get_inward(inward_id)
    return jsonify(result), status_code


@inventory_bp.route('/inward/<int:inward_id>/scan', methods=['POST'])
@jwt_required()
def scan_item(inward_id):
    """
    Warehouse staff scans a barcode to mark a garment as received.
    Response tells you whether the barcode was expected in this pickup.
    """
    data = request.get_json() or {}
    if not data.get('barcode'):
        return jsonify({'error': 'barcode is required'}), 400

    result, status_code = scan_inward_item(
        inward_id,
        barcode=data['barcode'],
        condition_notes=data.get('condition_notes'),
        is_received=data.get('is_received', True),
    )
    return jsonify(result), status_code


@inventory_bp.route('/inward/<int:inward_id>/complete', methods=['POST'])
@jwt_required()
def complete_inward_route(inward_id):
    """
    Finalise the inward. Un-scanned items are counted as missing.
    After completion, the inward is locked and processing can begin.
    """
    result, status_code = complete_inward(inward_id)
    return jsonify(result), status_code
