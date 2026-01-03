from flask import Blueprint, request, jsonify
from .models import DeliveryTask, DeliveryAgent

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route('/tasks', methods=['GET'])
def get_delivery_tasks():
    tasks = DeliveryTask.query.all()
    return jsonify([task.to_dict() for task in tasks])

@delivery_bp.route('/tasks', methods=['POST'])
def create_delivery_task():
    data = request.json
    new_task = DeliveryTask(**data)
    new_task.save()
    return jsonify(new_task.to_dict()), 201

@delivery_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_delivery_task(task_id):
    task = DeliveryTask.query.get_or_404(task_id)
    data = request.json
    for key, value in data.items():
        setattr(task, key, value)
    task.save()
    return jsonify(task.to_dict())

@delivery_bp.route('/agents', methods=['GET'])
def get_delivery_agents():
    agents = DeliveryAgent.query.all()
    return jsonify([agent.to_dict() for agent in agents])

@delivery_bp.route('/agents', methods=['POST'])
def create_delivery_agent():
    data = request.json
    new_agent = DeliveryAgent(**data)
    new_agent.save()
    return jsonify(new_agent.to_dict()), 201

@delivery_bp.route('/agents/<int:agent_id>', methods=['PUT'])
def update_delivery_agent(agent_id):
    agent = DeliveryAgent.query.get_or_404(agent_id)
    data = request.json
    for key, value in data.items():
        setattr(agent, key, value)
    agent.save()
    return jsonify(agent.to_dict())