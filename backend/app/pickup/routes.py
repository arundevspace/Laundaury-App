from flask import Blueprint, request, jsonify
from .models import PickupTask, PickupAgent
from .views import create_pickup_task, update_pickup_task, get_pickup_tasks

pickup_bp = Blueprint('pickup', __name__)

@pickup_bp.route('/pickup', methods=['POST'])
def add_pickup():
    data = request.get_json()
    return create_pickup_task(data)

@pickup_bp.route('/pickup/<int:task_id>', methods=['PUT'])
def modify_pickup(task_id):
    data = request.get_json()
    return update_pickup_task(task_id, data)

@pickup_bp.route('/pickup', methods=['GET'])
def list_pickups():
    return get_pickup_tasks()