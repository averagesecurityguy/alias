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
@app.route("/targets/<key>")
def targets(key=None):
    if key is None:
        keys = sorted(set([u[:2] for u in alias.db.get_targets_with_data()]))

        if len(keys) == 0:
            keys = None
        
        users = None
    else:
        keys = None
        users = sorted(alias.db.get_targets_with_data(key))

    return flask.render_template('targets.html', keys=keys, users=users)
    

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
        count = alias.db.load_new_targets(flask.request.form)

        if count > 0:
            message = 'Loaded {0} account(s)'.format(count)

    return flask.render_template('load.html', message=message)
