from flask import Flask
from app.core.config import Config
from app.core.database import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    db.init_app(app)

    # Register blueprints
    # from app.crm.routes import crm_bp
    # from app.order.routes import order_bp
    # from app.pickup.routes import pickup_bp
    # from app.delivery.routes import delivery_bp
    # from app.processing.routes import processing_bp
    # from app.inventory.routes import inventory_bp
    # from app.sales.routes import sales_bp

    # app.register_blueprint(crm_bp, url_prefix="/crm")
    # app.register_blueprint(order_bp, url_prefix="/orders")
    # app.register_blueprint(pickup_bp, url_prefix="/pickups")
    # app.register_blueprint(delivery_bp, url_prefix="/deliveries")
    # app.register_blueprint(processing_bp, url_prefix="/processing")
    # app.register_blueprint(inventory_bp, url_prefix="/inventory")
    # app.register_blueprint(sales_bp, url_prefix="/sales")

    return app
