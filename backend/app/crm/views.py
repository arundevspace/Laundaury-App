from flask import Blueprint, request, jsonify
from .models import Customer, Interaction
from app import db

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    new_customer = Customer(name=data['name'], email=data['email'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'Customer created', 'customer_id': new_customer.id}), 201

@crm_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({'id': customer.id, 'name': customer.name, 'email': customer.email})

@crm_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    customer = Customer.query.get_or_404(customer_id)
    customer.name = data['name']
    customer.email = data['email']
    db.session.commit()
    return jsonify({'message': 'Customer updated'})

@crm_bp.route('/customers/<int:customer_id>/interactions', methods=['POST'])
def add_interaction(customer_id):
    data = request.get_json()
    new_interaction = Interaction(customer_id=customer_id, notes=data['notes'])
    db.session.add(new_interaction)
    db.session.commit()
    return jsonify({'message': 'Interaction added', 'interaction_id': new_interaction.id}), 201

@crm_bp.route('/customers/<int:customer_id>/interactions', methods=['GET'])
def get_interactions(customer_id):
    interactions = Interaction.query.filter_by(customer_id=customer_id).all()
    return jsonify([{'id': interaction.id, 'notes': interaction.notes} for interaction in interactions])