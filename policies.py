#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTful_JSON

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


def to_entityName(entityType):
    switcher = {
        "APPLICATION_COMPONENT": "TIER",
        "APPLICATION_COMPONENT_NODE": "NODE",
        "JMX_INSTANCE_NAME": "JMX_OBJECT",
        "INFO_POINT": "INFORMATION_POINT",
        "MACHINE_INSTANCE": "SERVER",
        "BACKEND": "DATABASES",
        "SERVICE_END_POINT": "SERVICE_ENDPOINTS"
    }
    return switcher.get(entityType, entityType)

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
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched policies. Zero if no policy was found.
###
def fetch_policies(app_ID,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    # Retrieve a list of Policies associated with an Application
    # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies"
    if serverURL and userName and password:
        policies = fetch_RESTful_JSON(restfulPath,serverURL=serverURL,userName=userName,password=password)
    else:
        policies = fetch_RESTful_JSON(restfulPath)

    if policies is None:
        print "fetch_policies: Failed to retrieve policies for application " + str(app_ID)
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

def fetch_policies_legacy(app_ID,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportPolicies
    # export policies to a JSON file.
    # GET /controller/policies/application_id
    restfulPath = "/controller/policies/" + str(app_ID)
    if serverURL and userName and password:
        policies = fetch_RESTful_JSON(restfulPath,serverURL=serverURL,userName=userName,password=password)
    else:
        policies = fetch_RESTful_JSON(restfulPath)

    if policies is None:
        print "fetch_policies: Failed to retrieve policies for application " + str(app_ID)
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
                EntityDescription = "ALL "+to_entityName(entTemplate['entityType'])
            elif entTemplate['matchCriteriaType'] == "RelatedEntities":
                EntityDescription = to_entityName(entTemplate['entityType'])+" within the Tiers: "
                for tier in entTemplate['relatedEntityNames']:
                    EntityDescription = EntityDescription + tier['entityName'] + ", "
            elif entTemplate['matchCriteriaType'] == "SpecificEntities":
                EntityDescription = "These specific "+ to_entityName(entTemplate['entityType'])+": "
                for entityName in entTemplate['entityNames']:
                    EntityDescription = EntityDescription + entityName['entityName'] + ", "
            elif entTemplate['matchCriteriaType'] == "CustomEntities":
                EntityDescription = to_entityName(entTemplate['entityType'])+" matching the following criteria: "
                EntityDescription = EntityDescription + " " + entTemplate['stringMatchType'] + " " + entTemplate['stringMatchExpression']
            elif entTemplate['entityType'] == "JMX_INSTANCE_NAME":
                nodeEntCriteria = entTemplate['nodeEntityMatchCriteria']
                if nodeEntCriteria['matchCriteriaType'] == "AllEntities":
                    EntityDescription = "JMX Objects from ALL"+to_entityName(nodeEntCriteria['entityType'])
                elif nodeEntCriteria['matchCriteriaType'] == "RelatedEntities":
                    EntityDescription = to_entityName(nodeEntCriteria['entityType'])+" within the Tiers: "
                    for tier in entTemplate['relatedEntityNames']:
                        EntityDescription = EntityDescription + tier['entityName'] + ", "
                elif nodeEntCriteria['matchCriteriaType'] == "SpecificEntities":
                    EntityDescription = "These specific "+ to_entityName(nodeEntCriteria['entityType'])+": "
                    for entityName in entTemplate['entityNames']:
                        EntityDescription = EntityDescription + entityName['entityName'] + ", "
                elif nodeEntCriteria['matchCriteriaType'] == "CustomEntities":
                    EntityDescription = to_entityName(nodeEntCriteria['entityType'])+" matching the following criteria: "
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

def generate_policies_CSV(app_ID,policies=None,fileName=None):
    if policies is None and str(app_ID) not in policyDict:
        print "Policies for application "+str(app_ID)+" not loaded."
        return
    elif policies is None and str(app_ID) in policyDict:
        policies = policyDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Policy', 'Application', 'Events', 'Entities', 'Actions']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for policy in policies:
        if 'reactorType' in policy:
            if 'DEBUG' in locals(): print "Policy found in legacy JSON format."
            policyData = parse_policy_JSON_legacy(policy)
        elif 'selectedEntityType' in policy:
            if 'DEBUG' in locals(): print "Policy found in JSON format."
            policyData = parse_policy_JSON(policy)
        else:
            continue
        
        try:
            filewriter.writerow({'Policy': policyData.name,
                                 'Application': app_ID,
                                 'Events': str(policyData.events),
                                 'Entities': str(policyData.entities),
                                 'Actions': str(policyData.actions)})
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            return (-1)
    if 'DEBUG' in locals(): print "INFO: Displayed number of policies:" + str(len(policies))
    if fileName is not None: csvfile.close()

def generate_policies_JSON(app_ID,policies=None,fileName=None):
    if policies is None and str(app_ID) not in policyDict:
        print "Policies for application "+str(app_ID)+" not loaded."
        return
    elif policies is None and str(app_ID) in policyDict:
        policies = policyDict[str(app_ID)]

    if fileName is not None:
        try:
            JSONfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        JSONfile = sys.stdout

    data=json.dump(policies,JSONfile)
    JSONfile.close()


###### FROM HERE PUBLIC FUNCTIONS ######

def get_policies_from_server(inFileName,outFilename=None):
    json_file = open(inFileName)
    policies = json.load(json_file)
    generate_policies_CSV(app_ID=0,policies=policies,fileName=outFilename)

def get_policies(app_ID,serverURL,userName=None,password=None,token=None):
    if serverURL == "dummyserver":
        build_test_policies(app_ID)
    elif userName and password:
        if fetch_policies(app_ID,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_policies: Failed to retrieve policies for application " + str(app_ID)
            return None
    else:
        if fetch_policies(app_ID,token=token) == 0:
            print "get_policies: Failed to retrieve policies for application " + str(app_ID)
            return None
    generate_policies_CSV(app_ID)

def get_policies_legacy(app_ID,serverURL,userName=None,password=None,token=None,fileName=None):
    if userName and password:
        if fetch_policies_legacy(app_ID,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_policies: Failed to retrieve policies for application " + str(app_ID)
            return None
    else:
        if fetch_policies_legacy(app_ID,token=token) == 0:
            print "get_policies: Failed to retrieve policies for application " + str(app_ID)
            return None
    generate_policies_CSV(app_ID,fileName=fileName)

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