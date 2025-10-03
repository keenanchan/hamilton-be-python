from flask import Flask, jsonify
from src.core.config import config
from src.api.routes_auth import bp_auth

def create_app():
    app = Flask(config.APP_NAME)
    app.register_blueprint(bp_auth)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=config.DEBUG)