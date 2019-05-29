"""
Routes for handling individual samples.
"""
import datetime
import json
from typing import Dict

import flask
import flask_jwt_extended
import psycopg2

from app import db, storage, env
from app import image

samples_bp = flask.Blueprint('samples', __name__)


@samples_bp.route('/datasets/<dataset_name>/samples/')
@flask_jwt_extended.jwt_required
def list_samples(dataset_name):
    # 1. Parse params
    params = flask.request.args
    limit = params.get('limit', None)
    offset = params.get('offset', 0)
    prefix = params.get('prefix', '')
    label = params.get('label', '')
    split = params.get('split', '')

    # 2. Query the database
    # Duplication in sample_images
    conn = db.get_conn()
    prefix_pattern = prefix + '%'
    with conn.cursor() as cur:
        # Performance note: not doing a join reduces the query cost from
        # 2-5 seconds to less than 20 ms
        dataset_id = db.dataset_id(cur, dataset_name)

        cur.execute(
            """
            SELECT s.name, s.info, s.created_at, s.last_updated
            FROM samples AS s
            WHERE s.dataset_id = %s
              AND s.name ILIKE %s
              AND (%s = '' OR s.info->>'label' = %s)
              AND (%s = '' OR s.info->>'split' = %s)
            ORDER BY s.id
            LIMIT %s OFFSET %s;
            """,
            (dataset_id,
             prefix_pattern,
             label, label,
             split, split,
             limit, offset)
        )
        results = cur.fetchall()

    samples = []
    for row in results:
        samples.append({
            'name': row[0],
            'info': row[1],
            'created_at': row[2],
            'last_updated': row[3],
        })

    return flask.jsonify({
        'samples': samples,
    })


@samples_bp.route('/datasets/<dataset_name>/samples/count')
@flask_jwt_extended.jwt_required
def count_samples(dataset_name):
    conn = db.get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
            FROM samples AS s
            JOIN datasets AS d
            ON s.dataset_id = d.id
            WHERE d.name = %s;
            """,
            (dataset_name,)
        )
        result = cur.fetchone()
    if result is None:
        raise db.NotFoundException(f"Dataset '{dataset_name}' was not found")

    count = int(result[0])
    return flask.jsonify({
        'count': count,
    })


@samples_bp.route('/datasets/<dataset_name>/samples/<name>', methods=['PUT'])
@flask_jwt_extended.jwt_required
def register_sample(dataset_name, name):
    # 1. Validate the payload
    payload = flask.request.get_json()

    if payload is None:
        return flask.jsonify({
            'message': 'No JSON payload found. Cannot register the sample'
        }), 400

    info = payload.get('info', None)

    if info is None:
        return flask.jsonify({
            'message': 'No info object found. Cannot register the sample'
        }), 400
    if 'data' not in info:
        return flask.jsonify({
            'message': 'No data field found in info.'
                       ' Cannot register the sample.'
        }), 400
    if 'url' not in info['data']:
        return flask.jsonify({
            'message': 'No url field found in info["data"].'
                       ' Cannot register the sample.'
        }), 400

    # 2. Check whether the sample exists at the given data_url
    data_url: str = info['data']['url']

    if payload.get('validate', True):
        try:
            client = storage.get_storage_client(
                data_url)
        except ValueError:
            return flask.jsonify({
                'message': f'Cannot find valid storage client for {data_url}.'
                ' Validation failed.'
            }), 400
        if not client.exists(data_url):
            return flask.jsonify({
                'message': f'No data was found at info["data"]={data_url}.'
                ' Validation failed.'
            }), 400

    # 3. Update info['info']
    if 'image' in info:
        image_type = info['image'].get('type', None)
        if image_type is None:
            return flask.jsonify({
                'message': 'No type field found in info["image"].'
                           ' Cannot make an image of the sample.'
            }), 400
        # TODO: Allow users to define their own image url root through the
        #  admin page
        if env.FILESYSTEM_STORE_ROOT is None:
            return flask.jsonify({
                'message': 'Filesystem store not enabled, not creating images.'
            }), 400
        image_url = f'file://images/{dataset_name}/{name}'
        info['image']['url'] = image_url
        info['image']['status'] = 'CREATING'
        # We create the images once we know the sample ID
    elif data_url.startswith((storage.clients.AZURE_PREFIX,
                              storage.clients.GCS_PREFIX)) \
            and data_url.lower().endswith(('.png', '.jpg', '.jpeg')):
        info['image'] = {
            'url': data_url,
            'type': 'FROM_DATA',
            'status': 'CREATED',
        }

    # 4. Register the sample in the database
    conn = db.get_conn()
    created_at = datetime.datetime.now(datetime.timezone.utc)
    info_json = json.dumps(info)

    with conn.cursor() as cur:
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
            raise db.NotFoundException(f"Dataset '{dataset_name}' not found")
        dataset_id = result[0]

        try:
            cur.execute(
                """
                INSERT INTO samples (
                    name,
                    info,
                    dataset_id,
                    created_at,
                    last_updated)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (name,
                 info_json,
                 dataset_id,
                 created_at,
                 created_at)
            )
        except psycopg2.IntegrityError:
            conn.rollback()
            raise db.ConflictException(f"Sample '{name}' already exists.")
        else:
            conn.commit()
            sample_id = cur.fetchone()[0]

    # 5. Create the image now or queue a job to create the image
    if ('image' in info
            and info['image']['status'] == 'CREATING'
            and data_url.startswith(storage.clients.FILESYSTEM_PREFIX)):
        if info['image']['type'] == '2D':
            image.create_images(sample_id)
        else:
            image.enqueue_create_images(sample_id)

    return flask.jsonify({
        'id': sample_id,
    })


@samples_bp.route('/datasets/<dataset_name>/samples/<name>',
                  methods=['DELETE'])
@flask_jwt_extended.jwt_required
def delete_sample(dataset_name, name):
    payload = flask.request.json
    conn = db.get_conn()

    if payload and payload.get('purge', None):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.info
                FROM samples AS s
                JOIN datasets AS d
                ON s.dataset_id = d.id
                WHERE s.name = %s AND d.name = %s;
                """,
                (name, dataset_name)
            )
            row = cur.fetchone()
            if row is None:
                raise db.NotFoundException(f"Could not find sample '{name}'")
            info = row[0]
        data_info: Dict = info['data']
        data_url: str = data_info['url']
        storage_client = storage.get_storage_client(data_url)
        storage_client.delete(data_url)

    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM samples
            WHERE name = %s AND dataset_id = (
                SELECT id
                FROM datasets
                WHERE name = %s
            )
            RETURNING id;
            """,
            (name, dataset_name)
        )
        conn.commit()
        returned_row = cur.fetchone()
    if returned_row is None:
        raise db.NotFoundException(f"Sample '{name}' was not found")

    deleted_id = returned_row[0]
    return flask.jsonify({
        'id': deleted_id,
    })
