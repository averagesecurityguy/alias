#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import multiprocessing
import Queue
import logging

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

    for key in data:
        if key == 'url':
            continue
        if key == 'starred_url':
            continue
        if key == 'events_url':
            continue
        if key == 'received_events_url':
            continue

        if key.starts_with('_url'):
            url = data[key]
            idx = url.find('{')

            if idx == -1:
                url_list.append(url)
            else:
                url_list.append(url[:idx + 1])

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


def __worker(user_queue, result_queue, key):
    '''
    Thread to lookup Github users.
    '''
    logger.debug('Starting new worker thread.')
    while True:
        # If there are no creds to test, stop the thread
        try:
            user = user_queue.get(timeout=10)
        except Queue.Empty:
            logger.debug('User queue is empty, quitting.')
            return

        # Lookup user
        url = 'https://api.github.com/users/{0}'.format(user)
        auth = requests.auth.HTTPBasicAuth(key, 'x-oauth-basic')        
        resp = requests.get(url, auth=auth)

        # Ensure we haven't hit our rate limit.
        if resp.headers['X-RateLimit-Remaining'] == '0':
            logger.warning('Rate limit exceeded. Finished for now.')
            return

        # If we have not hit our rate limit then add the result to the queue.
        result_queue.put((user, resp.json()))


def __writer(result_queue):
    '''
    Thread to write Github results to the database.
    '''
    logger.debug('Starting writer thread.')
    count = 0
    while True:
        count += 1

        # If there are no results to write, stop the thread
        try:
            result = result_queue.get(timeout=30)
        except Queue.Empty:
            logger.debug('Result queue is empty, quitting')
            return

        # Process the result pulled from the queue
        __process_results(result)

        if count % 1000 == 0:
            logger.debug('Processed {0}'.format(count))


#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
logger = logging.getLogger('GITHUB')

def lookup():
    logger.info('Starting Github lookup.')

    cfg = alias.config.AliasConfig()
    user_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    procs = []

    # Load targets from the database.
    count = 0
    logger.info('Loading screen names into queue.')
    for target in alias.db.get_unchecked_targets('github', 'user'):
        count += 1
        user_queue.put(target)

    logger.info('Loaded {0} targets into the queue.'.format(count))

    # Create lookup threads.
    for i in range(4):
        p = multiprocessing.Process(target=__worker, args=(user_queue,
                                                           result_queue,
                                                           cfg.github_token))
        procs.append(p)
        p.start()


    # Create a thread to write the results to the file.
    w = multiprocessing.Process(target=__writer, args=(result_queue,))
    procs.append(w)
    w.start()

    # Wait for all worker processes to finish
    for p in procs:
        p.join()

    logger.info('Finished Github lookup.')