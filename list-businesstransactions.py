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
    BTs = json.load(json_file)
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

    print ("Fetching business transactions for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "rest/applications/" + app_ID + "/business-transactions", auth=(userName, password), params={"output": "JSON"})
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
        BTs = json.loads(response.content)
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
    if options.outFileName:
        csvfile = open(options.outFileName, 'w')
    else:
        csvfile = sys.stdout
except:
    print ("Could not open output file " + options.outFileName + ".")
    exit(1)

fieldnames = ['name', 'entryPointType', 'tierName']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

for BT in BTs:
    try:
        filewriter.writerow({'name': BT['name'],
                           'entryPointType': BT['entryPointType'],
                            'tierName': BT['tierName']})
    except:
        print ("Could not write to the output file " + fileName + ".")
        csvfile.close()
        exit(1)