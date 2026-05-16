from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.base import db
from app.models.customer import Customer, StateUT, CustomerType

crm_bp = Blueprint('crm', __name__)

VALID_CUSTOMER_TYPES = [t.value for t in CustomerType]


# ── States ────────────────────────────────────────────────────────────────────

@crm_bp.route('/states', methods=['GET'])
def get_states():
    states = StateUT.query.order_by(StateUT.state_name).all()
    return jsonify([{'state_code': s.state_code, 'state_name': s.state_name,
                     'is_union_territory': s.is_union_territory} for s in states]), 200


@crm_bp.route('/states', methods=['POST'])
@jwt_required()
def create_state():
    data = request.get_json() or {}
    if not data.get('state_code') or not data.get('state_name'):
        return jsonify({'error': 'state_code and state_name are required'}), 400
    if StateUT.query.get(data['state_code']):
        return jsonify({'error': 'State already exists'}), 409
    state = StateUT(
        state_code=data['state_code'].upper(),
        state_name=data['state_name'],
        is_union_territory=data.get('is_union_territory', False),
    )
    db.session.add(state)
    db.session.commit()
    return jsonify({'state_code': state.state_code, 'state_name': state.state_name}), 201


# ── Customers ─────────────────────────────────────────────────────────────────

@crm_bp.route('/customers', methods=['GET'])
@jwt_required()
def list_customers():
    customers = Customer.query.filter_by(is_active=True).all()
    return jsonify([_customer_dict(c) for c in customers]), 200


@crm_bp.route('/customers/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    c = Customer.query.get_or_404(customer_id)
    return jsonify(_customer_dict(c)), 200


@crm_bp.route('/customers', methods=['POST'])
@jwt_required()
def create_customer():
    data = request.get_json() or {}

    required = ['name', 'phone', 'customer_type']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    if data['customer_type'] not in VALID_CUSTOMER_TYPES:
        return jsonify({'error': f'customer_type must be one of: {VALID_CUSTOMER_TYPES}'}), 400

    if Customer.query.filter_by(phone=data['phone']).first():
        return jsonify({'error': 'Phone number already registered'}), 409

    customer = Customer(
        customer_type=CustomerType(data['customer_type']),
        name=data['name'],
        phone=data['phone'],
        email=data.get('email'),
        address=data.get('address'),
        state_code=data.get('state_code'),
        gstin=data.get('gstin'),
        billing_cycle=data.get('billing_cycle'),
        tagging_enabled=data.get('tagging_enabled', False),
        credit_limit=data.get('credit_limit'),
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify(_customer_dict(customer)), 201


@crm_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json() or {}

    allowed = ['name', 'email', 'address', 'state_code', 'gstin',
               'billing_cycle', 'tagging_enabled', 'credit_limit', 'is_active']
    for key in allowed:
        if key in data:
            setattr(customer, key, data[key])

    db.session.commit()
    return jsonify(_customer_dict(customer)), 200


@crm_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def deactivate_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.is_active = False
    db.session.commit()
    return jsonify({'message': 'Customer deactivated'}), 200


def _customer_dict(c):
    return {
        'customer_id': c.customer_id,
        'customer_type': c.customer_type.value,
        'name': c.name,
        'phone': c.phone,
        'email': c.email,
        'address': c.address,
        'state_code': c.state_code,
        'gstin': c.gstin,
        'billing_cycle': c.billing_cycle,
        'tagging_enabled': c.tagging_enabled,
        'credit_limit': float(c.credit_limit) if c.credit_limit else None,
        'is_active': c.is_active,
        'created_at': str(c.created_at) if c.created_at else None,
    }
