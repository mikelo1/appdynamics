#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI

class ApplicationDict:
    applicationDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.applicationDict)

    def __test_applications_with_tiers_and_nodes():
        applications=json.loads('[{"name":"evo-api-logalty-aks","description":"","id":15713322,"accountGuid":"edbe509e-bd4d-4ba9-a588-e761827a8730"},{"name":"ev-cajeros-web-srv","description":"","id":57502,"accountGuid":"edbe509e-bd4d-4ba9-a588-e761827a8730"}]')
        tiers=json.loads('[{"agentType":"APP_AGENT","name":"evo-api-logalty","description":"","id":16314693,"numberOfNodes":21,"type":"Application Server"}]')
        nodes=json.loads('[{"appAgentVersion":"ServerAgent#4.5.14.27768v4.5.14GAcompatiblewith4.4.1.0red42728e1ef0d74a209f248f56b5cdac8d2bdea0","machineAgentVersion":"","agentType":"APP_AGENT","type":"Other","machineName":"ebd06983f3c0","appAgentPresent":true,"nodeUniqueLocalId":"","machineId":6593822,"machineOSType":"Linux","tierId":16314693,"tierName":"evo-api-logalty","machineAgentPresent":false,"name":"evo-api-logalty--17","ipAddresses":{"ipAddresses":["10.98.32.86"]},"id":28214869},{"appAgentVersion":"ServerAgent#20.5.0.30113v20.5.0GAcompatiblewith4.4.1.0r474b6e3c8f55ababbb11a87ff265d8ce34eb0414release/20.5.0","machineAgentVersion":"","agentType":"APP_AGENT","type":"Other","machineName":"5c9c3b5b80a0","appAgentPresent":true,"nodeUniqueLocalId":"","machineId":6572599,"machineOSType":"Linux","tierId":16314693,"tierName":"evo-api-logalty","machineAgentPresent":false,"name":"evo-api-logalty--18","ipAddresses":{"ipAddresses":["10.98.32.138"]},"id":28214882}]')

        for application in applications:
            for tier in tiers:
                tier.update({'nodes':nodes})
            application.update({'tiers':tiers})
            app_ID = application['id']
            self.applicationDict.update({str(app_ID):application})


    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from applications data
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,fileName=None):
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

        for appID in self.applicationDict:
            application = self.applicationDict[appID]
            if 'header_is_printed' not in locals(): 
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

    ###
     # Generate JSON output from applications data
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,fileName=None):
        data = [self.applicationDict[appID] for appID in self.applicationDict]
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(data, outfile)
                outfile.close()
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(data)


    ###
     # Load applications from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @return the number of loaded applications. Zero if no application was loaded.
    ###
    def load(self,streamdata):
        try:
            applications = json.loads(streamdata)
        except TypeError as error:
            print ("load_application: "+str(error))
            return 0

        #print json.dumps(applications)
        for application in applications:
            # Add loaded application to the application dictionary
            if 'accountGuid' not in application: continue
            app_ID = application['id']
            self.applicationDict.update({str(app_ID):application})

        return len(applications)

    ###
     # Load tiers and nodes details for one specific application
     # @param app_ID the ID number of the application tiers and nodes to fetch
     # @return the number of tiers. Zero if no tier was found.
    ###
    def load_tiers_and_nodes(self,app_ID):
        if str(app_ID) in self.applicationDict:
            # Add tiers and nodes to the application data
            tiers = json.loads(RESTfulAPI().fetch_tiers(app_ID))
            if tiers is not None:
                for tier in tiers:
                    nodes = json.loads(RESTfulAPI().fetch_nodes(app_ID,tier['name']))
                    if nodes is not None:
                        tier.update({'nodes':nodes})
                self.applicationDict.update({str(appID):{'tiers':tiers}})
                return len(tiers)

    ###
     # Get a list with all application names.
     # @return a list with all application names. None if no application was found.
    ###
    def get_application_Name_list(self):
        if len(self.applicationDict) > 0:
            return [self.applicationDict[str(appID)]['name'] for appID in self.applicationDict]
        return None

    ###
     # Get a list with all application IDs.
     # @return a list with all application IDs. None if no application was found.
    ###
    def get_application_ID_list(self):
        if len(self.applicationDict) > 0:
            return [self.applicationDict[str(appID)]['id'] for appID in self.applicationDict]
        return None

    ###
     # Get the ID for an application name.
     # @param appName the name of the application
     # @return the ID of the specified application name. None if the application was not found.
    ###
    def getAppID(self,appName):
        searchList = [ self.applicationDict[str(application)]['id'] for application in self.applicationDict if self.applicationDict[application]['name'] == appName ]
        return searchList[0] if len(searchList) > 0 else None

    ###
     # Get the name for an application ID. Fetch applications data if not loaded yet.
     # @param appID the ID of the application
     # @return the name of the specified application ID. None if the application was not found.
    ###
    def getAppName(self,appID):
        if str(appID) in self.applicationDict:
            return self.applicationDict[str(appID)]['name']
        return None