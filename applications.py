#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from entities import ControllerEntity

class ApplicationDict(ControllerEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_applications}

    def __init__(self):
        self.entityDict = dict()

    def __test_applications_with_tiers_and_nodes():
        applications=json.loads('[{"name":"evo-api-logalty-aks","description":"","id":15713322,"accountGuid":"edbe509e-bd4d-4ba9-a588-e761827a8730"},{"name":"ev-cajeros-web-srv","description":"","id":57502,"accountGuid":"edbe509e-bd4d-4ba9-a588-e761827a8730"}]')
        tiers=json.loads('[{"agentType":"APP_AGENT","name":"evo-api-logalty","description":"","id":16314693,"numberOfNodes":21,"type":"Application Server"}]')
        nodes=json.loads('[{"appAgentVersion":"ServerAgent#4.5.14.27768v4.5.14GAcompatiblewith4.4.1.0red42728e1ef0d74a209f248f56b5cdac8d2bdea0","machineAgentVersion":"","agentType":"APP_AGENT","type":"Other","machineName":"ebd06983f3c0","appAgentPresent":true,"nodeUniqueLocalId":"","machineId":6593822,"machineOSType":"Linux","tierId":16314693,"tierName":"evo-api-logalty","machineAgentPresent":false,"name":"evo-api-logalty--17","ipAddresses":{"ipAddresses":["10.98.32.86"]},"id":28214869},{"appAgentVersion":"ServerAgent#20.5.0.30113v20.5.0GAcompatiblewith4.4.1.0r474b6e3c8f55ababbb11a87ff265d8ce34eb0414release/20.5.0","machineAgentVersion":"","agentType":"APP_AGENT","type":"Other","machineName":"5c9c3b5b80a0","appAgentPresent":true,"nodeUniqueLocalId":"","machineId":6572599,"machineOSType":"Linux","tierId":16314693,"tierName":"evo-api-logalty","machineAgentPresent":false,"name":"evo-api-logalty--18","ipAddresses":{"ipAddresses":["10.98.32.138"]},"id":28214882}]')

        for application in applications:
            for tier in tiers:
                tier.update({'nodes':nodes})
            application.update({'tiers':tiers})
            app_ID = application['id']
            self.entityDict.update({str(app_ID):application})


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

        fieldnames = ['Name', 'Description', 'Id', 'AccountGuid', 'Tiers', 'Nodes']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            application = self.entityDict[appID]
            # Check if data belongs to an application
            if 'accountGuid' not in application: continue
            elif 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True
            tierList = [tier['name'] for tier in application['tiers']] if 'tiers' in application else []
            nodeList = [node['name'] for tier in application['tiers'] for node in tier['nodes']] if 'tiers' in application else []

            try:
                filewriter.writerow({'Name': application['name'],
                                    'Description': application['description'],
                                    'Id': application['id'],
                                    'AccountGuid': application['accountGuid'],
                                    'Tiers': ','.join(map(lambda x: str(x.text),tierList)),
                                    'Nodes': ','.join(map(lambda x: str(x.text),nodeList)) })
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                exit(1)
        if fileName is not None: csvfile.close()


    def load_tiers_and_nodes(self,app_ID):
        """
        Load tiers and nodes details for one specific application
        :param app_ID: the ID number of the application tiers and nodes to fetch
        :returns: the number of tiers. Zero if no tier was found.
        """
        if str(app_ID) in self.entityDict:
            # Add tiers and nodes to the application data
            tiers = json.loads(RESTfulAPI().fetch_tiers(app_ID))
            if tiers is not None:
                for tier in tiers:
                    nodes = json.loads(RESTfulAPI().fetch_tier_nodes(app_ID,tier['name']))
                    if nodes is not None:
                        tier.update({'nodes':nodes})
                self.entityDict.update({str(app_ID):{'tiers':tiers}})
                return len(tiers)


    def get_application_Name_list(self):
        """
        Get a list with all application names.
        :returns: a list with all application names. None if no application was found.
        """
        if len(self.entityDict) > 0:
            return [self.entityDict[str(appID)]['name'] for appID in self.entityDict]
        return None


    def get_application_ID_list(self):
        """
        Get a list with all application IDs.
        :returns: a list with all application IDs. None if no application was found.
        """
        if len(self.entityDict) > 0:
            return [self.entityDict[str(appID)]['id'] for appID in self.entityDict]
        return None


    def getAppID(self,appName):
        """
        Get the ID for an application name.
        :param appName: the name of the application
        :returns: the ID of the specified application name. None if the application was not found.
        """
        searchList = [ self.entityDict[str(application)]['id'] for application in self.entityDict if self.entityDict[application]['name'] == appName ]
        return searchList[0] if len(searchList) > 0 else None


    def getAppName(self,appID):
        """
        Get the name for an application ID.
        :param appID: the ID of the application
        :returns: the name of the specified application ID. None if the application was not found.
        """
        if str(appID) in self.entityDict:
            return self.entityDict[str(appID)]['name']
        if 'DEBUG' in locals(): sys.stderr.write("Application "+str(appID)+" is not loaded.\n")
        return None


    def getTiers_ID_List(self,appID):
        """
        Get a list of tier IDs for an application.
        :returns: a list with all tier IDs for an application. None if no tier was found.
        """
        if len(self.entityDict) > 0:
            return [ tier['id'] for tier in self.entityDict[str(appID)]['tiers'] ]
        return None

    def getTierName(self,appID,tierID):
        """
        Get the name for a tier ID.
        :param appID: the ID of the application
        :param tierID: the ID of the tier
        :returns: the name of the specified tier ID. None if the tier was not found.
        """
        if len(self.entityDict) > 0 and str(appID) in self.entityDict and 'tiers' in self.entityDict[str(appID)]:
            for tier in self.entityDict[str(appID)]['tiers']:
                if tier['id'] == tierID:
                    return tier['name']
        return None