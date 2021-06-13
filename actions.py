#!/usr/bin/python
import json
import csv
import sys
from applications import applications
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity
from policies import policies


class ActionDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_actions_legacy,
                          'fetchByID': RESTfulAPI().fetch_action_by_ID}
    entityJSONKeyword = "actionType"

    def __init__(self):
        self.entityDict = dict()

    def __str_action_properties(self,action):
        """
        toString private method, extracts properties from action
        :param action: JSON data containing an action
        :returns: string with a comma separated list of properties
        """
        if 'id' in action: # New JSON format
            return ""
        else: # Legacy JSON format
            if action['actionType'] == "EmailAction":
                return ""
            elif action['actionType'] == "CustomEmailAction":
                return ','.join(map(lambda x: str(x+":"+action['customProperties'][x].encode('ASCII', 'ignore')),action['customProperties'])) if (len(action['customProperties']) > 0) else ""
            elif action['actionType'] == "SMSAction":
                return ""
            elif action['actionType'] == "DiagnosticSessionAction":
               return 'Number of snapshots per minute: '+str(action['numberOfSnapshotsPerMinute']), 'Duration in minutes: '+str(action['durationInMinutes'])
            elif action['actionType'] == "ThreadDumpAction":
                return 'Number of thread dumps: '+str(action['numberOfSamples']), 'Interval: '+str(action['samplingIntervalMills'])
            elif action['actionType'] == "RunLocalScriptAction":
                return 'Script path: '+str(action['scriptPath']), 'timeout(minutes): '+str(action['timeoutMinutes'])
            elif action['actionType'] == "HttpRequestAction":
                return action['customProperties']
            elif action['actionType'] == "CustomAction":
                return 'Custom action: '+str(['customType'])


    def __str_action_recipients(self,action):
        """
        toString private method, extracts recipients from action
        :param action: JSON data containing an action
        :returns: string with a comma separated list of recipients
        """
        if 'id' in action: # New JSON format
            return ""
        else: # Legacy JSON format
            if action['actionType'] == "EmailAction":
                return action['toAddress']
            elif action['actionType'] == "CustomEmailAction":
                return ','.join(map(lambda x: str(x),action['to'])) if (len(action['to']) > 0) else ""
            elif action['actionType'] == "SMSAction":
                return action['toNumber']
            elif action['actionType'] == "DiagnosticSessionAction":
                return ""
            elif action['actionType'] == "ThreadDumpAction":
                return ""
            elif action['actionType'] == "RunLocalScriptAction":
                return ""
            elif action['actionType'] == "HttpRequestAction":
                return ""
            elif action['actionType'] == "CustomAction":
                return ""


    def __str_action_plan(self,action):
        """
        toString private method, extracts action plans from action
        :param action: JSON data containing an action
        :returns: string with a comma separated list of action plans
        """
        if 'id' in action: # New JSON format
            return ""
        else: # Legacy JSON format
            if action['actionType'] == "EmailAction":
                return ""
            elif action['actionType'] == "CustomEmailAction":
                return action['customEmailActionPlanName'].encode('ASCII', 'ignore')
            elif action['actionType'] == "SMSAction":
                return action['actionType']
            elif action['actionType'] == "DiagnosticSessionAction":
                return action['actionType']+": "+str(action['businessTransactionTemplates'])
            elif action['actionType'] == "ThreadDumpAction":
                return action['actionType']
            elif action['actionType'] == "RunLocalScriptAction":
                return action['actionType']
            elif action['actionType'] == "HttpRequestAction":
                return action['httpRequestActionPlanName']
            elif action['actionType'] == "CustomAction":
                return action['actionType']



    ###### FROM HERE PUBLIC FUNCTIONS ######


    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from actions data
        :param appID_List: list of application IDs, in order to obtain actions from local actions dictionary
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

        fieldnames = ['ActionName', 'Application', 'ActionType', 'Recipients', 'Policies', 'CustomProperties']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print "Application "+appID +" is not loaded in dictionary."
                continue
            for action in self.entityDict[appID]:
                # Check if data belongs to an action
                if 'actionType' not in action: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True
                try:
                    filewriter.writerow({'ActionName': action['name'].encode('ASCII', 'ignore'),
                                        'Application': applications.getAppName(appID),
                                        'ActionType': action['actionType'],
                                        'Recipients': self.__str_action_recipients(action),
                                        'Policies': "", #policies.get_policies_matching_action(app_ID,action['name']),
                                        'CustomProperties': self.__str_action_properties(action)})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()

# Global object that works as Singleton
actions = ActionDict()