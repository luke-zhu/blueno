"""
Application database-layer.

All database queries should be made in this module to make
it easier to handle schema changes or improve performance.
"""
import pathlib

import flask
import psycopg2

from app import env


class ConflictException(Exception):
    def __init__(self, message, status_code=409):
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {'message': self.message}


class NotFoundException(Exception):
    def __init__(self, message, status_code=404):
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {'message': self.message}


def get_conn():
    if 'db' not in flask.g:
        flask.g.db = psycopg2.connect(**env.POSTGRES_CONFIG)
    return flask.g.db


def close_conn(e=None):
    # teardown_appcontext requires close_conn to have a positional argument
    db = flask.g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    conn = psycopg2.connect(**env.POSTGRES_CONFIG)
    with conn.cursor() as cursor:
        schema_path = (pathlib.Path(__file__) / '..' / 'schema.sql').resolve()
        cursor.execute(open(schema_path).read())
    conn.commit()


def dataset_id(cur, dataset_name):
    cur.execute(
        """
        SELECT id
        FROM datasets
        WHERE name = %s;
        """,
        (dataset_name,)
    )
    result = cur.fetchone()
    if result is None:
        raise NotFoundException(f"Dataset '{dataset_name}' was not found")
    return result[0]
