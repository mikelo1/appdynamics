#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class BusinessTransactionDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_business_transactions}
    entityJSONKeyword = "internalName"
    applications = None

    def __init__(self,applications):
        self.entityDict  = dict()
        self.applications = applications

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from business transactions data
        :param appID_List: list of application IDs, in order to obtain business transactions from local business transactions dictionary
        :param custom_transactionDict: dictionary containing business transactions
        :param fileName: output file name
        :returns: None
        """
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

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print "Application "+appID +" is not loaded in dictionary."
                continue
            for BT in self.entityDict[appID]:
                # Check if data belongs to a business transaction
                if 'entryPointType' not in BT: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'name': BT['name'].encode('ASCII', 'ignore'),
                                         'Application': self.applications.getAppName(appID),
                                         'entryPointType': BT['entryPointType'],
                                         'tierName': BT['tierName']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)
            if fileName is not None: csvfile.close()


    def get_business_transaction_ID(self,appID,transactionName):
        """
        Get the ID for a business transaction name.
        :param appID: the ID of the application
        :param transactionName: the name of the business transaction
        :returns: the ID of the specified business transaction name. Zero if no business transaction was found.
        """
        if appID < 0: return 0
        if str(appID) in self.entityDict:
            for transaction in self.entityDict[str(appID)]:
                if transaction['name'] == transactionName:
                    return transaction['id']
        return 0

    def get_business_transaction_name(self,appID,transactionID):
        """
        Get the name for a business transaction ID. Fetch business transaction data if not loaded yet.
        :param appID: the ID of the application
        :param transactionID: the ID of the business transaction
        :returns: the name of the specified business transaction ID. Empty string if no business transaction was found.
        """
        if appID <= 0 or transactionID <= 0: return None
        if str(appID) in self.entityDict:
            for transaction in entityDict[str(appID)]:
                if transaction['id'] == transactionID:
                    return transaction['name']
        return ""


    def get_business_transaction_nameList(self,appID):
        """
        Get the list of business transaction names for an application.
        :param appID: the ID of the application
        :returns: the list of business application names of the specified application ID. None if no business transaction was found.
        """
        if appID < 0: return None
        if str(appID) in self.entityDict:
            return [transaction['name'] for transaction in custom_transactionDict[str(appID)]]
        return None
