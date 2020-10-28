#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath

applicationDict = dict()

###
 # Fetch application from a controller then add it to the application dictionary. Provide either an username/password or an access token.
 # @param key name or ID number of the application to fetch
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the id of the fetched application. Zero if no application was found.
###
def fetch_application(key,serverURL=None,userName=None,password=None,token=None,includeNodes=False):
    if 'DEBUG' in locals(): print ("Fetching application "+str(key)+"...")
    # Retrieve a specific Business Application
    # GET /controller/rest/applications/application_name
    restfulPath = "/controller/rest/applications/" + str(key)
    params = {"output": "JSON"}

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    if response is None: return None

    try:
        application = json.loads(response)
    except:
        print "fetch_application: Could not process JSON content."
        return None

    if includeNodes:
        # Add tiers and nodes to the application data
        tiers = fetch_tiers(application['name'],serverURL,userName,password,token)
        if tiers is not None:
            for tier in tiers:
                nodes = fetch_nodes(applicationJSON['name'],tier['name'],serverURL,userName,password,token)
                if nodes is None: continue
                tier.append(nodes)
            application.append(tiers)

    # Add loaded application to the application dictionary
    app_ID = application[0]['id']
    applicationDict.update({str(app_ID):application[0]})
 
    if 'DEBUG' in locals():
        print "Loaded application:" + str(application)

    return app_ID

###
 # Fetch applications from a controller, then add them to the application dictionary. Provide either an username/password or an access token.
 # @param selectors fetch only applications filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @param includeNodes flag to determine if nodes and tiers need to be loaded as well
 # @return the number of fetched applications. Zero if no application was found.
###
def fetch_applications(selectors=None,serverURL=None,userName=None,password=None,token=None,includeNodes=False):
    if 'DEBUG' in locals(): print ("Fetching applications for controller " + serverURL + "...")
    # Retrieve All Business Applications
    # GET /controller/rest/applications
    restfulPath = "/controller/rest/applications/"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    if response is None: return None
    
    try:
        applications = json.loads(response)
    except:
        print ("fetch_application: Could not process JSON content.")
        return None

    for application in applications:
        if includeNodes:
            # Add tiers and nodes to the application data
            tiers = fetch_tiers(application['name'],serverURL,userName,password,token)
            if tiers is not None:
                for tier in tiers:
                    nodes = fetch_nodes(application['name'],tier['name'],serverURL,userName,password,token)
                    if nodes is None: continue
                    tier.update({'nodes':nodes})
                application.update({'tiers':tiers})
        # Add loaded application to the application dictionary
        app_ID = application['id']
        applicationDict.update({str(app_ID):application})

    if 'DEBUG' in locals():
        print "Loaded applications:" + str(len(applicationDict))
        for appID in applicationDict:
            print str(applicationDict[appID])

    return len(applications)

###
 # Fetch tiers for an application. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @param includeNodes flag to determine if nodes and tiers need to be loaded as well
 # @return the number of fetched tiers. Zero if no tier was found.
