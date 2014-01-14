alias
=====
The alias tool takes a list of usernames and attempts to gather information about the username from Twitter and Gravatar.

Prerequisites
-------------
pip install flask
pip install pyredis
install redis

Server Management
-----------------
start_alias.sh - Starts the Redis server and the alias web server.
stop_alias.sh - Stops the Redis server and the alias web server.

Building the Database
---------------------
To build the database you must first load the usernames using `load_usernames username_file`. After the usernames are loaded, lookup the users using the `lookup_twitter_users` and `lookup_gravatar_users` scripts. When processing a large set of usernames, the lookup_* scripts may fail for various reasons. If the scripts fail for any reason, restart them and they will resume where they left off. The scripts should be run until there are no more usernames to be processed.

The database only has to be built once. After that you can search through the data as often as you want. The Redis database is saved in the data folder as alias.rdb. This file can be renamed to save the dataset for later use.

View the Data
-------------
Once the database is built, you can go to [http://127.0.0.1:5000/](http://127.0.0.1:5000) to view the data.
