#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTful_JSON

BTDict = dict()

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

###
 # Fetch application business transactions from a controller then add them to the business transactions dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application business transactions to fetch
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched business transactions. Zero if no business transaction was found.
###
def fetch_business_transactions(app_ID,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching business transactions for App " + str(app_ID) + "...")

    # Retrieve All Business Transactions in a Business Application
    # GET /controller/rest/applications/application_name/business-transactions
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/business-transactions"
    if serverURL and userName and password:
        transactions = fetch_RESTful_JSON(restfulPath,params={"output": "JSON"},serverURL=serverURL,userName=userName,password=password)
    else:
        transactions = fetch_RESTful_JSON(restfulPath,params={"output": "JSON"})

    if transactions is None:
        print "fetch_business_transactions: Failed to retrieve business transactions for application " + str(app_ID)
        return None
  
    # Add loaded business transactions to the business transaction dictionary
    BTDict.update({str(app_ID):transactions})

    if 'DEBUG' in locals():
        print "fetch_business_transactions: Loaded " + str(len(transactions)) + " transactions."
        #for appID in BTDict:
        #    print str(BTDict[appID])

    return len(transactions)

def generate_business_transactions_CSV(app_ID,transactions=None,fileName=None):
    if transactions is None and str(app_ID) not in BTDict:
        print "Business transaction for application "+str(app_ID)+" not loaded."
        return
    elif transactions is None and str(app_ID) in BTDict:
        transactions = BTDict[str(app_ID)]

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

    for BT in transactions:
        if 'entryPointType' not in BT:
            continue

        try:
            filewriter.writerow({'name': BT['name'].encode('ASCII', 'ignore'),
                                 'entryPointType': BT['entryPointType'],
                                 'tierName': BT['tierName']})
        except:
            print ("Could not write to the output file.")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

def generate_business_transactions_JSON(app_ID,transactions=None,fileName=None):
    if transactions is None and str(app_ID) not in BTDict:
        print "Business transaction for application "+str(app_ID)+" not loaded."
        return
    elif transactions is None and str(app_ID) in BTDict:
        transactions = BTDict[str(app_ID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(transactions, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(transactions)


###### FROM HERE PUBLIC FUNCTIONS ######


def get_business_transactions_from_stream(streamdata,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        BTs = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    generate_business_transactions_CSV(app_ID=0,transactions=BTs,fileName=outFilename)

def get_business_transactions(app_ID,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_policies(app_ID)
    elif serverURL and userName and password:
        if fetch_business_transactions(app_ID,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_business_transactions: Failed to retrieve business transactions for application " + str(app_ID)
            return None
    else:
        if fetch_business_transactions(app_ID,token=token) == 0:
            print "get_business_transactions: Failed to retrieve business transactions for application " + str(app_ID)
            return None
    if outputFormat and outputFormat == "JSON":
        generate_business_transactions_JSON(app_ID)
    else:
        generate_business_transactions_CSV(app_ID)

def get_business_transaction_ID(appID,transactionName):
    if appID <= 0: return 0
    if str(appID) not in BTDict:
        if fetch_business_transactions(appID) == 0:
            print "get_business_transaction_ID: Failed to retrieve business transactions for application " + str(app_ID)
            return 0
    for transaction in BTDict[str(appID)]:
        if transaction['name'] == transactionName:
            return transaction['id']
    return 0

def get_business_transaction_name(appID,transactionID):
    if appID <= 0 or transactionID <= 0: return None
    if str(appID) not in BTDict:
        if fetch_business_transactions(appID) == 0:
            print "get_business_transaction_name: Failed to retrieve business transactions for application " + str(app_ID)
            return None
    for transaction in BTDict[str(appID)]:
        if transaction['id'] == transactionID:
            return transaction['name']
    return None