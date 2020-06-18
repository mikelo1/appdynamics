#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTful_JSON
from policies import get_policies_matching_action

actionDict = dict()

class Action:
    name      = ""
    emails    = []
    policies  = []
    actionPlan= ""
    properties= []
    def __init__(self,name,emails,policies,actionPlan,customProperties):
        self.name      = name
        self.emails    = emails
        self.policies  = policies
        self.actionPlan= actionPlan
        self.properties= customProperties
    def __str__(self):
        return "({0},{1},{2},{3},{4})".format(self.name,self.emails,self.policies,self.actionPlan,self.properties)

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
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param app_ID the ID number of the application actions to fetch
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched actions. Zero if no action was found.
###
def fetch_actions(serverURL,app_ID,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching actions for App " + str(app_ID) + "...")
    # Retrieve a List of Actions for a Given Application
    # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions"
    if userName and password:
        actions = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
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

def fetch_actions_legacy(serverURL,app_ID,userName=None,password=None,token=None):
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

def load_actions_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    actions = json.load(json_file)
    return actions

def generate_actions_CSV(app_ID,actions=None,fileName=None):
    if actions is None and str(app_ID) not in actionDict:
        print "Actions for application "+str(app_ID)+" not loaded."
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

    fieldnames = ['ActionName', 'ActionType', 'Destination', 'Policies', 'CustomProperties']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for action in actions:
        try:
            filewriter.writerow({'ActionName': action['name'],
                                'ActionType': action['actionType'],
                                'Destination': "",
                                'Policies': "",
                                'CustomProperties': ""})
        except:
            print ("Could not write action "+action['name']+" to the output.")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

def generate_actions_CSV_legacy(app_ID,actions=None,fileName=None):
    if actions is None and str(app_ID) not in actionDict:
        print "Actions for application "+str(app_ID)+" not loaded."
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

    fieldnames = ['ActionName', 'Emails', 'Policies', 'ActionPlan', 'CustomProperties']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for action in actions:

        if 'actionType' not in action:
            print "Warn: ActionType not recognized: " + str(action)
            continue
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
            print("Warning: Unknown action type ",action['actionType'])
            continue

        Policies = get_policies_matching_action(app_ID,action['name'])

        emails_str    = ""
        for email in Emails:
            if emails_str != "": emails_str = emails_str + "\n"
            emails_str = emails_str + email
        policies_str  = ""
        for policy in Policies:
            if policies_str != "": policies_str = policies_str + "\n"
            policies_str = policies_str + policy
        properties_str= ""
        for property in CustomProperties:
            if properties_str != "": properties_str = properties_str + "\n"
            properties_str = properties_str + property

        try:
            filewriter.writerow({'ActionName': action['name'],
                                'Emails': emails_str,
                                'Policies': policies_str,
                                'ActionPlan': ActionPlan,
                                'CustomProperties': properties_str})
        except:
            print ("Could not write action "+action['name']+" to the output.")
            csvfile.close()
            exit(1)
    csvfile.close()

def get_actions(serverURL,app_ID,userName=None,password=None,token=None):
    if serverURL == "dummyserver":
        build_test_actions(app_ID)
    elif userName and password:
        if fetch_actions(serverURL,app_ID,userName=userName,password=password) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    elif token:
        if fetch_actions(serverURL,app_ID,token=token) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    generate_actions_CSV(app_ID)

def get_actions_legacy(serverURL,app_ID,userName=None,password=None,token=None,fileName=None):
    if userName and password:
        if fetch_actions_legacy(serverURL,app_ID,userName,password) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None    
    elif token:
        if fetch_actions_legacy(serverURL,app_ID,token=token) == 0:
            print "get_actions: Failed to retrieve actions for application " + str(app_ID)
            return None
    generate_actions_CSV_legacy(app_ID,fileName=fileName)