from flask import Blueprint, request, jsonify
from .models import Invoice, Payment
from .views import create_invoice, get_invoice, record_payment

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/invoices', methods=['POST'])
def add_invoice():
    data = request.get_json()
    invoice = create_invoice(data)
    return jsonify(invoice), 201

@sales_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
def fetch_invoice(invoice_id):
    invoice = get_invoice(invoice_id)
    if invoice:
        return jsonify(invoice), 200
    return jsonify({'message': 'Invoice not found'}), 404

@sales_bp.route('/payments', methods=['POST'])
def add_payment():
    data = request.get_json()
    payment = record_payment(data)
    return jsonify(payment), 201