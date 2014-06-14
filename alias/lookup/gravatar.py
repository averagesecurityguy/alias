#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging

import alias.db

#-----------------------------------------------------------------------------
# Function Definitions
#-----------------------------------------------------------------------------
def __get_names(name):
    '''
    Get the formatted name if available, if not build the name from the given
    and family names.
    '''
    logger.debug('Processing name.')
    name_list = []

    if (name == []) or (name is None):
        return name_list

    if name.get('formatted') is not None:
        name_list.append(unicode(name['formatted']))
    else:
        given = name.get('givenName', u'')
        family = name.get('familyName', u'')
        name_list.append(u'{0} {1}'.format(given, family).strip())

    return name_list


def __get_locations(location):
    '''
    Get the location data.
    '''
    logger.debug('Processing locations.')
    locations = []

    if location is not None:
        locations.append(location)

    return locations


def __get_emails(emails, ims):
    '''
    Pull any email addresses from the emails list and from the IMs list.
    '''
    logger.debug('Processing email addresses.')
    email_list = []

    if emails is not None:
        e = [e['value'] for e in emails]
        email_list.extend(e)

    if ims is not None:
        for i in ims:
            if '@' in i['value']:
                email_list.append(i['value'])

    return email_list


def __get_accounts(accounts):
    '''
    Pull any additional usernames from the accounts list.
    '''
    logger.debug('Processing accounts.')
    acct_list = []

    if accounts is not None:
        for a in accounts:
            acct_list.append('{0} ({1})'.format(a['username'], a['shortname']))

    return acct_list


def __get_urls_from_accounts(accounts):
    '''
    Pull any additional URLs from the accounts list.
    '''
    logger.debug('Processing URLs.')
    url_list = []

    if accounts is not None:
        for a in accounts:
            url_list.append(a.get('url', '').replace('\/', '/'))

    return url_list


def __get_nyms(ims):
    '''
    Pull any additional usernames from the IMs list.
    '''
    logger.debug('Processing IM list.')
    nym_list = []

    if ims is not None:
        for i in ims:
            nym_list.append('{0} ({1})'.format(i['value'], i['type']))

    return nym_list


def __get_images(data):
    '''
    Pull any image links from the gravatar data.
    '''
    logger.debug('Processing image list.')
    image_list = []

    if data.get('thumbnailUrl') is not None:
        image_list.append(data['thumbnailUrl'])

    if data.get('profileBackground') is not None:
        if data['profileBackground'].get('url') is not None:
            image_list.append(data['profileBackground']['url'])

    if data.get('photos') is not None:
        for u in data.get('photos'):
            image_list.append(u['value'])

    return image_list


def __get_urls(data):
    '''
    Pull any urls from the gravatar data.
    '''
    logger.debug('Processing URLs.')
    url_list = []

    if data.get('urls') is not None:
        for u in data.get('urls'):
            url_list.append(u['value'])

    return url_list


def __get_descriptions(description):
    '''
    Get the description data.
    '''
    logger.debug('Processing description.')
    descriptions = []

    if description is not None:
        descriptions.append(description)

    return descriptions


def __process_results(result):
    '''
    Get each of the data items we are looking for from the result and write
    them to the databases.
    '''
    logger.debug('Processing result.')

    username = result[0]

    if result[1] is not None:
        data = result[1]['entry'][0]
        emails = __get_emails(data.get('emails'), data.get('ims'))
        for email in sorted(set(emails)):
            alias.db.add_target_email(username, email)

        nyms = __get_nyms(data.get('ims'))
        for nym in sorted(set(nyms)):
            alias.db.add_target_nym(username, nym)

        accts = __get_accounts(data.get('accounts'))
        for acct in sorted(set(accts)):
            alias.db.add_target_nym(username, acct)
        
        urls = __get_urls(data)
        for url in sorted(set(urls)):
            alias.db.add_target_url(username, url)

        urls = __get_urls_from_accounts(data.get('accounts'))
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

        # If we have valid data add this target to the gravatar source list
        alias.db.add_target_to_source_list(username, 'gravatar')

    alias.db.mark_source_complete(username, 'gravatar')


def __lookup_user(user):
    '''
    Lookup the user. Sometimes Gravatar will have an alternate username as
    the primary username on the account. We track that username using the
    user['gvuser'] value.
    '''

    try:
        url = 'http://en.gravatar.com/{0}.json'.format(user['gvuser'])
        resp = requests.get(url, allow_redirects=False)
        if resp.status_code == 404:
            __process_results((user['user'], None))
            return None

        elif resp.status_code == 302:
            location = resp.headers['location']
            if location == '/profiles/no-such-user':
                __process_results((user['user'], None))
                return None

            if not location.startswith('http://en.gravatar.com'):
                user['gvuser'] = location.lstrip('/').lower()
                return user 
        
        else:
            __process_results((user['user'], resp.json()))
            return None

    except Exception as e:
        logger.debug(str(e))
        return None


#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
logger = logging.getLogger('Gravatar')

def lookup():
    logger.info('Starting Gravatar lookup.')
    
    # Load targets from the database.
    count = 0
    logger.info('Getting unprocessed Gravatar usernames from database.')
    for target in alias.db.get_unchecked_targets('gravatar', 'user'):
        count += 1

        # Skip targets with a . in them.
        if target.find('.') != -1:
            continue

        resp = __lookup_user({'user': target, 'gvuser': target})
        if resp is not None:
            # 
            # When the response is not None, the user has an alternate name on
            # Gravatar. Lookup that name instead.
            __lookup_user(resp)

        if count % 1000 == 0:
            logger.info('Processed {0} Gravatar users.'.format(count))

    logger.info('Processed {0} Gravatar users.'.format(count))
    logger.info('Finished Gravatar lookup.')

    return None
