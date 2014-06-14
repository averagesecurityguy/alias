#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging
import time

import alias.db
import alias.config

#-----------------------------------------------------------------------------
# Function Definitions
#-----------------------------------------------------------------------------
def __get_urls(data):
    '''
    Pull any urls from the gravatar data.
    '''
    logger.debug('Processing URLs.')
    url_list = []

    if data.get('html_url') is not None:
        url_list.append(data.get('html_url', ''))

    if data.get('avatar_url') is not None:
        url_list.append(data.get('avatar_url', ''))

    if data.get('blog') is not None:
        url_list.append(data.get('blog', ''))

    return url_list


def __process_results(result):
    '''
    Get each of the data items we are looking for from the result and write
    them to the databases.
    '''
    logger.debug('Processing result.')

    username = result[0]
    data = result[1]

    if data.get('message') is None:
        email = data.get('email')
        if (email is not None) and (email != ''):
            alias.db.add_target_email(username, email)
        
        nym = data.get('gravatar_id')
        if (nym is not None) and (nym != ''):
            alias.db.add_target_nym(username, nym)

        urls = __get_urls(data)
        for url in sorted(set(urls)):
            alias.db.add_target_url(username, url)

        loc = data.get('location')
        if (loc is not None) and (loc != ''):
            alias.db.add_target_location(username, loc)

        name = data.get('name')
        if (name is not None) and (name != ''):
            alias.db.add_target_name(username, name)

        bio = data.get('bio')
        if (bio is not None) and (bio != ''):
            alias.db.add_target_description(username, bio)

        # If we have valid data add this target to the gravatar source list
        alias.db.add_target_to_source_list(username, 'github')

    alias.db.mark_source_complete(username, 'github')


def __request(url, key):
    '''
    Make a request to the Github api.
    '''
    try:
        auth = requests.auth.HTTPBasicAuth(key, 'x-oauth-basic')        
        resp = requests.get(url, auth=auth)

        if resp.status_code == 200:
            return resp.json()
        else:
            return None

    except Exception as e:
        logger.error(e)
        return None


def __lookup_user(user, key):
    '''
    Lookup a Github user.
    '''

    try:
        # Lookup user
        resp = __request('https://api.github.com/users/' + user, key)

        if resp.status_code == 200:
            __process_results((user, resp))

        return None

    except Exception as e:
        logger.debug(str(e))
        return None


def __check_rate_limit():
    '''
    Check to see if we have hit our rate limit.
    '''
    resp = __request('https://api.github.com/rate_limit')

    if resp is not None:
        rate = resp.get('rate', {})
        if rate.get('remaining', 0) == 0:
            return True
        else:
            return False

    else:
        return False


#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
logger = logging.getLogger('Github')

def lookup():
    logger.info('Starting Github lookup.')

    cfg = alias.config.AliasConfig()

    # Load targets from the database.
    count = 0
    logger.info('Getting unprocessed Github usernames from database.')

    limited = True
    for target in alias.db.get_unchecked_targets('github', 'user'):
        count += 1
        
        if limited is False:
            __lookup_user(target, cfg.github_token)

        if (not limited) and (count % 100 == 0):
            limited = __check_rate_limit()

        if count % 1000 == 0:
            logger.info('Processed {0} Github users.'.format(count))

    logger.info('Processed {0} Github users.'.format(count))
    logger.info('Finished Github lookup.')
    return None
