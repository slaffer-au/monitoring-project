#!/usr/bin/env python

import json
import os
import numpy as np
import requests


def load_json(filename):
    '''
    Reads in a plain text file formatted as JSON
    and returns a json object.

    Keyword arguments:
    filename -- file name to read in

    Returns:
    json object of the file
    '''

    with open(filename) as file:
        json_file = json.load(file)

    return json_file


def get_files(directory, prefix):
    '''
    Find all the files in directory starting with a given prefix

    Keyword arguments:
    directory -- the relative directory path to load
    prefix -- the prefix filename, for example "histogram_"

    Returns:
    List of filename strings
    '''

    result_list = []
    file_list = os.listdir(directory)

    for file in file_list:
        if file.find(prefix) >= 0:
            result_list.append(file)

    return result_list


def mutate(str):
    '''
    Fix broken stats
    '''
    if str == "0:959":
        return "0:959"
    if str == "1536:2495":
        return "960:2495"
    if str == "3072:4031":
        return "2496:4031"
    if str == "4608:5567":
        return "4032:5567"
    if str == "6144:7103":
        return "5568:7103"
    if str == "7680:8639":
        return "7104:8639"
    if str == "9216:10175":
        return "8640:10175"
    if str == "10752:11711":
        return "10176:11711"
    if str == "12288:13247":
        return "11712:13247"
    if str == "13824:*":
        return "13248:*"


def buffer_influx_measurements(json_data):
    '''
    Consumes json_data of buffer stats.

    Does not process anything other than egress queue.
    '''

    '''
    {
   "timestamp_info":{
      "start_datetime":"2017-03-28 01:19:29.623804",
      "end_datetime":"2017-03-28 01:19:29.628947"
   },
   "buffer_info":{
      "swp2":{
         "ingress priority":{
            "0":{
               "current_value":960,
               "watermark_value":3552
            },
            "1":{
               "current_value":0,
               "watermark_value":0
            },
            "2":{
               "current_value":0,
               "watermark_value":0
            },
            "3":{
               "current_value":0,
               "watermark_value":0
            },
            "4":{
               "current_value":0,
               "watermark_value":0
            },
            "5":{
               "current_value":0,
               "watermark_value":0
            },
            "6":{
               "current_value":0,
               "watermark_value":0
            },
            "7":{
               "current_value":0,
               "watermark_value":0
            }
         },
         "egress queue":{
            "0":{
               "current_value":0,
               "watermark_value":0
            },
            "1":{
               "current_value":0,
               "watermark_value":0
            },
            "2":{
               "current_value":0,
               "watermark_value":0
            },
            "3":{
               "current_value":0,
               "watermark_value":0
            },
            "4":{
               "current_value":0,
               "watermark_value":0
            },
            "5":{
               "current_value":0,
               "watermark_value":0
            },
            "6":{
               "current_value":0,
               "watermark_value":0
            },
            "7":{
               "current_value":0,
               "watermark_value":0
            }
         },
         "ingress port":{
            "0":{
               "current_value":960,
               "watermark_value":3360
            },
            "1":{
               "current_value":0,
               "watermark_value":0
            },
            "2":{
               "current_value":0,
               "watermark_value":0
            },
            "3":{
               "current_value":0,
               "watermark_value":0
            }
         }
      },
      '''

    # This is the InfluxDB key
    measurement_name = "buffer_stat"

    # Python doesn't like nanoseconds.
    # In order to convert to a Unix Epoch in nanoseconds we need numpy.
    # The .items() method returns the unix nanoseconds since epoch value.
    timestamp = np.datetime64(json_data["timestamp_info"]["end_datetime"]).astype('uint64')

    output = []

    # Loop over every interface captures in this run
    for interface in json_data["buffer_info"].keys():

        for queue in json_data["buffer_info"][interface]["egress queue"]:
            output.append(measurement_name + "," + "interface=" + interface + ",queue=" +
                          str(queue) + " watermark=" +
                          str(json_data["buffer_info"][interface]["egress queue"][queue]["watermark_value"]) + " " + str(timestamp))

    return output


