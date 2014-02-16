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
about_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.about_db)
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
    targets = [user_db.hget(i, 'key') for i in user_db.keys('id:*')]
    return targets


def get_unchecked_targets(source, key_type):
    '''
    Return a list of targets that have not been looked up at the specified
    source. In addition, make sure the key_type matches the requested type.
    Some sources work well with usernames, others with emails, and others will
    work with either.
    '''
    targets = []

    if source not in cfg.valid_sources:
        return targets

    if key_type not in ['user', 'email', 'all']:
        return targets

    for tid in user_db.keys('id:*'):
        user_type = user_db.hget(tid, 'type')

        if (key_type != user_type) and (key_type != 'all'):
            continue

        if user_db.hget(tid, source) == '0':
            targets.append(user_db.hget(tid, 'key'))

    return targets


def get_targets_with_data():
    '''
    Return a list of all targets that have data associated with them.
    '''
    # Create a set of all the ids in each 
    ids = set(email_db.keys('id:*'))
    ids.union(nym_db.keys('id:*'), url_db.keys('id:*'))
    ids.union(loc_db.keys('id:*'), name_db.keys('id:*'))
    ids.union(about_db.keys('id:*'), image_db.keys('id:*'))

    targets = [user_db.hget(i, 'key') for i in ids]

    return targets


def add_new_target(target, key_type):
    '''
    Adds a new target to the database.
    '''
    key_id = user_db.get('key_id')
    user_db.incr('key_id')

    data = {'key': target, 'type': key_type}
    for source in cfg.valid_sources:
        data[source] = '0'

    tid = 'id:' + key_id
    user_db.hmset(tid, data)
    user_db.set(target, tid)


def mark_source_complete(target, source):
    '''
    Change the value of the specified source from None to 1 to indicate that
    this source has been checked for this user.
    '''
    tid = user_db.get(target)
    user_db.hset(tid, source, '1')


def get_target_data(target):
    tid = user_db.get(target)
    data = {}

    data['emails'] = email_db.lrange(tid, 0, -1)
    data['nyms'] = nym_db.lrange(tid, 0, -1)
    data['urls'] = url_db.lrange(tid, 0, -1)
    data['locs'] = loc_db.lrange(tid, 0, -1)
    data['names'] = name_db.lrange(tid, 0, -1)
    data['abouts'] = about_db.lrange(tid, 0, -1)
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
    about_db.lpush(tid, desc)


def add_target_image(target, url):
    tid = user_db.get(target)
    image_db.lpush(tid, url)
