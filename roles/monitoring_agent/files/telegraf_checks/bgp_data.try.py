#!/usr/bin/env python2.7

# Note: You can't run this in the same folder (network_common/files) as ujson.so.
# Python will try to load the .so and it will fail since it was built for CL

import json
import subprocess
from output_module import ExportData

#-------------------------------------------------------------------------------

def run_json_command(command):
    """
    Run a command that returns json data. Takes in a list of command arguments
    :return: JSON string output from command
    """
    json_str = ''
    try:
        json_str = subprocess.check_output(command)
    except OSError as e:
        print("problem executing vtysh %s " % (e))
        exit(3)

    return json_str

#-------------------------------------------------------------------------------

def bgp_neighbor_information():

    data = ExportData("bgpstat")

    # get number of good and failed neighbors
    #
    neighbor_sum_output = run_json_command(
        ['net', 'show', 'bgp', 'ipv4', 'unicast', 'summary', 'json'])

    # if bgp is not configured no output is returned
    if len(neighbor_sum_output) == 0:
        print("No neighbor output. Is BGP configured?")
        exit(3)

# this line causes problems with telegraf
    json_neighbor_sum = json.loads(neighbor_sum_output.decode('utf-8'))

    if len(json_neighbor_sum["peers"]) == 0:
        print("No BGP peers found. Are any BGP peers configured?")
        exit(3)

    num_peers=0
    failed_peers=0
    for peer in json_neighbor_sum["peers"].keys():

        #Check if the current state of the peer is establishes to count number of up peers
        if json_neighbor_sum["peers"][peer]["state"] == "Established":
            num_peers += 1
        else:
            failed_peers += 1
    data.add_row({},{"num_peers":num_peers, "failed_peers":failed_peers})

    # get number of external BGP routes
    #
    route_output = run_json_command(
        ['net', 'show', 'bgp', 'ipv4', 'unicast', 'json'])

    if len(route_output) == 0:
        print("No route output. Is BGP configured?")
        exit(3)

# this line causes problems with telegraf
    json_route_output = json.loads(route_output.decode('utf-8'))

    internal = 0
    external = 0
    for (route, info) in json_route_output['routes'].iteritems():
        if info[0]['pathFrom'] == "external":
            external += 1
        if info[0]['pathFrom'] == "internal":
            internal += 1
    data.add_row({},{"num_external":external, "num_internal":internal})

    # data.show_data()
    data.send_data("cli")

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    bgp_neighbor_information()
    exit(0)

