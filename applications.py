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
    def __init__(self,name,description,id,accountGuid):
        self.name       = name
        self.description= description
        self.id         = id
        self.accountGuid= accountGuid
    def __str__(self):
        return "({0},{1},{2},{3})".format(self.name,self.description,self.id,self.accountGuid)

def fetch_applications(baseUrl,userName,password):
    print ("Fetching applications for controller " + baseUrl + "...")
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
    parse_applications(applications)

def load_applications_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    applications = json.load(json_file)
    parse_applications(applications)

def parse_applications(applications):
  #  applicationList = applications
    for application in applications:
        applicationList.append(Application(application['name'],application['description'],application['id'],application['accountGuid']))

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

def getID(appName):
    for application in applicationList:
        if application.name == appName:
            return application.id
    return -1

def getName(appID):
    for application in applicationList:
        if application.id == appID:
            return application.name
    return None