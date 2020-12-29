#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict
from entities import AppEntity

class BackendDict(AppEntity):
    backendDict = dict()

    def __init__(self):
        self.backendDict = self.entityDict

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from backends data
     # @param appID_List list of application IDs, in order to obtain backends from local backends dictionary
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

        fieldnames = ['name', 'Application', 'exitPointType']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.backendDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for BE in self.backendDict[str(appID)]:
                # Check if data belongs to a backend
                if 'exitPointType' not in BE: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'name': BE['name'].encode('ASCII', 'ignore'),
                                         'Application': ApplicationDict().getAppName(appID),
                                         'exitPointType': BE['exitPointType']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()