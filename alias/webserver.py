# -*- coding: utf-8 -*-

import flask

import alias.lookup
import alias.db


#-----------------------------------------------------------------------------
# WEB SERVER
#-----------------------------------------------------------------------------
app = flask.Flask(__name__)

@app.route("/")
def index():
    return flask.render_template('index.html')

@app.route("/targets")
def targets():
    targets = sorted(alias.db.get_targets_with_data())

    return flask.render_template('targets.html', targets=targets)
    

@app.route('/target/<key>')
def get_target(key):
    '''
    Get all data about a target.
    '''
    data = alias.db.get_target_data(key)

    return flask.render_template('target.html', target=key, data=data)


@app.route('/load', methods=['GET', 'POST'])
def load():
    message = None

    if flask.request.method == 'POST':
        count = alias.db.load_new_targets(flask.request.form['targets'])

        if count > 0:
            message = 'Loaded {0} account(s)'.format(count)

    return flask.render_template('load.html', message=message)
