from flask import Blueprint, request, jsonify
from .models import ProcessingStage, ProcessingItem

processing_bp = Blueprint('processing', __name__)

@processing_bp.route('/stages', methods=['GET'])
def get_processing_stages():
    stages = ProcessingStage.query.all()
    return jsonify([stage.to_dict() for stage in stages])

@processing_bp.route('/stages', methods=['POST'])
def create_processing_stage():
    data = request.json
    new_stage = ProcessingStage(name=data['name'])
    new_stage.save()
    return jsonify(new_stage.to_dict()), 201

@processing_bp.route('/items', methods=['GET'])
def get_processing_items():
    items = ProcessingItem.query.all()
    return jsonify([item.to_dict() for item in items])

@processing_bp.route('/items', methods=['POST'])
def create_processing_item():
    data = request.json
    new_item = ProcessingItem(name=data['name'], stage_id=data['stage_id'])
    new_item.save()
    return jsonify(new_item.to_dict()), 201

@processing_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_processing_item(item_id):
    data = request.json
    item = ProcessingItem.query.get_or_404(item_id)
    item.name = data['name']
    item.stage_id = data['stage_id']
    item.save()
    return jsonify(item.to_dict())

@processing_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_processing_item(item_id):
    item = ProcessingItem.query.get_or_404(item_id)
    item.delete()
    return jsonify({'message': 'Item deleted successfully'}), 204