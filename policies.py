#!/usr/bin/python
import requests
import json
import csv

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

class Entity:
    

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
        entTemplate = policy['entityFilterTemplates']
        if entTemplate is not None:
            pass
            for entity in entTemplate:
                pass
                # All <entities> in the Application
                # <entities> within the specified Tiers
                # These specified <entities>
                # <entities> matching the following criteria

                #Entities.append(entity['stringMatchExpression'])
        else:
            Entities = ["ANY"]

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
    fieldnames = ['Policy', 'Application', 'HealthRules', 'Actions']
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

            try:
                filewriter.writerow({'Policy': policy.name,
                                     'Application': policy.appName,
                                     'HealthRules': HR_String,
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