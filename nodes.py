#!/usr/bin/pythons
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath, create_RESTful_JSON
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
    DEBUG=True
    # Mark Nodes as Historical.Pass one or more identifiers of the node to be marked as historical, up to a maximum of 25 nodes.
    # POST /controller/rest/mark-nodes-historical?application-component-node-ids=value
    nodeList_str = ','.join(map(lambda x: str(x),nodeList))
    restfulPath= "/controller/rest/mark-nodes-historical?application-component-node-ids="+nodeList_str
    if 'DEBUG' in locals(): print "Unavailable node list:",nodeList
    response = create_RESTful_JSON(restfulPath,JSONdata="")
    return len(response.split("\n"))-2


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
        number = fetch_nodes(app_ID,selectors=selectors,serverURL=serverURL,userName=userName,password=password)
        if number == 0:
            print "get_nodes: Failed to retrieve nodes for application " + str(app_ID)
            return None
    else:
        number = fetch_nodes(app_ID,selectors=selectors,token=token)
        if number == 0:
            print "get_nodes: Failed to retrieve nodes for application " + str(app_ID)
            return None
    if 'DEBUG' in locals(): print "get_nodes: [INFO] Loaded",number,"nodes"
    if outputFormat and outputFormat == "JSON":
        generate_nodes_JSON(app_ID)
    elif not outputFormat or outputFormat == "CSV":
        generate_nodes_CSV(app_ID)
    return number

def update_nodes(app_ID,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if str(app_ID) not in nodeDict:
        if get_nodes(app_ID,outputFormat="none") is None: return

    disabled = updated = 0
    unavailNodeList = []
    update_availability_nodes(app_ID)
    for node in nodeDict[str(app_ID)]:
        if node['availability'] == 0.0:
            unavailNodeList.append(nodesHealth['data'][i]['nodeId'])
            if len(unavailNodeList) == 25:
                disabled = disabled + mark_nodes_as_historical(unavailNodeList)
                unavailNodeList *= 0
    if len(unavailNodeList) > 0:
        disabled = disabled + mark_nodes_as_historical(unavailNodeList)
        unavailNodeList *= 0
    if 'DEBUG' in locals():
        print "update_nodes: [INFO] Disabled nodes in application",app_ID,":",disabled
        print "update_nodes: [INFO] Updated nodes in application",app_ID,":",updated
    get_nodes(app_ID,outputFormat="none")
    return disabled+updated