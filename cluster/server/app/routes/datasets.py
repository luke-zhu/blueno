"""
Routes for handling datasets.
"""
import datetime
import json

import flask
import flask_jwt_extended
import psycopg2

from app import db

datasets_bp = flask.Blueprint('datasets', __name__)


@datasets_bp.route('/datasets/', methods=['GET'])
@flask_jwt_extended.jwt_required
def list_datasets():
    conn = db.get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT name, info, created_at
            FROM datasets
            ORDER BY name;
            """
        )
        results = cur.fetchall()

    datasets = []
    for name, info, created_at in results:
        datasets.append({
            'name': name,
            'info': info,
            'created_at': created_at
        })

    return flask.jsonify({
        'datasets': datasets,
    })


@datasets_bp.route('/datasets/<name>', methods=['PUT'])
@flask_jwt_extended.jwt_required
def create_dataset(name: str) -> flask.Response:
    payload = flask.request.get_json()
    if payload:
        info = payload.get('info', None)
    else:
        info = None

    conn = db.get_conn()
    with conn.cursor() as cur:
        created_at = datetime.datetime.now(datetime.timezone.utc)
        info_json = json.dumps(info)
        try:
            cur.execute(
                """
                INSERT INTO datasets (
                    name,
                    info,
                    created_at)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (name, info_json, created_at)
            )
        except psycopg2.IntegrityError:
            conn.rollback()
            raise db.ConflictException(
                f"Dataset '{name}' already exists.")
        else:
            conn.commit()
            created_id = cur.fetchone()[0]

    return flask.jsonify({
        'id': created_id,
    })


@datasets_bp.route('/datasets/<name>', methods=['DELETE'])
@flask_jwt_extended.jwt_required
def delete_dataset(name: str) -> flask.Response:
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM datasets
                WHERE name = %s
                RETURNING id;
                """,
                (name,)
            )
            conn.commit()
            returned_row = cur.fetchone()
    except psycopg2.IntegrityError:
        raise db.ConflictException(
            f"Samples in '{name}' must be deleted first.")
    if returned_row is None:
        raise db.NotFoundException(f"Dataset '{name}' was not found")

    deleted_id = returned_row[0]
    return flask.jsonify({
        'id': deleted_id,
    })
