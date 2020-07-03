#!/usr/bin/pythons
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath

nodeDict = dict()

###
 # Fetch application nodes from a controller then add them to the nodes dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the nodes to fetch
 # @param selectors fetch only nodes filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched nodes. Zero if no node was found.
###
def fetch_nodes(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching nodes for App " + str(app_ID) + "...")
    # Retrieve Node Information for All Nodes in a Business Application
    # GET /controller/rest/applications/application_name/nodes
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/nodes"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        nodes = json.loads(response)
    except JSONDecodeError:
        print ("fetch_nodes: Could not process JSON content.")
        return None

    if loadData:
        index = 0
        for node in nodes:
            if 'DEBUG' in locals(): print ("Fetching node " + node['name'] + "...")
            # Retrieve Node Information by Node Name
            # GET /controller/rest/applications/application_name/nodes/node_name
            restfulPath = "/controller/rest/applications/" + str(app_ID) + "/nodes/" + str(node['id'])
            if userName and password:
                nodeJSON = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
            else:
                nodeJSON = fetch_RESTful_JSON(restfulPath)
            if nodeJSON is None:
                "fetch_nodes: Failed to retrieve node " + str(node['id']) + " for application " + str(app_ID)
                continue
            nodes[index] = nodeJSON
            index = index + 1

    # Add loaded nodes to the node dictionary
    nodeDict.update({str(app_ID):nodes})

    if 'DEBUG' in locals():
        print "fetch_nodes: Loaded " + str(len(nodes)) + " nodes."
        for appID in nodeDict:
            print str(nodeDict[appID])

    return len(nodes)

def generate_nodes_CSV(app_ID,nodes=None,fileName=None):
    if nodes is None and str(app_ID) not in nodeDict:
        print "Nodes for application "+str(app_ID)+" not loaded."
        return
    elif nodes is None and str(app_ID) in nodeDict:
        nodes = nodeDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Node', 'Tier', 'Application', 'AgentVersion', 'MachineName', 'OSType']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for node in nodes:
        if 'nodeUniqueLocalId' not in node: continue
        
        try:
            filewriter.writerow({'Node': node['name'],
                                 'Tier': node['tierName'],
                                 'Application': app_ID,
                                 'AgentVersion': node['appAgentVersion'] if node['agentType']=="APP_AGENT" else node['agentType'],
                                 'MachineName': node['machineName'],
                                 'OSType': node['machineOSType']})
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            return (-1)
    if 'DEBUG' in locals(): print "generate_nodes_CSV: [INFO] Displayed number of nodes:" + str(len(nodes))
    if fileName is not None: csvfile.close()

def generate_nodes_JSON(app_ID,nodes=None,fileName=None):
    if nodes is None and str(app_ID) not in nodeDict:
        print "Nodes for application "+str(app_ID)+" not loaded."
        return
    elif nodes is None and str(app_ID) in nodeDict:
        nodes = nodeDict[str(app_ID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(nodes, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(nodes)


###### FROM HERE PUBLIC FUNCTIONS ######


def get_nodes_from_stream(streamdata,outputFormat=None,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        nodes = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_nodes_JSON(app_ID=0,nodes=nodes,fileName=outFilename)
    else:
        generate_nodes_CSV(app_ID=0,nodes=nodes,fileName=outFilename)

def get_nodes(app_ID,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and userName and password:
        if fetch_nodes(app_ID,selectors=selectors,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_allothertraffic: Failed to retrieve nodes for application " + str(app_ID)
            return None
    else:
        if fetch_nodes(app_ID,selectors=selectors,token=token) == 0:
            print "get_allothertraffic: Failed to retrieve nodes for application " + str(app_ID)
            return None
    if outputFormat and outputFormat == "JSON":
        generate_nodes_JSON(app_ID)
    else:
        generate_nodes_CSV(app_ID)