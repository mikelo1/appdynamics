#!/usr/bin/python
import requests
import json
import csv
import sys

BackendList = []
class Backend:
    name          = ""
    exitPointType = ""
    def __init__(self,name,exitPointType):
        self.name          = name
        self.exitPointType = exitPointType
    def __str__(self):
        return "({0},{1}".format(self.name,self.entryPointType)

def fetch_backends(baseUrl,userName,password,app_ID):
    print ("Fetching business transactions for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "rest/applications/" + app_ID + "/backends", auth=(userName, password), params={"output": "JSON"})
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    try:
        BEs = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_backends(BEs)

def load_backends_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    BEs = json.load(json_file)
    parse_backends(BEs)

def parse_backends(BEs):
    for BE in BEs:
        if 'exitPointType' not in BE:
            continue
        BE_name = BE['name'].encode('ASCII', 'ignore')
        BE_type = BE['exitPointType']
        BackendList.append(Backend(BE_name,BE_type))

def write_backends_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['name', 'exitPointType']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for BE in BackendList:
        try:
            filewriter.writerow({'name': BE.name,
                                 'exitPointType': BE.exitPointType})
        except:
            print ("Could not write to the output file. Backend: " + Backend['name'] + ", " + Backend['exitPointType'])
            csvfile.close()
            exit(1)
    csvfile.close()