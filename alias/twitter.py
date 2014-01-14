import time
import requests

import oauth

class TwitterConnectionException(Exception):
    pass


class Twitter():
    def __init__(self, ck, cs, t, ts):
        self.consumer_key = ck
        self.consumer_secret = cs
        self.token = t
        self.token_secret = ts
        self.__base = 'https://api.twitter.com/1.1'
        self.__ssn = requests.Session()
        self.__ssn.auth = oauth.TwitterSingleOAuth(self.consumer_key,
                                                   self.consumer_secret,
                                                   self.token,
                                                   self.token_secret)

    def __process_response(self, r):
        if r.status_code == 429:
            return {}
        elif r.status_code == 404:
            return {}
        else:
            try:
                return r.json()
            except:
                print r.content


    def __connect(self, method, resource, params=None, data=None):
        '''Make a GET or POST request to the API.'''
        url = self.__base + resource

        try:
            if method.upper() == 'GET':
                r = self.__ssn.get(url, params=params)
                return self.__process_response(r)

            if method.upper() == 'POST':
                r = self.__ssn.post(url, data=data)
                return self.__process_response(r)
        except requests.exceptions.ConnectionError, e:
            raise TwitterConnectionException(str(e))

    def __users(self, url, params={}, count=200, total=3000):
        '''
        Returns a list of items provided by the URL using the specified
        parameters. Should work for the following URLs:

        followers/list
        friends/list
        '''
        users = []
        cursor = -1

        while cursor != 0:
            params['next_cursor'] = cursor
            params['count'] = count

            resp = self.__connect('GET', url, params=params)
            if resp == {}:
                cursor = 0
            else:
                users.extend(resp['users'])
                cursor = resp['next_cursor']

        return users

    def __statuses(self, url, params={}, count=200, total=800):
        '''
        Get the statuses provided by the URL using the specified parameters.
        '''
        params['count'] = count

        statuses = []
        requested = 0

        while requested < total:
            ids = []
            resp = self.__connect('GET', url, params=params)

            if resp == {}:
                requested = total
            else:
                ids = [r['id'] for r in resp]
                statuses.extend(resp)

                params['max_id'] = min(ids)
                requested += count

        return statuses

    def followers(self, screen_name):
        '''
        Get the followers of the specified user account.
        ''' 
        params = {'screen_name': screen_name,
                  'include_user_entities': False}
    
        return self.__users('/followers/list.json', params)

    def friends(self, screen_name):
        '''
        Get the friends (people they follow) of the specified user account.
        '''
        params = {'screen_name': screen_name,
                  'include_user_entities': False}

        return self.__users('friends/list.json', params)

    def tweets(self, screen_name):
        '''
        Get the last 3200 statuses for the specified screen_name. Replies are
        not included in the results.
        '''
        params = {'screen_name': screen_name, 'include_rts': False}
        return self.__statuses('/statuses/user_timeline.json',
                               params=params,
                               total=3200)

    def user(self, screen_name):
        '''
        Get general information about the specified user account.
        '''
        params = {'screen_name': screen_name}
        return self.__connect('GET', '/users/show.json', params=params)

    def user_lookup(self, screen_names):
        '''
        Lookup details on up to 100 screen_names. If more than 100
        screen_names are provided, only the results for the first 100 will be
        returned. Sleep for 6 seconds after each request to prevent hitting
        the rate-limit. Do not like sleeping but not sure how else to do it.
        '''
        data = {'screen_name': ','.join(screen_names[:100]),
                'include_entities': False}

        users = self.__connect('POST', '/users/lookup.json', data=data)
        time.sleep(6)

        # If no usernames are found an empty dictionary will be returned.
        if users == {}:
            return []
        else:
            return users
