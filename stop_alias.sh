#!/bin/sh

echo 'Stopping Alias web server.'
alias_pid = `cat conf/alias.pid`
kill $alias_pid

echo 'Stopping Redis server.'
redis_pid = `cat conf/redis.pid`
kill $redis_pid