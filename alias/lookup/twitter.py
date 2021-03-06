#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import requests
import logging

import alias.twitter
import alias.db

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def __get_redirect(url):
    logger.debug('Tracing t.co link.')
    if url.startswith('https://t.co') or url.startswith('http://t.co'):
        resp = requests.get(url, allow_redirects=False)
        return resp.headers.get('location', url)

    return url


def __lookup_users(tw, screen_names):
    logger.debug('Looking up screen_names.')
    try:
        return tw.user_lookup(screen_names)
    except alias.twitter.TwitterConnectionException:
        logger.warning('Connection error: sleeping for 5 seconds.')
        time.sleep(5)
        return None


def __process_results(results):
    logger.debug('Processing results.')
    for user in results:
        username = user['screen_name'].lower()

        name = user.get('name')
        if (name is not None) and (name != ''):
            alias.db.add_target_name(username, name)

        loc = user.get('location')
        if (loc is not None) and  (loc != ''):
            alias.db.add_target_location(username, loc)

        desc = user.get('description')
        if (desc is not None) and (desc != ''):
            alias.db.add_target_description(username, desc)

        url = user.get('url')
        if (url is not None) and (url != ''):
            url = __get_redirect(url)
            alias.db.add_target_url(username, url)

        purl = user.get('profile_image_url')
        if (purl is not None) and (purl != ''):
            alias.db.add_target_image(username, purl)

        pburl = user.get('profile_background_image_url')
        if (pburl is not None) and (pburl != ''):
            alias.db.add_target_image(username, pburl)

        # If we have valid data add this target to the twitter source list
        alias.db.add_target_to_source_list(username, 'twitter')


def __mark_complete(users):
    logger.debug('Marking not found users as completed.')
    for user in users:
        alias.db.mark_source_complete(user, 'twitter')


def __get_twitter_connection(cfg):
    logger.debug('Getting Twitter connection.')
    return alias.twitter.Twitter(cfg.tw_consumer_key, cfg.tw_consumer_secret,
                                 cfg.tw_token, cfg.tw_token_secret)


#-----------------------------------------------------------------------------
# Lookup Method
#-----------------------------------------------------------------------------
logger = logging.getLogger('Twitter')

def lookup():
    logger.info('Starting Twitter lookup.')

    cfg = alias.config.AliasConfig()

    tw = __get_twitter_connection(cfg)
    count = 0
    users = []
    logger.info('Getting unprocessed Twitter usernames from database.')

    for target in alias.db.get_unchecked_targets('twitter', 'user'):
        count += 1
        users.append(target)

        if len(users) == 100:
            results = None
            while results is None:
                results = __lookup_users(tw, users)

            __process_results(results)
            __mark_complete(users)
            users = []

        if count % 1000 == 0:
            logger.info('Processed {0} Twitter users.'.format(count))
            tw = __get_twitter_connection(cfg)

    logger.info('Twitter lookup complete.')
    return None
