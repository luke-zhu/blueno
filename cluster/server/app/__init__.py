"""
Entry point for the entire server.
"""
import logging.config
import os

import flask
import flask_jwt_extended

from app import db, env
from app.routes.auth import auth_bp
from app.routes.data import data_bp
from app.routes.datasets import datasets_bp
from app.routes.register import register_bp
from app.routes.sample_images import sample_images_bp
from app.routes.samples import samples_bp

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s]'
                      ' %(name)s:%(lineno)d - %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
    }
})

app = flask.Flask(__name__,
                  template_folder='../build',
                  static_folder='../build/static',
                  static_url_path='/static')

app.register_blueprint(auth_bp)
app.register_blueprint(data_bp)
app.register_blueprint(datasets_bp)
app.register_blueprint(samples_bp)
app.register_blueprint(sample_images_bp)
app.register_blueprint(register_bp)

app.config['JWT_SECRET_KEY'] = env.JWT_SECRET_KEY
jwt = flask_jwt_extended.JWTManager(app)

app.teardown_appcontext(db.close_conn)


@app.route('/')
def index():
    return flask.redirect('/ui')


@app.route('/ui', defaults={'path': ''})
@app.route('/<path:path>')
def ui(path):
    return flask.render_template('index.html')


@app.route('/service-worker.js')
def service_worker():
    return flask.helpers.send_file(
        os.path.join(app.template_folder, 'service-worker.js'))


@app.errorhandler(db.ConflictException)
def handle_already_exists(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(db.NotFoundException)
def handle_not_found(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
