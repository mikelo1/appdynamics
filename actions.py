#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict
from appdRESTfulAPI import RESTfulAPI
from policies import PolicyDict

class ActionDict:
    actionDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.actionDict)

    ###
     # toString private method, extracts properties from action
     # @param action JSON data containing an action
     # @return string with a comma separated list of properties
    ###
    def __str_action_properties(self,action):
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

    ###
     # toString private method, extracts recipients from action
     # @param action JSON data containing an action
     # @return string with a comma separated list of recipients
    ###
    def __str_action_recipients(self,action):
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

    ###
     # toString private method, extracts action plans from action
     # @param action JSON data containing an action
     # @return string with a comma separated list of action plans
    ###
    def __str_action_plan(self,action):
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


    ###
     # Generate CSV output from actions data
     # @param appID_List list of application IDs, in order to obtain actions from local actions dictionary
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

        fieldnames = ['ActionName', 'Application', 'ActionType', 'Recipients', 'Policies', 'CustomProperties']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.actionDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for action in self.actionDict[str(appID)]:
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

    ###
     # Generate JSON output from actions data
     # @param appID_List list of application IDs, in order to obtain actions from local actions dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        actions = []
        for appID in appID_List:
            actions = actions + self.actionDict[str(appID)]

        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(actions, outfile)
                outfile.close()
            except:
                sys.stderr.write ("Could not open output file " + fileName + ".\n")
                return (-1)
        else:
            print json.dumps(actions)

    ###
     # Load actions from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID the ID number of the application where to load the actions data.
     # @return the number of loaded actions. Zero if no action was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            actions = json.loads(streamdata)
        except TypeError as error:
            print ("load_action: "+str(error))
            return 0
        # Add loaded actions to the actions dictionary
        if type(actions) is dict:
            self.actionDict.update({str(appID):[actions]})
        else:
            self.actionDict.update({str(appID):actions})
        return len(actions)

    ###
     # Load action details for all actions from an application
     # @param app_ID the ID number of the application actions to fetch
     # @return the number of fetched actions. Zero if no action was found.
    ###
    def load_details(self,app_ID):
        if str(appID) in self.actionDict:
            index = 0
            for action in self.actionDict[str(appID)]:
                actionJSON = RESTfulAPI().fetch_action_details(app_ID,actions['id'])
                if actionsJSON is None:
                    print "load_action_details: Failed to retrieve action " + str(action['id']) + " for application " + str(app_ID)
                    continue
                self.actionDict[str(appID)][index] = actionJSON
                index = index + 1