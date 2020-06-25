#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from applications import getName
from appdRESTfulAPI import fetch_RESTful_XML, fetch_RESTful_JSON, timerange_to_params

eventDict = dict()

###
 # Fetch healtrule violations from a controller then add them to the events dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application healtrule violations to fetch
 # @param minutesBeforeNow fetch only events newer than a relative duration in minutes
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched events. Zero if no event was found.
###
def fetch_healthrule_violations(app_ID,minutesBeforeNow,serverURL=None,userName=None,password=None,token=None):
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
            if serverURL and userName and password:
                data_chunck = fetch_RESTful_JSON(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
            else:
                data_chunck = fetch_RESTful_JSON(restfulPath,params=params)

            if data_chunck is not None:
                break
            elif retry < 3:
                print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
            else:
                print "Giving up."
                return None
    
        if 'events' not in locals():
            events = data_chunck
            if 'DEBUG' in locals(): print "fetch_healthrule_violations: Added " + str(len(data_chunck)) + " events."
        else:
            # Append retrieved data to root
            for new_event in data_chunck:
                events.append(new_event)
            if 'DEBUG' in locals(): print "fetch_healthrule_violations: Added " + str(len(data_chunck)) + " events."

    # Add loaded events to the event dictionary
    if 'events' in locals():
        eventDict.update({str(app_ID):events})
    else:
        return 0

    if 'DEBUG' in locals():
        print "fetch_healthrule_violations: Loaded " + str(len(events)) + " events."

    return len(events)

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

    for policyviolation in events:

        if 'affectedEntityDefinition' not in policyviolation: continue

        Start_Time_Epoch = policyviolation['startTimeInMillis']
        Start_Time = datetime.fromtimestamp(float(Start_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')

        Status = policyviolation['incidentStatus']
        if Status != "OPEN":
            End_Time_Epoch = policyviolation['endTimeInMillis']
            End_Time = datetime.fromtimestamp(float(End_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            End_Time = ""

        Severity = policyviolation['severity'] if 'severity' in policyviolation else "Undefined"

        triggeredEntitytype = policyviolation['triggeredEntityDefinition']['entityType']
        if triggeredEntitytype == "POLICY":
            if 'name' in policyviolation['triggeredEntityDefinition']:
                PolicyName = policyviolation['triggeredEntityDefinition']['name']
            else:
                PolicyName = policyviolation['triggeredEntityDefinition']['entityId']
        else:
            PolicyName = ""

        affectedEntityType = policyviolation['affectedEntityDefinition']['entityType']
        if affectedEntityType in ["BUSINESS_TRANSACTION","APPLICATION_DIAGNOSTIC_DATA","MOBILE_APPLICATION"]:
            if 'name' in policyviolation['affectedEntityDefinition']:
                EntityName = policyviolation['affectedEntityDefinition']['name']
            else:
                EntityName = policyviolation['affectedEntityDefinition']['entityId']
        else:
            EntityName = ""

        appName = str(app_ID)
        #appName = getName(app_ID)

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


###### FROM HERE PUBLIC FUNCTIONS ######


def get_healthrule_violations_from_server(inFileName,outFilename=None):
    DEBUG=True
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        json_file = open(inFileName)
        events = json.load(json_file)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    generate_events_CSV(app_ID=0,events=events,fileName=outFilename)

def get_healthrule_violations(app_ID,minutesBeforeNow,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_events(app_ID)
    elif serverURL and userName and password:
        if fetch_healthrule_violations(app_ID,minutesBeforeNow,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_healthrule_violations: Failed to retrieve events for application " + str(app_ID)
            return None
    else:
        if fetch_healthrule_violations(app_ID,minutesBeforeNow,token=token) == 0:
            print "get_healthrule_violations: Failed to retrieve events for application " + str(app_ID)
            return None
    generate_events_CSV(app_ID)