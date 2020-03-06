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

def fetch_policies(baseUrl,userName,password,app_ID):
    print ("Fetching policies for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "policies/" + app_ID, auth=(userName, password), params={"output": "JSON"})
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
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
    parse_policies(policies)

def load_policies_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    policies = json.load(json_file)
    parse_policies(policies)

def parse_policies(policies):
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

        policyList.append(Policy(Name,AppName,HealthRules,Entities,Actions))
#    print "Number of policies:" + str(len(policyList))
#    for policy in policyList:
#        print str(policy)    

def write_policies_CSV(fileName=None):
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

    if len(policyList) > 0:           
        for policy in policyList:
            HR_String = ""
            for healthrule in policy.healthRules:
                if HR_String is not "":
                    HR_String = HR_String + "\n"
                HR_String = HR_String + healthrule
            Action_String = ""
            for action in policy.actions:
                if Action_String is not "":
                    Action_String = Action_String + "\n"
                Action_String = Action_String + action
            Entity_String = ""
            for entity in policy.entities:
                if Entity_String is not "":
                    Entity_String = Entity_String + "\n"
                Entity_String = Entity_String + entity
            try:
                filewriter.writerow({'Policy': policy.name,
                                     'Application': policy.appName,
                                     'HealthRules': HR_String,
                                     'Entities': Entity_String,
                                     'Actions': Action_String})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()

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