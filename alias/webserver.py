# -*- coding: utf-8 -*-

import flask

import alias.config
import alias.lookup
import alias.db


#-----------------------------------------------------------------------------
# WEB SERVER
#-----------------------------------------------------------------------------
app = flask.Flask(__name__)

@app.route("/")
def index():
    return flask.render_template('index.html')

@app.route("/users")
@app.route("/users/<key>")
def users(key):
    if key is None:
        keys = sorted(set([u[:2] for u in alias.db.get_users_with_data()]))

        if len(keys) == 0:
            keys = None
        
        users = None
    else:
        keys = None
        users = sorted(alias.db.get_users_with_data(key))

    return flask.render_template('users.html', keys=keys, users=users)
    

@app.route('/user/<username>')
def get_user(username):
    '''
    Get all data about a user.
    '''
    data = alias.db.get_user_data(username)

    return flask.render_template('user.html', username=username, data=data)


@app.route("/emails")
@app.route("/emails/<key>")
def emails(key):
    if key is None:
        keys = alias.db.get_email_directory()
        emails = None
    else:
        keys = None
        emails = alias.db.get_emails_by_key(key)

    return flask.render_template('emails.html', keys=keys, emails=emails)


@app.route('/email/<address>')
def get_email(address):
    '''
    Get all usernames associated with an email address.
    '''
    usernames = alias.db.get_usernames_by_email(address)
    return flask.render_template('email.html',
                                 address=address, 
                                 usernames=usernames)


@app.route('/lookup')
@app.route('/lookup/<source>')
def lookup(source):
    msg = None
    if source.lower() == 'twitter':
        c = alias.lookup.twitter_lookup()
        msg = 'Found {0} targets with Twitter accounts.'.format(c)
    elif source.lower() == 'gravatar':
        c = alias.lookup.gravatar_lookup()
        msg = 'Found {0} targets with Gravatar accounts.'.format(c)
    else:
        return flask.render_template('404.html')


    return flask.render_template('lookup.html', msg=None)


@app.route('/load', methods=['GET', 'POST'])
def load():
    message = None

    if flask.request.method == 'POST':
        count = alias.db.load_new_targets(flask.request.form)

        if count > 0:
            message = 'Loaded {0} account(s)'.format(count)

    return flask.render_template('load.html', message=message)





