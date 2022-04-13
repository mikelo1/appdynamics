import json
import csv
import sys
from .entities import ControllerEntity

class ApplicationDict(ControllerEntity):

    def __init__(self,controller):
        super(ApplicationDict,self).__init__(controller)
        self['CSVfields'] = {'Name':        self.__str_application_name,
                             'Id':          self.__str_application_id,
                             'Types':       self.__str_application_types,
                             # 'Description': self.__str_application_description,
                             'Tiers':       self.__str_application_tiers,
                             'Nodes':       self.__str_application_nodes }

    def __str_application_name(self,application):
        return application['name'] if sys.version_info[0] >= 3 else application['name'].encode('ASCII', 'ignore')

    def __str_application_id(self,application):
        return application['id']

    def __str_application_types(self,application):
        return application['applicationTypeInfo']['applicationTypes']

#    def __str_application_description(self,application):
#        return application['description'] if sys.version_info[0] >= 3 and 'description' in application else application['description'].encode('ASCII', 'ignore') if 'description' in application else ""

    def __str_application_tiers(self,application):
        tierList = [tier['name'] for tier in application['tiers']] if 'tiers' in application else []
        return ','.join(map(lambda x: str(x.text),tierList))

    def __str_application_nodes(self,application):
        nodeList = [node['name'] for tier in application['tiers'] for node in tier['nodes']] if 'tiers' in application else []
        return ','.join(map(lambda x: str(x.text),nodeList))

