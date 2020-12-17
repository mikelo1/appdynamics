#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from applications import ApplicationDict

class EventDict:
    eventDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.eventDict)

###
 # Fetch healtrule violations from a controller then add them to the events dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application healtrule violations to fetch
 # @param minutesBeforeNow fetch only events newer than a relative duration in minutes
 # @param selectors fetch only events filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched events. Zero if no event was found.
###
#   def fetch_healthrule_violations(app_ID,minutesBeforeNow,selectors=None,serverURL=None,userName=None,password=None,token=None):
#       if 'DEBUG' in locals(): print ("Fetching healthrule violations for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
#       # https://docs.appdynamics.com/display/PRO45/Events+and+Action+Suppression+API
#       # Retrieve All Health Rule Violations that have occurred in an application within a specified time frame. 
#       # URI /controller/rest/applications/application_id/problems/healthrule-violations
#       restfulPath = "/controller/rest/applications/" + str(app_ID) + "/problems/healthrule-violations"
#   
#       for i in range(int(minutesBeforeNow),0,-1440): # loop "minutesBeforeNow" minutes in chunks of 1440 minutes (1 day)
#           sinceTime = datetime.today()-timedelta(minutes=i)
#           sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
#           params = timerange_to_params("AFTER_TIME",duration="1440",startEpoch=sinceEpoch)
#           params.update({"output": "JSON"})
#           if selectors: params.update(selectors)
#   
#           for retry in range(1,4):
#               if 'DEBUG' in locals(): print ("Fetching healthrule violations for App " + str(app_ID) + "params "+str(params)+"...")
#               if serverURL and userName and password:
#                   response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
#               else:
#                   response = fetch_RESTfulPath(restfulPath,params=params)
#   
#               try:
#                   data_chunck = json.loads(response)
#               except JSONDecodeError:
#                   if retry < 3:
#                       print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
#                   else:
#                       print "Giving up."
#                       return None
#               if data_chunck is not None: break
#       
#           if 'events' not in locals():
#               events = data_chunck
#               if 'DEBUG' in locals(): print "fetch_healthrule_violations: Added " + str(len(data_chunck)) + " events."
#           else:
#               # Append retrieved data to root
#               for new_event in data_chunck:
#                   events.append(new_event)
#               if 'DEBUG' in locals(): print "fetch_healthrule_violations: Added " + str(len(data_chunck)) + " events."
#   
#   
#       # Add loaded events to the event dictionary
#       if 'events' in locals():
#           eventDict.update({str(app_ID):events})
#       else:
#           sys.stderr.write("fetch_healthrule_violations: Failed to retrieve events for application " + str(app_ID)+"\n")
#           return 0
#   
#       if 'DEBUG' in locals():
#           print "fetch_healthrule_violations: Loaded " + str(len(events)) + " events."
#   
#       return len(events)

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
            if str(appID) not in self.eventDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for policyviolation in self.eventDict[str(appID)]:
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

    ###
     # Generate JSON output from healthrule violations data
     # @param appID_List list of application IDs, in order to obtain healtrule violations from local healthrule violations dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        events = [ self.eventDict[str(appID)] for appID in appID_List ]
        if fileName is not None:
            try:
                JSONfile = open(fileName, 'w')
                json.dumps(events,JSONfile)
                JSONfile.close()
            except:
                sys.stderr.write ("Could not open output file " + fileName + ".\n")
                return (-1)
        else:
            print json.dumps(events)


    ###
     # Load healtrule violations from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID the ID number of the application where to load the events data.
     # @return the number of loaded events. Zero if no event was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            events = json.loads(streamdata)
        except TypeError as error:
            print ("load_events: "+str(error))
            return 0
        # Add loaded events to the events dictionary
        if type(events) is dict:
            self.eventDict.update({str(appID):[events]})
        else:
            self.eventDict.update({str(appID):events})
        return len(events)