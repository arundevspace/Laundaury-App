from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from app.models.base import db
from app.core.config import Config

load_dotenv()


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Init extensions
    db.init_app(flask_app)
    Migrate(flask_app, db)
    JWTManager(flask_app)

    # Import all models so Flask-Migrate sees every table
    from app import models as _models  # noqa: F401

    # Register blueprints
    from app.user.routes import user_bp
    from app.crm.routes import crm_bp
    from app.order.routes import order_bp
    from app.pickup.routes import pickup_bp
    from app.inventory.routes import inventory_bp
    from app.delivery.routes import delivery_bp
    from app.processing.routes import processing_bp
    from app.sales.routes import sales_bp

    flask_app.register_blueprint(user_bp, url_prefix="/user")
    flask_app.register_blueprint(crm_bp, url_prefix="/crm")
    flask_app.register_blueprint(order_bp, url_prefix="")
    flask_app.register_blueprint(pickup_bp, url_prefix="")
    flask_app.register_blueprint(inventory_bp, url_prefix="/inventory")
    flask_app.register_blueprint(delivery_bp, url_prefix="/deliveries")
    flask_app.register_blueprint(processing_bp, url_prefix="/processing")
    flask_app.register_blueprint(sales_bp, url_prefix="/sales")

    @flask_app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK", "phase": "1"}), 200

    return flask_app
