from flask import Blueprint, request, jsonify
from .models import Customer, Interaction
from .views import create_customer, update_customer, get_customer, get_all_customers

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    customer = create_customer(data)
    return jsonify(customer), 201

@crm_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def modify_customer(customer_id):
    data = request.get_json()
    customer = update_customer(customer_id, data)
    return jsonify(customer), 200

@crm_bp.route('/customers/<int:customer_id>', methods=['GET'])
def retrieve_customer(customer_id):
    customer = get_customer(customer_id)
    return jsonify(customer), 200

@crm_bp.route('/customers', methods=['GET'])
def list_customers():
    customers = get_all_customers()
    return jsonify(customers), 200