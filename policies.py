#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName

policyDict = dict()

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
    params = {"output": "JSON"}
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

def fetch_policies_legacy(app_ID,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportPolicies
    # export policies to a JSON file.
    # GET /controller/policies/application_id
    restfulPath = "/controller/policies/" + str(app_ID)
    params = {"output": "JSON"}
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

###
 # toString method, extracts healthrules from policy
 # @param policy JSON data containing a policy
 # @return string with a comma separated list of health rule names
###
def str_policy_healthrules(policy):
    if 'eventFilterTemplate' in policy and policy['eventFilterTemplate']['healthRuleNames'] is not None:
        for healthRule in policy['eventFilterTemplate']['healthRuleNames']:
            healthrules = healthrules + "," + healthRule['entityName'] if 'healthrules' in locals() else healthRule['entityName']
        return healthrules
    elif 'events' in policy and policy['events']['healthRuleEvents']['healthRuleScope']['healthRuleScopeType'] == "SPECIFIC_HEALTH_RULES":
        return ",".join(policy['events']['healthRuleEvents']['healthRuleScope']['healthRules'])
    else:
        return "ANY"

###
 # toString method, extracts entities from policy
 # @param policy JSON data containing a policy
 # @return string with a comma separated list of entity names
###
def str_policy_entities(policy):
    if 'entityFilterTemplates' in policy:
        for entTemplate in policy['entityFilterTemplates']:
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
            entities = entities + " " + EntityDescription if 'entities' in locals() else EntityDescription
    elif 'selectedEntities' in policy and policy['selectedEntities']['selectedEntityType'] == "SPECIFIC_ENTITIES":
        for entity in policy['selectedEntities']['entities']:
            entities = entities + "\n" if 'entities' in locals() else ""
            if entity['entityType']   == "BUSINESS_TRANSACTION":
                if entity['selectedBusinessTransactions']['businessTransactionScope'] == "ALL_BUSINESS_TRANSACTIONS":
                    entities = entities + "\nAll Business Transactions" if 'entities' in locals() else "All Business Transactions"
                elif entity['selectedBusinessTransactions']['businessTransactionScope'] == "SPECIFIC_BUSINESS_TRANSACTIONS":
                    entities = entities + ",".join(entity['selectedBusinessTransactions']['businessTransactions'])
                else:
                    pass
            # TO DO: print out rest of entities
            elif entity['entityType'] == "DATABASES_IN_APPLICATION":
                entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
            elif entity['entityType'] == "TIER_NODE":
                entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
            elif entity['entityType'] == "INFORMATION_POINTS":
                entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
            elif entity['entityType'] == "SERVERS_IN_APPLICATION":
                entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
            elif entity['entityType'] == "ERRORS":
                entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
            elif entity['entityType'] == "PAGE":
                entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
    else:
        return "ANY"
    if 'entities' in locals(): return entities
    else: return "ANY"

###
 # toString method, extracts actions from policy
 # @param policy JSON data containing a policy
 # @return string with a comma separated list of action names
###
def str_policy_actions(policy):
    if 'actionWrapperTemplates' in policy:
        for action in policy['actionWrapperTemplates']:
            actions = actions + " " + action['actionTag'] if 'actions' in locals() else action['actionTag']
        if 'actions' in locals(): return actions
        else: return "ANY"
    elif 'actions' in policy:
        return "Output not implemented yet."
    else:
        return "ANY"

###
 # Generate CSV output from policies data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain policies from local policies dictionary
 # @param custom_policyDict dictionary containing policies
 # @param fileName output file name
 # @return None
###
def generate_policies_CSV(appID_List,custom_policyDict=None,fileName=None):
    if appID_List is None and custom_policyDict is None:
        return
    elif custom_policyDict is None:
        custom_policyDict = policyDict

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

    for appID in appID_List:
        for policy in custom_policyDict[str(appID)]:
            # Check if data belongs to a policy
            if 'reactorType' not in policy and 'selectedEntities' not in policy: continue
            try:
                filewriter.writerow({'Policy': policy['name'],
                                     'Application': getAppName(appID),
                                     'Events': str_policy_healthrules(policy),
                                     'Entities': str_policy_entities(policy),
                                     'Actions': str_policy_actions(policy)})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                return (-1)
    if 'DEBUG' in locals(): print "INFO: Displayed number of policies:" + str(len(policies))
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from policies data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain policies from local policies dictionary
 # @param custom_policyDict dictionary containing policies
 # @param fileName output file name
 # @return None
###
def generate_policies_JSON(appID_List,custom_policyDict=None,fileName=None):
    if appID_List is None and custom_policyDict is None:
        return
    elif custom_policyDict is None:
        custom_policyDict = policyDict

    policies = []
    for appID in appID_List:
        policies = policies + custom_policyDict[str(appID)]

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

    custom_policyDict = {"0":[policies]} if type(policies) is dict else {"0":policies}
    if outputFormat and outputFormat == "JSON":
        generate_policies_JSON(appID_List=[0],custom_policyDict=custom_policyDict,fileName=outFilename)
    else:
        generate_policies_CSV(appID_List=[0],custom_policyDict=custom_policyDict,fileName=outFilename)

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
        numPolicies = numPolicies + fetch_policies(appID)
    if numPolicies == 0:
        sys.stderr.write("get_policies: Could not fetch any policies.\n")
    elif outputFormat and outputFormat == "JSON":
        generate_policies_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_policies_CSV(appID_List)
    return numPolicies

def get_policies_legacy(appID_List,selectors=None,outputFormat=None):
    numPolicies = 0
    for appID in appID_List:
        sys.stderr.write("get policies " + getAppName(appID) + "...\n")
        numPolicies = numPolicies + fetch_policies_legacy(appID)
    if numPolicies == 0:
        sys.stderr.write("get_policies: Could not fetch any policies.\n")
    elif outputFormat and outputFormat == "JSON":
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