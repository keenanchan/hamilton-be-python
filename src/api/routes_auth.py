from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from src.db.base import get_db
from src.services.auth_service import AuthService
from src.db.models import ProviderEnum


bp_auth = Blueprint("auth", __name__, url_prefix="/auth")
auth_service = AuthService()


@bp_auth.route("/login", methods=["POST"])
def login():
    db: Session = next(get_db())
    data = request.get_json(force=True) or {}
    identifier = data.get("identifier")
    password = data.get("password")
    provider = data.get("provider")

    # Corece provider string to enum if given (ignore invalid)
    provider_enum = None
    if provider:
        try:
            provider_enum = ProviderEnum(provider)
        except ValueError:
            provider_enum = None
    
    token = auth_service.login(
        db,
        identifier=identifier,
        password=password,
        provider=provider_enum,
    )

    if not token: return jsonify({"details": "Invalid credentials"}), 401
    return jsonify({"access_token": token, "token_type": "bearer"})