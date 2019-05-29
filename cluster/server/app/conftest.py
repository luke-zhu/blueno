import datetime
import random
import string
from typing import Tuple

import psycopg2
import pytest
import testing.postgresql
from werkzeug import security

from app import env, db


@pytest.fixture(scope='session')
def test_user() -> Tuple[str, str]:
    created_at = datetime.datetime.now(datetime.timezone.utc)
    test_email = f"test-{created_at.utcnow()}"
    test_password = ''.join(random.choice(string.ascii_letters)
                            for _ in range(24))
    pwd_hash = security.generate_password_hash(test_password)

    # Initialize a testing database if env vars not defined
    if not env.POSTGRES_CONFIG:
        postgresql = testing.postgresql.Postgresql()
        env.POSTGRES_CONFIG = postgresql.dsn()
        db.init_db()

    conn = psycopg2.connect(**env.POSTGRES_CONFIG)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, pwhash, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (test_email, pwd_hash, created_at)
        )
        conn.commit()

    yield test_email, test_password

    # Clean up the database
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM samples
            WHERE dataset_id IN (
                SELECT datasets.id
                FROM datasets
                WHERE datasets.name ILIKE %s);
            """,
            ('test%',)
        )

        cur.execute(
            """
            DELETE FROM datasets
            WHERE datasets.name ILIKE %s;
            """,
            ('test%',)
        )

        cur.execute(
            """
            DELETE FROM users
            WHERE email = %s;
            """,
            (test_email,)
        )
        conn.commit()
