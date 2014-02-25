# -*- coding: utf-8 -*-

import re
import redis
import logging

import alias.config

logger = logging.getLogger('DB')
email_re = re.compile(r'.*@.*\..*')
cfg = alias.config.AliasConfig()

logger.info('Configuring databases.')
user_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.user_db)
email_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.email_db)
nym_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.nym_db)
loc_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.loc_db)
url_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.url_db)
name_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.name_db)
about_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.about_db)
image_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.image_db)
admin_db = redis.StrictRedis(host='localhost', port=6379, db=cfg.admin_db)

def load_new_targets(targets):
    logger.info('Loading new targets.')
    # Make sure the key_id is available before adding data.
    if admin_db.get('key_id') is None:
        admin_db.set('key_id', 1)

    # Add usernames and email addresses.
    count = 0
    for target in targets.split(','):
        target = target.lower().strip()
        if target == '':
            continue

        if email_re.search(target) is None:
            if add_new_target(target, 'user'):
                count += 1
        else:
            if add_new_target(target, 'email'):
                count += 1            

    return count


def get_all_targets():
    '''
    Return a list of all targets.
    '''
    logger.debug('Get all targets.')

    targets = [user_db.hget(i, 'key') for i in user_db.keys('id:*')]
    return targets


def get_unchecked_targets(source, key_type):
    '''
    Return a list of targets that have not been looked up at the specified
    source. In addition, make sure the key_type matches the requested type.
    Some sources work well with usernames, others with emails, and others will
    work with either.
    '''
    logger.debug('Getting unchecked targets for {0}.'.format(source))
    
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
    logger.debug('Getting all targets with data.')

    # Create a set of all the ids in each database
    ids = set(email_db.keys('id:*'))
    ids = ids.union(nym_db.keys('id:*'), url_db.keys('id:*'))
    ids = ids.union(loc_db.keys('id:*'), name_db.keys('id:*'))
    ids = ids.union(about_db.keys('id:*'), image_db.keys('id:*'))

    targets = [user_db.hget(i, 'key') for i in ids]

    return targets


def add_new_target(target, key_type):
    '''
    Adds a new target to the database.
    '''
    target = target.strip()
    logger.debug(u'Adding new target {0}.'.format(target))
    tid = user_db.get(target)

    if tid is None:
        key_id = admin_db.get('key_id')
        admin_db.incr('key_id')

        data = {'key': target, 'type': key_type}
        for source in cfg.valid_sources:
            data[source] = '0'

        tid = 'id:' + key_id
        user_db.hmset(tid, data)
        user_db.set(target, tid)

        return True

    return False

def mark_source_complete(target, source):
    '''
    Change the value of the specified source from 0 to 1 to indicate that
    this source has been checked for this user.
    '''
    logger.debug(u'Marking {0} complete for {1}.'.format(source, target))
    if source in cfg.valid_sources:
        tid = user_db.get(target)
        user_db.hset(tid, source, '1')


def add_target_to_source_list(target, source):
    '''
    Add target to the list of other targets with data from the specified
    source.
    '''
    logger.debug(u'Adding {0} to source list {1}.'.format(target, source))
    if source in cfg.valid_sources:
        tid = user_db.get(target)
        admin_db.lpush('source:' + source, tid)


def get_targets_from_source(source):
    '''
    Return all targets with data from the specified source.
    '''
    logger.debug(u'Getting all targets associated with {0}.'.format(source))
    if source in cfg.valid_sources:
        tids = admin_db.lrange('source:' + source, 0, -1)
        return sorted([user_db.hget(tid, 'key') for tid in tids])


def get_sources_with_data():
    '''
    Get all sources that have data associated with them.
    '''
    logger.debug('Getting list of sources with target data.')
    return sorted([s.split(':')[1] for s in admin_db.keys('source:*')])


def get_target_data(target):
    logger.debug(u'Getting all data associated with {0}.'.format(target))
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


def get_correlated_targets(dataset, target):
    logger.debug(u'Getting all targets using the {0} {1}.'.format(dataset,
                                                                 target))
    if dataset == 'email':
        ids = email_db.lrange(target, 0, -1)
    elif dataset == 'nym':
        ids = nym_db.lrange(target, 0, -1)
    elif dataset == 'name':
        ids = name_db.lrange(target, 0, -1)
    else:
        return None
    
    return [user_db.hget(i, 'key') for i in ids]


def add_target_email(target, address):
    logger.debug(u'Adding new email {0} to {1}.'.format(address, target))
    address = address.strip()
    tid = user_db.get(target)
    email_db.lpush(tid, address.lower())
    email_db.lpush(address.lower(), tid)


def add_target_nym(target, nym):
    logger.debug(u'Adding pseudonym {0} to {1}.'.format(nym, target))
    nym = nym.strip()
    tid = user_db.get(target)
    nym_db.lpush(tid, nym)
    nym_db.lpush(nym, tid)


def add_target_url(target, url):
    logger.debug(u'Adding url {0} to {1}.'.format(url, target))
    url = url.strip()
    tid = user_db.get(target)
    url_db.lpush(tid, url)


def add_target_location(target, location):
    logger.debug(u'Adding location {0} to {1}.'.format(location, target))
    location = location.strip()
    tid = user_db.get(target)
    loc_db.lpush(tid, location)


def add_target_name(target, name):
    logger.debug(u'Adding name {0} to {1}.'.format(name, target))
    name = name.strip()
    tid = user_db.get(target)
    name_db.lpush(tid, name)
    name_db.lpush(name, tid)


def add_target_description(target, desc):
    logger.debug(u'Adding desc {0} to {1}.'.format(desc[:40], target))
    desc = desc.strip()
    tid = user_db.get(target)
    about_db.lpush(tid, desc)


def add_target_image(target, url):
    logger.debug(u'Adding image URL {0} to {1}.'.format(url, target))
    url = url.strip()
    tid = user_db.get(target)
    image_db.lpush(tid, url)
