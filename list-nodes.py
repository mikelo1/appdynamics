#!/usr/bin/python
import requests
import json
import csv
import sys
from optparse import OptionParser

userName = ""
password = ""
fileName = ""
port = ""

agentTypes = {"MACHINE_AGENT": "Machine Agent",
              "APP_AGENT": "Java Agent",
              "DOT_NET_APP_AGENT": ".Net Agent",
              "PYTHON_APP_AGENT": "Python Agent",
              "PHP_APP_AGENT": "PHP Agent",
              "NODEJS_APP_AGENT": "Node.js Agent",
              "GOLANG_SDK": "Go Agent",
              "NATIVE_SDK": "Native SDK"}

usage = "usage: %prog [options] controller username@account password"

parser = OptionParser(usage=usage)
parser.add_option("-o", "--outfile", action="store", dest="fileName",
                  help="write report to FILE.  If not provided, output to STDOUT", metavar="FILE")
parser.add_option("-p", "--port",
                  action="store", dest="port",
                  help="Controller port")
parser.add_option("-s", "--ssl",
                  action="store_true", dest="ssl",
                  help="Use SSL")

(options, args) = parser.parse_args()

if len(args) != 3:
    parser.error("incorrect number of arguments")

controller = args[0]
userName = args[1]
password = args[2]

if options.port:
    port = options.port

if options.fileName:
    fileName = options.fileName

baseUrl = "http"

if options.ssl:
    baseUrl = baseUrl + "s"
    if (port == "") :
        port = "443"
else:
    if (port == "") :
        port = "80"

baseUrl = baseUrl + "://" + controller + ":" + port + "/controller/"

try:
    f = requests.get(baseUrl + "rest/applications", auth=(userName, password), params={"output": "JSON"})
except:
    print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
    exit(1)

try:
    apps = json.loads(f.text)
except:
    print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
    exit(1)

try:
    if options.fileName:
        csvfile = open(fileName, 'w')
    else:
        csvfile = sys.stdout
except:
    print ("Could not open output file " + fileName + ".")
    exit(1)

fieldnames = ['Application', 'Tier', 'Agent Type', 'Node Name', 'Machine Name']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

for app in apps:
    print ("")
    print (app['name'])

    try:
        f = requests.get(baseUrl + "rest/applications/" + str(app['id']) + "/tiers", auth=(userName, password), params={"output": "JSON"})
    except:
        print ("Could not get the tiers of application " + app['name'] + ".")

    try:
        tiers = json.loads(f.text)
    except:
        print ("Could not parse the tiers for application " + app['name'] + ".")

    for tier in tiers:
        try:
            f = requests.get(baseUrl + "rest/applications/" + str(app['id']) + "/tiers/" + str(tier['id']) + "/nodes", auth=(userName, password), params={"output": "JSON"})
        except:
            print ("Could not get the nodes of tier " + tier['name'] + ".")

        try:
            nodes = json.loads(f.text)
        except:
            print ("Could not parse the nodes for tier " + tier['name'] + " in application " + app['name'] + ".")

        for node in nodes:
            if node['agentType'] in agentTypes:
                agentType = agentTypes[node['agentType']]
            else:
                agentType = node['agentType']
            try:
                filewriter.writerow({'Application': app['name'],
                                    'Tier': tier['name'],
                                    'Agent Type': agentType,
                                    'Node Name': node['name'],
                                    'Machine Name': node['machineName']})
            except:
                print ("Could not write to the output file " + fileName + ".")
                csvfile.close()
                exit(1)
