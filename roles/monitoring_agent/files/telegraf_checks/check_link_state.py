#! /usr/bin/python

import sys
import os
from socket import gethostname
import subprocess
import json
from output_module import ExportData

"""
Checks the link state information and exports it as link data
Saves last link state in /var/run/check_link_state
"""

#-------------------------------------------------------------------------------

def check_link_state():
    # get the list of up interfaces
    #
    output=subprocess.check_output(['/usr/bin/netshow interface all -j'],shell=True)
    parsed_output=json.loads(output)
    UP = list()
    for I in parsed_output:
        if parsed_output[I]['linkstate'] == "UP":
            UP.append(I)

    # get the last set of up interfaces and save the current one for next go
    #
    LAST_FILE = "/tmp/check_link_state"
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, 'r') as f:
	    LAST = json.load(f)
    else:
        LAST = None
    with open(LAST_FILE, 'w') as f:
        json.dump(UP, f)
    
    # compare the two sets and log the differences (this is ugly, but it's late)
    #
    if LAST != None:
        data = ExportData("logs")
        changed = list()
        for I in UP:
            if I not in LAST:
                changed.append(I)
        if changed:
            data.add_row({"msg":"link"},{"reason":'"'+",".join(changed)+" up"+'"',"peer":'""'})
        changed = list()
        for I in LAST:
            if I not in UP:
                changed.append(I)
        if changed:
            data.add_row({"msg":"link"},{"reason":'"'+",".join(changed)+" down"+'"',"peer":'""'})
    data.send_data("cli")

    # track the number of front panel interfaces
    #
    num_swp = 0
    num_fp = 0
    for I in UP:
        if str(I).startswith("swp"):
            num_swp += 1
        if str(I).startswith("_fp"):
            num_swp += 1
    data = ExportData("link_state")
    data.add_row({},{"num_swp":num_swp, "num_fp":num_fp})
    data.send_data("cli")


#-------------------------------------------------------------------------------

if __name__ == "__main__":
    check_link_state()
    exit(0)