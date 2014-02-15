# -*- coding: utf-8 -*-

import re
import redis

import alias.config

email_re = re.compile(r'.*@.*\..*')

cfg = alias.config.AliasConfig()

user_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.user_db)
email_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.email_db)
nym_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.nym_db)
loc_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.loc_db)
url_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.url_db)
name_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.name_db)
desc_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.desc_db)
image_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.image_db)

def get_email_directory():
    return sorted(set([i[:2] for i in email_db.keys('*@*.*')]))


def get_emails_by_key(key):
    return sorted(email_db.keys(key + '*@*.*'))


def get_usernames_by_email(address):
    ids = email_db.lrange(address, 0, -1)
    return sorted(set([user_db.hget(i, 'key') for i in ids]))


def load_new_targets(targets):
    # Make sure the key_id is available before adding data.
    if user_db.get('key_id') is None:
        user_db.set('key_id', 1)

    # Add usernames and email addresses.
    count = 0
    for target in targets.split(','):
        target = target.lower().strip()
        if target == '':
            continue

        if email_re.search(target) is None:
            add_new_target(target, 'user')
        else:
            add_new_target(target, 'email')            
        
        count += 1

    return count


def get_users_with_data(key=None):
    '''
    Return a list of all users with data associated with the username or email
    address.
    '''
    if key is None:
        keys = user_db.keys('*:data')
    else:
        keys = user_db.keys(key + '*:data')

    users = []
    for key in keys:
        u, j = key.split(':')
        user_id = user_db.get(u)
        user = user_db.hget(user_id, 'key')
        users.append(user)

    return users


def add_new_target(target, key_type):
    '''
    Adds a new target to the database.
    '''
    key_id = user_db.get('key_id')
    user_db.incr('key_id')

    data = {'key': target, 'type': key_type,
            'gravatar': None, 'twitter': None}

    user_db.hmset('id:' + key_id, data)
    user_db.set(target, 'id:' + key_id)


def get_user_data(username):
    user_id = user_db.get(username)
    data = {}

    data['emails'] = email_db.lrange(user_id, 0, -1)
    data['nyms'] = nym_db.lrange(user_id, 0, -1)
    data['urls'] = url_db.lrange(user_id, 0, -1)
    data['locs'] = loc_db.lrange(user_id, 0, -1)
    data['names'] = name_db.lrange(user_id, 0, -1)
    data['descs'] = desc_db.lrange(user_id, 0, -1)
    data['images'] = image_db.lrange(user_id, 0, -1)

    return data
