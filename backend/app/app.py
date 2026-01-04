from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from app.crm.views import crm_bp
from app.order.routes import order_bp
from app.user.routes import user_bp
from app.models.base import db 
from dotenv import load_dotenv
import os
from app.core.config import Config

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    db.init_app(app)
    Migrate(app, db)


    # Register blueprints

    # from app.crm.routes import crm_bp
    from app.order.routes import order_bp
    from app.user.routes import user_bp
    # from app.pickup.routes import pickup_bp
    # from app.delivery.routes import delivery_bp
    # from app.processing.routes import processing_bp
    # from app.inventory.routes import inventory_bp
    # from app.sales.routes import sales_bp
    app.register_blueprint(user_bp, url_prefix="/user")  # Ensure this is registered
    # app.register_blueprint(crm_bp, url_prefix="/crm")
    app.register_blueprint(order_bp, url_prefix="/orders")
    # app.register_blueprint(pickup_bp, url_prefix="/pickups")
    # app.register_blueprint(delivery_bp, url_prefix="/deliveries")
    # app.register_blueprint(processing_bp, url_prefix="/processing")
    # app.register_blueprint(inventory_bp, url_prefix="/inventory")
    # app.register_blueprint(sales_bp, url_prefix="/sales")

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK"}), 200

    return app
