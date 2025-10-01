from flask import Flask, jsonify
from src.core.config import config

def create_app():
    app = Flask(config.APP_NAME)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=config.DEBUG)