#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName

BTDict = dict()

###
 # Fetch application business transactions from a controller then add them to the business transactions dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application business transactions to fetch
 # @param selectors fetch only business transactions filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched business transactions. Zero if no business transaction was found.
###
def fetch_business_transactions(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching business transactions for App " + str(app_ID) + "...")

    # Retrieve All Business Transactions in a Business Application
    # GET /controller/rest/applications/application_name/business-transactions
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/business-transactions"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        transactions = json.loads(response)
    except JSONDecodeError:
        print ("fetch_business_transactions: Could not process JSON content.")
        return None
  
    # Add loaded business transactions to the business transaction dictionary
    BTDict.update({str(app_ID):transactions})

    if 'DEBUG' in locals():
        print "fetch_business_transactions: Loaded " + str(len(transactions)) + " transactions."
        #for appID in BTDict:
        #    print str(BTDict[appID])

    return len(transactions)

###
 # Generate CSV output from business transactions data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain business transactions from local business transactions dictionary
 # @param custom_transactionDict dictionary containing business transactions
 # @param fileName output file name
 # @return None
###
def generate_business_transactions_CSV(appID_List,custom_transactionDict=None,fileName=None):
    if appID_List is None and custom_transactionDict is None:
        return
    elif custom_transactionDict is None:
        custom_transactionDict = BTDict

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['name', 'Application', 'entryPointType', 'tierName']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for appID in appID_List:
        for BT in custom_transactionDict[str(appID)]:
            # Check if data belongs to a business transaction
            if 'entryPointType' not in BT: continue

            try:
                filewriter.writerow({'name': BT['name'].encode('ASCII', 'ignore'),
                                     'Application': getAppName(appID),
                                     'entryPointType': BT['entryPointType'],
                                     'tierName': BT['tierName']})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                exit(1)
        if fileName is not None: csvfile.close()

###
 # Generate JSON output from business transactions data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain business transactions from local business transactions dictionary
 # @param custom_transactionDict dictionary containing business transactions
 # @param fileName output file name
 # @return None
###
def generate_business_transactions_JSON(appID_List=None,custom_transactionDict=None,fileName=None):
    if appID_List is None and custom_transactionDict is None:
        return
    elif custom_transactionDict is None:
        custom_transactionDict = BTDict

    transactions = []
    for appID in appID_List:
        transactions = transactions + custom_transactionDict[str(appID)]

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


###
 # Display business transactions from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_business_transactions_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        transactions = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file data.")
        return 0
    custom_transactionDict = {"0":[transactions]} if type(transactions) is dict else {"0":transactions}
    if outputFormat and outputFormat == "JSON":
        generate_business_transactions_JSON(appID_List=[0],custom_transactionDict=custom_transactionDict,fileName=outFilename)
    else:
        generate_business_transactions_CSV(appID_List=[0],custom_transactionDict=custom_transactionDict,fileName=outFilename)

###
 # Display business transactions for a list of applications.
 # @param appID_List list of application IDs to fetch business transactions
 # @param selectors fetch only actions filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched business transactions. Zero if no business transaction was found.
###
def get_business_transactions(appID_List,selectors=None,outputFormat=None):
    numBTs = 0
    for appID in appID_List:
        sys.stderr.write("get business-transactions " + getAppName(appID) + "...\n")
        numBTs = numBTs + fetch_business_transactions(appID,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_business_transactions_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_business_transactions_CSV(appID_List)
    return numBTs

###
 # Get the ID for a business transaction name. Fetch business transaction data if not loaded yet.
 # @param appID the ID of the application
 # @param transactionName the name of the business transaction
 # @return the ID of the specified business transaction name.
###
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

###
 # Get the name for a business transaction ID. Fetch business transaction data if not loaded yet.
 # @param appID the ID of the application
 # @param transactionID the ID of the business transaction
 # @return the name of the specified business transaction ID.
###
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