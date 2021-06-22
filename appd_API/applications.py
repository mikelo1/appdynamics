#!/usr/bin/python
import json
import csv
import sys
from entities import ControllerEntity

class ApplicationDict(ControllerEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_applicationsAllTypes }
        self.entityJSONKeyword = 'apmApplications'

    def __fetch_tiers_and_nodes(self,app_ID):
        """
        Fetch tiers and nodes details for one specific application
        :param app_ID: the ID number of the application tiers and nodes to fetch
        :returns: a dictionary with tiers and nodes. None if no tier was found.
        """
        tiers = json.loads(self.controller.RESTfulAPI.fetch_tiers(app_ID))
        if tiers is not None:
            for tier in tiers:
                nodes = json.loads(self.controller.RESTfulAPI.fetch_tier_nodes(app_ID,tier['name']))
                if nodes is not None:
                    tier.update({'nodes':nodes})
            return {'tiers':tiers}

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
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        fieldnames = ['Name', 'Id', 'Type', 'Description', 'Tiers', 'Nodes']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appType in self.entityDict:
            # Check if data belongs to an application
            if appType not in ['eumWebApplications','dbMonApplication','mobileAppContainers','cloudMonitoringApplication',
                                     'iotApplications','simApplication','apmApplications']: continue
            elif self.entityDict[appType] is None: continue
            elif type(self.entityDict[appType]) is dict:
                appList = [self.entityDict[appType]]
            elif type(self.entityDict[appType]) is list:
                appList = self.entityDict[appType]
            else: continue

            if 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True

            for application in appList:
                tierList = [tier['name'] for tier in application['tiers']] if 'tiers' in application else []
                nodeList = [node['name'] for tier in application['tiers'] for node in tier['nodes']] if 'tiers' in application else []

                try:
                    filewriter.writerow({'Name': application['name'],
                                        'Id': application['id'],
                                        'Type': appType,
                                        'Description': application['description'],
                                        'Tiers': ','.join(map(lambda x: str(x.text),tierList)),
                                        'Nodes': ','.join(map(lambda x: str(x.text),nodeList)) })
                except (TypeError,ValueError) as error:
                    sys.stderr.write("generate_CSV: "+str(error)+"\n")
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()


    def load_tiers_and_nodes(self,app_ID):
        """
        Load tiers and nodes details for one specific application
        :param app_ID: the ID number of the application tiers and nodes to fetch
        :returns: the number of tiers. Zero if no tier was found.
        """
        if 'apmApplications' not in self.entityDict or self.entityDict['apmApplications'] is None: return 0
        if type(app_ID) is str: app_ID = int(app_ID)
        if type(self.entityDict['apmApplications']) is dict:
            appList = []
            if self.entityDict['apmApplications']['id'] == app_ID:
                self.entityDict['apmApplications'].update(self.__fetch_tiers_and_nodes(app_ID))
                return len(self.entityDict['apmApplications']['tiers'])
        elif type(self.entityDict['apmApplications']) is list:
            for i in range(len(self.entityDict['apmApplications'])):
                if self.entityDict['apmApplications'][i]['id'] == app_ID:
                    self.entityDict['apmApplications'][i].update(self.__fetch_tiers_and_nodes(app_ID))
                    return len(self.entityDict['apmApplications'][i]['tiers'])

    def get_application_Name_list(self,application_type=None):
        """
        Get a list with all application names.
        :application_type: could be one of these [apiMonitoringApplications,analyticsApplication,eumWebApplications,dbMonApplication,mobileAppContainers,cloudMonitoringApplication,iotApplications,simApplication,apmApplications]
        :returns: a list with all application names. None if no application was found.
        """
        appNameList=[]
        for appType in self.entityDict:
            if application_type and appType != application_type: continue
            if type(self.entityDict[appType]) is dict:
                appNameList.append(self.entityDict[appType]['name'])
            elif type(self.entityDict[appType]) is list:
                appNameList += [ application['name'] for application in self.entityDict[appType] ]
        if len(appNameList) > 0: return appNameList

    def get_application_ID_list(self,application_type=None):
        """
        Get a list with all application IDs.
        :application_type: could be one of these [apiMonitoringApplications,analyticsApplication,eumWebApplications,dbMonApplication,mobileAppContainers,cloudMonitoringApplication,iotApplications,simApplication,apmApplications]
        :returns: a list with all application IDs. None if no application was found.
        """
        appNameList=[]
        for appType in self.entityDict:
            if application_type and appType != application_type: continue
            if type(self.entityDict[appType]) is dict:
                appNameList.append(self.entityDict[appType]['id'])
            elif type(self.entityDict[appType]) is list:
                appNameList += [ application['id'] for application in self.entityDict[appType] ]
        if len(appNameList) > 0: return appNameList

    def getAppID(self,appName):
        """
        Get the ID for an application name.
        :param appName: the name of the application
        :returns: the ID of the specified application name. None if the application was not found.
        """
        for appType in self.entityDict:
            if type(self.entityDict[appType]) is dict:
                if self.entityDict[appType]['name'] == appName:
                    return application['id']
            elif type(self.entityDict[appType]) is list:
                for application in self.entityDict[appType]:
                    if application['name'] == appName:
                        return application['id']
        if 'DEBUG' in locals(): sys.stderr.write("Application "+appName+" is not loaded.\n")

    def getAppName(self,appID):
        """
        Get the name for an application ID.
        :param appID: the ID of the application
        :returns: the name of the specified application ID. None if the application was not found.
        """
        if type(appID) in [str,unicode]: appID = int(appID)
        for appType in self.entityDict:
            if type(self.entityDict[appType]) is dict:
                if self.entityDict[appType]['id'] == appID:
                    return self.entityDict[appType]['name']
            elif type(self.entityDict[appType]) is list:
                for application in self.entityDict[appType]:
                    if application['id'] == appID:
                        return application['name']
        if 'DEBUG' in locals(): sys.stderr.write("Application "+str(appID)+" is not loaded.\n")

    def getTiers_ID_List(self,appID):
        """
        Get a list of tier IDs for an application.
        :returns: a list with all tier IDs for an application. None if no tier was found.
        """
        if 'apmApplications' not in self.entityDict or self.entityDict['apmApplications'] is None: return None
        if type(appID) is str: appID = int(appID)
        if type(self.entityDict['apmApplications']) is dict and self.entityDict['apmApplications']['id'] == appID:
            if 'tiers' not in self.entityDict['apmApplications']:
                self.load_tiers_and_nodes(appID)
            return [ tier['id'] for tier in self.entityDict['apmApplications']['tiers'] ]
        elif type(self.entityDict['apmApplications']) is list:
            for apmApp in self.entityDict['apmApplications']:
                if apmApp['id'] == appID:
                    if 'tiers' not in apmApp:
                        self.load_tiers_and_nodes(appID)
                    return [ tier['id'] for tier in apmApp['tiers'] ]

    def getTierName(self,appID,tierID):
        """
        Get the name for a tier ID.
        :param appID: the ID of the application
        :param tierID: the ID of the tier
        :returns: the name of the specified tier ID. None if the tier was not found.
        """
        if 'apmApplications' not in self.entityDict or self.entityDict['apmApplications'] is None: return None
        if type(appID) is str: appID = int(appID)
        if type(self.entityDict['apmApplications']) is dict and self.entityDict['apmApplications']['id'] == appID:
            return [ tier['name'] for tier in apmApp['tiers'] if tier['id'] == tierID ][0]
        elif type(self.entityDict['apmApplications']) is list:
            for apmApp in self.entityDict['apmApplications']:
                if apmApp['id'] == appID:
                    for tier in apmApp['tiers']:
                        if tier['id'] == tierID:
                            return tier['name']
