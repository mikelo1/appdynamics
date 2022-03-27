import json
import sys
from .entities import AppEntity


class ActionDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        #self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_actions_legacy,
        #                            'fetchByID': self.controller.RESTfulAPI.fetch_action_by_ID }
        self.entityKeywords = ["actionType"]
        self.CSVfields = {  'ActionName':       self.__str_action_name,
                            'ActionType':       self.__str_action_type,
                            'Recipients':       self.__str_action_recipients,
                            'CustomProperties': self.__str_action_properties }

    def __str_action_name(self,action):
        return action['name'] if sys.version_info[0] >= 3 else action['name'].encode('ASCII', 'ignore')

    def __str_action_type(self,action):
        return action['actionType']

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
                return ','.join(map(lambda x: str(x+":"+action['customProperties'][x]),action['customProperties'])) if (len(action['customProperties']) > 0) else ""
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

