#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import multiprocessing
import Queue

import alias.db

#-----------------------------------------------------------------------------
# Function Definitions
#-----------------------------------------------------------------------------
def __get_names(name):
    '''
    Get the formatted name if available, if not build the name from the given
    and family names.
    '''
    name_list = []

    if (name == []) or (name is None):
        return name_list

    if name.get('formatted') is not None:
        name_list.append(name['formatted'])
    else:
        given = name.get('given')
        family = name.get('family')
        name_list.append('{0} {1}'.format(given, family).strip())

    return name_list


def __get_locations(location):
    '''
    Get the location data.
    '''
    locations = []

    if location is not None:
        locations.append(location)

    return locations


def __get_emails(emails, ims):
    '''
    Pull any email addresses from the emails list and from the IMs list.
    '''
    email_list = []

    if emails is not None:
        e = [e['value'] for e in emails]
        email_list.extend(e)

    if ims is not None:
        for i in ims:
            if '@' in i['value']:
                email_list.append(i['value'])

    return email_list


def __get_nyms(ims):
    '''
    Pull any additional usernames from the IMs list.
    '''
    nym_list = []

    if ims is not None:
        for i in ims:
            nym_list.append('{0} ({1})'.format(i['value'], i['type']))

    return nym_list


def __get_images(data):
    '''
    Pull any image links from the gravatar data.
    '''
    image_list = {}

    if data.get('thumbnailUrl') is not None:
        image_list[data['thumbnailUrl']] = 1

    if data.get('profileBackground') is not None:
        if data['profileBackground'].get('url') is not None:
            image_list[data['profileBackground']['url']] = 1

    if data.get('photos') is not None:
        for u in data.get('photos'):
            image_list[u['value']] = 1

    return image_list.keys()


def __get_urls(data):
    '''
    Pull any urls from the gravatar data.
    '''
    url_list = {}

    if data.get('urls') is not None:
        for u in data.get('urls'):
            url_list[u['value']] = 1

    return url_list.keys()


def __get_descriptions(description):
    '''
    Get the description data.
    '''
    descriptions = []

    if description is not None:
        descriptions.append(description)

    return descriptions


def __process_results(result):
    '''
    Get each of the data items we are looking for from the result and write
    them to the databases.
    '''
    username = result[0]
    data = result[1]['entry'][0]

    emails = __get_emails(data.get('emails'), data.get('ims'))
    for email in sorted(set(emails)):
        alias.db.add_target_email(username, email)

    nyms = __get_nyms(data.get('ims'))
    for nym in sorted(set(nyms)):
        alias.db.add_target_nym(username, nym)
    
    urls = __get_urls(data)
    for url in sorted(set(urls)):
        alias.db.add_target_url(username, url)

    locations = __get_locations(data.get('currentLocation'))
    for loc in sorted(set(locations)):
        alias.db.add_target_location(username, loc)

    names = __get_names(data.get('name'))
    for name in sorted(set(names)):
        alias.db.add_target_name(username, name)

    descriptions = __get_descriptions(data.get('aboutMe'))
    for desc in descriptions:
        alias.db.add_target_description(username, desc)

    alias.db.mark_source_complete(username, 'gravatar')


def __worker(user_queue, result_queue):
    '''
    Thread to lookup gravatar results.
    '''
    print '[*] Starting new worker thread.'
    while True:
        # If there are no creds to test, stop the thread
        try:
            user = user_queue.get(timeout=10)
        except Queue.Empty:
            print '[-] User queue is empty, quitting.'
            return

        url = 'http://en.gravatar.com/{0}.json'.format(user['gvuser'])
        resp = requests.get(url, allow_redirects=False)
        if resp.status_code == 404:
            result_queue.put(None)
        elif resp.status_code == 302:
            location = resp.headers['location']
            if location == '/profiles/no-such-user':
                result_queue.put(None)

            if not location.startswith('http://en.gravatar.com'):
                user['gvuser'] = location.lstrip('/').lower()
                user_queue.put(user)
        else:
            result_queue.put((user['user'], resp.json()))


def __writer(result_queue):
    '''
    Thread to write Gravatar results to the database.
    '''
    print '[*] Starting writer thread.'
    count = 0
    while True:
        count += 1

        # If there are no results to write, stop the thread
        try:
            result = result_queue.get(timeout=30)
        except Queue.Empty:
            print '[-] Result queue is empty, quitting'
            return

        # Process the result pulled from the queue
        if result is not None:
            __process_results(result)

        if count % 1000 == 0:
            print '[*] Processed {0}'.format(count)


#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
def lookup():
    user_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    procs = []

    # Load targets from the database.
    count = 0
    print '[*] Loading screen names into queue.'
    for target in alias.db.get_unchecked_targets('gravatar', 'all'):
        count += 1
        user_queue.put({'user': target, 'gvuser': target})

    print '[*] Loaded {0} targets into the queue.'.format(count)

    for i in range(4):
        p = multiprocessing.Process(target=__worker, args=(user_queue,
                                                         result_queue))
        procs.append(p)
        p.start()


    # Create a thread to write the results to the file.
    w = multiprocessing.Process(target=__writer, args=(result_queue,))
    procs.append(w)
    w.start()

    # Wait for all worker processes to finish
    for p in procs:
        p.join()
