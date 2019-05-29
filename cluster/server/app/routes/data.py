import flask
import flask_jwt_extended

from app import storage

data_bp = flask.Blueprint('data', __name__)


@data_bp.route('/data/upload',
               methods=['POST'])
@flask_jwt_extended.jwt_required
def upload_object():
    # 1. Validate the request
    object_url = flask.request.args.get('url', None)
    if object_url is None:
        return flask.jsonify({'message': "No url query param found"}), 400
    if 'file' not in flask.request.files:
        return flask.jsonify({'message': "No file found"}), 400
    file = flask.request.files['file']

    # 2. Save the data
    try:
        storage_client = storage.get_storage_client(object_url)
    except ValueError as e:
        return flask.jsonify({'message': str(e)}), 400
    storage_client.put(object_url, file.stream)

    return flask.jsonify({})


@data_bp.route('/data/download',
               methods=['GET'])
def download_object():
    object_url = flask.request.args.get('url', None)
    # TODO: Implement signed URLs so that we can secure this endpoint
    token = flask.request.args.get('token', None)  # noqa: F841
    try:
        storage_client = storage.get_storage_client(object_url)
    except ValueError as e:
        return flask.jsonify({'message': str(e)}), 400
    stream = storage_client.get(object_url)
    return flask.send_file(stream,
                           mimetype='application/octet-stream',
                           attachment_filename=object_url)
