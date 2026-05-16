from flask import Flask, jsonify, send_from_directory
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from app.models.base import db
from app.core.config import Config

load_dotenv()


def create_app():
    flask_app = Flask(__name__, static_folder='static')
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

    # ── Swagger UI ────────────────────────────────────────────────────────────
    @flask_app.route("/openapi.yaml")
    def openapi_spec():
        return send_from_directory(flask_app.static_folder, "openapi.yaml",
                                   mimetype="application/yaml")

    @flask_app.route("/docs")
    def swagger_ui():
        return """<!DOCTYPE html>
<html>
<head>
  <title>Laundry API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  SwaggerUIBundle({
    url: "/openapi.yaml",
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "BaseLayout",
    deepLinking: true,
    persistAuthorization: true,
  })
</script>
</body>
</html>"""

    # ── Health ────────────────────────────────────────────────────────────────
    @flask_app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK", "phase": "1"}), 200

    return flask_app
