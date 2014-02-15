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
    return sorted(set([i[:2] for i in cfg.email_db.keys('*@*.*')]))


def get_emails_by_key(key):
    return sorted(cfg.email_db.keys(key + '*@*.*'))


def get_usernames_by_email(address):
    ids = cfg.email_db.lrange(address, 0, -1)
    return sorted(set([cfg.user_db.hget(i, 'key') for i in ids]))


def load_new_targets(targets):
    # Make sure the key_id is available before adding data.
    if cfg.user_db.get('key_id') is None:
        cfg.user_db.set('key_id', 1)

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
        keys = cfg.user_db.keys('*:data')
    else:
        keys = cfg.user_db.keys(key + '*:data')

    users = []
    for key in keys:
        u, j = key.split(':')
        user_id = cfg.user_db.get(u)
        user = cfg.user_db.hget(user_id, 'key')
        users.append(user)

    return users


def add_new_target(target, key_type):
    '''
    Adds a new target to the database.
    '''
    key_id = cfg.user_db.get('key_id')
    cfg.user_db.incr('key_id')

    data = {'key': target, 'type': key_type,
            'gravatar': None, 'twitter': None}

    cfg.user_db.hmset('id:' + key_id, data)
    cfg.user_db.set(target, 'id:' + key_id)


def get_user_data(username):
    user_id = cfg.user_db.get(username)
    data = {}

    data['emails'] = cfg.email_db.lrange(user_id, 0, -1)
    data['nyms'] = cfg.nym_db.lrange(user_id, 0, -1)
    data['urls'] = cfg.url_db.lrange(user_id, 0, -1)
    data['locs'] = cfg.loc_db.lrange(user_id, 0, -1)
    data['names'] = cfg.name_db.lrange(user_id, 0, -1)
    data['descs'] = cfg.desc_db.lrange(user_id, 0, -1)
    data['images'] = cfg.image_db.lrange(user_id, 0, -1)

    return data
