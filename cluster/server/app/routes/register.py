import json
from typing import Optional

import flask
import flask_jwt_extended
from kubernetes import config
from kubernetes.client import BatchV1Api
from kubernetes.client.rest import ApiException
from werkzeug import security

from app import db

register_bp = flask.Blueprint('register', __name__)


def create_register_job(dataset, email, password) -> Optional[str]:
    config.load_incluster_config()
    batch_v1 = BatchV1Api()
    # job names cannot include underscores
    job_name = f'register-{dataset}'.replace('_', '-')
    # TODO: Handle datasets that require extra dependencies (matplotlib, etc.)
    #  Also remove those extra dependencies from requirements.txt
    try:
        batch_v1.create_namespaced_job('default', {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job_name},
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": job_name,
                            "image": "cyclotomic/blueno-registration-pipelines",
                            "imagePullPolicy": "Always",
                            "command": ["python"],
                            "args": [
                                "main.py",
                                dataset,
                                email,
                                password
                            ],
                            "env": [
                                {
                                    "name": "FILESYSTEM_STORE_ROOT",
                                    "value": "/root"
                                },
                                {
                                    "name": "BLUENO_SERVER",
                                    "value": "http://blueno-server"
                                }
                            ],
                            "volumeMounts": [
                                {
                                    # We mount to /root because tensorflow
                                    # datasets still downloads data to
                                    # the default (~/tensorflow_datasets)
                                    "mountPath": "/root",
                                    "name": "nfs"
                                }
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "2Gi",
                                }
                            },
                        }],
                        "volumes": [
                            {
                                "name": "nfs",
                                "persistentVolumeClaim": {
                                    "claimName": "blueno-nfs"
                                }
                            }
                        ],
                        # We avoid restarting on failure because a new
                        # NFS mount is needed if the NFS server pod fails
                        "restartPolicy": "Never"
                    }
                }
            }
        })
        return None
    except ApiException as e:
        return json.loads(e.body)['message']


@register_bp.route('/register', methods=['POST'])
@flask_jwt_extended.jwt_required
def register_datasets():
    try:
        payload = flask.request.json
        datasets = payload['datasets']
        email = payload['email']
        password = payload['password']
    except TypeError:
        return flask.jsonify({'message': f'Missing JSON payload'}), 400
    except KeyError as e:
        return flask.jsonify({'message': f'Missing JSON parameter: {e}'}), 400

    conn = db.get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
                    SELECT pwhash
                    FROM users
                    WHERE email = %s;
                    """,
            (email,)
        )
        result = cur.fetchone()
    db_pwd = result[0]
    if not security.check_password_hash(db_pwd, password):
        return flask.jsonify({'message': 'Invalid password'}), 400

    returned_info = []
    for d in datasets:
        error_message = create_register_job(d, email, password)
        if error_message:
            returned_info.append({
                'dataset': d,
                'status': 'failed',
                'message': error_message,
            })
        else:
            returned_info.append({
                'dataset': d,
                'status': 'started',
                'message': f'Creating dataset {d}'
            })

    return flask.jsonify({
        'datasets': returned_info,
    })
