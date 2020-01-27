#!/usr/bin/python
import requests
import json
import csv
import sys

BTList = []
class BusinessTransaction:
    name          = ""
    BT_id         = 0
    entryPointType= ""
    tierName      = ""
    def __init__(self,name,BT_id,entryPointType,tierName):
        self.name          = name
        self.BT_id         = BT_id
        self.entryPointType= entryPointType
        self.tierName      = tierName
    def __str__(self):
        return "({0},{1},{2})".format(self.name,self.BT_id,self.entryPointType,self.tierName)

def fetch_business_transactions(baseUrl,userName,password,app_ID):
    print ("Fetching business transactions for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "rest/applications/" + app_ID + "/business-transactions", auth=(userName, password), params={"output": "JSON"})
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
        BTs = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_business_transactions(BTs)

def load_business_transactions_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    BTs = json.load(json_file)
    parse_business_transactions(BTs)

def parse_business_transactions(BTs):
    for BT in BTs:
        if 'entryPointType' not in BT:
            continue
        name = BT['name'].encode('ASCII', 'ignore')
        BTList.append(BusinessTransaction(name,BT['id'],BT['entryPointType'],BT['tierName']))
#    print "Number of business transactions:" + str(len(BTList))
#    for BT in BTList:
#        print str(BT)

def get_business_transaction_ID(name):
    for BT in BTList:
        if BT.name == name:
            return BT.id
    return None

def write_business_transactions_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['name', 'entryPointType', 'tierName']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for BT in BTList:
        try:
            filewriter.writerow({'name': BT.name,
                                 'entryPointType': BT.entryPointType,
                                 'tierName': BT.tierName})
        except:
            print ("Could not write to the output file.")
            csvfile.close()
            exit(1)
    csvfile.close()