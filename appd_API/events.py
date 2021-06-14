#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class EventDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_healthrule_violations}
    entityJSONKeyword = "affectedEntityDefinition"
    applications = None

    def __init__(self,applications):
        self.entityDict  = dict()
        self.applications = applications


    def __str_event_policy(self,event):
        """
        toString private method, extracts policy from event
        :param event: JSON data containing an event
        :returns: string with a comma separated list of policy names
        """
        triggeredEntitytype = event['triggeredEntityDefinition']['entityType']
        if triggeredEntitytype == "POLICY":
            if 'name' in event['triggeredEntityDefinition']:
                return event['triggeredEntityDefinition']['name'].encode('ASCII', 'ignore')
            else:
                return event['triggeredEntityDefinition']['entityId']
        else:
            return ""


    def __str_event_entity(self,event):
        """
        toString private method, extracts policy from event
        :param event: JSON data containing an event
        :returns: string with a comma separated list of entity names
        """
        affectedEntityType = event['affectedEntityDefinition']['entityType']
        if affectedEntityType in ["BUSINESS_TRANSACTION","APPLICATION_DIAGNOSTIC_DATA","MOBILE_APPLICATION"]:
            if 'name' in event['affectedEntityDefinition']:
                return event['affectedEntityDefinition']['name'].encode('ASCII', 'ignore')
            else:
                return event['affectedEntityDefinition']['entityId']
        else:
            return ""


    def __str_event_description(self,event):
        """
        toString private method, extracts description from event
        :param event: JSON data containing an event
        :returns: string with the description of the event
        """
        desc_pos = event['description'].find("All of the following conditions were found to be violating")
        Description = event['description'][desc_pos+58:] if desc_pos > 0 else event['description']
        Description = Description.replace("<br>","\n")
        return Description


    def __str_event_start_time(self,event):
        """
        toString private method, extracts starting time from event
        :param event: JSON data containing an event
        :returns: date
        """
        Start_Time_Epoch = event['startTimeInMillis']
        return datetime.fromtimestamp(float(Start_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')


    def __str_event_end_time(self,event):
        """
        toString private method, extracts ending time from event
        :param event: JSON data containing an event
        :returns: date
        """
        Status = event['incidentStatus']
        if Status != "OPEN":
            End_Time_Epoch = event['endTimeInMillis']
            return datetime.fromtimestamp(float(End_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return ""


    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from healthrule violations data
        :param appID_List: list of application IDs, in order to obtain healtrule violations from local healthrule violations dictionary
        :param fileName: output file name
        :returns: None
        """
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

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print "Application "+appID +" is not loaded in dictionary."
                continue
            for policyviolation in self.entityDict[appID]:
                # Check if data belongs to an event
                if 'affectedEntityDefinition' not in policyviolation: continue
                elif 'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True

                app_ID  = policyviolation['deepLinkUrl'][policyviolation['deepLinkUrl'].find("application"):].split('&')[0].split('=')[1]

                try:
                    filewriter.writerow({'PolicyName': self.__str_event_policy(policyviolation),
                                        'EntityName': self.__str_event_entity(policyviolation),
                                        'Severity': policyviolation['severity'] if 'severity' in policyviolation else "Undefined",
                                        'Status': policyviolation['incidentStatus'],
                                        'Start_Time': self.__str_event_start_time(policyviolation),
                                        'End_Time': self.__str_event_end_time(policyviolation),
                                        'Application': self.applications.getAppName(app_ID),
                                        'Description': self.__str_event_description(policyviolation)})
                except ValueError as valError:
                    sys.stderr.write(valError+"\n")
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()



class ErrorDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_errors}
    entityJSONKeyword = "metricPath"
    applications = None

    def __init__(self,applications):
        self.entityDict  = dict()
        self.applications = applications

    def fetch_after_time(self,appID,duration,sinceEpoch,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        count = 0
        for tierID in self.applications.getTiers_ID_List(appID):
            tierName = self.applications.getTierName(appID,tierID)
            data = self.entityAPIFunctions['fetch'](app_ID=appID,tier_ID=tierName,time_range_type="AFTER_TIME",duration=duration,startEpoch=sinceEpoch,selectors=selectors)
            count += self.load(streamdata=data,appID=appID)
        return count

    ###### FROM HERE PUBLIC FUNCTIONS ######
    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from error metrics data
        :param appID_List: list of application IDs, in order to obtain error metrics from local error metrics dictionary
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write ("Could not open output file " + fileName + ".\n")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['Application', 'ErrorCode', 'Value', 'Max', 'Min', 'Sum', 'Count']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print "Application "+appID +" is not loaded in dictionary."
                continue
            for errorMetric in self.entityDict[appID]:
                # Check if data belongs to an event
                if 'metricPath' not in errorMetric: continue
                elif len(errorMetric['metricValues']) == 0: continue
                elif 'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'Application': self.applications.getAppName(appID),
                                        'ErrorCode': errorMetric['metricPath'].split("|")[2],
                                        'Value': errorMetric['metricValues'][0]['value'],
                                        'Max':   errorMetric['metricValues'][0]['max'],
                                        'Min':   errorMetric['metricValues'][0]['min'],
                                        'Sum':   errorMetric['metricValues'][0]['sum'],
                                        'Count': errorMetric['metricValues'][0]['count']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()
