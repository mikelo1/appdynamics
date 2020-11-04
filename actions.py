#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName
from policies import get_policies_matching_action

actionDict = dict()

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
    params = {"output": "JSON"}

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

###
 # Fetch application actions from a controller then add them to the actions dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application actions to fetch
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched actions. Zero if no action was found.
###
def fetch_actions_legacy(app_ID,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching actions for App " + str(app_ID) + "...")
    # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportActionsfromanApplication
    # Exports all actions in the specified application to a JSON file.
    # GET /controller/actions/application_id
    restfulPath = "/controller/actions/" + str(app_ID)
    params = {"output": "JSON"}
    
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


###
 # toString method, extracts properties from action
 # @param action JSON data containing an action
 # @return string with a comma separated list of properties
###
def str_action_properties(action):
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
 # toString method, extracts recipients from action
 # @param action JSON data containing an action
 # @return string with a comma separated list of recipients
###
def str_action_recipients(action):
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
 # toString method, extracts action plans from action
 # @param action JSON data containing an action
 # @return string with a comma separated list of action plans
###
def str_action_plan(action):
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

###
 # Generate CSV output from actions data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain actions from local actions dictionary
 # @param custom_actionDict dictionary containing actions
 # @param fileName output file name
 # @return None
###
def generate_actions_CSV(appID_List,custom_actionDict=None,fileName=None):
    if appID_List is None and custom_actionDict is None:
        return
    elif custom_actionDict is None:
        custom_actionDict = actionDict

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
    filewriter.writeheader()

    for appID in appID_List:
        for action in custom_actionDict[str(appID)]:
            # Check if data belongs to an action
            if 'actionType' not in action: continue
            try:
                filewriter.writerow({'ActionName': action['name'].encode('ASCII', 'ignore'),
                                    'Application': getAppName(appID),
                                    'ActionType': action['actionType'],
                                    'Recipients': str_action_recipients(action),
                                    'Policies': "", #get_policies_matching_action(app_ID,action['name']),
                                    'CustomProperties': str_action_properties(action)})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                return (-1)
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from actions data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain actions from local actions dictionary
 # @param custom_actionDict dictionary containing actions
 # @param fileName output file name
 # @return None
###
def generate_actions_JSON(appID_List,custom_actionDict=None,fileName=None):
    if appID_List is None and custom_actionDict is None:
        return
    elif custom_actionDict is None:
        custom_actionDict = actionDict

    actions = []
    for appID in appID_List:
        actions = actions + custom_actionDict[str(appID)]

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


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display actions from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_actions_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        actions = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_actions_from_stream: Could not process JSON data.")
        return 0
    custom_actionDict = {"0":[actions]} if type(actions) is dict else {"0":actions}
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(appID_List=[0],custom_actionDict=custom_actionDict,fileName=outFilename)
    else:
        generate_actions_CSV(appID_List=[0],custom_actionDict=custom_actionDict,fileName=outFilename)

###
 # Display actions for a list of applications.
 # @param appID_List list of application IDs to fetch actions
 # @param selectors fetch only actions filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched actions. Zero if no actions was found.
###
def get_actions(appID_List,selectors=None,outputFormat=None):
    numActions = 0
    for appID in appID_List:
        sys.stderr.write("get actions " + getAppName(appID) + "...\n")
        numActions = numActions + fetch_actions(appID)
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_actions_CSV(appID_List)
    return numActions

def get_actions_legacy(appID_List,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None,fileName=None):
    numActions = 0
    for appID in appID_List:
        sys.stderr.write("get actions " + getAppName(appID) + "...\n")
        numActions = numActions + fetch_actions_legacy(appID)
    if outputFormat and outputFormat == "JSON":
        generate_actions_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_actions_CSV(appID_List)
    return numActions