# -*- coding: utf-8 -*-

import json
import redis

class AliasConfig():
    def __init__(self, config_file):
        self.config = self.__load_config(config_file)
        self.user_db = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.email_db = redis.StrictRedis(host='localhost', port=6379, db=1)
        self.nym_db = redis.StrictRedis(host='localhost', port=6379, db=2)
        self.loc_db = redis.StrictRedis(host='localhost', port=6379, db=3)
        self.url_db = redis.StrictRedis(host='localhost', port=6379, db=4)
        self.name_db = redis.StrictRedis(host='localhost', port=6379, db=5)
        self.desc_db = redis.StrictRedis(host='localhost', port=6379, db=6)
        self.image_db = redis.StrictRedis(host='localhost', port=6379, db=7)

    def __load_config(self, filename):
        try:
            with open(filename) as cfg:
                return json.loads(cfg.read())
        except:
            return None

    def tw_consumer_key(self):
        return self.config.get('tw_consumer_key')

    def tw_consumer_secret(self):
        return self.config.get('tw_consumer_secret')

    def tw_token(self):
        return self.config.get('tw_token')

    def tw_token_secret(self):
        return self.config.get('tw_token_secret')