#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import redis

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def load_usernames(filename):
    '''
    Open the username file and load the data into the user database.
    '''
    print '[*] Loading usernames into the database.'
    count = 0
    with open(filename) as userfile:
        for line in userfile:
            count += 1
            data = {'gravatar': None, 'twitter': None}
            user = line.lower().strip().replace('\x00', '')
            user_db.hmset(user, data)

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
if len(sys.argv) != 2:
    print 'Usage: load_usernames username_file'
    sys.exit(1)

cfg = load_configuration(os.path.join('conf', 'app.conf'))
user_db = redis.StrictRedis(host='localhost', port=6379, db=cfg['user_db'])

load_usernames(sys.argv[1])
