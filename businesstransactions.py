#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict
from entities import AppEntity

class BusinessTransactionDict(AppEntity):
    BTDict = dict()

    def __init__(self):
        self.BTDict = self.entityDict

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from business transactions data
     # @param appID_List list of application IDs, in order to obtain business transactions from local business transactions dictionary
     # @param custom_transactionDict dictionary containing business transactions
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

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

        for appID in appID_List:
            if str(appID) not in self.BTDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for BT in self.BTDict[str(appID)]:
                # Check if data belongs to a business transaction
                if 'entryPointType' not in BT: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'name': BT['name'].encode('ASCII', 'ignore'),
                                         'Application': ApplicationDict().getAppName(appID),
                                         'entryPointType': BT['entryPointType'],
                                         'tierName': BT['tierName']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)
            if fileName is not None: csvfile.close()

    ###
     # Get the ID for a business transaction name.
     # @param appID the ID of the application
     # @param transactionName the name of the business transaction
     # @return the ID of the specified business transaction name. Zero if no business transaction was found.
    ###
    def get_business_transaction_ID(self,appID,transactionName):
        if appID < 0: return 0
        if str(appID) in self.BTDict:
            for transaction in self.BTDict[str(appID)]:
                if transaction['name'] == transactionName:
                    return transaction['id']
        return 0

    ###
     # Get the name for a business transaction ID. Fetch business transaction data if not loaded yet.
     # @param appID the ID of the application
     # @param transactionID the ID of the business transaction
     # @return the name of the specified business transaction ID. Empty string if no business transaction was found.
    ###
    def get_business_transaction_name(self,appID,transactionID):
        if appID <= 0 or transactionID <= 0: return None
        if str(appID) in self.BTDict:
            for transaction in BTDict[str(appID)]:
                if transaction['id'] == transactionID:
                    return transaction['name']
        return ""

    ###
     # Get the list of business transaction names for an application.
     # @param appID the ID of the application
     # @return the list of business application names of the specified application ID. None if no business transaction was found.
    ###
    def get_business_transaction_nameList(self,appID):
        if appID < 0: return None
        if str(appID) in self.BTDict:
            return [transaction['name'] for transaction in custom_transactionDict[str(appID)]]
        return None