def histogram_influx_measurements(json_data, mutate=False):
    '''
    Read in JSON formatted data from a histogram measurement.
    Return a string based on InfuxDB v1.2 Line Protocol.

    Keyword Arguments:
    json_data -- json formatted data to put into InfluxDB

    Returns:
    A list of InfluxDB v1.2 Line Protocol Strings
    '''

    '''
    InfluxDB line protocol docs:
    https://docs.influxdata.com/influxdb/v1.2/write_protocols/line_protocol_reference/

    Output Format:
    <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]

    Histogram Input Example:
        {
           "timestamp_info":{
              "start_datetime":"2017-03-28 01:13:09.355872",
              "end_datetime":"2017-03-28 01:13:09.357612"
           },
           "buffer_info":null,
           "packet_info":null,
           "histogram_info":{
              "swp2":{
                 "0:959":1016104
              },
              "swp32":{
                 "1536:2495":112701,
                 "0:959":904572,
                 "3072:4031":184
              },
              "swp1":{
                 "0:959":1016728
              }
           }
        }
    '''

    # This is the InfluxDB key
    measurement_name = "histogram"

    # Python doesn't like nanoseconds.
    # In order to convert to a Unix Epoch in nanoseconds we need numpy.
    # The .items() method returns the unix nanoseconds since epoch value.
    timestamp = np.datetime64(json_data["timestamp_info"]["end_datetime"]).astype('uint64')

    output = []

    # Loop over every interface captures in this run
    for interface, queues in json_data["histogram_info"].iteritems():
        buffer_depth = 0

        # look at all the queues under that interface and build the influx message
        for queue_number in queues:
            # The queues are a range
            # Let's simplify and just provide the low end of the range
            if mutate:  # use this if the provided buffer numbers were off.
                mutated_queue = mutate(queue_number)
            else:
                mutated_queue = queue_number

            buffer_num = mutated_queue[0:mutated_queue.find(":")]
            buffer_depth = buffer_depth + (float(buffer_num) * float(queues[queue_number]))
            output.append(measurement_name + "," + "interface=" + interface + ",buffer=" + str(buffer_num) + " " +
                          "buffer_value=" + str(queues[queue_number]) + " " + str(timestamp))

        # Convert buffer_depth from bytes to bits, then divide by egress interface speed, in our case 100Gbps
        output.append("delay,interface=" + interface + " delay=" + str((buffer_depth * 8) / 100000000000) + " " + str(timestamp))
    return output


