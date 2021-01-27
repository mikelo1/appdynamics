#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class BackendDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_backends}

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,appID_List,fileName=None):
        """
        Generate CSV output from backends data
        :param appID:_List list of application IDs, in order to obtain backends from local backends dictionary
        :param fileName: output file name
        :returns: None
        """
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
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for BE in self.entityDict[str(appID)]:
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


class EntrypointDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_entrypoints_TierRules}

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,appID_List,fileName=None):
        """
        Generate CSV output from backends data
        :param appID:_List list of application IDs, in order to obtain backends from local backends dictionary
        :param fileName: output file name
        :returns: None
        """
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
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for BE in self.entityDict[str(appID)]:
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