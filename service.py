import os
import numpy as np
import pandas as pd
import settings
import pickle
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS, cross_origin
from waitress import serve

srv_URL = settings.SERVICE_URL if settings.SERVICE_URL else '/'
app = Flask(__name__)
cors = CORS(app, resources={srv_URL: {'origins': '*'}})
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['CORS_HEADERS'] = 'Content-Type'

pipeline = None
model = None
required_columns = [f'site{n // 2 + 1}' if n % 2 == 0 else f'time{n // 2 + 1}' for n in range(20)]


def prepare_prediction_system():
    """ Load data preparation pipeline and prediction model """
    logger.info('Loading data preparation pipeline...')
    with open('models/prepare_pipeline.cpkl', 'rb') as pf:
        ppl = pickle.load(pf)

    logger.info('Loading model...')
    with open('models/model.cpkl', 'rb') as pf:
        mdl = pickle.load(pf)
    return ppl, mdl


def generate_test_sample(**params):
    """ Generate test sample
    :param params: can contain the next keys:
        :key size - number of samples
        :key target - set 0 for non-alice sample, 1 - alice sample, -1 - mixed sample
        :key min_sites - minimal amount of not NaN site-time pairs
    """
    # init
    train_path = 'modeling/train_data/source/'
    site_dict = pickle.load(open(f'modeling/train_data/site_dic.pkl', 'rb'))
    files = [f for f in os.listdir(train_path) if os.path.isfile(os.path.join(train_path, f)) and f != 'Alice_log.csv']
    # read params
    size = params.get('size', 10)
    target = params.get('target', -1)
    min_sites = params.get('min_sites', 2)
    # generate
    rnd = np.random.default_rng()
    result = pd.DataFrame()
    truth_target = []
    for i in range(size):
        if (rnd.integers(2) and abs(target) == 1) or target == 1:
            # gen alice
            dt = pd.read_csv(f'{train_path}/Alice_log.csv')
            truth_target.append(1)
        else:
            # gen non-alice
            rand_file = rnd.choice(files)
            dt = pd.read_csv(f'{train_path}' + rand_file)
            truth_target.append(0)

        # generate
        dt['site'] = dt['site'].map(site_dict)
        si = dt.sample().index[0]
        bundle = dt.loc[si:si + rnd.integers(10 - min_sites) + min_sites, ['site', 'timestamp']]  # minimal 2 sites

        col_prepared = np.append(bundle.to_numpy().flatten(), [None, None] * (10 - bundle.shape[0]))
        sample = pd.DataFrame(col_prepared, index=required_columns).T
        result = pd.concat([result, sample], axis=0)
    result.insert(0, 'session_id', 0)
    result['session_id'] = range(size)
    result.index = range(size)

    return result, truth_target


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
        # check if all required columns are in place
        col_diff = set(list(data.keys())) ^ set(required_columns + ['session_id'])
        if not data or (col_diff and 'get_test_sample' not in data.keys()):
            return jsonify({'response': 'I used to be an adventurer like you. Then I took an arrow in the knee.'})
        elif params := data.get('get_test_sample', None):
            # get test sample
            samples, targets = generate_test_sample(**params)
            return jsonify([samples.to_dict(), targets])

        # return predicts
        x = pd.DataFrame(data)
        prepared = pipeline.transform(x)
        result = model.predict_proba(prepared)
        return jsonify(pd.DataFrame(result).to_dict())


if __name__ == '__main__':
    # setup logger
    rfh = RotatingFileHandler('service.log', mode='a', maxBytes=5 * 1024 * 1024,
                              backupCount=2, encoding=None, delay=False)
    logging.basicConfig(level=logging.INFO, handlers=[rfh],
                        format="%(asctime)s : %(message)s", datefmt="%y-%m-%d %H:%M:%S",)
    logger = logging.getLogger('main')

    pipeline, model = prepare_prediction_system()
    logger.info('Running HTTP server...')
    if settings.PRIVATE_KEY and settings.CERTIFICATE:
        # run with TLS
        serve(app, host="0.0.0.0", port=settings.PORT, keyfile=settings.PRIVATE_KEY, certfile=settings.CERTIFICATE)
    else:
        # run without TLS: data is not encrypted!
        serve(app, host="0.0.0.0", port=settings.PORT)
