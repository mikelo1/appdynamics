#!/usr/bin/python
import requests
import json
import csv

policyList = []

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
        HealthRules = ""
        evTemplate = policy['eventFilterTemplate']
        if evTemplate['healthRuleNames'] is not None:
            for healthRule in evTemplate['healthRuleNames']:
                if HealthRules is not "":
                    HealthRules = HealthRules + "\n"
                HealthRules = HealthRules + healthRule['entityName']
        else:
            HealthRules = "ANY"

        Actions = ""
        actTemplate = policy['actionWrapperTemplates']
        if actTemplate is not None:
            for action in actTemplate:
                if Actions is not "":
                    Actions = Actions + "\n"
                Actions = Actions + action['actionTag']
        else:
            Actions = "ANY"
        policyList.append([policy['name'],policy['applicationName'],HealthRules,Actions])

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
            try:
                filewriter.writerow({'Policy': policy[0],
                                    'Application': policy[1],
                                    'HealthRules': policy[2],
                                    'Actions': policy[3]})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()