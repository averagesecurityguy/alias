alias
=====
The alias tool takes a list of usernames and attempts to gather information about the username from Twitter and Gravatar.

Prerequisites
-------------
flask - http://flask.pocoo.org/
redis-py - https://github.com/andymccurdy/redis-py
redis - http://redis.io/

Installation
------------
git clone https://github.com/averagesecurityguy/alias

Configuration
-------------
Rename and edit the conf/alias.conf.template and conf/redis.conf.template files as needed. You must add the Twitter and Github OAuth keys to retrieve data from those services.

Server Management
-----------------
start_alias - Starts the Redis server, the alias web server, and the lookup services.
stop_alias - Stops the Redis server, the alias web server, and the lookup services.

Usage
-----
Run the start_alias script. If the script runs successfully go to http://127.0.0.1:5000. Next, go to the Add Users tab and upload a comma delimited list of usernames. You can find a list of 10,000 usernames from the Snapchat leak in the data folder. Next, go to the View Targets tab and view the information found on the uploaded usernames. The lookup services run in the background so data will be continually added to this page until all the users have been looked up on each service. You will need to refresh the page regularly to see any updates. You can also look at the View Services tab to get a list of services where the uploaded usernames were found.

Data Sources
------------
Alias will search for users on Twitter, Gravatar, and Github.
