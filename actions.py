#!/usr/bin/python
import requests
import json
import csv
import sys
from policies import get_policies_matching_action

actionsList = []
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

def fetch_actions():
    print ("Fetching actions for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "actions/" + app_ID, auth=(userName, password), params={"output": "JSON"})
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
        actions = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_actions(actions)

def load_actions_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    actions = json.load(json_file)
    parse_actions(actions)

def parse_actions(actions):
    for action in actions:
        if 'actionType' not in action:
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
        else:
            print("Warning: Unknown action type ",action['actionType'])
            return

        Policies = get_policies_matching_action(action['name'])

        actionsList.append(Action(action['name'],Emails,Policies,ActionPlan,CustomProperties))

def write_actions_CSV(fileName=None):
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

    for action in actionsList:
        emails_str    = ""
        for email in action.emails:
            if emails_str != "": emails_str = emails_str + "\n"
            emails_str = emails_str + email
        policies_str  = ""
        for policy in action.policies:
            if policies_str != "": policies_str = policies_str + "\n"
            policies_str = policies_str + policy
        properties_str= ""
        for property in action.properties:
            if properties_str != "": properties_str = properties_str + "\n"
            properties_str = properties_str + property
        try:
            filewriter.writerow({'ActionName': action.name,
                                'Emails': emails_str,
                                'Policies': policies_str,
                                'ActionPlan': action.actionPlan,
                                'CustomProperties': properties_str})
        except:
            print ("Could not write action "+action.name+" to the output.")
            csvfile.close()
            exit(1)
    csvfile.close()