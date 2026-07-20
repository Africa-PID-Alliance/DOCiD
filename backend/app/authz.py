"""Reusable database-backed authorization helpers for Flask routes."""

from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import UserAccount


ADMIN_ROLE = "admin"
PID_MINTER_ROLE = "pid_minter"


def _current_database_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return db.session.get(UserAccount, user_id)


def database_user_required(function):
    """Require that the JWT still maps to an existing database account."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = _current_database_user()
        if user is None:
            return jsonify({"error": "Authenticated user not found"}), 401
        g.current_user = user
        return function(*args, **kwargs)

    return wrapper


def owner_or_admin_required(parameter="user_id"):
    """Authorize a path-bound user ID against the current DB user or admin."""
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            user = _current_database_user()
            if user is None:
                return jsonify({"error": "Authenticated user not found"}), 401
            try:
                target_user_id = int(kwargs.get(parameter))
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid user identifier"}), 400
            if user.user_id != target_user_id and user.role != ADMIN_ROLE:
                return jsonify({"error": "Forbidden"}), 403
            g.current_user = user
            return function(*args, **kwargs)

        return wrapper
    return decorator


def roles_required(*allowed_roles):
    """Require the authenticated JWT user to have one of ``allowed_roles``.

    This decorator deliberately reads the current role from the database instead
    of trusting a role claim that may be stale or client-controlled. It must be
    placed below ``@jwt_required()`` on a route.
    """

    normalized_roles = {str(role).strip().lower() for role in allowed_roles}

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            user = _current_database_user()
            if user is None:
                return jsonify({"error": "Authenticated user not found"}), 401

            role = (user.role or "user").strip().lower()
            if role not in normalized_roles:
                return jsonify({"error": "Insufficient permissions"}), 403

            g.current_user = user
            return function(*args, **kwargs)

        return wrapper

    return decorator


admin_required = roles_required(ADMIN_ROLE)
pid_minter_required = roles_required(PID_MINTER_ROLE, ADMIN_ROLE)
