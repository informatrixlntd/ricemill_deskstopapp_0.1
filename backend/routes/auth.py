from flask import Blueprint, request, jsonify
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """User login endpoint with proper connection management"""
    conn = None
    cursor = None
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
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/api/users', methods=['GET'])
def get_users():
    """Get all users - proper connection management"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
            SELECT id, username, full_name, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')

        users = cursor.fetchall()

        # Format datetime objects for JSON serialization
        for user in users:
            if user.get('created_at'):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if user.get('last_login'):
                user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'success': True,
            'users': users
        }), 200

    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/api/users', methods=['POST'])
def add_user():
    """
    Add new user
    Admin-only operation (should be checked on frontend)
    """
    conn = None
    cursor = None
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'user')
        requesting_user_role = data.get('requesting_user_role', 'user')

        # Backend admin check
        if requesting_user_role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Only administrators can add users'
            }), 403

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 400

        cursor.execute('''
            INSERT INTO users (username, password, full_name, role)
            VALUES (%s, %s, %s, %s)
        ''', (username, password, full_name, role))

        user_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User created successfully'
        }), 201

    except Exception as e:
        print(f"Error adding user: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user
    Admin-only operation
    """
    conn = None
    cursor = None
    try:
        data = request.json
        full_name = data.get('full_name', '').strip()
        role = data.get('role', 'user')
        is_active = data.get('is_active', True)
        password = data.get('password', '').strip()
        requesting_user_role = data.get('requesting_user_role', 'user')

        # Backend admin check
        if requesting_user_role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Only administrators can update users'
            }), 403

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

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        }), 200

    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete user (soft delete by setting is_active to FALSE)
    Admin-only operation
    """
    conn = None
    cursor = None
    try:
        data = request.json or {}
        requesting_user_role = data.get('requesting_user_role', 'user')

        # Backend admin check
        if requesting_user_role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Only administrators can delete users'
            }), 403

        # Prevent deleting the last admin
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if this is the last admin
        cursor.execute('''
            SELECT COUNT(*) as admin_count
            FROM users
            WHERE role = 'admin' AND is_active = TRUE
        ''')
        admin_count = cursor.fetchone()['admin_count']

        cursor.execute('SELECT role FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()

        if user and user['role'] == 'admin' and admin_count <= 1:
            return jsonify({
                'success': False,
                'message': 'Cannot delete the last administrator'
            }), 400

        cursor.execute('''
            UPDATE users SET is_active = FALSE WHERE id = %s
        ''', (user_id,))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        }), 200

    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
