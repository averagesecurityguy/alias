#!/bin/sh

echo 'Starting Redis server.'
echo '/usr/local/bin/redis-server conf/redis.conf &'
/usr/local/bin/redis-server conf/redis.conf &
echo $! > redis.pid

echo 'Starting Alias web server.'
echo 'alias.py &'
./alias.py &
echo $! > alias.pid
