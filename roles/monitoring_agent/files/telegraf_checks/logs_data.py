from pygtail import Pygtail
import sys
from output_module import ExportData
from socket import gethostname


"""
Collects log information and uploads it as a metric.
Uses the pygtail library which is installed via pip
"""


def parse_logs():
    data = ExportData("logs")
    reason = ""
    peer = ""

    for line in Pygtail("/var/log/syslog"):
        # print line
        #if "sent to neighbor" in line:
            #reason = line.split('(')[1].split(')')[0]
        if "%ADJCHANGE: neighbor" in line:
            # print "***found*** " + '"'+str(line.split(' ')[5])+'"'
            msg = line.split()
            peer = msg[5]
            status = msg[9]
            reason = msg[-2]+" "+msg[-1]
        if len(reason) > 0 and len(peer) > 0:
            data.add_row({"msg":"log"},{"reason":'"BGP Neighbor '+status+": "+reason+" on "+gethostname()+" from "+peer+'"',"peer":'"'+peer+'"'})
            reason = ""
            peer = ""

    # data.show_data()
    data.send_data("cli")

parse_logs()

exit(0)
