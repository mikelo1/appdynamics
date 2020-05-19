#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta
import time

eventList = []
class Event:
    name      = ""
    entityName= ""
    severity  = ""
    status    = ""
    startTime = 0
    endTime   = 0
    def __init__(self,name,entityName,severity,status,startTime,endTime):
        self.name      = name
        self.entityName= entityName
        self.severity  = severity
        self.status    = status
        self.startTime = startTime
        self.endTime   = endTime
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5}".format(self.name,self.entityName,self.severity,self.status,self.startTime,self.endTime)


def fetch_healthrule_violations(baseUrl,userName,password,app_ID,time_range_type,range_param1,range_param2):
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
            print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BEFORE_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"end-time": end_time})
        except:
            print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "AFTER_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        start_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"start-time": start_time})
        except:
            print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BETWEEN_TIMES" and range_param1 is not None and range_param2 is not None:
        start_time = long(time.mktime(range_param1.timetuple())*1000)
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching healthrule violations for App "+app_ID+", "+time_range_type+", "+range_param1+", "+range_param2+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/problems/healthrule-violations", auth=(userName, password),\
                                params={"time-range-type": time_range_type,"start-time": start_time,"end-time": end_time})
        except:
            print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
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
    elif 'DEBUG' in locals():
        file1 = open("response.txt","w") 
        file1.write(response.content)

    try:
        root = ET.fromstring(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_events_XML(root)
    return root

def load_events_XML(fileName):
    print "Parsing file " + fileName + "..."
    tree = ET.parse(fileName)
    root = tree.getroot()
    parse_events_XML(root)

def parse_events_XML(root):
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
            entity = Definition.find('name')
            if entity is not None:
                PolicyName = entity.text
            else:
                PolicyName = Definition.find('entityId').text
        else:
            continue

        Definition = policyviolation.find('affectedEntityDefinition')
        Type = Definition.find('entityType')
        if Type.text == "BUSINESS_TRANSACTION" or Type.text == "APPLICATION_DIAGNOSTIC_DATA" or Type.text == "MOBILE_APPLICATION":
            entity = Definition.find('name')
            if entity is not None:
                EntityName = entity.text
            else:
                EntityName = Definition.find('entityId').text
        else:
            continue

        eventList.append(Event(PolicyName,EntityName,Severity,Status,Start_Time,End_Time))
#    print "Number of events:" + str(len(eventList))
#    for event in eventList:
#        print str(event)

def write_events_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['PolicyName', 'EntityName', 'Severity', 'Status', 'Start_Time', 'End_Time']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    if len(eventList) > 0:
        for event in eventList:
            try:
                filewriter.writerow({'PolicyName': event.name,
                                    'EntityName': event.entityName,
                                    'Severity': event.severity,
                                    'Status': event.status,
                                    'Start_Time': event.startTime,
                                    'End_Time': event.endTime})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()

def serialize():
    for event in eventList:
        data=data+"\n"+str(event)
    return data