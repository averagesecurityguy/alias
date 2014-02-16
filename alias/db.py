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


def get_all_targets():
    '''
    Return a list of all targets.
    '''
    targets = [user_db.hget(i, 'key') for i in user_db.keys('*')]
    return targets


def get_targets_with_data():
    '''
    Return a list of all targets that have data associated with them.
    '''
    ids = set(email_db.keys('*'))
    ids.union(nym_db.keys('*'), url_db.keys('*'))
    ids.union(loc_db.keys('*'), name_db.keys('*'))
    ids.union(desc_db.keys('*'), image_db.keys('*'))

    targets = [user_db.hget(i, 'key') for i in ids]

    return targets


def add_new_target(target, key_type):
    '''
    Adds a new target to the database.
    '''
    key_id = user_db.get('key_id')
    user_db.incr('key_id')

    data = {'key': target, 'type': key_type,
            'gravatar': None, 'twitter': None}

    user_db.hmset(key_id, data)
    user_db.set(target, key_id)


def get_target_data(target):
    tid = user_db.get(target)
    data = {}

    data['emails'] = email_db.lrange(tid, 0, -1)
    data['nyms'] = nym_db.lrange(tid, 0, -1)
    data['urls'] = url_db.lrange(tid, 0, -1)
    data['locs'] = loc_db.lrange(tid, 0, -1)
    data['names'] = name_db.lrange(tid, 0, -1)
    data['descs'] = desc_db.lrange(tid, 0, -1)
    data['images'] = image_db.lrange(tid, 0, -1)

    return data


def add_target_email(target, address):
    tid = user_db.get(target)
    email_db.lpush(tid, address.lower())


def add_target_nym(target, nym):
    tid = user_db.get(target)
    nym_db.lpush(tid, nym)


def add_target_url(target, url):
    tid = user_db.get(target)
    url_db.lpush(tid, url)


def add_target_location(target, location):
    tid = user_db.get(target)
    loc_db.lpush(tid, location)


def add_target_name(target, name):
    tid = user_db.get(target)
    name_db.lpush(tid, name)


def add_target_description(target, desc):
    tid = user_db.get(target)
    desc_db.lpush(tid, desc)


def add_target_image(target, url):
    tid = user_db.get(target)
    image_db.lpush(tid, url)
