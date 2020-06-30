#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTful_JSON
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
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched actions. Zero if no action was found.
###
def fetch_actions(app_ID,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching actions for App " + str(app_ID) + "...")
    # Retrieve a List of Actions for a Given Application
    # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions"
    if serverURL and userName and password:
        actions = fetch_RESTful_JSON(restfulPath,serverURL=serverURL,userName=userName,password=password)
    else:
        actions = fetch_RESTful_JSON(restfulPath)

    if actions is None:
        print "fetch_actions: Failed to retrieve actions for application " + str(app_ID)
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

def fetch_actions_legacy(app_ID,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching actions for App " + str(app_ID) + "...")
    # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportActionsfromanApplication
    # Exports all actions in the specified application to a JSON file.
    # GET /controller/actions/application_id
    restfulPath = "/controller/actions/" + str(app_ID)
    if userName and password:
        actions = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
    else:
        actions = fetch_RESTful_JSON(restfulPath)

    if actions is None:
        print "fetch_actions: Failed to retrieve actions for application " + str(app_ID)
        return None

    # Add loaded actions to the actions dictionary
    actionDict.update({str(app_ID):actions})

    if 'DEBUG' in locals():
        print "fetch_actions: Loaded " + str(len(actionDict)) + " actions:"
        for appID in actionDict:
            print str(actionDict[appID])

    return len(actions)

def parse_action_legacy(action):
    if action['actionType'] == "EmailAction":
        CustomProperties = []
        Emails = [action['toAddress']]
        ActionPlan = ""
    elif action['actionType'] == "CustomEmailAction":
        CustomProperties = []
        custProp = action['customProperties']
        for prop in custProp:
            CustomProperties.append(prop + " : " + custProp[prop].encode('ASCII', 'ignore'))
        Emails = []
        emailList = action['to']
        for email in emailList:
             Emails.append(email['emailAddress'])
        ActionPlan = action['customEmailActionPlanName'].encode('ASCII', 'ignore')
    elif action['actionType'] == "SMSAction":
        ActionPlan=action['actionType']
        CustomProperties = []
        Emails = [action['toNumber']]
    elif action['actionType'] == "DiagnosticSessionAction":
        ActionPlan=action['actionType']+": "+str(action['businessTransactionTemplates'])
        CustomProperties = [ 'Number of snapshots per minute: '+str(action['numberOfSnapshotsPerMinute']), 'Duration in minutes: '+str(action['durationInMinutes'])  ]
        Emails = []
    elif action['actionType'] == "ThreadDumpAction":
        ActionPlan=action['actionType']
        CustomProperties = [ 'Number of thread dumps: '+str(action['numberOfSamples']), 'Interval: '+str(action['samplingIntervalMills']) ]
        Emails = []
    elif action['actionType'] == "RunLocalScriptAction":
        ActionPlan=action['actionType']
        CustomProperties = [ 'Script path: '+str(action['scriptPath']), 'timeout(minutes): '+str(action['timeoutMinutes']) ]
        Emails = []
    elif action['actionType'] == "HttpRequestAction":
        ActionPlan=action['httpRequestActionPlanName']
        CustomProperties = action['customProperties']
        Emails = []
    elif action['actionType'] == "CustomAction":
        ActionPlan=action['actionType']
        CustomProperties = [ 'Custom action: '+str(['customType'])]
        Emails = []
    else:
        print("parse_action_legacy: [Warn] Unknown action type ",action['actionType'])

    return Action(name=action['name'],actiontype=action['actionType'],recipients=Emails,customProperties=CustomProperties)

def parse_action(action):
    return Action(name=action['name'],actiontype=action['actionType'],recipients="",customProperties="")

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
            actionData = parse_action(action) if 'id' in action else parse_action_legacy(action)
            Policies = get_policies_matching_action(app_ID,action['name'])
        else: # Data does not belong to an action
            continue
        try:
            filewriter.writerow({'ActionName': actionData.name,
                                'ActionType': actionData.type,
                                'Recipients': actionData.recipients,
                                'Policies': Policies,
                                'CustomProperties': actionData.properties})
        except:
            print ("Could not write action "+action['name']+" to the output.")
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


def get_actions_from_stream(streamdata,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        actions = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    generate_actions_CSV(app_ID=0,actions=actions,fileName=outFilename)

def get_actions(app_ID,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_actions(app_ID)
    elif serverURL and userName and password:
        if fetch_actions(app_ID,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    else:
        if fetch_actions(app_ID,token=token) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(app_ID)
    else:
        generate_actions_CSV(app_ID)

def get_actions_legacy(app_ID,outputFormat=None,serverURL=None,userName=None,password=None,token=None,fileName=None):
    if serverURL and userName and password:
        if fetch_actions_legacy(app_ID,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None    
    else:
        if fetch_actions_legacy(app_ID,token=token) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(app_ID,fileName=fileName)
    else:
        generate_actions_CSV(app_ID,fileName=fileName)