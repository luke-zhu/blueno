"""
User authentication related code.

We use JSON web tokens to login users. Routes with the decorator
@flask_jwt_extended only accepts HTTP requests with an
"Authorization: Bearer" token. See api.js for how you can properly set
the token.
"""
import datetime

import flask
import flask_jwt_extended
from werkzeug import security

from app import db

auth_bp = flask.Blueprint('auth', __name__)


@auth_bp.route('/refresh', methods=['POST'])
@flask_jwt_extended.jwt_refresh_token_required
def refresh():
    user_id = flask_jwt_extended.get_jwt_identity()
    access_token = flask_jwt_extended.create_access_token(identity=user_id)
    return flask.json.jsonify(access_token=access_token), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    # Payload validation copied in /setup
    if not flask.request.is_json:
        return flask.jsonify({'message': "Missing JSON in request"}), 400

    body = flask.request.json
    request_email = body.get('email', None)
    request_password = body.get('password', None)
    if not request_email:
        return flask.jsonify({'message': "Missing email parameter"}), 400
    if not request_password:
        return flask.jsonify({'message': "Missing password parameter"}), 400

    conn = db.get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
                    SELECT id, pwhash
                    FROM users
                    WHERE email = %s;
                    """,
            (request_email,)
        )
        result = cur.fetchone()
    if result is None:
        raise db.NotFoundException(
            f"User with email '{request_email}' not found")
    user_id, db_pwhash = result

    if not security.check_password_hash(db_pwhash, request_password):
        return flask.jsonify({'message': 'Invalid password'}), 400

    access_token = flask_jwt_extended.create_access_token(identity=user_id)
    refresh_token = flask_jwt_extended.create_refresh_token(identity=user_id)
    return flask.json.jsonify(access_token=access_token,
                              refresh_token=refresh_token), 200


@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    conn = db.get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM users;
            """,
        )
        result = cur.fetchone()
    user_count = result[0]

    if flask.request.method == 'GET':
        return flask.jsonify({
            'initialized': user_count > 0,
        })
    elif flask.request.method == 'POST':
        if user_count > 0:
            return flask.jsonify(
                {'message': "A user was already created"}), 400

        # Payload validation copied from /login
        if not flask.request.is_json:
            return flask.jsonify({'message': "Missing JSON in request"}), 400

        body = flask.request.json
        email = body.get('email', None)
        password = body.get('password', None)
        if not email:
            return flask.jsonify({'message': "Missing email parameter"}), 400
        if not password:
            return flask.jsonify(
                {'message': "Missing password parameter"}), 400

        created_at = datetime.datetime.now(datetime.timezone.utc)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, pwhash, created_at)
                VALUES (%s, %s, %s);
                """,
                (email, security.generate_password_hash(password), created_at)
            )
        conn.commit()
        return flask.jsonify({})
