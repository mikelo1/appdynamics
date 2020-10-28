#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName

policyDict = dict()

class Policy:
    id      = 0
    name    = ""
    appID   = 0
    events  =[]
    entities=[]
    actions =[]
    def __init__(self,id,name,events,entities,actions,appID=0):
        self.id      = id
        self.name    = name
        self.events  = events
        self.entities= entities
        self.actions = actions
        self.appID   = appID
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5})".format(self.id,self.name,self.events,self.entities,self.actions,self.appID)


def build_test_policies(app_ID):
    policies1=json.loads('[{"id":1854,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
    policies2=json.loads('[{"id":1855,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
    #policies3=json.loads('[{"id":1856,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
    policyDict.update({str(app_ID):policies1})
    policyDict.update({str(app_ID+1):policies2})
#    policyDict.update({str(app_ID+1):policies3})
    print "Number of entries: " + str(len(policyDict))
    if str(app_ID) in policyDict:
        print (policyDict[str(app_ID)])

###
 # Fetch application policies from a controller then add them to the policies dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application policies to fetch
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched policies. Zero if no policy was found.
###
def fetch_policies(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    # Retrieve a list of Policies associated with an Application
    # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        policies = json.loads(response)
    except JSONDecodeError:
        print ("fetch_policies: Could not process JSON content.")
        return None

    if loadData:
        index = 0
        for policy in policies:
            if 'DEBUG' in locals(): print ("Fetching policy " + policy['name'] + "...")
            # Retrieve Details of a Specified Policy
            # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies/{policy-id}
            restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies/" + str(policy['id'])
            if userName and password:
                policyJSON = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
            else:
                policyJSON = fetch_RESTful_JSON(restfulPath)
            if policyJSON is None:
                "fetch_policies: Failed to retrieve policy " + str(policy['id']) + " for application " + str(app_ID)
                continue
            policies[index] = policyJSON
            index = index + 1

    # Add loaded policies to the policy dictionary
    policyDict.update({str(app_ID):policies})

    if 'DEBUG' in locals():
        print "fetch_policies: Loaded " + str(len(policies)) + " policies."
        for appID in policyDict:
            print str(policyDict[appID])

    return len(policies)

def fetch_policies_legacy(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportPolicies
    # export policies to a JSON file.
    # GET /controller/policies/application_id
    restfulPath = "/controller/policies/" + str(app_ID)
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        policies = json.loads(response)
    except JSONDecodeError:
        print ("fetch_policies: Could not process JSON content.")
        return None

    # Add loaded policies to the policy dictionary
    policyDict.update({str(app_ID):policies})

    if 'DEBUG' in locals():
        print "fetch_policies: Loaded " + str(len(policyDict)) + " policies."
        for appID in policyDict:
            print str(policyDict[appID])

    return len(policies)

def parse_policy_JSON(policy):
    Events = []
    if len(policy['events']['healthRuleEvents']) > 0:
        Events.append(policy['events']['healthRuleEvents']['healthRuleScopeType'])
    # TODO elif len(policy['events']['customEvents']) > 0:
    # TODO elif len(policy['events']['anomalyEvents']) > 0:
    # TODO elif len(policy['events']['otherEvents']) > 0:
    Entities = []
    Actions = []
    for action in policy['actions']:
        Actions.append(action['actionName'])

    return Policy(policy['id'],policy['name'],Events,Entities,Actions)

def parse_policy_JSON_legacy(policy):
    Name = policy['name']
    AppName = policy['applicationName']
    HealthRules = []
    evTemplate = policy['eventFilterTemplate']
    if evTemplate['healthRuleNames'] is not None:
        for healthRule in evTemplate['healthRuleNames']:
            HealthRules.append(healthRule['entityName'])
    else:
        HealthRules = "ANY"

    Entities = []
    entityTemplates = policy['entityFilterTemplates']
    if entityTemplates is None:
        Entities = ["ANY"]
    else:
        for entTemplate in entityTemplates:
            if entTemplate['matchCriteriaType'] == "AllEntities":
                EntityDescription = "ALL "+entTemplate['entityType']
            elif entTemplate['matchCriteriaType'] == "RelatedEntities":
                EntityDescription = entTemplate['entityType']+" within the Tiers: "
                for tier in entTemplate['relatedEntityNames']:
                    EntityDescription = EntityDescription + tier['entityName'] + ", "
            elif entTemplate['matchCriteriaType'] == "SpecificEntities":
                EntityDescription = "These specific "+ entTemplate['entityType']+": "
                for entityName in entTemplate['entityNames']:
                    EntityDescription = EntityDescription + entityName['entityName'] + ", "
            elif entTemplate['matchCriteriaType'] == "CustomEntities":
                EntityDescription = entTemplate['entityType']+" matching the following criteria: "
                EntityDescription = EntityDescription + " " + entTemplate['stringMatchType'] + " " + entTemplate['stringMatchExpression']
            elif entTemplate['entityType'] == "JMX_INSTANCE_NAME":
                nodeEntCriteria = entTemplate['nodeEntityMatchCriteria']
                if nodeEntCriteria['matchCriteriaType'] == "AllEntities":
                    EntityDescription = "JMX Objects from ALL"+nodeEntCriteria['entityType']
                elif nodeEntCriteria['matchCriteriaType'] == "RelatedEntities":
                    EntityDescription = nodeEntCriteria['entityType']+" within the Tiers: "
                    for tier in entTemplate['relatedEntityNames']:
                        EntityDescription = EntityDescription + tier['entityName'] + ", "
                elif nodeEntCriteria['matchCriteriaType'] == "SpecificEntities":
                    EntityDescription = "These specific "+ nodeEntCriteria['entityType']+": "
                    for entityName in entTemplate['entityNames']:
                        EntityDescription = EntityDescription + entityName['entityName'] + ", "
                elif nodeEntCriteria['matchCriteriaType'] == "CustomEntities":
                    EntityDescription = nodeEntCriteria['entityType']+" matching the following criteria: "
                    EntityDescription = EntityDescription + " " + nodeEntCriteria['stringMatchType'] + " " + nodeEntCriteria['stringMatchExpression']
            Entities.append(EntityDescription)

    Actions = []
    actTemplate = policy['actionWrapperTemplates']
    if actTemplate is not None:
        for action in actTemplate:
            Actions.append(action['actionTag'])
    else:
        Actions = ["ANY"]

    return Policy(id=0,name=policy['name'],events=HealthRules,entities=Entities,actions=Actions)

###
 # Generate CSV output from policies data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain policies from local policies dictionary
 # @param policies data stream containing policies
 # @param fileName output file name
 # @return None
###
def generate_policies_CSV(appID_List=None,policies=None,fileName=None):
    if appID_List is None and policies is None:
        return
    elif policies is None:
        policies = []
        for appID in appID_List:
            policies = policies + policyDict[str(appID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Policy', 'Events', 'Entities', 'Actions']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for policy in policies:
        if 'reactorType' in policy:
            if 'DEBUG' in locals(): print "Policy found in legacy JSON format."
            policyData = parse_policy_JSON_legacy(policy)
        elif 'selectedEntityType' in policy:
            if 'DEBUG' in locals(): print "Policy found in JSON format."
            policyData = parse_policy_JSON(policy)
        else: # Data does not belong to a policy
            continue
        
        try:
            filewriter.writerow({'Policy': policyData.name,
                                 'Events': str(policyData.events),
                                 'Entities': str(policyData.entities),
                                 'Actions': str(policyData.actions)})
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            return (-1)
    if 'DEBUG' in locals(): print "INFO: Displayed number of policies:" + str(len(policies))
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from policies data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain policies from local policies dictionary
 # @param policies data stream containing policies
 # @param fileName output file name
 # @return None
###
def generate_policies_JSON(appID_List=None,policies=None,fileName=None):
    if appID_List is None and policies is None:
        return
    elif policies is None:
        policies = []
        for appID in appID_List:
            policies = policies + policyDict[str(appID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(policies, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(policies)


###### FROM HERE PUBLIC FUNCTIONS ######

def get_policies_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        policies = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_policies_from_stream: Could not process JSON content.")
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_policies_JSON(policies=policies,fileName=outFilename)
    else:
        generate_policies_CSV(policies=policies,fileName=outFilename)

###
 # Display actions for a list of applications.
 # @param appID_List list of application IDs to fetch actions
 # @param selectors fetch only actions filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched actions. Zero if no actions was found.
###
def get_policies(appID_List,selectors=None,outputFormat=None):
    numPolicies = 0
    for appID in appID_List:
        sys.stderr.write("get policies " + getAppName(appID) + "...\n")
        numPolicies = numPolicies + fetch_policies(appID,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_policies_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_policies_CSV(appID_List)
    return numPolicies

def get_policies_legacy(appID_List,selectors=None,outputFormat=None):
    numPolicies = 0
    for appID in appID_List:
        sys.stderr.write("get policies " + getAppName(appID) + "...\n")
        numPolicies = numPolicies + fetch_policies_legacy(appID,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_policies_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_policies_CSV(appID_List)
    return numPolicies

def get_policies_matching_action(app_ID,name):
    MatchList = []
    if str(app_ID) in policyDict:
        for policy in policyDict[str(app_ID)]:
            for policy_action in policy['actions']:
                if policy_action['actionName'] == name:
                    MatchList.append(policy.name)
    return MatchList
	
#### TO DO:
####        get_policies_matching_health_rule(app_ID,name)
####        get_policies_matching_business_transaction
####        get_policies_matching_tiers_and_nodes
####        get_policies_matching_JMX
####        get_policies_matching_Information_Point
####        get_policies_matching_Server
####        get_policies_matching_Database
####        get_policies_matching_Service_Endpoint
####        get_policies_matching_Error