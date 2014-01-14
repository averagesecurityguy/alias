#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sys
import json
import redis
import os

import lib.twitter

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def lookup_users(screen_names):
    try:
        return tw.user_lookup(screen_names)
    except lib.twitter.TwitterConnectionException:
        print 'Connection error: sleeping for 5 seconds.'
        time.sleep(5)
        return None


def process_results(results):
    for user in results:
        screen_name = user['screen_name'].lower()
        name = user.get('name')
        if (name is not None) and (name != ''):
            name_db.lpush(screen_name + ':twitter', name)
            name_db.lpush(name.lower(), screen_name)

        loc = user.get('location')
        if (loc is not None) and  (loc != ''):
            loc_db.lpush(screen_name + ':twitter', loc)
            loc_db.lpush(loc.lower(), screen_name)

        desc = user.get('description')
        if (desc is not None) and (desc != ''):
            about_db.lpush(screen_name + ':twitter', desc)
            about_db.lpush(desc, screen_name)

        url = user.get('url')
        if (url is not None) and (url != ''):
            url_db.lpush(screen_name + ':twitter', url)
            url_db.lpush(url, screen_name)

        purl = user.get('profile_image_url')
        if (purl is not None) and (purl != ''):
            url_db.lpush(screen_name + ':twitter', purl)
            url_db.lpush(purl, screen_name)

        user_db.hset(screen_name, 'twitter', 1)


def get_twitter_connection():
    return lib.twitter.Twitter(cfg['tw_consumer_key'],
                               cfg['tw_consumer_secret'],
                               cfg['tw_token'],
                               cfg['tw_token_secret'])


def load_configuration(filename):
    '''
    Loads the JSON configuration file specified by filename.
    '''
    try:
        with open(filename) as config_file:
            return json.loads(config_file.read())
    except Exception as e:
        print '[-] Could not load configuration.'
        print '[-] {0}'.format(e)
        sys.exit(1)

#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
cfg = load_configuration(os.path.join('conf', 'app.conf'))

user_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['user_db'])
email_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['email_db'])
nym_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['nym_db'])
url_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['url_db'])
loc_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['loc_db'])
name_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['name_db'])
about_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['about_db'])

tw = get_twitter_connection()
count = 0
users = []
for user in user_db.keys('*'):
    if user_db.hget(user, 'twitter') == '1':
        continue

    count += 1
    users.append(user)

    if len(users) == 100:
        results = None
        while results is None:
            results = lookup_users(users)

        process_results(results)
        users = []

    if count % 1000 == 0:
        print 'Processed {0}'.format(count)
        tw = get_twitter_connection()