###
def fetch_tiers(appName,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching tiers for application " + appName + "...")
    # Retrieve All Tiers in a Business Application
    # GET /controller/rest/applications/application_name/tiers
    restfulPath = "/controller/rest/applications/" + appName + "/tiers"
    if serverURL and userName and password:
        tiers = fetch_RESTful_JSON(restfulPath,serverURL=serverURL,userName=userName,password=password)
    else:
        tiers = fetch_RESTful_JSON(restfulPath)

    if tiers is None:
        print "fetch_tiers: Failed to retrieve the tiers for application " + appName + "."
        return None
    return tiers

###
 # Fetch nodes for an application. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched nodes. Zero if no node was found.
###
def fetch_nodes(appName,tierName,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching nodes for tier " + tierName + ", application " + appName)
    # Retrieve Node Information for All Nodes in a Tier
    # GET /controller/rest/applications/application_name/tiers/tier_name/nodes
    restfulPath = "/controller/rest/applications/" + appName + "/tiers/" + tierName + "/nodes"
    if serverURL and userName and password:
        nodes = fetch_RESTful_JSON(restfulPath,serverURL=serverURL,userName=userName,password=password)
    else:
        nodes = fetch_RESTful_JSON(restfulPath)

    if nodes is None:
        print "fetch_tiers: Failed to retrieve the nodes for tier " + tierName + " in application " + appName + "."
        return None
    return nodes

###
 # Generate CSV output from applications data, either from the local dictionary or from streamed data
 # @param appDict dictionary of applications, containing application data
 # @param fileName output file name
 # @return None
###
def generate_applications_CSV(appDict=None,fileName=None):
    if appDict is None and len(applicationDict) == 0:
        print "generate_applications_CSV: Applications not loaded."
        return
    elif appDict is None:
        appDict = applicationDict

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
    filewriter.writeheader()

    for appID in appDict:
        application = appDict[appID]
        Tiers_str = ""
        Nodes_str = ""
        if 'tiers' in application:
            for tier in application['tiers']:
                Tiers_str = Tiers_str + tier['name'] + " "
                for node in tier['nodes']:
                    Nodes_str = Nodes_str + node['name'] + " "
        try:        
            filewriter.writerow({'Name': application['name'],
                                'Description': application['description'],
                                'Id': application['id'],
                                'AccountGuid': application['accountGuid'],
                                'Tiers': Tiers_str,
                                'Nodes': Nodes_str})
        except:
            print ("Could not write application "+application['name']+" to the output.")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from applications data, either from the local dictionary or from streamed data
 # @param appDict dictionary of applications, containing application data
 # @param fileName output file name
 # @return None
###
def generate_applications_JSON(appDict=None,fileName=None):
    if appDict is None and len(applicationDict) == 0:
        print "generate_applications_CSV: Applications not loaded."
        return
    elif appDict is None:
        appDict = applicationDict

    data = []
    for appID in appDict:
        data.append(appDict[appID])

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

def test_applications_with_tiers_and_nodes():
    applications=json.loads('[{"name":"evo-api-logalty-aks","description":"","id":15713322,"accountGuid":"edbe509e-bd4d-4ba9-a588-e761827a8730"},{"name":"ev-cajeros-web-srv","description":"","id":57502,"accountGuid":"edbe509e-bd4d-4ba9-a588-e761827a8730"}]')
    tiers=json.loads('[{"agentType":"APP_AGENT","name":"evo-api-logalty","description":"","id":16314693,"numberOfNodes":21,"type":"Application Server"}]')
    nodes=json.loads('[{"appAgentVersion":"ServerAgent#4.5.14.27768v4.5.14GAcompatiblewith4.4.1.0red42728e1ef0d74a209f248f56b5cdac8d2bdea0","machineAgentVersion":"","agentType":"APP_AGENT","type":"Other","machineName":"ebd06983f3c0","appAgentPresent":true,"nodeUniqueLocalId":"","machineId":6593822,"machineOSType":"Linux","tierId":16314693,"tierName":"evo-api-logalty","machineAgentPresent":false,"name":"evo-api-logalty--17","ipAddresses":{"ipAddresses":["10.98.32.86"]},"id":28214869},{"appAgentVersion":"ServerAgent#20.5.0.30113v20.5.0GAcompatiblewith4.4.1.0r474b6e3c8f55ababbb11a87ff265d8ce34eb0414release/20.5.0","machineAgentVersion":"","agentType":"APP_AGENT","type":"Other","machineName":"5c9c3b5b80a0","appAgentPresent":true,"nodeUniqueLocalId":"","machineId":6572599,"machineOSType":"Linux","tierId":16314693,"tierName":"evo-api-logalty","machineAgentPresent":false,"name":"evo-api-logalty--18","ipAddresses":{"ipAddresses":["10.98.32.138"]},"id":28214882}]')

    for application in applications:
        for tier in tiers:
            tier.update({'nodes':nodes})
        application.update({'tiers':tiers})
        app_ID = application['id']
        applicationDict.update({str(app_ID):application})


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display applications from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_applications_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        applications = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_applications_from_stream: Could not process JSON data.")
        return 0

    appDict = dict()
    for application in applications:
        # Add loaded application to the application dictionary
        if 'accountGuid' not in application: continue
        app_ID = application['id']
        appDict.update({str(app_ID):application})
    if outputFormat and outputFormat == "JSON":
        generate_applications_JSON(appDict=appDict)
    else:
        generate_applications_CSV(appDict=appDict)

###
 # Display all applications from a controller.
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param includeNodes flag to determine if nodes and tiers need to be loaded as well
 # @return the number of fetched applications. Zero if no application was found.
###
def get_applications(outputFormat=None,includeNodes=False):
    sys.stderr.write("get applications...\n")
    numApplications = fetch_applications(includeNodes=includeNodes)
    if numApplications == 0:
        print "get_applications: Failed to retrieve policies for application " + str(app_ID)
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_applications_JSON()
    elif not outputFormat or outputFormat == "CSV":
        generate_applications_CSV()
    return numApplications

###
 # Get a list with all application names. Fetch applications data if not loaded yet.
 # @return a list with all application names.
###
def get_application_Name_list():
    if len(applicationDict) == 0:
        # Request for applications data
        if fetch_applications() == 0: return -1
    appList = []
    for appID in applicationDict:
        appList.append(applicationDict[str(appID)]['name'])
    return appList

###
 # Get a list with all application IDs. Fetch applications data if not loaded yet.
 # @return a list with all application IDs.
###
def get_application_ID_list():
    if len(applicationDict) == 0:
        # Request for applications data
        if fetch_applications() == 0: return -1
    appList = []
    for appID in applicationDict:
        appList.append(applicationDict[str(appID)]['id'])
    return appList

###
 # Get the ID for an application name. Fetch applications data if not loaded yet.
 # @param appName the name of the application
 # @return the ID of the specified application name.
###
def getAppID(appName):
    for appID in applicationDict:
        if applicationDict[appID]['name'] == appName:
            return applicationDict[str(appID)]['id']
    # Request for provided application, although is not in the loaded application list
    return fetch_application(appName)

###
 # Get the name for an application ID. Fetch applications data if not loaded yet.
 # @param appID the ID of the application
 # @return the name of the specified application ID.
###
def getAppName(appID):
    if appID is None or appID <= 0: return 0
    if str(appID) in applicationDict:
        return applicationDict[str(appID)]['name']
    # Request for provided application, although is not in the loaded application list
    if fetch_application(appID) is not None:
        return applicationDict[str(appID)]['name']
    else:
        return ""