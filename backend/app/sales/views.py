from flask import Blueprint, request, jsonify
from .models import Invoice, Payment
from app import db

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/invoices', methods=['POST'])
def create_invoice():
    data = request.get_json()
    new_invoice = Invoice(**data)
    db.session.add(new_invoice)
    db.session.commit()
    return jsonify(new_invoice.to_dict()), 201

@sales_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify(invoice.to_dict())

@sales_bp.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    new_payment = Payment(**data)
    db.session.add(new_payment)
    db.session.commit()
    return jsonify(new_payment.to_dict()), 201

@sales_bp.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return jsonify(payment.to_dict())