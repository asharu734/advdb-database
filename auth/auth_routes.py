from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from auth.jwt_utils import create_token
from database import get_user_by_username  # You’ll need to implement this

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        token = create_token({"username": username})
        return jsonify({"access_token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401
