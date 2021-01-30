#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from applications import ApplicationDict
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class EventDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_healthrule_violations}

    def __init__(self):
        self.entityDict = dict()

    ###
     # toString private method, extracts policy from event
     # @param event JSON data containing an event
     # @return string with a comma separated list of policy names
    ###
    def __str_event_policy(self,event):
        triggeredEntitytype = event['triggeredEntityDefinition']['entityType']
        if triggeredEntitytype == "POLICY":
            if 'name' in event['triggeredEntityDefinition']:
                return event['triggeredEntityDefinition']['name'].encode('ASCII', 'ignore')
            else:
                return event['triggeredEntityDefinition']['entityId']
        else:
            return ""

    ###
     # toString private method, extracts policy from event
     # @param event JSON data containing an event
     # @return string with a comma separated list of entity names
    ###
    def __str_event_entity(self,event):
        affectedEntityType = event['affectedEntityDefinition']['entityType']
        if affectedEntityType in ["BUSINESS_TRANSACTION","APPLICATION_DIAGNOSTIC_DATA","MOBILE_APPLICATION"]:
            if 'name' in event['affectedEntityDefinition']:
                return event['affectedEntityDefinition']['name'].encode('ASCII', 'ignore')
            else:
                return event['affectedEntityDefinition']['entityId']
        else:
            return ""

    ###
     # toString private method, extracts description from event
     # @param event JSON data containing an event
     # @return string with the description of the event
    ###
    def __str_event_description(self,event):
        desc_pos = event['description'].find("All of the following conditions were found to be violating")
        Description = event['description'][desc_pos+58:] if desc_pos > 0 else event['description']
        Description = Description.replace("<br>","\n")
        return Description

    ###
     # toString private method, extracts starting time from event
     # @param event JSON data containing an event
     # @return date
    ###
    def __str_event_start_time(self,event):
        Start_Time_Epoch = event['startTimeInMillis']
        return datetime.fromtimestamp(float(Start_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')

    ###
     # toString private method, extracts ending time from event
     # @param event JSON data containing an event
     # @return date
    ###
    def __str_event_end_time(self,event):
        Status = event['incidentStatus']
        if Status != "OPEN":
            End_Time_Epoch = event['endTimeInMillis']
            return datetime.fromtimestamp(float(End_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return ""


    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from healthrule violations data
     # @param appID_List list of application IDs, in order to obtain healtrule violations from local healthrule violations dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write ("Could not open output file " + fileName + ".\n")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['PolicyName', 'EntityName', 'Severity', 'Status', 'Start_Time', 'End_Time', 'Application', 'Description']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')


        for appID in appID_List:
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for policyviolation in self.entityDict[str(appID)]:
                # Check if data belongs to an event
                if 'affectedEntityDefinition' not in policyviolation: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                app_ID  = policyviolation['deepLinkUrl'][policyviolation['deepLinkUrl'].find("application"):].split('&')[0].split('=')[1]
                appName = ApplicationDict().getAppName(app_ID)

                try:
                    filewriter.writerow({'PolicyName': self.__str_event_policy(policyviolation),
                                        'EntityName': self.__str_event_entity(policyviolation),
                                        'Severity': policyviolation['severity'] if 'severity' in policyviolation else "Undefined",
                                        'Status': policyviolation['incidentStatus'],
                                        'Start_Time': self.__str_event_start_time(policyviolation),
                                        'End_Time': self.__str_event_end_time(policyviolation),
                                        'Application': appName,
                                        'Description': self.__str_event_description(policyviolation)})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()