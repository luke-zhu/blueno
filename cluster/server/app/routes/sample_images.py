import flask
import flask_jwt_extended

from app import db, image

sample_images_bp = flask.Blueprint('sample_images', __name__)


@sample_images_bp.route('/datasets/<dataset_name>/samples/images')
@flask_jwt_extended.jwt_required
def list_sample_images(dataset_name):
    params = flask.request.args
    limit = params.get('limit', None)
    offset = params.get('offset', 0)
    prefix = params.get('prefix', '')
    label = params.get('label', '')
    split = params.get('split', '')

    # Duplication in samples.list_samples()
    conn = db.get_conn()
    prefix_pattern = prefix + '%'
    with conn.cursor() as cur:
        dataset_id = db.dataset_id(cur, dataset_name)
        cur.execute(
            """
            SELECT s.info
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

    images = []
    for row in results:
        info = row[0]
        # TODO: inspect for other possible errors
        try:
            image_urls = image.get_images(info, 1, 0)
        except KeyError:
            images.append(None)
        else:
            if image_urls:
                images.append(image_urls[0])
            else:
                images.append(None)

    return flask.jsonify({
        'images': images,
    })


@sample_images_bp.route('/datasets/<dataset_name>/samples/<name>/images')
@flask_jwt_extended.jwt_required
def get_sample_images(dataset_name, name):
    conn = db.get_conn()
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

    params = flask.request.args
    limit = params.get('limit', default=None, type=int)
    offset = params.get('offset', default=0, type=int)

    try:
        images = image.get_images(info, limit, offset)
    except KeyError:
        images = []

    return flask.jsonify({
        'images': images,
    })
