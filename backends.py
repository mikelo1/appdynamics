#!/usr/bin/python
import json
import csv
import sys
from applications import applications
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class BackendDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_backends}
    entityKeyword = "exitPointType"

    def __init__(self):
        self.entityDict = dict()

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
            for backend in self.entityDict[str(appID)]:
                # Check if data belongs to a backend
                if 'exitPointType' not in backend: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'name': backend['name'].encode('ASCII', 'ignore'),
                                         'Application': applications.getAppName(appID),
                                         'exitPointType': backend['exitPointType']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()

# Global object that works as Singleton
backends = BackendDict()

class EntrypointDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_entrypoints_TierRules}
    entityKeyword = "hierarchicalConfigKey"

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def fetch(self,appID,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        applications.load_tiers_and_nodes(appID)
        count = 0
        for tierID in applications.getTiers_ID_List(appID):
            data = self.entityAPIFunctions['fetch'](tier_ID=tierID,selectors=selectors)
            count += self.load(streamdata=data,appID=appID)
        return count

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

        fieldnames = ['name', 'Tier', 'matchCondition', 'priority']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for entrypoint in self.entityDict[str(appID)]:
                # Check if data belongs to a backend
                if 'entryPointType' not in entrypoint: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                reload(sys)
                sys.setdefaultencoding('utf8')
                name = entrypoint['definitionName'].encode('ascii', 'ignore')
                tierName = applications.getTierName(appID,entrypoint['hierarchicalConfigKey']['attachedEntity']['entityId'])
                matchCondition = entrypoint['matchPointRule']['uri']['matchType']+"  "+entrypoint['matchPointRule']['uri']['matchPattern']
                if entrypoint['matchPointRule']['uri']['inverse'] == True: matchCondition = "NOT "+matchCondition
                
                try:
                    filewriter.writerow({'name': name,
                                         'Tier': tierName,
                                         'matchCondition': matchCondition,
                                         'priority': entrypoint['matchPointRule']['priority'] })
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()

# Global object that works as Singleton
entrypoints = EntrypointDict()
