from flask import Blueprint, request, jsonify
from .models import PickupTask, PickupAgent
from app import db

pickup_bp = Blueprint('pickup', __name__)

@pickup_bp.route('/pickup/tasks', methods=['GET'])
def get_pickup_tasks():
    tasks = PickupTask.query.all()
    return jsonify([task.to_dict() for task in tasks])

@pickup_bp.route('/pickup/tasks', methods=['POST'])
def create_pickup_task():
    data = request.json
    new_task = PickupTask(**data)
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@pickup_bp.route('/pickup/tasks/<int:task_id>', methods=['PUT'])
def update_pickup_task(task_id):
    task = PickupTask.query.get_or_404(task_id)
    data = request.json
    for key, value in data.items():
        setattr(task, key, value)
    db.session.commit()
    return jsonify(task.to_dict())

@pickup_bp.route('/pickup/tasks/<int:task_id>', methods=['DELETE'])
def delete_pickup_task(task_id):
    task = PickupTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'}), 204

@pickup_bp.route('/pickup/agents', methods=['GET'])
def get_pickup_agents():
    agents = PickupAgent.query.all()
    return jsonify([agent.to_dict() for agent in agents])