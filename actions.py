#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity
from policies import PolicyDict


class ActionDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_actions_legacy}

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



    def generate_CSV(self,appID_List,fileName=None):
        """
        Generate CSV output from actions data
        :param appID_List: list of application IDs, in order to obtain actions from local actions dictionary
        :param fileName: output file name
        :returns: None
        """
        if type(appID_List) is not list or len(appID_List)==0: return

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

        for appID in appID_List:
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for action in self.entityDict[str(appID)]:
                # Check if data belongs to an action
                if 'actionType' not in action: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True
                try:
                    filewriter.writerow({'ActionName': action['name'].encode('ASCII', 'ignore'),
                                        'Application': ApplicationDict().getAppName(appID),
                                        'ActionType': action['actionType'],
                                        'Recipients': self.__str_action_recipients(action),
                                        'Policies': "", #PolicyDict().get_policies_matching_action(app_ID,action['name']),
                                        'CustomProperties': self.__str_action_properties(action)})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()


    def load_details(self,app_ID):
        """
        Load action details for all actions from an application
        :param app_ID: the ID number of the application actions to fetch
        :returns: the number of fetched actions. Zero if no action was found.
        """
        if str(appID) in self.entityDict:
            index = 0
            for action in self.entityDict[str(appID)]:
                actionJSON = RESTfulAPI().fetch_action_details(app_ID,actions['id'])
                if actionsJSON is None:
                    print "load_action_details: Failed to retrieve action " + str(action['id']) + " for application " + str(app_ID)
                    continue
                self.entityDict[str(appID)][index] = actionJSON
                index = index + 1
