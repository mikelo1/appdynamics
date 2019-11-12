#!/usr/bin/python
import requests
import json
import csv
import sys
from optparse import OptionParser

policyList = []

def buildBaseURL(controller,port):
    url = "http"

    if options.ssl:
        url = url + "s"
        if (port == "") :
            port = "443"
    else:
        if (port == "") :
            port = "80"

    return url + "://" + controller + ":" + port + "/controller/"

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
    return actions

def fetch_policies():
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
    return policies

def build_policy_to_action_list():
    policies = fetch_policies()
    for policy in policies:
        actionList = []
        actTemplate = policy['actionWrapperTemplates']
        if actTemplate is not None:
            for action in actTemplate:
                actionList.append((action['actionTag']))
        #print(policy['name']," ",actionList)
        policyList.append((policy['name'],actionList))

def write_element_action(actions,filewriter):
    for action in actions:
        if action['actionType'] == "EmailAction":
            CustomProperties = ""
            Emails = action['toAddress']
            ActionPlan = ""
        elif action['actionType'] == "CustomEmailAction":
            CustomProperties = ""
            custProp = action['customProperties']
            if custProp is not None:
                for prop in custProp:
                    if CustomProperties is not "":
                        CustomProperties = CustomProperties + "\n" 
                    CustomProperties = CustomProperties + prop + " : " + custProp[prop].encode('ASCII', 'ignore') 
            Emails = ""
            emailList = action['to']
            if emailList is not None:
                for email in emailList:
                    if Emails is not "":
                        Emails = Emails + "\n" 
                    Emails = Emails + email['emailAddress']
            ActionPlan = action['customEmailActionPlanName'].encode('ASCII', 'ignore')
        else:
            print("Warning: Unknown action type ",action['actionType'])
            return

        Policies = ""
        if len(policyList) > 0:
            for policy in policyList:
                for policy_action in policy[1]:
                    if policy_action == action['name']:
                        if Policies is not "":
                            Policies = Policies + "\n"    
                        Policies = Policies + policy[0]

        try:
            filewriter.writerow({'ActionName': action['name'],
                                'Emails': Emails,
                                'Policies': Policies,
                                'ActionPlan': ActionPlan,
                                'CustomProperties': CustomProperties})
        except:
            print ("Could not write action "+action['name']+" to the output file " + fileName + ".")
            csvfile.close()
            exit(1)

usage = "usage: %prog [options] controller username@account password Application_ID"
epilog= "example: %prog -s -p 443 ad-financial.saas.appdynamics.com johndoe@ad-financial s3cr3tp4ss 1001"

parser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
parser.add_option("-i", "--inputfile", action="store", dest="inFileName",
                  help="read source data from FILE.  If not provided, read from URL", metavar="FILE")
parser.add_option("-o", "--outfile", action="store", dest="outFileName",
                  help="write report to FILE.  If not provided, output to STDOUT", metavar="FILE")
parser.add_option("-p", "--port",
                  action="store", dest="port",
                  help="Controller port")
parser.add_option("-s", "--ssl",
                  action="store_true", dest="ssl",
                  help="Use SSL")

(options, args) = parser.parse_args()

if options.inFileName:
    print "Parsing file " + options.inFileName + "..."
    json_file = open(options.inFileName)
    actions = json.load(json_file)
else:
    if len(args) != 4:
        parser.error("incorrect number of arguments")
    if options.port:
        baseUrl = buildBaseURL(args[0],options.port)
    else:
        baseUrl = buildBaseURL(args[0],"")
    userName = args[1]
    password = args[2]
    app_ID   = args[3]

try:
    if options.outFileName:
        csvfile = open(options.outFileName, 'w')
    else:
        csvfile = sys.stdout
except:
    print ("Could not open output file " + options.outFileName + ".")
    exit(1)

fieldnames = ['ActionName', 'Emails', 'Policies', 'ActionPlan', 'CustomProperties']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

if 'baseUrl' in locals():
    build_policy_to_action_list()
    data_chunck = fetch_actions()
    if data_chunck is not None:
        write_element_action(data_chunck,filewriter)
elif 'root' in locals():
    write_element_action(root,filewriter)
else:
    print ("Nothing to do.")
