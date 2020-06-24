#!/usr/bin/python
import json
import csv
import sys
from appdconfig import get_current_context_serverURL, get_current_context_username
from appdRESTfulAPI import get_access_token, fetch_RESTful_JSON

applicationDict = dict()

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

###
 # Fetch applications from a controller then add it to the application dictionary. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param key name or ID number of the application to fetch
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the id of the fetched application. Zero if no application was found.
###
def fetch_application(serverURL,key,userName=None,password=None,token=None,includeNodes=False):
    if 'DEBUG' in locals(): print ("Fetching applications for controller " + serverURL + "...")
    # Retrieve a specific Business Application
    # GET /controller/rest/applications/application_name
    restfulPath = "/controller/rest/applications/" + str(key)
    if userName and password:
        application = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
    else:
        application = fetch_RESTful_JSON(restfulPath)

    if application is None:
        print "fetch_application: Failed to retrieve applications for controller " + serverURL
        return 0

    if includeNodes:
        # Add tiers and nodes to the application data
        tiers = fetch_tiers(serverURL,application['name'],userName,password,token)
        if tiers is not None:
            for tier in tiers:
                nodes = fetch_nodes(serverURL,applicationJSON['name'],tier['name'],userName,password,token)
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
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @param includeNodes flag to determine if nodes and tiers need to be loaded as well
 # @return the number of fetched applications. Zero if no application was found.
###
def fetch_applications(serverURL,userName=None,password=None,token=None,includeNodes=False):
    if 'DEBUG' in locals(): print ("Fetching applications for controller " + serverURL + "...")
    # Retrieve All Business Applications
    # GET /controller/rest/applications
    restfulPath = "/controller/rest/applications/"
    if userName and password:
        applications = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
    else:
        applications = fetch_RESTful_JSON(restfulPath)

    if applications is None:
        print "fetch_application: Failed to retrieve applications for controller " + serverURL
        return 0

    for application in applications:
        if includeNodes:
            # Add tiers and nodes to the application data
            tiers = fetch_tiers(serverURL,application['name'],userName,password,token)
            if tiers is not None:
                for tier in tiers:
                    nodes = fetch_nodes(serverURL,application['name'],tier['name'],userName,password,token)
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

def fetch_tiers(serverURL,appName,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching tiers for application " + appName + "...")
    # Retrieve All Tiers in a Business Application
    # GET /controller/rest/applications/application_name/tiers
    restfulPath = "/controller/rest/applications/" + appName + "/tiers"
    if userName and password:
        tiers = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
    else:
        tiers = fetch_RESTful_JSON(restfulPath)

    if tiers is None:
        print "fetch_tiers: Failed to retrieve the tiers for application " + appName + "."
        return None
    return tiers

def fetch_nodes(serverURL,appName,tierName,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching nodes for tier " + tierName + ", application " + appName)
    # Retrieve Node Information for All Nodes in a Tier
    # GET /controller/rest/applications/application_name/tiers/tier_name/nodes
    restfulPath = "/controller/rest/applications/" + appName + "/tiers/" + tierName + "/nodes"
    if userName and password:
        nodes = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
    else:
        nodes = fetch_RESTful_JSON(restfulPath)

    if nodes is None:
        print "fetch_tiers: Failed to retrieve the nodes for tier " + tierName + " in application " + appName + "."
        return None
    return nodes

def load_applications_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    applications = json.load(json_file)
    return applications

def generate_applications_CSV(fileName=None):
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

    for appID in applicationDict:
        application = applicationDict[appID]
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

def get_applications(serverURL,appList=None,userName=None,password=None,token=None,includeNodes=False):
    if userName and password:
        if fetch_applications(serverURL,userName=userName,password=password,includeNodes=includeNodes) > 0:
            generate_applications_CSV()
    elif token:
        if fetch_applications(serverURL,token=token,includeNodes=includeNodes) > 0:
            generate_applications_CSV()

def load_applications(serverURL,userName=None,password=None,token=None,includeNodes=False):
#    applicationDict.clear()
    if userName and password:
        val = fetch_applications(serverURL,userName=userName,password=password)
    elif token:
        val = fetch_applications(serverURL,token=token)
    else:
        print "load_applications: Incorrect parameters."
        return 0
    if 'DEBUG' in locals(): print "Loaded applications: "+str(val)
    return val

def get_application_list():
    if len(applicationDict) == 0:
        # Request for applications data
        server = get_current_context_serverURL()
        username = get_current_context_username()
        token=get_access_token(server,username)
        if token is None: return -1
        if fetch_applications(server,token=token) == 0: return -1
    appList = []
    for appID in applicationDict:
        appList.append(applicationDict[appID]['name'])
    return appList

def getID(appName):
    for appID in applicationDict:
        if applicationDict[appID]['name'] == appName:
            return applicationDict[appID]['id']
    # Request for provided application, although is not in the loaded application list
    server = get_current_context_serverURL()
    username = get_current_context_username()
    token=get_access_token(server,username)
    if token is None: return -1
    return fetch_application(server,appName,token=token)

def getName(appID):
    if appID in applicationDict:
        return applicationDict[appID]['name']
    # Request for provided application, although is not in the loaded application list
    server = get_current_context_serverURL()
    username = get_current_context_username()
    token=get_access_token(server,username)
    if token is None: return -1
    return fetch_application(server,appID,token=token)

def getNodeName(nodeID):
    # TODO: search in data for node and return name
    return str(nodeID)

def getTierName(tierID):
    # TODO: search in data for tier and return name
    return str(tierID)
