from flask import Blueprint, request, jsonify
from jwt_utils import generate_token
from utils import get_db_connection, hash_password, check_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password(password, user['password']):
        token = generate_token(user['user_id'], user['role'])
        return jsonify({'token': token, 'role': user['role']}), 200
    return jsonify({'error': 'Invalid credentials'}), 401
