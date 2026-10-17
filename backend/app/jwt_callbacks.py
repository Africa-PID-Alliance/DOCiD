"""JWT error responses shared by every protected route."""

from flask import jsonify


def register_jwt_callbacks(jwt_manager):
    @jwt_manager.invalid_token_loader
    def invalid_token_response(reason):
        # flask_jwt_extended answers malformed or wrongly signed tokens with 422.
        # Use 401 like expired tokens, so the frontend refreshes or signs the
        # user out instead of staying "logged in" while every request fails.
        return jsonify(msg=reason), 401
