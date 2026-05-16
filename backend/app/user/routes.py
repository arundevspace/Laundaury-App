from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.base import db
from app.user.models import User, UserType

user_bp = Blueprint('user', __name__)

VALID_USER_TYPES = [t.value for t in UserType]


@user_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    data = request.get_json() or {}

    required = ['username', 'email', 'password', 'user_type']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    if data['user_type'] not in VALID_USER_TYPES:
        return jsonify({'error': f'Invalid user_type. Must be one of: {VALID_USER_TYPES}'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409
    if data.get('phone') and User.query.filter_by(phone=data['phone']).first():
        return jsonify({'error': 'Phone already registered'}), 409

    user = User(
        username=data['username'],
        email=data['email'],
        phone=data.get('phone'),
        password_hash=generate_password_hash(data['password']),
        user_type=UserType(data['user_type']),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201


@user_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    users = User.query.filter_by(is_active=True).all()
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@user_bp.route('/login', methods=['POST'])
def login():
    """
    Login with username, email, or phone + password.
    Returns a JWT access token valid for 8 hours.
    """
    data = request.get_json() or {}
    identifier = data.get('username') or data.get('email') or data.get('phone')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({'error': 'identifier (username/email/phone) and password are required'}), 400

    user = User.query.filter(
        (User.username == identifier) |
        (User.email == identifier) |
        (User.phone == identifier)
    ).filter_by(is_active=True).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={'user_type': user.user_type.value, 'username': user.username},
    )
    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'user': user.to_dict(),
    }), 200


@user_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify(user.to_dict()), 200
