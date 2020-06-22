#!/usr/bin/python
import xml.etree.ElementTree as ET
import csv
import sys
from datetime import datetime, timedelta
import time
from applications import getName
from appdRESTfulAPI import fetch_RESTful_XML, timerange_to_params

eventDict = dict()

###
 # Fetch healtrule violations from a controller then add them to the events dictionary. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param app_ID the ID number of the application healtrule violations to fetch
 # @param minutesBeforeNow fetch only events newer than a relative duration in minutes
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched events. Zero if no event was found.
###
def fetch_healthrule_violations(serverURL,app_ID,minutesBeforeNow,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching healthrule violations for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
    # https://docs.appdynamics.com/display/PRO45/Events+and+Action+Suppression+API
    # Retrieve All Health Rule Violations that have occurred in an application within a specified time frame. 
    # URI /controller/rest/applications/application_id/problems/healthrule-violations
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/problems/healthrule-violations"

    for i in range(int(minutesBeforeNow),0,-1440): # loop "minutesBeforeNow" minutes in chunks of 1440 minutes (1 day)
        sinceTime = datetime.today()-timedelta(minutes=i)
        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
        params = timerange_to_params("AFTER_TIME",duration="1440",startEpoch=sinceEpoch)

        for retry in range(1,4):
            if 'DEBUG' in locals(): print ("Fetching healthrule violations for App " + str(app_ID) + "params "+str(params)+"...")
            if userName and password:
                chunked_root = fetch_RESTful_XML(restfulPath,params=params,userName=userName,password=password)
            elif token:
                chunked_root = fetch_RESTful_XML(restfulPath,params=params)

            if chunked_root is not None:
                break
            elif retry < 3:
                print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
            else:
                print "Giving up."
                return None
    
        if 'root' not in locals():
            root = chunked_root
            if 'DEBUG' in locals(): print "fetch_healthrule_violations: Added " + str(len(root.getchildren())) + " events."
        else:
            # Append retrieved data to root
            for element in chunked_root:
                root.append(element)
            if 'DEBUG' in locals(): print "fetch_healthrule_violations: Added " + str(len(chunked_root.getchildren())) + " events."

    # Add loaded events to the event dictionary
    if 'root' in locals():
        eventDict.update({str(app_ID):root})
    else:
        return 0

    if 'DEBUG' in locals():
        print "fetch_healthrule_violations: Loaded " + str(len(root.getchildren())) + " events."

    return len(root.getchildren())

def convert_events_XML_to_CSV(inFileName,outFilename=None):
    tree = ET.parse(inFileName)
    root = tree.getroot()
    generate_events_CSV(app_ID=0,events=root,fileName=outFilename)

def generate_events_CSV(app_ID,events=None,fileName=None):
    if events is None and str(app_ID) not in eventDict:
        print "Events for application "+str(app_ID)+" not loaded."
        return
    elif events is None and str(app_ID) in eventDict:
        events = eventDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['PolicyName', 'EntityName', 'Severity', 'Status', 'Start_Time', 'End_Time', 'Application']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for policyviolation in events.findall('policy-violation'):

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
            entity = Definition.find('name')
            if entity is not None:
                PolicyName = entity.text
            else:
                PolicyName = Definition.find('entityId').text
        else:
            PolicyName = ""

        Definition = policyviolation.find('affectedEntityDefinition')
        Type = Definition.find('entityType')
        if Type.text == "BUSINESS_TRANSACTION" or Type.text == "APPLICATION_DIAGNOSTIC_DATA" or Type.text == "MOBILE_APPLICATION":
            entity = Definition.find('name')
            if entity is not None:
                EntityName = entity.text
            else:
                EntityName = Definition.find('entityId').text
        else:
            EntityName = ""

        #appName = str(app_ID)
        appName = getName(app_ID)

        try:
            filewriter.writerow({'PolicyName': PolicyName,
                                'EntityName': EntityName,
                                'Severity': Severity,
                                'Status': Status,
                                'Start_Time': Start_Time,
                                'End_Time': End_Time,
                                'Application': appName})
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            return (-1)
    if fileName is not None: csvfile.close()

def get_healthrule_violations(serverURL,app_ID,minutesBeforeNow,userName=None,password=None,token=None):
    if serverURL == "dummyserver":
        build_test_events(app_ID)
    elif userName and password:
        if fetch_healthrule_violations(serverURL,app_ID,minutesBeforeNow,userName=userName,password=password) == 0:
            print "get_healthrule_violations: Failed to retrieve events for application " + str(app_ID)
            return None
    elif token:
        if fetch_healthrule_violations(serverURL,app_ID,minutesBeforeNow,token=token) == 0:
            print "get_healthrule_violations: Failed to retrieve events for application " + str(app_ID)
            return None
    generate_events_CSV(app_ID)