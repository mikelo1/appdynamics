#!/usr/bin/python
import requests
import json
import csv
import sys

applicationList = []

class Application:
    id         = 0
    name       = ""
    description= ""
    accountGuid= ""
    tierList   = []
    def __init__(self,id,name,description,accountGuid,tierList=None):
        self.id         = id
        self.name       = name
        self.description= description
        self.accountGuid= accountGuid
        self.tierList   = tierList
    def __str__(self):
        return "({0},{1},{2},{3},{4})".format(self.id,self.name,self.description,self.accountGuid,self.tierList)

class Tier:
    id         = 0
    name       = ""
    nodeList   = []
    def __init__(self,id,name,nodeList):
        self.id         = id
        self.name       = name
        self.nodeList   = nodeList
    def __str__(self):
        return "({0},{1},{2})".format(self.id,self.name,self.nodeList)

class Node:
    id         = 0
    name       = ""
    def __init__(self,id,name):
        self.id         = id
        self.name       = name
    def __str__(self):
        return "({0},{1})".format(self.id,self.name)


###
 # Fetch applications from a controller. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @param includeNodes flag to determine if nodes and tiers need to be loaded as well
 # @return the number of fetched applications. Zero if no application was found.
###
def fetch_applications(serverURL,userName=None,password=None,token=None,includeNodes=False):
    if 'DEBUG' in locals(): print ("Fetching applications for controller " + serverURL + "...")
    try:
        if userName and password:
            response = requests.get(serverURL + "/controller/rest/applications/", auth=(userName, password), params={"output": "JSON"})
        elif token:
            response = requests.get(serverURL + "/controller/rest/applications/", headers={"Authorization": "Bearer "+token}, params={"output": "JSON"})
        else:
            print "fetch_applications: Incorrect parameters."
            return 0
    except requests.exceptions.InvalidURL:
        print ("Could not get authentication token from " + serverURL + ". Do you have the right controller hostname?")
        return 0

    if response.status_code != 200:
        print "fetch_applications: Something went wrong on HTTP request. Status:", response.status_code
        if 'DEBUG' in locals():
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w") 
            file1.write(response.content)
            file1.close() 
        return 0

    try:
        applicationsJSON = json.loads(response.content)
    except:
        print ("Could not process response content. Did you mess up your username/password or token?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return 0

    for application in applicationsJSON:
        if includeNodes:
            tiers = fetch_tiers(serverURL,application['name'],userName,password,token)
            if tiers is None: continue
            tierList = []
            for tier in tiers:
                nodes = fetch_nodes(serverURL,application['name'],tier['name'],userName,password,token)
                if nodes is None: continue
                nodeList = []
                for node in nodes:
                    nodeList.append(Node(node['id'],node['name']))
                tierList.append(Tier(tier['id'],tier['name'],nodeList))
            applicationList.append(Application(application['id'],application['name'],application['description'],application['accountGuid'],tierList))
        else:
            applicationList.append(Application(application['id'],application['name'],application['description'],application['accountGuid']))

    if 'DEBUG' in locals():
        print "Loaded applications:" + str(len(applicationList))
        for application in applicationList:
            print str(application)

    return len(applicationsJSON)

def fetch_tiers(serverURL,appName,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching tiers for application " + appName + "...")
    try:
        if userName and password:
            response = requests.get(serverURL + "/controller/rest/applications/" + appName + "/tiers", auth=(userName, password), params={"output": "JSON"})
        elif token:
            response = requests.get(serverURL + "/controller/rest/applications/" + appName + "/tiers", headers={"Authorization": "Bearer "+token}, params={"output": "JSON"})
        else:
            print "fetch_tiers: Incorrect parameters."
            return None
    except requests.exceptions.InvalidURL:
       print ("Invalid URL: " + serverURL + "/controller/rest/applications/" + appName + "/tiers")
       return None

    try:
        tiers = json.loads(response.content)
    except:
        print ("Could not parse the tiers for application " + appName + ".")
        return None
    return tiers

def fetch_nodes(serverURL,appName,tierName,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching nodes for tier " + tierName + "...")
    try:
        if userName and password:
            response = requests.get(serverURL + "/controller/rest/applications/" + appName + "/tiers/" + tierName + "/nodes", auth=(userName, password), params={"output": "JSON"})
        elif token:
            response = requests.get(serverURL + "/controller/rest/applications/" + appName + "/tiers/" + tierName + "/nodes", headers={"Authorization": "Bearer "+token}, params={"output": "JSON"})
        else:
            print "fetch_nodes: Incorrect parameters."
            return None
    except requests.exceptions.InvalidURL:
        print ("Invalid URL: " + serverURL + "/controller/rest/applications/" + appName + "/tiers/" + tierName + "/nodes")
        return None

    try:
        nodes = json.loads(response.content)
    except:
        print ("Could not parse the nodes for tier " + tierName + " in application " + appName + ".")
        return None
    return nodes

def load_applications_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    applications = json.load(json_file)
    return applications

def generate_applications_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Name', 'Description', 'Id', 'AccountGuid', 'Tiers', 'Nodes']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for application in applicationList:
        Tiers_str = ""
        Nodes_str = ""
        if application.tierList is not None and len(application.tierList) > 0:
            for tier in application.tierList:
                Tiers_str = Tiers_str + tier.name + " "
                for node in tier.nodeList:
                    Nodes_str = Nodes_str + node.name + " "
        try:
            filewriter.writerow({'Name': application.name,
                                'Description': application.description,
                                'Id': application.id,
                                'AccountGuid': application.accountGuid,
                                'Tiers': Tiers_str,
                                'Nodes': Nodes_str})
        except:
            print ("Could not write application "+application.name+" to the output.")
            csvfile.close()
            exit(1)
    csvfile.close()

def get_applications_list(serverURL,userName=None,password=None,token=None,includeNodes=False):
    if userName and password:
        if fetch_applications(serverURL,userName=userName,password=password,includeNodes=includeNodes) > 0:
            generate_applications_CSV()
    elif token:
        if fetch_applications(serverURL,token=token,includeNodes=includeNodes) > 0:
            generate_applications_CSV()

def load_applications(serverURL,userName=None,password=None,token=None,includeNodes=False):
#    del applicationList
    if userName and password:
        val = fetch_applications(serverURL,userName=userName,password=password)
    elif token:
        val = fetch_applications(serverURL,token=token)
    else:
        print "load_applications: Incorrect parameters."
        return 0
    print "Loaded applications: "+str(val)
    return val



def getID(appName):
    if applicationList is None or len(applicationList) == 0:
        print "getID: Application list is empty"
        return -1
    for application in applicationList:
        if application.name == appName:
            return application.id
    return -1

def getName(appID):
    if applicationList is None or len(applicationList) == 0:
        print "getName: Application list is empty"
        return -1
    for application in applicationList:
        if application.id == int(appID):
            return application.name
    return None