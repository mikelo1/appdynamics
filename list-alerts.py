#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import libxml2
import csv
import sys
from optparse import OptionParser
from datetime import datetime, timedelta
import time

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
    tree = ET.parse(options.inFileName)
    root = tree.getroot()
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
    
def fetch_healthrule_violations(time_range_type,range_param1,range_param2):
   # time_range_type="AFTER_TIME" # {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"
   # duration_in_mins: {1day:"1440" 1week:"10080" 1month:"43200"}
   # range_param1=datetime.today()-timedelta(days=1)
    if time_range_type == "BEFORE_NOW" and range_param1 > 0:
        duration_in_mins = range_param1
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                    params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BEFORE_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"end-time": end_time})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "AFTER_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        start_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"start-time": start_time})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BETWEEN_TIMES" and range_param1 is not None and range_param2 is not None:
        start_time = long(time.mktime(range_param1.timetuple())*1000)
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+", "+range_param2+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"start-time": start_time,"end-time": end_time})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    else:
        print ("Unknown time range or missing arguments. Exiting...")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    try:
        root = ET.fromstring(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "status:", response.status_code
        print "header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    return root

def write_element_policyviolation(root,filewriter):
    for policyviolation in root.findall('policy-violation'):

        Start_Time_Epoch = policyviolation.find('startTimeInMillis').text
        Start_Time = datetime.fromtimestamp(float(Start_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')

        Status = policyviolation.find('incidentStatus').text
        if Status != "OPEN":
            End_Time_Epoch = policyviolation.find('endTimeInMillis').text
            End_Time = datetime.fromtimestamp(float(End_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            End_Time = ""

        sev = policyviolation.find('severity')
        if sev is not None:
            Severity = sev.text
        else:
            Severity = "Undefined"

        Definition = policyviolation.find('triggeredEntityDefinition')
        Type = Definition.find('entityType')
        if Type.text == "POLICY":
            PolicyName = Definition.find('name').text
        else:
            continue

        Definition = policyviolation.find('affectedEntityDefinition')
        Type = Definition.find('entityType')
        if Type.text == "BUSINESS_TRANSACTION" or Type.text == "APPLICATION_DIAGNOSTIC_DATA" or Type.text == "MOBILE_APPLICATION":
            EntityName = Definition.find('name').text
        else:
            continue

        try:
            filewriter.writerow({'PolicyName': PolicyName,
                                'EntityName': EntityName,
                                'Severity': Severity,
                                'Status': Status,
                                'Start_Time': Start_Time,
                                'End_Time': End_Time})
        except:
            print ("Could not write to the output file " + options.outFileName + ".")
            csvfile.close()
            exit(1)


try:
    if options.outFileName:
        csvfile = open(options.outFileName, 'w')
    else:
        csvfile = sys.stdout
except:
    print ("Could not open output file " + options.outFileName + ".")
    exit(1)

# create the csv writer object
fieldnames = ['PolicyName', 'EntityName', 'Severity', 'Status', 'Start_Time', 'End_Time']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

#for health_rule in ctxt.xpathEval("/health-rules/health-rule[type[text()="BUSINESS_TRANSACTION"] and enabled[text()="true"] and is-default[text()="false"]]"):
#    BT = health_rule.xpathEval("/affected-entities-match-criteria/affected-bt-match-criteria")

for i in range(30,0,-1):
    for retry in range(1,4):
        root = fetch_healthrule_violations("AFTER_TIME","1440",datetime.today()-timedelta(days=i))
        if root is not None:
            break
        elif retry < 3:
            print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
        else:
            print "Giving up."
            exit (1)
    write_element_policyviolation(root,filewriter)

#doc.freeDoc()
#ctxt.xpathFreeContext()
