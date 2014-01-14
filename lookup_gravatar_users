#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import multiprocessing
import json
import os
import sys
import redis
import Queue

#-----------------------------------------------------------------------------
# Function Definitions
#-----------------------------------------------------------------------------
def get_names(name):
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


def get_locations(location):
    '''
    Get the location data.
    '''
    locations = []

    if location is not None:
        locations.append(location)

    return locations


def get_emails(emails, ims):
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


def get_nyms(ims):
    '''
    Pull any additional usernames from the IMs list.
    '''
    nym_list = []

    if ims is not None:
        for i in ims:
            nym_list.append('{0} ({1})'.format(i['value'], i['type']))

    return nym_list


def get_urls(data):
    '''
    Pull any urls from the gravatar data.
    '''
    url_list = {}

    if data.get('profileUrl') is not None:
        url_list[data['profileUrl']] = 1

    if data.get('thumbnailUrl') is not None:
        url_list[data['thumbnailUrl']] = 1

    if data.get('urls') is not None:
        for u in data.get('urls'):
            url_list[u['value']] = 1

    if data.get('profileBackground') is not None:
        if data['profileBackground'].get('url') is not None:
            url_list[data['profileBackground']['url']] = 1

    if data.get('photos') is not None:
        for u in data.get('photos'):
            url_list[u['value']] = 1

    return url_list.keys()


def get_descriptions(description):
    '''
    Get the description data.
    '''
    descriptions = []

    if description is not None:
        descriptions.append(description)

    return descriptions


def process_results(result):
    '''
    Get each of the data items we are looking for from the result and write
    them to the databases.
    '''
    username = result[0]
    data = result[1]['entry'][0]

    emails = get_emails(data.get('emails'), data.get('ims'))
    for email in emails:
        email_db.lpush(username + ':gravatar', email.lower())
        email_db.lpush(email.lower(), username)

    nyms = get_nyms(data.get('ims'))
    for nym in nyms:
        nym_db.lpush(username + ':gravatar', nym.lower())
        nym_db.lpush(nym.lower(), username)
    
    urls = get_urls(data)
    for url in urls:
        url_db.lpush(username + ':gravatar', url)
        url_db.lpush(url, username)

    locations = get_locations(data.get('currentLocation'))
    for loc in locations:
        loc_db.lpush(username + ':gravatar', loc.lower())
        loc_db.lpush(loc.lower(), username)

    names = get_names(data.get('name'))
    for name in names:
        name_db.lpush(username + ':gravatar', name.lower())
        name_db.lpush(name.lower(), username)

    descriptions = get_descriptions(data.get('aboutMe'))
    for desc in descriptions:
        about_db.lpush(username + ':gravatar', desc)

    user_db.hset(username, 'gravatar', 1)


def worker(user_queue, result_queue):
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


def writer(result_queue):
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
            process_results(result)

        if count % 1000 == 0:
            print '[*] Processed {0}'.format(count)


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

user_queue = multiprocessing.Queue()
result_queue = multiprocessing.Queue()
procs = []

# Load screen names from a file.
sn_count = 0
print '[*] Loading screen names into queue.'
for user in user_db.keys('*'):
    if user_db.hget(user, 'gravatar') == '1':
        continue
    
    sn_count += 1
    user_queue.put({'user': user, 'gvuser': user})

print '[*] Loaded {0} screen names into the queue.'.format(sn_count)

for i in range(4):
    p = multiprocessing.Process(target=worker, args=(user_queue,
                                                     result_queue))
    procs.append(p)
    p.start()


# Create a thread to write the results to the file.
w = multiprocessing.Process(target=writer, args=(result_queue,))
procs.append(w)
w.start()

# Wait for all worker processes to finish
for p in procs:
    p.join()