def packet_influx_measurements(json_data):
    '''
    Read in JSON formatted data from a all_packets measurement.
    Return a string based on InfuxDB v1.2 Line Protocol.

    Keyword Arguments:
    json_data -- json formatted data to put into InfluxDB

    Returns:
    A list of InfluxDB v1.2 Line Protocol Strings
    '''

    '''
    InfluxDB line protocol docs:
    https://docs.influxdata.com/influxdb/v1.2/write_protocols/line_protocol_reference/

    Output Format:
    <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]

    Histogram Input Example:
        {
           "timestamp_info":{
              "start_datetime":"2017-03-23 04:31:35.672225",
              "end_datetime":"2017-03-23 04:31:35.701568"
           },
           "buffer_info":null,
           "packet_info":{
              "swp2":{
                 "total":{
                    "ingress":{
                       "mc":0,
                       "bc":0,
                       "bytes":0,
                       "jumbo":0,
                       "frames":0,
                       "uc":0
                    },
                    "egress":{
                       "mc":4,
                       "bc":0,
                       "bytes":0,
                       "jumbo":0,
                       "ecn_marked":0,
                       "frames":4,
                       "uc":0,
                       "wait":0
                    }
                 },
                 "discard":{
                    "ingress":{
                       "vlan_membership":0,
                       "opcodes":0,
                       "runt":0,
                       "tag_frame_type":0,
                       "buffer":0,
                       "general":0,
                       "other":0,
                       "policy":0
                    },
                    "egress":{
                       "vlan_membership":0,
                       "link_down":0,
                       "general":0,
                       "other":0,
                       "hoq":0,
                       "policy":0,
                       "mc_buffer":0
                    },
                    "general":{
                       "in_range_length":0,
                       "fcs":0,
                       "out_of_range_length":0,
                       "symbol_error":0,
                       "loopback_filter":0,
                       "too_long":0,
                       "port_isolation":0,
                       "alignment":0
                    }
                 },
                 "good":{
                    "ingress":{
                       "pause_mac_ctrl":0,
                       "mc":0,
                       "bc":0,
                       "mac_control":0,
                       "bytes":0,
                       "frames":0
                    },
                    "egress":{
                       "pause_mac_ctrl":0,
                       "mc":4,
                       "bc":0,
                       "mac_control":0,
                       "bytes":622,
                       "frames":4
                    }
                 },
                 "queue":{
                    "0":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":622,
                          "length":0,
                          "frames":4,
                          "uc":0
                       }
                    },
                    "1":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "2":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "3":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "4":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "5":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "6":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "7":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "8":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "9":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "10":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "11":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "12":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "13":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "14":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "15":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    }
                 },
                 "prio":{
                    "0":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "1":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "2":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "3":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "4":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "5":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "6":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    }
                 }
              },
              "swp32":{
                 "total":{
                    "ingress":{
                       "mc":0,
                       "bc":0,
                       "bytes":0,
                       "jumbo":0,
                       "frames":0,
                       "uc":0
                    },
                    "egress":{
                       "mc":10,
                       "bc":0,
                       "bytes":0,
                       "jumbo":0,
                       "ecn_marked":0,
                       "frames":10,
                       "uc":0,
                       "wait":0
                    }
                 },
                 "discard":{
                    "ingress":{
                       "vlan_membership":0,
                       "opcodes":0,
                       "runt":0,
                       "tag_frame_type":0,
                       "buffer":0,
                       "general":0,
                       "other":0,
                       "policy":0
                    },
                    "egress":{
                       "vlan_membership":0,
                       "link_down":0,
                       "general":0,
                       "other":0,
                       "hoq":0,
                       "policy":0,
                       "mc_buffer":0
                    },
                    "general":{
                       "in_range_length":0,
                       "fcs":0,
                       "out_of_range_length":0,
                       "symbol_error":0,
                       "loopback_filter":0,
                       "too_long":0,
                       "port_isolation":0,
                       "alignment":0
                    }
                 },
                 "good":{
                    "ingress":{
                       "pause_mac_ctrl":0,
                       "mc":0,
                       "bc":0,
                       "mac_control":0,
                       "bytes":0,
                       "frames":0
                    },
                    "egress":{
                       "pause_mac_ctrl":0,
                       "mc":10,
                       "bc":0,
                       "mac_control":0,
                       "bytes":1034,
                       "frames":10
                    }
                 },
                 "queue":{
                    "0":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":1034,
                          "length":0,
                          "frames":10,
                          "uc":0
                       }
                    },
                    "1":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "2":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "3":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "4":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "5":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "6":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "7":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "8":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "9":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "10":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "11":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "12":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "13":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "14":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "15":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    }
                 },
                 "prio":{
                    "0":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "1":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "2":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "3":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "4":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "5":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "6":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    }
                 }
              },
              "swp1":{
                 "total":{
                    "ingress":{
                       "mc":0,
                       "bc":0,
                       "bytes":0,
                       "jumbo":0,
                       "frames":0,
                       "uc":0
                    },
                    "egress":{
                       "mc":6,
                       "bc":0,
                       "bytes":0,
                       "jumbo":0,
                       "ecn_marked":0,
                       "frames":6,
                       "uc":0,
                       "wait":0
                    }
                 },
                 "discard":{
                    "ingress":{
                       "vlan_membership":0,
                       "opcodes":0,
                       "runt":0,
                       "tag_frame_type":0,
                       "buffer":0,
                       "general":0,
                       "other":0,
                       "policy":0
                    },
                    "egress":{
                       "vlan_membership":0,
                       "link_down":0,
                       "general":0,
                       "other":0,
                       "hoq":0,
                       "policy":0,
                       "mc_buffer":0
                    },
                    "general":{
                       "in_range_length":0,
                       "fcs":0,
                       "out_of_range_length":0,
                       "symbol_error":0,
                       "loopback_filter":0,
                       "too_long":0,
                       "port_isolation":0,
                       "alignment":0
                    }
                 },
                 "good":{
                    "ingress":{
                       "pause_mac_ctrl":0,
                       "mc":0,
                       "bc":0,
                       "mac_control":0,
                       "bytes":0,
                       "frames":0
                    },
                    "egress":{
                       "pause_mac_ctrl":0,
                       "mc":6,
                       "bc":0,
                       "mac_control":0,
                       "bytes":730,
                       "frames":6
                    }
                 },
                 "queue":{
                    "0":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":730,
                          "length":0,
                          "frames":6,
                          "uc":0
                       }
                    },
                    "1":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "2":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "3":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "4":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "5":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "6":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "7":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "8":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "9":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "10":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "11":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "12":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "13":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "14":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    },
                    "15":{
                       "egress":{
                          "uc_buffer":0,
                          "mc":0,
                          "bc":0,
                          "bytes":0,
                          "length":0,
                          "frames":0,
                          "uc":0
                       }
                    }
                 },
                 "prio":{
                    "0":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "1":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "2":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "3":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "4":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "5":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    },
                    "6":{
                       "ingress":{
                          "frames":0,
                          "discard":0,
                          "pause_frames":0,
                          "pause_duration":0
                       },
                       "egress":{
                          "pause_frames":0,
                          "pause_duration":0
                       }
                    }
                 }
              }
           },
           "histogram_info":null
        }
    '''

    # This is the InfluxDB key
    measurement_name = "packet_stats"

    # Python doesn't like nanoseconds.
    # In order to convert to a Unix Epoch in nanoseconds we need numpy.
    # The .items() method returns the unix nanoseconds since epoch value.
    timestamp = np.datetime64(json_data["timestamp_info"]["end_datetime"]).astype('uint64')

    output = []

    for interface in json_data["packet_info"].keys():
        ingress_frames_total = json_data["packet_info"][interface]["total"]["ingress"]["frames"]
        egress_frames_total = json_data["packet_info"][interface]["total"]["egress"]["frames"]

        mc_total_ingress = json_data["packet_info"][interface]["total"]["ingress"]["mc"]
        mc_total_egress = json_data["packet_info"][interface]["total"]["egress"]["mc"]

        mc_buffer_drop = json_data["packet_info"][interface]["discard"]["egress"]["mc_buffer"]

        mc_good_ingress = json_data["packet_info"][interface]["good"]["ingress"]["mc"]
        mc_good_egress = json_data["packet_info"][interface]["good"]["egress"]["mc"]

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=total,direction=ingress" + " " + "ingress_frames_total=" + str(ingress_frames_total) + " " + str(timestamp))

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=total,direction=egress" + " " + "ingress_frames_total=" + str(egress_frames_total) + " " + str(timestamp))

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=total,direction=ingress" + " " + "mc_total_ingress=" + str(mc_total_ingress) + " " + str(timestamp))

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=total,direction=egress" + " " + "mc_total_egress=" + str(mc_total_egress) + " " + str(timestamp))

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=discard,direction=egress" + " " + "mc_buffer_drop=" + str(mc_buffer_drop) + " " + str(timestamp))

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=good,direction=ingress" + " " + "mc_good_ingress=" + str(mc_good_ingress) + " " + str(timestamp))

        output.append(measurement_name + "," + "interface=" + interface +
                      ",type=good,direction=egress" + " " + "mc_good_egress=" + str(mc_good_egress) + " " + str(timestamp))

    return output


