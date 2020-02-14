#!/usr/bin/python
import requests
import json
import csv
import sys
from datetime import datetime, timedelta
import time

tierList = []
snapshotList = []
class Snapshot:
    time     = 0
    URL      = ""
    BT_ID    = 0
    tier     = ""
    node     = ""
    timeTaken= 0
    def __init__(self,time,URL,BT_ID,tier,node,timeTaken):
        self.time     = time
        self.URL      = URL
        self.BT_ID    = BT_ID
        self.tier     = tier
        self.node     = node
        self.timeTaken= timeTaken
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5})".format(self.time,self.URL,self.BT_ID,self.tier,self.node,self.timeTaken)


def fetch_tiers_and_nodes():
    try:
        print ("Fetching tiers for application " + app_ID + "...")
        response = requests.get(baseUrl + "rest/applications/" + app_ID + "/tiers", auth=(userName, password), params={"output": "JSON"})
    except:
       print ("Could not get the tiers of application " + app_ID + ".")

    try:
        tiers = json.loads(response.content)
    except:
        print ("Could not parse the tiers for application " + app_ID + ".")
    for tier in tiers:
        try:
            print ("Fetching nodes for tier " + tier['name'] + "...")
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/tiers/" + str(tier['id']) + "/nodes", auth=(userName, password), params={"output": "JSON"})
        except:
            print ("Could not get the nodes of tier " + tier['name'] + ".")

        try:
            nodes = json.loads(response.content)
        except:
            print ("Could not parse the nodes for tier " + tier['name'] + " in application " + app_ID + ".")

        nodeList = []
        for node in nodes:
            nodeList.append((node['id'],node['name']))
        tierList.append((tier['id'],tier['name'],nodeList))

def print_tiers_and_nodes():
    if len(tierList) > 0:
        for tier in tierList:
            print ("Tier ID: " + str(tier[0]) + " Tier Name: " + tier[1])
            for node in tier[2]:
                print ("  Node ID: " + str(node[0]) + "Node Name: " + node[1])
    else:
        print("Tier list is empty.")

def fetch_snapshots(baseUrl,userName,password,app_ID,time_range_type,range_param1,range_param2):
   # time_range_type="AFTER_TIME" # {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"
   # duration_in_mins: {1day:"1440" 1week:"10080" 1month:"43200"}
   # range_param1=datetime.today()-timedelta(days=1)
    MAX_RESULTS="9999"

    if time_range_type == "BEFORE_NOW" and range_param1 > 0:
        duration_in_mins = range_param1
        print ("Fetching snapshots for App "+app_ID+", "+time_range_type+", "+range_param1+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                    params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BEFORE_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching snapshots for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"end-time": end_time, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "AFTER_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        start_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching snapshots for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"start-time": start_time, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BETWEEN_TIMES" and range_param1 is not None and range_param2 is not None:
        start_time = long(time.mktime(range_param1.timetuple())*1000)
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching snapshots for App "+app_ID+", "+time_range_type+", "+range_param1+", "+range_param2+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"start-time": start_time,"end-time": end_time, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    else:
        print ("Unknown time range or missing arguments. Exiting...")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    try:
        snapshots = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_snapshots(snapshots)
    return snapshots

def load_snapshots_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    snapshots = json.load(json_file)
    parse_snapshots(snapshots)

def parse_snapshots(snapshots):
    for snapshot in snapshots:
        Time = datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        Tier = snapshot['applicationComponentId']
        Node = snapshot['applicationComponentNodeId']
        if len(tierList) > 0:
            for tier in tierList:
                if tier[0] == snapshot['applicationComponentId']:
                    Tier = tier[1]
                    for node in tier[2]:
                        if node[0] == snapshot['applicationComponentNodeId']:
                            Node = node[1]
        snapshotList.append(Snapshot(Time,snapshot['URL'],snapshot['businessTransactionId'],Tier,Node,snapshot['timeTakenInMilliSecs']))
#    print "Number of snapshots:" + str(len(snapshotList))
#    for snapshot in snapshotList:
#        print str(snapshot) 

def write_snapshots_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Time', 'URL', 'BussinessTransaction', 'Tier', 'Node', 'ExeTime']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for snapshot in snapshotList:
        try:
            filewriter.writerow({'Time': snapshot.time,
                                'URL': snapshot.URL,
                                'BussinessTransaction': snapshot.BT_ID,
                                'Tier': snapshot.tier,
                                'Node': snapshot.node,
                                'ExeTime': snapshot.timeTaken})
        except:
            print ("Could not write to the output file " + fileName + ".")
            csvfile.close()
            exit(1)