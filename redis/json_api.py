import redis
from subprocess import call

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)
#print redis_db.keys()

commands = ["ls -l","ls"]

for command in commands:
  #call(["ls", "-l"])
  call(command.split())