#    def __fetch_tiers_and_nodes(self,app_ID):
#        """
#        Fetch tiers and nodes details for one specific application
#        :param app_ID: the ID number of the application tiers and nodes to fetch
#        :returns: a dictionary with tiers and nodes. None if no tier was found.
#        """
#        tiers = json.loads(self.controller.RESTfulAPI.fetch_tiers(app_ID))
#        if tiers is not None:
#            for tier in tiers:
#                nodes = json.loads(self.controller.RESTfulAPI.fetch_tier_nodes(app_ID,tier['name']))
#                if nodes is not None:
#                    tier.update({'nodes':nodes})
#            return {'tiers':tiers}

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,fileName=None):
        """
        Generate CSV output from applications data
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

        fieldnames = [ name for name in self['CSVfields'] ]
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
        keywords   = ['accountGuid','eumWebApplications','dbMonApplication','mobileAppContainers','cloudMonitoringApplication',
                             'iotApplications','simApplication','apmApplications']

        for appType in self['entities']:
            # Check if data belongs to a recognized application type
            if appType not in keywords: continue
            elif self['entities'][appType] is None: continue
            elif type(self['entities'][appType]) is dict:
                appList = [self['entities'][appType]]
            elif type(self['entities'][appType]) is list:
                appList = self['entities'][appType]
            else: continue

            if 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True

            for application in appList:
                row = { name: self['CSVfields'][name](application) for name in self['CSVfields'] }
                try:
                    filewriter.writerow(row)
                except (TypeError,ValueError) as error:
                    sys.stderr.write("generate_CSV: "+str(error)+"\n")
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()

    def get_application_Name_list(self,application_type=None):
        """
        Get a list with all application names.
        :application_type: could be one of these [apiMonitoringApplications,analyticsApplication,eumWebApplications,dbMonApplication,mobileAppContainers,cloudMonitoringApplication,iotApplications,simApplication,apmApplications]
        :returns: a list with all application names. None if no application was found.
        """
        appNameList=[]
        for appType in self['entities']:
            if application_type and appType != application_type: continue
            if type(self['entities'][appType]) is dict:
                appNameList.append(self['entities'][appType]['name'])
            elif type(self['entities'][appType]) is list:
                appNameList += [ application['name'] for application in self['entities'][appType] ]
        if len(appNameList) > 0: return appNameList

    def get_application_ID_list(self,application_type=None):
        """
        Get a list with all application IDs.
        :application_type: could be one of these [apiMonitoringApplications,analyticsApplication,eumWebApplications,dbMonApplication,mobileAppContainers,cloudMonitoringApplication,iotApplications,simApplication,apmApplications]
        :returns: a list with all application IDs. None if no application was found.
        """
        appNameList=[]
        for appType in self['entities']:
            if application_type and appType != application_type: continue
            if type(self['entities'][appType]) is dict:
                appNameList.append(self['entities'][appType]['id'])
            elif type(self['entities'][appType]) is list:
                appNameList += [ application['id'] for application in self['entities'][appType] ]
        if len(appNameList) > 0: return appNameList

    def getAppID(self,appName):
        """
        Get the ID for an application name.
        :param appName: the name of the application
        :returns: the ID of the specified application name. None if the application was not found.
        """
        if self['entities'] is None: return -1
        for appType in self['entities']:
            if type(self['entities'][appType]) is dict:
                if self['entities'][appType]['name'] == appName:
                    return application['id']
            elif type(self['entities'][appType]) is list:
                for application in self['entities'][appType]:
                    if application['name'] == appName:
                        return application['id']
        if 'DEBUG' in locals(): sys.stderr.write("Application "+appName+" is not loaded.\n")

    def getAppName(self,appID):
        """
        Get the name for an application ID.
        :param appID: the ID of the application
        :returns: the name of the specified application ID. None if the application was not found.
        """
        #if type(appID) in [str,unicode]: appID = int(appID)
        if type(appID) in [str]: appID = int(appID)
        if self['entities'] is None: return str(appID)
        for appType in self['entities']:
            if type(self['entities'][appType]) is dict:
                if self['entities'][appType]['id'] == appID:
                    return self['entities'][appType]['name']
            elif type(self['entities'][appType]) is list:
                for application in self['entities'][appType]:
                    if application['id'] == appID:
                        return application['name']
        if 'DEBUG' in locals(): sys.stderr.write("Application "+str(appID)+" is not loaded.\n")

    def hasTiers(self,appID):
        """
        Check if an application has tiers.
        :param appID: the ID of the application
        :returns: true if the specified application has Tiers. False otherwise.
        """
        if 'apmApplications' not in self['entities'] or self['entities']['apmApplications'] is None: return False
        if type(appID) is str: appID = int(appID)
        for apmApp in self['entities']['apmApplications']:
            if apmApp['id'] == appID:
                return apmApp['applicationTypeInfo']['hasTiers']
        return False


#    def load_tiers_and_nodes(self,app_ID):
#        """
#        Load tiers and nodes details for one specific application
#        :param app_ID: the ID number of the application tiers and nodes to fetch
#        :returns: the number of tiers. Zero if no tier was found.
#        """
#        if 'apmApplications' not in self['entities'] or self['entities']['apmApplications'] is None: return 0
#        if type(app_ID) is str: app_ID = int(app_ID)
#        if type(self['entities']['apmApplications']) is dict:
#            appList = []
#            if self['entities']['apmApplications']['id'] == app_ID:
#                self['entities']['apmApplications'].update(self.__fetch_tiers_and_nodes(app_ID))
#                return len(self['entities']['apmApplications']['tiers'])
#        elif type(self['entities']['apmApplications']) is list:
#            for i in range(len(self['entities']['apmApplications'])):
#                if self['entities']['apmApplications'][i]['id'] == app_ID:
#                    self['entities']['apmApplications'][i].update(self.__fetch_tiers_and_nodes(app_ID))
#                    return len(self['entities']['apmApplications'][i]['tiers'])
#
#    def getTiers_ID_List(self,appID):
#        """
#        Get a list of tier IDs for an application.
#        :returns: a list with all tier IDs for an application. None if no tier was found.
#        """
#        if 'apmApplications' not in self['entities'] or self['entities']['apmApplications'] is None: return None
#        if type(appID) is str: appID = int(appID)
#        if type(self['entities']['apmApplications']) is dict and self['entities']['apmApplications']['id'] == appID:
#            if 'tiers' not in self['entities']['apmApplications']:
#                self.load_tiers_and_nodes(appID)
#            return [ tier['id'] for tier in self['entities']['apmApplications']['tiers'] ]
#        elif type(self['entities']['apmApplications']) is list:
#            for apmApp in self['entities']['apmApplications']:
#                if apmApp['id'] == appID:
#                    if 'tiers' not in apmApp:
#                        self.load_tiers_and_nodes(appID)
#                    return [ tier['id'] for tier in apmApp['tiers'] ]
#
#    def getTierName(self,tierID,appID=None):
#        """
#        Get the name for a tier ID.
#        :param appID: the ID of the application
#        :param tierID: the ID of the tier
#        :returns: the name of the specified tier ID. None if the tier was not found.
#        """
#        if 'apmApplications' not in self['entities'] or self['entities']['apmApplications'] is None: return None
#        if type(appID) is str: appID = int(appID)
#        for apmApp in self['entities']['apmApplications']:
#            if appID and apmApp['id'] != appID: continue
#            if 'tiers' not in apmApp: continue
#            for tier in apmApp['tiers']:
#               if tier['id'] == tierID:
#                   return tier['name']