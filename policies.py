#!/usr/bin/python
import requests
import json
import csv
import sys

policyDict = dict()
class Policy:
    id   = 0
    name = ""
    appID= 0
    data = None
    def __init__(self,id,name,appID,data):
        self.id   = id
        self.name = name
        self.appID= appID
        self.data = data
    def __str__(self):
        return "({0},{1},{2},{3})".format(self.id,self.name,self.appID,self.data)


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

def test_policies(app_ID):
    policies1=json.loads('{"appID": "'+str(app_ID)+'", "policies": [{"id":1854,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}}]}')
    policies2=json.loads('{"appID": "'+str(app_ID+1)+'", "policies": [{"id":1855,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}}]}')
    #policies3=json.loads('{"appID": "'+str(app_ID+1)+'", "policies": [{"id":1856,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}}]}')
    policyDict.update({str(app_ID):policies1})
    policyDict.update({str(app_ID+1):policies2})
#    policyDict.update({str(app_ID+1):policies3})
    print "Number of entries: " + str(len(policyDict))
    if str(app_ID) in policyDict:
        print (policyDict[str(app_ID)])

def fetch_policies(serverURL,app_ID,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    try:
        # Retrieve a list of Policies associated with an Application
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies
        if userName and password:
            response = requests.get(serverURL + "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies", auth=(userName, password), params={"output": "JSON"})
        elif token:
            response = requests.get(serverURL + "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies", headers={"Authorization": "Bearer "+token}, params={"output": "JSON"})
        else:
            print "fetch_policies_list: Incorrect parameters."
            return None
    except requests.exceptions.InvalidURL:
        print ("Invalid URL: " + serverURL + ".  Do you have the right controller hostname?")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request. Status:", response.status_code
        if 'DEBUG' in locals():
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w") 
            file1.write(response.content)
            file1.close() 
        return None

    try:
        policies = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        return None
    if loadData:
        for policy in policies:
            if 'DEBUG' in locals(): print ("Fetching policy " + policy['name'] + "...")
            try:
                # Retrieve Details of a Specified Policy
                # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies/{policy-id}
                if userName and password:
                    response = requests.get(serverURL + "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies/" + str(policy['id']),
                                            auth=(userName, password), params={"output": "JSON"})
                elif token:
                    response = requests.get(serverURL + "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies/" + str(policy['id']),
                                            headers={"Authorization": "Bearer "+token}, params={"output": "JSON"})
            except requests.exceptions.InvalidURL:
                print ("Invalid URL: " + serverURL + "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies/" + str(policy['id']))
                return None
            try:
                policyJSON = json.loads(response.content)
            except:
                print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
                return None
            policy = policyJSON

    # Add loaded policies to the policy dictionary
    policyDict.update({str(app_ID):policies})
    if 'DEBUG' in locals(): print (policyDict[str(app_ID)])

    return policies

def fetch_policies_legacy(serverURL,app_ID,userName,password):
    if 'DEBUG' in locals(): print ("Fetching policies for App " + str(app_ID) + "...")
    try:
        # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportPolicies
        # export policies to a JSON file.
        # GET /controller/policies/application_id 
        response = requests.get(serverURL + "/controller/policies/" + str(app_ID), auth=(userName, password), params={"output": "JSON"})
    except:
        print ("Could not get authentication token from " + serverURL + ".  Do you have the right controller hostname?")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    try:
        policies = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    return policies

def load_policies_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    policies = json.load(json_file)
    generate_policies_CSV_legacy(policies,0)

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
    fieldnames = ['Policy', 'Application', 'Events', 'Actions']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for policy in policies:
        if len(policy['events']['healthRuleEvents']) > 0:
            events = policy['events']['healthRuleEvents']['healthRuleScopeType']
        # TODO elif len(policy['events']['customEvents']) > 0:
        # TODO elif len(policy['events']['anomalyEvents']) > 0:
        # TODO elif len(policy['events']['otherEvents']) > 0:
        else:
            events = "None"
        if len(policy['actions']) > 0:
            Action_String = ""
            for action in policy['actions']:
                if Action_String is not "":
                    Action_String = Action_String + "\n"
                Action_String = Action_String + action['actionName']
        else:
            Action_String = ""
        try:
            filewriter.writerow({'Policy': policy['name'],
                                 'Application': app_ID,
                                 'Events': events,
                                 'Actions': Action_String})
        except:
            print ("Could not write to the output.")
            csvfile.close()
            return (-1)
    if 'DEBUG' in locals(): print "INFO: Displayed number of policies:" + str(len(policies))
    csvfile.close()

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

def generate_policies_CSV_legacy(app_ID,policies=None,fileName=None):
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
    fieldnames = ['Policy', 'Application', 'HealthRules', 'Entities', 'Actions']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for policy in policies:
        if 'reactorType' not in policy:
            continue        
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

        HR_String = ""
        for healthrule in HealthRules:
            if HR_String is not "":
                HR_String = HR_String + "\n"
            HR_String = HR_String + healthrule
        Action_String = ""
        for action in Actions:
            if Action_String is not "":
                Action_String = Action_String + "\n"
            Action_String = Action_String + action
        Entity_String = ""
        for entity in Entities:
            if Entity_String is not "":
                Entity_String = Entity_String + "\n"
            Entity_String = Entity_String + entity

        try:
            filewriter.writerow({'Policy': policy['name'],
                                 'Application': app_ID,
                                 'HealthRules': HR_String,
                                 'Entities': Entity_String,
                                 'Actions': Action_String})
        except:
            print ("Could not write to the output.")
            csvfile.close()
            return (-1)
    if 'DEBUG' in locals(): print "INFO: Number of policies:" + str(len(policies))
    csvfile.close()

def get_policies(serverURL,app_ID,userName=None,password=None,token=None):
    if userName and password:
        if fetch_policies(serverURL,app_ID,userName=userName,password=password) is not None:
            generate_policies_CSV(app_ID)
    elif token:
        if fetch_policies(serverURL,app_ID,token=token) is not None:
            generate_policies_CSV(app_ID)

def get_policies_legacy(serverURL,app_ID,userName=None,password=None,token=None,fileName=None):
    if userName and password:
        policies_List = fetch_policies_legacy(serverURL,app_ID,userName,password)
        generate_policies_CSV_legacy(app_ID,policies=policies_List,fileName=fileName)
    elif token:
        policies_List = fetch_policies_legacy(serverURL,app_ID,token=token)
        generate_policies_CSV_legacy(policies_List,app_ID,fileName=fileName)

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