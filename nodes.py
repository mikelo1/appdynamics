#!/usr/bin/pythons
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath, create_RESTful_JSON
from applications import getAppName
from datetime import datetime, timedelta
import time

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

    if response is None: return 0

    try:
        nodes = json.loads(response)
    except:
        print ("fetch_nodes: Could not process JSON content for application"+str(app_ID))
        return 0

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

###
 # Generate CSV output from nodes data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain nodes from local nodes dictionary
 # @param nodes data stream containing nodes
 # @param fileName output file name
 # @return None
###
def generate_nodes_CSV(appID_List=None,nodes=None,fileName=None):
    if appID_List is None and nodes is None:
        return
    elif nodes is None:
        nodes = []
        for appID in appID_List:
            nodes = nodes + nodeDict[str(appID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Node', 'Tier', 'AgentVersion', 'MachineName', 'OSType']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for node in nodes:
        if 'nodeUniqueLocalId' not in node: continue
        
        try:
            filewriter.writerow({'Node': node['name'],
                                 'Tier': node['tierName'],
                                 'AgentVersion': node['appAgentVersion'] if node['agentType']=="APP_AGENT" else node['agentType'],
                                 'MachineName': node['machineName'],
                                 'OSType': node['machineOSType']})
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            return (-1)
    if 'DEBUG' in locals(): print "generate_nodes_CSV: [INFO] Displayed number of nodes:" + str(len(nodes))
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from nodes data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain nodes from local nodes dictionary
 # @param nodes data stream containing nodes
 # @param fileName output file name
 # @return None
###
def generate_nodes_JSON(appID_List=None,nodes=None,fileName=None):
    if appID_List is None and nodes is None:
        return
    elif nodes is None:
        nodes = []
        for appID in appID_List:
            nodes = nodes + nodeDict[str(appID)]

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

###
 # Update nodes availability with the last hour availability percentage
 # @source https://community.appdynamics.com/t5/Controller-SaaS-On-Premise/Export-app-and-machine-agent-status-by-Rest-Api/m-p/38378#M1983
 # @param app_ID the application ID number where to look for node availability
 # @return the number of updated nodes. Zero if no node was updated.
###
def update_availability_nodes(app_ID):
    updated = 0
    if str(app_ID) in nodeDict:
        nodeList = []
        for node in nodeDict[str(app_ID)]: nodeList.append(node['id'])
        end_time   = datetime.today()-timedelta(minutes=5)
        start_time = end_time-timedelta(minutes=60)
        start_epoch= long(time.mktime(start_time.timetuple())*1000)
        end_epoch  = long(time.mktime(end_time.timetuple())*1000)
        # Retrieve app and machine agent status by Rest API
        # POST /controller/restui/v1/nodes/list/health/ids
        # BODY {"requestFilter":[<comma seperated list of node id's>],"resultColumns":["LAST_APP_SERVER_RESTART_TIME","VM_RUNTIME_VERSION","MACHINE_AGENT_STATUS","APP_AGENT_VERSION","APP_AGENT_STATUS","HEALTH"],"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[],"timeRangeStart":<start_time>,"timeRangeEnd":<end_time>}
        restfulPath= "/controller/restui/v1/nodes/list/health/ids"
        params     = {"requestFilter":nodeList,"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[],
                      "resultColumns":["APP_AGENT_STATUS","HEALTH"],
                      "timeRangeStart":start_epoch,"timeRangeEnd":end_epoch}
        response = create_RESTful_JSON(restfulPath,JSONdata=params)
        if response is not None:
            nodesHealth = json.loads(response)
            for node in nodeDict[str(app_ID)]:
                for i in range(0, len(nodeList), 1):
                    if nodesHealth['data'][i]['nodeId'] == node['id']:
                        percentage = nodesHealth['data'][i]['healthMetricStats']['appServerAgentAvailability']['percentage']
                        node.update({"availability": percentage})
                        #nodeDict[str(app_ID)] = node
                        updated = updated +1
                        continue
    return updated

###
 # Mark nodes as historical
 # @source https://docs.appdynamics.com/display/PRO45/Configuration+API#ConfigurationAPI-MarkNodesasHistorical
 # @param nodeList the list of node IDs to be maked as historical
 # @return the number of marked nodes. Zero if no node was marked.
###
def mark_nodes_as_historical(nodeList):
    DEBUG=1
    # Mark Nodes as Historical.Pass one or more identifiers of the node to be marked as historical, up to a maximum of 25 nodes.
    # POST /controller/rest/mark-nodes-historical?application-component-node-ids=value
    nodeList_str = ','.join(map(lambda x: str(x),nodeList))
    restfulPath= "/controller/rest/mark-nodes-historical?application-component-node-ids="+nodeList_str
    if 'DEBUG' in locals(): print "Unavailable node list:",nodeList
    response = create_RESTful_JSON(restfulPath,JSONdata="")
    if response is None:
        return 0
    else:
        return len(response.split("\n"))-2


###### FROM HERE PUBLIC FUNCTIONS ######

###
 # Display nodes from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_nodes_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        nodes = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON data.")
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_nodes_JSON(nodes=nodes,fileName=outFilename)
    else:
        generate_nodes_CSV(nodes=nodes,fileName=outFilename)

###
 # Display nodes for a list of applications.
 # @param appID_List list of application IDs to fetch nodes
 # @param selectors fetch only nodes filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched nodes. Zero if no node was found.
###
def get_nodes(appID_List,selectors=None,outputFormat=None):
    numNodes = 0
    for appID in appID_List:
        sys.stderr.write("get nodes " + getAppName(appID) + "...\n")
        numNodes = numNodes + fetch_nodes(appID,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_nodes_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_nodes_CSV(appID_List)
    return numNodes

###
 # Update node status for a list of applications.
 # @param appID_List list of application IDs to fetch nodes
 # @param selectors fetch only nodes filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of updated nodes. Zero if no node was found.
###
def update_nodes(appID_List,selectors=None,outputFormat=None):
    disabled = updated = 0
    for appID in appID_List:
        sys.stderr.write("update nodes " + getAppName(appID) + "...\n")
        if str(appID) not in nodeDict:
            if fetch_nodes(appID,selectors=selectors) == 0: continue
        unavailNodeList = []
        update_availability_nodes(appID)
        for node in nodeDict[str(appID)]:
            if node['availability'] == 0.0:
                unavailNodeList.append(node['id'])
                if len(unavailNodeList) == 25:
                    disabled = disabled + mark_nodes_as_historical(unavailNodeList)
                    unavailNodeList *= 0
        if len(unavailNodeList) > 0:
            disabled = disabled + mark_nodes_as_historical(unavailNodeList)
            unavailNodeList *= 0
        if 'DEBUG' in locals():
            print "update_nodes: [INFO] Disabled nodes in application",appID,":",disabled
            print "update_nodes: [INFO] Updated nodes in application",appID,":",updated
        fetch_nodes(appID,selectors=selectors)
    return disabled+updated

###
 # Get the name for a tier ID. Fetch tiers data if not loaded yet.
 # @param appID the ID of the application
 # @param tierID the ID of the tier
 # @return the name of the specified tier ID.
###
def getTierName(app_ID,tierID):
    if tierID <= 0: return 0
    if str(app_ID) not in nodeDict:
        if fetch_nodes(app_ID) == 0: return ""
    for node in nodeDict[str(app_ID)]:
        if node['tierId'] == tierID:
            return node['tierName']
    return ""

###
 # Get the name for a node ID. Fetch nodes data if not loaded yet.
 # @param appID the ID of the application
 # @param nodeID the ID of the node
 # @return the name of the specified node ID.
###
def getNodeName(app_ID,nodeID):
    if nodeID <= 0: return 0
    if str(app_ID) not in nodeDict:
        if fetch_nodes(app_ID) == 0: return ""
    for node in nodeDict[str(app_ID)]:
        if node['id'] == nodeID:
            return node['name']
    return ""