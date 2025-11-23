from flask import Blueprint, request, jsonify
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
            SELECT id, username, full_name, role, is_active
            FROM users
            WHERE username = %s AND password = %s AND is_active = TRUE
        ''', (username, password))

        user = cursor.fetchone()

        if user:
            cursor.execute('''
                UPDATE users SET last_login = %s WHERE id = %s
            ''', (datetime.now(), user['id']))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'role': user['role']
                }
            }), 200
        else:
            cursor.close()
            conn.close()

            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
            SELECT id, username, full_name, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')

        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'users': users
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/api/users', methods=['POST'])
def add_user():
    """Add new user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'user')

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (username, password, full_name, role)
            VALUES (%s, %s, %s, %s)
        ''', (username, password, full_name, role))

        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User created successfully'
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user"""
    try:
        data = request.json
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'user')
        is_active = data.get('is_active', True)
        password = data.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        if password:
            cursor.execute('''
                UPDATE users
                SET full_name = %s, role = %s, is_active = %s, password = %s
                WHERE id = %s
            ''', (full_name, role, is_active, password, user_id))
        else:
            cursor.execute('''
                UPDATE users
                SET full_name = %s, role = %s, is_active = %s
                WHERE id = %s
            ''', (full_name, role, is_active, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user (soft delete by setting is_active to FALSE)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users SET is_active = FALSE WHERE id = %s
        ''', (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
