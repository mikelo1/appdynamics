#!/usr/bin/python
import requests
import json
import csv
import sys

applicationList = []

class Application:
    name       = ""
    description= ""
    id         = 0
    accountGuid= ""
    tierList   = []
    def __init__(self,name,description,id,accountGuid,tierList=None):
        self.name       = name
        self.description= description
        self.id         = id
        self.accountGuid= accountGuid
        self.tierList   = tierList
    def __str__(self):
        return "({0},{1},{2},{3},{4})".format(self.name,self.description,self.id,self.accountGuid,self.tierList)

class Tier:
    name       = ""
    id         = 0
    nodeList   = []
    def __init__(self,name,id,nodeList):
        self.name       = name
        self.id         = id
        self.nodeList   = nodeList
    def __str__(self):
        return "({0},{1},{2})".format(self.name,self.id,self.nodeList)

class Node:
    name       = ""
    id         = 0
    def __init__(self,name,id):
        self.name       = name
        self.id         = id
    def __str__(self):
        return "({0},{1})".format(self.name,self.id)

def fetch_applications(baseUrl,userName,password):
    if 'DEBUG' in locals(): print ("Fetching applications for controller " + baseUrl + "...")
    try:
        response = requests.get(baseUrl + "rest/applications/", auth=(userName, password), params={"output": "JSON"})
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
        applications = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    return applications

def fetch_tiers(baseUrl,userName,password,appName):
    try:
        print ("Fetching tiers for application " + appName + "...")
        response = requests.get(baseUrl + "rest/applications/" + appName + "/tiers", auth=(userName, password), params={"output": "JSON"})
    except:
       print ("Could not get the tiers of application " + appName + ".")
       return

    try:
        tiers = json.loads(response.content)
    except:
        print ("Could not parse the tiers for application " + appName + ".")
        return
    return tiers

def fetch_nodes(baseUrl,userName,password,appName,tierName):
    try:
        print ("Fetching nodes for tier " + tierName + "...")
        response = requests.get(baseUrl + "rest/applications/" + appName + "/tiers/" + tierName + "/nodes", auth=(userName, password), params={"output": "JSON"})
    except:
        print ("Could not get the nodes of tier " + tierName + ".")
        return

    try:
        nodes = json.loads(response.content)
    except:
        print ("Could not parse the nodes for tier " + tierName + " in application " + appName + ".")
        return
    return nodes

def load_applications_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    applications = json.load(json_file)
    parse_applications(applications)

def parse_applications(applications,includeNodes=False):
    for application in applications:
        if includeNodes:
            tiers = fetch_tiers(baseUrl,userName,password,application['name'])
            tierList = []
            for tier in tiers:
                nodes = fetch_nodes(baseUrl,userName,password,appName,tier['name'])
                nodeList = []
                for node in nodes:
                    nodeList.append(Node(node['id'],node['name']))
                tierList.append(Tier(tier['id'],tier['name'],nodeList))
            applicationList.append(Application(application['name'],application['description'],application['id'],application['accountGuid'],tierList))
        else:
            applicationList.append(Application(application['name'],application['description'],application['id'],application['accountGuid']))
    if 'DEBUG' in locals():
        print "Number of applications:" + str(len(applicationList))
        for application in applicationList:
            print str(application)

def write_applications_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Name', 'Description', 'Id', 'AccountGuid']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for application in applicationList:
        try:
            filewriter.writerow({'Name': application.name,
                                'Description': application.description,
                                'Id': application.id,
                                'AccountGuid': application.accountGuid})
        except:
            print ("Could not write application "+application.name+" to the output.")
            csvfile.close()
            exit(1)
    csvfile.close()

def export_applications_CSV(outFileName,inFileName):
    if not inFileName or not outFileName:
        print "Missing arguments"
        return
    applications = load_applications_JSON(inFileName)
    applicationList = parse_applications(applications)
    write_applications_CSV(applicationList,outFileName)

def export_applications_CSV(outFileName,baseUrl,userName,password,includeNodes=False):
    if not outFileName or not baseUrl or not userName or not password:
        print "Missing arguments"
        return        
    # Obtain the applications list
    applications = fetch_applications(baseUrl,userName,password)
    applicationList = parse_applications(applications,includeNodes)
    write_applications_CSV(applicationList,outFileName)

def load_applications(baseUrl,userName,password,includeNodes=False):
    if not baseUrl or not userName or not password:
        print "Missing arguments"
        return        
    # Obtain the applications list
    applications = fetch_applications(baseUrl,userName,password)
    applicationList = parse_applications(applications,includeNodes)

def getID(appName):
    for application in applicationList:
        if application.name == appName:
            return application.id
    return -1

def getName(appID):
    for application in applicationList:
        if application.id == int(appID):
            return application.name
    return None