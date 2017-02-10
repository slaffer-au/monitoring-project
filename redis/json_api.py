import redis
import subprocess
import json
import time

redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)
# print redis_db.keys()

# commands = ["ls -l","ls"]
commands = ["netq check bgp json"]
failed_nodes = []

for command in commands:
  # call(["ls", "-l"])
  result = subprocess.check_output(command, shell=True)
  print result
  parsed_json =  json.loads(result)
  # print parsed_json
  # print
  # print parsed_json[0]
  # print
  # print parsed_json[0][0]
  for node in parsed_json[0]:
    #print node['reason']
    if node['reason'] != '':
      #print node['reason']
      failed_nodes.append(node)
  print failed_nodes

print len(failed_nodes)
print len(parsed_json[0])

failed_output = '{"target":"failed_peers", "datapoints": [[%d,%d]]}' % (len(failed_nodes), time.time())
total_output = '{"target":"total_peers", "datapoints": [[%d,%d]]}' % (len(parsed_json[0]), time.time())
# print output

target = open("series.json",'w')

target.truncate()

target.write("[\n")
target.write("\t"+total_output+",\n")
target.write("\t"+failed_output)
target.write("\n]")
target.close()
