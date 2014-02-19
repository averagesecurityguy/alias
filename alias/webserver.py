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

@app.route('/email/<email>')
def get_targets_with_email(email):
    '''
    Get list of targets that share the specified email address.
    '''
    targets = alias.db.get_correlated_targets('email', email)

    return flask.render_template('same_email.html', targets=targets)

@app.route('/name/<name>')
def get_targets_with_name(name):
    '''
    Get list of targets that share the specified name.
    '''
    targets = alias.db.get_correlated_targets('name', name)

    return flask.render_template('same_name.html', targets=targets)

@app.route('/nym/<nym>')
def get_targets_with_nym(nym):
    '''
    Get list of targets that share the specified pseudonym.
    '''
    targets = alias.db.get_correlated_targets('nym', nym)

    return flask.render_template('same_nym.html', targets=targets)


@app.route('/source/<source>')
def get_targets_from_source(source):
    '''
    Get list of targets with data from the specified source.
    '''
    targets = alias.db.get_targets_from_source(source)

    return flask.render_template('source.html', source=source,
                                                targets=targets)


@app.route('/load', methods=['GET', 'POST'])
def load():
    message = None

    if flask.request.method == 'POST':
        count = alias.db.load_new_targets(flask.request.form['targets'])
        message = 'Loaded {0} account(s)'.format(count)

    return flask.render_template('load.html', message=message)
