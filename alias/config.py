# -*- coding: utf-8 -*-

import json
import os

class AliasConfig():
    def __init__(self):
        config_file = os.path.join('conf', 'alias.conf')
        config = self.__load_config(config_file)

        self.tw_consumer_key = config.get('tw_consumer_key', '')
        self.tw_consumer_secret = config.get('tw_consumer_secret', '')
        self.tw_token = config.get('tw_token', '')
        self.tw_token_secret = config.get('tw_token_secret', '')
        self.github_token = config.get('github_token', '')
        self.user_db = config.get('user_db')
        self.email_db = config.get('email_db')
        self.nym_db = config.get('nym_db')
        self.loc_db = config.get('loc_db')
        self.url_db = config.get('url_db')
        self.name_db = config.get('name_db')
        self.about_db = config.get('about_db')
        self.image_db = config.get('image_db')
        self.valid_sources = config.get('valid_sources')

    def __load_config(self, filename):
        try:
            with open(filename) as cfg:
                return json.loads(cfg.read())
        except:
            return None
