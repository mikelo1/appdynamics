#!/usr/bin/python
import requests
import json
import csv
import sys

policyList = []
class Policy:
    name       = ""
    appName    = ""
    healthRules= []
    entities   = []
    actions    = []
    def __init__(self,name,appName,healthRules,entities,actions):
        self.name       = name
        self.appName    = appName
        self.healthRules= healthRules
        self.entities   = entities
        self.actions    = actions
    def __str__(self):
        return "({0},{1},{2},{3},{4})".format(self.name,self.appName,self.healthRules,self.entities,self.actions)


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

def fetch_policies(serverURL,app_ID,userName=None,password=None,token=None):
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

def generate_policies_CSV_legacy(policyList,app_ID,fileName=None):
    if len(policyList) == 0: return
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

    for policy in policyList:
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
    if 'DEBUG' in locals(): print "INFO: Number of policies:" + str(len(policyList))
    csvfile.close()


def generate_policies_CSV(policyList,app_ID,fileName=None):
    if len(policyList) == 0: return
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

    for policy in policyList:
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
    if 'DEBUG' in locals(): print "INFO: Number of policies:" + str(len(policyList))
    csvfile.close()

def get_policies_list(serverURL,userName=None,password=None,token=None,app_ID=None,fileName=None):
    if app_ID and userName and password:
        policies_List = fetch_policies(serverURL,app_ID,userName=userName,password=password)
        generate_policies_CSV(policies_List,app_ID,fileName=fileName)
    elif app_ID and token:
        policies_List = fetch_policies(serverURL,app_ID,token=token)
        generate_policies_CSV(policies_List,app_ID,fileName=fileName)
    else:
        # TODO: get all aplications list and fetch the policies list 
        pass




def get_policies_matching_action(name):
    MatchList = []
    if len(policyList) > 0:
        for policy in policyList:
            for policy_action in policy.actions:
                if policy_action == name:
                    MatchList.append(policy.name)
    else:
        pass # Policy list is empty
    return MatchList

def get_policies_matching_health_rule(name):
    MatchList = []
    if len(policyList) > 0:
        for policy in policyList:
            for policy_healthrule in policy.healthRules:
                if policy_healthrule == name:
                    MatchList.append(policy.name)
    else:
        pass # Policy list is empty
    return MatchList
	
#### TO DO:
####        get_policies_matching_business_transaction
####        get_policies_matching_tiers_and_nodes
####        get_policies_matching_JMX
####        get_policies_matching_Information_Point
####        get_policies_matching_Server
####        get_policies_matching_Database
####        get_policies_matching_Service_Endpoint
####        get_policies_matching_Error