from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base import db
from app.user.models import User, UserType

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')  # Use pbkdf2:sha256
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        user_type=data.get('user_type', UserType.CUSTOMER),
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details by ID."""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@user_bp.route('/users/login', methods=['POST'])
def login_user():
    """Authenticate a user."""
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

@user_bp.route('/users/logout', methods=['POST'])
def logout_user():
    """Log out the current user."""
    if 'user_id' in session:
        session.clear()  # Clear all session data
        return jsonify({'message': 'Logout successful'}), 200
    return jsonify({'message': 'No user is currently logged in'}), 400