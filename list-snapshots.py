#!/usr/bin/python
import requests
import json
import csv
import sys
from optparse import OptionParser
from datetime import datetime, timedelta
import time

tierList = []

def buildBaseURL(controller,port):
    url = "http"

    if options.ssl:
        url = url + "s"
        if (port == "") :
            port = "443"
    else:
        if (port == "") :
            port = "80"

    return url + "://" + controller + ":" + port + "/controller/"

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

def fetch_snapshots(time_range_type,range_param1,range_param2):
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
        print "status:", response.status_code
        print "header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    return snapshots

def write_element_snapshot(root,filewriter):
    for snapshot in root:
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

        try:
            filewriter.writerow({'Time': Time,
                                'URL': snapshot['URL'],
                                'BussinessTransaction': snapshot['businessTransactionId'],
                                'Tier': Tier,
                                'Node': Node,
                                'ExeTime': snapshot['timeTakenInMilliSecs']})
        except:
            print ("Could not write to the output file " + fileName + ".")
            csvfile.close()
            exit(1)

usage = "usage: %prog [options] controller username@account password Application_ID"
epilog= "example: %prog -s -p 443 ad-financial.saas.appdynamics.com johndoe@ad-financial s3cr3tp4ss 1001"

parser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
parser.add_option("-i", "--inputfile", action="store", dest="inFileName",
                  help="read source data from FILE.  If not provided, read from URL", metavar="FILE")
parser.add_option("-o", "--outfile", action="store", dest="outFileName",
                  help="write report to FILE.  If not provided, output to STDOUT", metavar="FILE")
parser.add_option("-p", "--port",
                  action="store", dest="port",
                  help="Controller port")
parser.add_option("-s", "--ssl",
                  action="store_true", dest="ssl",
                  help="Use SSL")

(options, args) = parser.parse_args()

if options.inFileName:
    print "Parsing file " + options.inFileName + "..."
    json_file = open(options.inFileName)
    snapshots = json.load(json_file)
else:
    if len(args) != 4:
        parser.error("incorrect number of arguments")
    if options.port:
        baseUrl = buildBaseURL(args[0],options.port)
    else:
        baseUrl = buildBaseURL(args[0],"")
    userName = args[1]
    password = args[2]
    app_ID   = args[3]
    fetch_tiers_and_nodes()

try:
    if options.outFileName:
        csvfile = open(options.outFileName, 'w')
    else:
        csvfile = sys.stdout
except:
    print ("Could not open output file " + options.outFileName + ".")
    exit(1)

fieldnames = ['Time', 'URL', 'BussinessTransaction', 'Tier', 'Node', 'ExeTime']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

if 'baseUrl' in locals():
    for i in range(3,48,3): # loop latest 48 hours in chunks of 3 hours
        for retry in range(1,4):
            data_chunck = fetch_snapshots("AFTER_TIME","180",datetime.today()-timedelta(hours=i)) # fetch 3 hours of data
            if data_chunck is not None:
                break
            elif retry < 3:
                print "Failed to fetch snapshots. Retrying (",retry," of 3)..."
            else:
                print "Giving up."
                exit (1)
        write_element_snapshot(data_chunck,filewriter)
elif 'root' in locals():
    write_element_policyviolation(root,filewriter)
else:
    print ("Nothing to do.")
