import flask
import pandas as pd
from sklearn.pipeline import Pipeline

import settings
import pickle
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin
from waitress import serve

srv_URL = settings.SERVICE_URL if settings.SERVICE_URL else '/'
app = Flask(__name__)
cors = CORS(app, resources={srv_URL: {'origins': '*'}})
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['CORS_HEADERS'] = 'Content-Type'

pipeline = Pipeline
model = Pipeline

pickle.DEFAULT_PROTOCOL = 3


def prepare_prediction_system():
    """ Load data preparation pipeline and prediction model """
    global pipeline
    global model

    logger.info('Loading data preparation pipeline...')
    with open('prepare_pipeline.cpkl', 'rb') as pf:
        pipeline = pickle.load(pf)

    logger.info('Loading model...')
    with open('model.cpkl', 'rb') as pf:
        model = pickle.load(pf)


@app.route(f'{srv_URL}', methods=['get', 'post'])
@cross_origin()
def get_prediction():
    """ Predictions API
    :return {predicted class: {object_index: probability}, ... }
    """
    if request.method == 'GET':
        return render_template('test.html')
    if request.method == 'POST':
        data = request.json
        if not data:
            return 'I used to be an adventurer like you. Then I took an arrow in the knee.'
        x = pd.DataFrame(data)
        prepared = pipeline.transform(x)
        result = model.predict_proba(prepared)
        return flask.jsonify(pd.DataFrame(result).to_dict())


if __name__ == '__main__':
    # setup logger
    rfh = RotatingFileHandler('service.log', mode='a', maxBytes=5 * 1024 * 1024,
                              backupCount=2, encoding=None, delay=False)
    logging.basicConfig(level=logging.INFO, handlers=[rfh],
                        format="%(asctime)s : %(message)s", datefmt="%y-%m-%d %H:%M:%S",)
    logger = logging.getLogger('main')

    prepare_prediction_system()
    logger.info('Running HTTP server...')
    if settings.PRIVATE_KEY and settings.CERTIFICATE:
        # run with TLS
        serve(app, host="0.0.0.0", port=settings.PORT, keyfile=settings.PRIVATE_KEY, certfile=settings.CERTIFICATE)
    else:
        # run without TLS: data is not encrypted!
        serve(app, host="0.0.0.0", port=settings.PORT)
