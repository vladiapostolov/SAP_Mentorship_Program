from flask import Flask 
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.inventory_routes import inventory_bp
from routes.scan_routes import scan_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(scan_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
