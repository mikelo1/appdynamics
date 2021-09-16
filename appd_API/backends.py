import json
import csv
import sys
from .entities import AppEntity

class BackendDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_backends }
        self.entityKeywords = ["exitPointType"]


    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from backends data
        :param appID:_List list of application IDs, in order to obtain backends from local backends dictionary
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        fieldnames = ['name', 'Application', 'exitPointType']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print ("Application "+appID +" is not loaded in dictionary.")
                continue
            for backend in self.entityDict[appID]:
                if 'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'name': backend['name'].encode('ASCII', 'ignore'),
                                         'Application': self.controller.applications.getAppName(appID),
                                         'exitPointType': backend['exitPointType']})
                except ValueError as valError:
                    sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()


class EntrypointDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = {'fetch': self.controller.RESTfulAPI.fetch_entrypoints_TierRules}
        self.entityKeywords = ["hierarchicalConfigKey"]


    ###### FROM HERE PUBLIC FUNCTIONS ######

    def fetch(self,appID,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        self.controller.applications.load_tiers_and_nodes(appID)
        count = 0
        for tierID in self.controller.applications.getTiers_ID_List(appID):
            data = self.entityAPIFunctions['fetch'](tier_ID=tierID,selectors=selectors)
            count += self.load(streamdata=data,appID=appID)
        return count

    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from backends data
        :param appID:_List list of application IDs, in order to obtain backends from local backends dictionary
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        fieldnames = ['name', 'Tier', 'matchCondition', 'priority']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print ("Application "+appID +" is not loaded in dictionary.")
                continue
            for entrypoint in self.entityDict[appID]:
                if 'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True

                reload(sys)
                sys.setdefaultencoding('utf8')
                name = entrypoint['definitionName'].encode('ascii', 'ignore')
                tierName = self.controller.applications.getTierName(appID,entrypoint['hierarchicalConfigKey']['attachedEntity']['entityId'])
                matchCondition = entrypoint['matchPointRule']['uri']['matchType']+"  "+entrypoint['matchPointRule']['uri']['matchPattern']
                if entrypoint['matchPointRule']['uri']['inverse'] == True: matchCondition = "NOT "+matchCondition
                
                try:
                    filewriter.writerow({'name': name,
                                         'Tier': tierName,
                                         'matchCondition': matchCondition,
                                         'priority': entrypoint['matchPointRule']['priority'] })
                except ValueError as valError:
                    sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()
