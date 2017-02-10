import redis
import subprocess
import json

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)
#print redis_db.keys()

#commands = ["ls -l","ls"]
commands = ["net"]

for command in commands:
  #call(["ls", "-l"])
  result = subprocess.check_output(batcmd, shell=True)
  print result