def load_telegraf_data(filename):
    '''
    Read in a telegraf generated text file
    and import it into InfluxDB

    Keyword Arguments:
    filename -- telegraf generated file to load
    '''

    url = "http://localhost:8086/write?db=network"

    with open(filename, 'r') as file:
        telegraf_data = file.readlines()

    counter = 0
    batch = []
    for line in telegraf_data:
        line.replace(",host=host=mlx-2700-06", ",host=leaf01,role=leaf")
        batch.append(line)

        if counter % 100 == 0:
            data = "\n".join(batch)
            r = requests.post(url, data)
            batch = []
            if not r.ok:
                print("Error with " + str(data))
                break

        counter = counter + 1

    print("Loaded " + str(counter) + " telegraf records")


def load_histogram_data(directory):
    histogram_files = get_files(directory, "histogram_")

    # InfluxDB expects nanosecond precision. We have timestamps in microseconds
    # Trust me, if you don't pass "precision=u" you'll have a bad time
    url = "http://localhost:8086/write?db=network&precision=u"

    data = []
    counter = 0

    for file in histogram_files:
        output = histogram_influx_measurements(load_json(directory + file))

        data = "\n".join(output)

        # print data
        # print load_json(file)
        r = requests.post(url, data)
        # break
        if not r.ok:
            print "Error on: " + data
            print "File: " + file
            print str(counter) + " histogram records loaded"
            break

        counter = counter + 1

    print str(counter) + " histogram records loaded"


def load_buffer_data(directory):
    buffer_files = get_files(directory, "buffer_stats_")

    # InfluxDB expects nanosecond precision. We have timestamps in microseconds
    # Trust me, if you don't pass "precision=u" you'll have a bad time
    url = "http://localhost:8086/write?db=network&precision=u"

    data = []
    counter = 0

    for file in buffer_files:
        output = buffer_influx_measurements(load_json(directory + file))

        data = "\n".join(output)

        # print data
        # print load_json(file)
        r = requests.post(url, data)
        # break
        if not r.ok:
            print "Error on: " + data
            print "File: " + file
            print str(counter) + " buffer stats records loaded"
            break

        counter = counter + 1

    print str(counter) + " buffer stats records loaded"


def load_packet_data(directory):
    buffer_files = get_files(directory, "all_packet_stats_")

    # InfluxDB expects nanosecond precision. We have timestamps in microseconds
    # Trust me, if you don't pass "precision=u" you'll have a bad time
    url = "http://localhost:8086/write?db=network&precision=u"

    data = []
    counter = 0

    for file in buffer_files:
        output = packet_influx_measurements(load_json(directory + file))

        data = "\n".join(output)

        # print data
        # print load_json(file)
        r = requests.post(url, data)
        # break
        if not r.ok:
            print "Error on: " + data
            print "File: " + file
            print str(counter) + " packet stats records loaded"
            break

        counter = counter + 1

    print str(counter) + " packet stats records loaded"


if __name__ == "__main__":

    # Directories require trailing /
    load_telegraf_data("buffer_stats/metrics.out")
    load_histogram_data("buffer_stats/")
    load_buffer_data("buffer_stats/")
    load_packet_data("buffer_stats/")

    exit(0)
