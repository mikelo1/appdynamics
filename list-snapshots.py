#!/usr/bin/python
import requests
import json
import csv
import sys
from optparse import OptionParser
from datetime import datetime

userName = ""
password = ""
fileName = ""
port = ""

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

    controller = args[0]
    userName = args[1]
    password = args[2]
    app_ID = args[3]

    if options.port:
        port = options.port

    baseUrl = "http"

    if options.ssl:
        baseUrl = baseUrl + "s"
        if (port == "") :
            port = "443"
    else:
        if (port == "") :
            port = "80"

    baseUrl = baseUrl + "://" + controller + ":" + port + "/controller/"

    print ("Fetching policies for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password), params={"time-range-type": "BEFORE_NOW", "duration-in-mins": "180", "maximum-results": "5000", "output": "JSON"})
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        exit(1)

    try:
        snapshots = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        exit(1)

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



for snapshot in snapshots:

    Time = datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
    Tier = snapshot['applicationComponentId']
    Node = snapshot['applicationComponentNodeId']
    if (baseUrl and tiers and nodes):
        for tier in tiers:
            if tier['id'] == snapshot['applicationComponentId']:
                Tier = tier['name']
                for node in nodes:
                    if node['id'] == snapshot['applicationComponentNodeId']:
                        Node = node['name']

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
