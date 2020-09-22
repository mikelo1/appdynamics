#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from policies import get_policies_matching_action

actionDict = dict()

class Action:
    name      = ""
    type      = ""
    recipients= []
    properties= []
    def __init__(self,name,actiontype,recipients,customProperties):
        self.name      = name
        self.type      = actiontype
        self.recipients= recipients
        self.properties= customProperties
    def __str__(self):
        return "({0},{1},{2},{3})".format(self.name,self.type,self.recipients,self.properties)

def build_test_actions(app_ID):
    actions1=json.loads('[{"id":2183,"actionType":"EMAIL","emails":["gogs@acme.com"]},{"id":2184,"actionType":"EMAIL","emails":["gogs@acme.com"]}]')
    actions2=json.loads('[{"id":2185,"actionType":"EMAIL","emails":["gogs@acme.com"]},{"id":2186,"actionType":"EMAIL","emails":["gogs@acme.com"]}]')
    # Add loaded actions to the actions dictionary
    actionDict.update({str(app_ID):actions1})
    actionDict.update({str(app_ID+1):actions2})
    if 'DEBUG' in locals():
        print "Number of entries: " + str(len(actionDict))
        if str(app_ID) in actionDict:
            print (actionDict[str(app_ID)])

###
 # Fetch application actions from a controller then add them to the actions dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application actions to fetch
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched actions. Zero if no action was found.
###
def fetch_actions(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching actions for App " + str(app_ID) + "...")
    # Retrieve a List of Actions for a Given Application
    # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        actions = json.loads(response)
    except JSONDecodeError:
        print ("fetch_actions: Could not process JSON content.")
        return None

    if loadData:
        index = 0
        for action in actions:
            if 'DEBUG' in locals(): print ("Fetching action "+str(actions['id'])+" for App " + str(app_ID) + "...")
            # Retrieve Details of a Specified Action
            # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions/{action-id}
            restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions/" + str(action['id'])
            if userName and password:
                actionJSON = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
            else:
                actionJSON = fetch_RESTful_JSON(restfulPath)
            if actionsJSON is None:
                "fetch_actions: Failed to retrieve action " + str(action['id']) + " for application " + str(app_ID)
                continue
            actions[index] = actionJSON
            index = index + 1
    
    # Add loaded actions to the actions dictionary
    actionDict.update({str(app_ID):actions})

    if 'DEBUG' in locals():
        print "fetch_actions: Loaded " + str(len(actions)) + " actions:"
        for appID in actionDict:
            print str(actionDict[appID])

    return len(actions)

def fetch_actions_legacy(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching actions for App " + str(app_ID) + "...")
    # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportActionsfromanApplication
    # Exports all actions in the specified application to a JSON file.
    # GET /controller/actions/application_id
    restfulPath = "/controller/actions/" + str(app_ID)
    params = {"output": "JSON"}
    if selectors: params.update(selectors)
    
    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        actions = json.loads(response)
    except JSONDecodeError:
        print ("fetch_actions: Could not process JSON content.")
        return None

    # Add loaded actions to the actions dictionary
    actionDict.update({str(app_ID):actions})

    if 'DEBUG' in locals():
        print "fetch_actions: Loaded " + str(len(actionDict)) + " actions:"
        for appID in actionDict:
            print str(actionDict[appID])

    return len(actions)

def generate_actions_CSV(app_ID,actions=None,fileName=None):
    if actions is None and str(app_ID) not in actionDict:
        print "generate_actions_CSV: [Warn] Actions for application "+str(app_ID)+" not loaded."
        return
    elif actions is None and str(app_ID) in actionDict:
        actions = actionDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['ActionName', 'ActionType', 'Recipients', 'Policies', 'CustomProperties']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for action in actions:
        if 'actionType' in action:
            if 'id' in action: # New JSON format
                Properties = ""
                Recipients = ""
            else: # Legacy JSON format
                if action['actionType'] == "EmailAction":
                    Properties = ""
                    Recipients = action['toAddress']
                    ActionPlan = ""
                elif action['actionType'] == "CustomEmailAction":
                    Properties = ','.join(map(lambda x: str(x+":"+action['customProperties'][x].encode('ASCII', 'ignore')),action['customProperties'])) if (len(action['customProperties']) > 0) else ""
                    Recipients = ','.join(map(lambda x: str(x),action['to'])) if (len(action['to']) > 0) else ""
                    ActionPlan = action['customEmailActionPlanName'].encode('ASCII', 'ignore')
                elif action['actionType'] == "SMSAction":
                    Properties = ""
                    Recipients = action['toNumber']
                    ActionPlan = action['actionType']
                elif action['actionType'] == "DiagnosticSessionAction":
                    Properties = 'Number of snapshots per minute: '+str(action['numberOfSnapshotsPerMinute']), 'Duration in minutes: '+str(action['durationInMinutes'])
                    Recipients = ""
                    ActionPlan = action['actionType']+": "+str(action['businessTransactionTemplates'])
                elif action['actionType'] == "ThreadDumpAction":
                    Properties = 'Number of thread dumps: '+str(action['numberOfSamples']), 'Interval: '+str(action['samplingIntervalMills'])
                    Recipients = ""
                    ActionPlan = action['actionType']
                elif action['actionType'] == "RunLocalScriptAction":
                    CustomProperties = 'Script path: '+str(action['scriptPath']), 'timeout(minutes): '+str(action['timeoutMinutes'])
                    Recipients = ""
                    ActionPlan = action['actionType']
                elif action['actionType'] == "HttpRequestAction":
                    Properties = action['customProperties']
                    Recipients = ""
                    ActionPlan = action['httpRequestActionPlanName']
                elif action['actionType'] == "CustomAction":
                    Properties = 'Custom action: '+str(['customType'])
                    Recipients = ""
                    ActionPlan=action['actionType']

            Policies = get_policies_matching_action(app_ID,action['name'])
        else: # Data does not belong to an action
            continue
        try:
            filewriter.writerow({'ActionName': action['name'].encode('ASCII', 'ignore'),
                                'ActionType': action['actionType'],
                                'Recipients': Recipients,
                                'Policies': Policies,
                                'CustomProperties': Properties})
        except:
            print ("Could not write action "+action['name'].encode('ASCII', 'ignore')+" to the output.")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

def generate_actions_JSON(app_ID,actions=None,fileName=None):
    if actions is None and str(app_ID) not in actionDict:
        print "generate_actions_JSON: [Warn] Actions for application "+str(app_ID)+" not loaded."
        return
    elif actions is None and str(app_ID) in actionDict:
        actions = actionDict[str(app_ID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(actions, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(actions)

###### FROM HERE PUBLIC FUNCTIONS ######


def get_actions_from_stream(streamdata,outputFormat=None,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        actions = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(app_ID=0,actions=actions,fileName=outFilename)
    else:
        generate_actions_CSV(app_ID=0,actions=actions,fileName=outFilename)

def get_actions(app_ID,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_actions(app_ID)
    elif serverURL and userName and password:
        number = fetch_actions(app_ID,selectors=selectors,serverURL=serverURL,userName=userName,password=password)
        if number == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    else:
        number = fetch_actions(app_ID,selectors=selectors,token=token)
        if number == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    if 'DEBUG' in locals(): print "get_actions: [INFO] Loaded",number,"actions"
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(app_ID)
    elif not outputFormat or outputFormat == "CSV":
        generate_actions_CSV(app_ID)

def get_actions_legacy(app_ID,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None,fileName=None):
    if serverURL and userName and password:
        number = fetch_actions_legacy(app_ID,selectors=selectors,serverURL=serverURL,userName=userName,password=password)
        if number == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None    
    else:
        number = fetch_actions_legacy(app_ID,selectors=selectors,token=token)
        if number == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    if 'DEBUG' in locals(): print "get_actions: [INFO] Loaded",number,"actions"
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(app_ID,fileName=fileName)
    elif not outputFormat or outputFormat == "CSV":
        generate_actions_CSV(app_ID,fileName=fileName)