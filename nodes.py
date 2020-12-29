#!/usr/bin/pythons
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from applications import ApplicationDict
from datetime import datetime, timedelta
import time


class NodeDict:
    nodeDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.nodeDict)

    ###
     # Update nodes availability with the last hour availability percentage
     # @source https://community.appdynamics.com/t5/Controller-SaaS-On-Premise/Export-app-and-machine-agent-status-by-Rest-Api/m-p/38378#M1983
     # @param app_ID the application ID number where to look for node availability
     # @return the number of updated nodes. Zero if no node was updated.
    ###
    def __update_availability_nodes(self,app_ID):
        updated = 0
        if str(app_ID) in self.nodeDict:
            nodeList = [ node['id'] for node in self.nodeDict[str(app_ID)] ]
            end_time   = datetime.today()-timedelta(minutes=5)
            start_time = end_time-timedelta(minutes=60)
            start_epoch= long(time.mktime(start_time.timetuple())*1000)
            end_epoch  = long(time.mktime(end_time.timetuple())*1000)
            response = RESTfulAPI().fetch_agent_status(nodeList=nodeList,start_epoch=start_epoch,end_epoch=end_epoch)
            if response is not None:
                nodesHealth = json.loads(response)
                for node in self.nodeDict[str(app_ID)]:
                    for i in range(0, len(nodeList), 1):
                        if nodesHealth['data'][i]['nodeId'] == node['id']:
                            percentage = nodesHealth['data'][i]['healthMetricStats']['appServerAgentAvailability']['percentage']
                            node.update({"availability": percentage})
                            #self.nodeDict[str(app_ID)] = node
                            updated = updated +1
                            continue
        return updated


    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from nodes data
     # @param appID_List list of application IDs, in order to obtain nodes from local nodes dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

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

        for appID in appID_List:
            if str(appID) not in self.nodeDict:
                if 'DEBUG' in locals(): print ("Application "+str(appID) +" is not loaded in dictionary.")
                continue
            for node in self.nodeDict[str(appID)]:
                # Check if data belongs to a node
                if 'nodeUniqueLocalId' not in node: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'Node': node['name'],
                                         'Tier': node['tierName'],
                                         'Application': ApplicationDict().getAppName(appID),
                                         'AgentVersion': node['appAgentVersion'] if node['agentType']=="APP_AGENT" else node['agentType'],
                                         'MachineName': node['machineName'],
                                         'OSType': node['machineOSType']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()

    ###
     # Generate JSON output from nodes data
     # @param appID_List list of application IDs, in order to obtain nodes from local nodes dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_nodes_JSON(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        nodes = []
        for appID in appID_List:
            nodes = nodes + self.nodeDict[str(appID)]

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
     # Load nodes from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @return the number of loaded nodes. Zero if no node was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            nodes = json.loads(streamdata)
        except TypeError as error:
            print ("load_nodes: "+str(error))
            return 0
        # Add loaded nodes to the nodes dictionary
        if type(nodes) is dict:
            self.nodeDict.update({str(appID):[nodes]})
        else:
            self.nodeDict.update({str(appID):nodes})
        return len(nodes)

    ###
     # Load node details for all nodes from an application
     # @param app_ID the ID number of the application nodes to fetch
     # @return the number of fetched nodes. Zero if no node was found.
    ###
    def load_details(self,app_ID):
        if str(app_ID) in self.nodeDict:
            index = 0
            for node in self.nodeDict[str(app_ID)]:
                streamdata = RESTfulAPI().fetch_node_details(app_ID,node['id'])
                if streamdata is None:
                    print ("load_node_details: Failed to retrieve node " + str(node['id']) + " for application " + str(app_ID) )
                    continue
                try:
                    nodeJSON = json.loads(streamdata)
                except TypeError as error:
                    print ("load_node_detail: "+str(error))
                    continue
                self.nodeDict[str(app_ID)][index] = nodeJSON
                index = index + 1
            return index
        else:
            print (self)
        return 0

    ###
     # Update node status for a list of applications.
     # @param appID_List list of application IDs to fetch nodes
     # @param selectors fetch only nodes filtered by specified selectors
     # @return the number of updated nodes. Zero if no node was found.
    ###
    def update(self,appID_List,selectors=None):
        DEBUG=True
        updated = 0
        for appID in appID_List:
            sys.stderr.write("update nodes " + str(appID) + "...\n")
            if str(appID) not in self.nodeDict:
                if self.load(RESTfulAPI().fetch_nodes(appID,selectors=selectors),appID) == 0: continue
            self.__update_availability_nodes(appID)
            unavailNodeList = [ node['id'] for node in self.nodeDict[str(appID)] if node['availability'] == 0.0 ]
            for i in range(0,len(unavailNodeList),25):
                if 'DEBUG' in locals(): print ("Unavailable node list:",unavailNodeList)
                response = RESTfulAPI().mark_nodes_as_historical(unavailNodeList[i:i+25])
            RESTfulAPI().fetch_nodes(appID,selectors=selectors)
            print ("update_nodes: [INFO] Disabled nodes in application",appID,":",len(unavailNodeList) )
            updated += len(unavailNodeList)
        return updated

    ###
     # Get the name for a tier ID. Fetch tiers data if not loaded yet.
     # @param appID the ID of the application
     # @param tierID the ID of the tier
     # @return the name of the specified tier ID.
    ###
    def getTierName(self,app_ID,tierID):
        if tierID <= 0: return 0
        if str(app_ID) in self.nodeDict:
            for node in self.nodeDict[str(app_ID)]:
                if node['tierId'] == tierID:
                    return node['tierName']
        return ""

    ###
     # Get the name for a node ID. Fetch nodes data if not loaded yet.
     # @param appID the ID of the application
     # @param nodeID the ID of the node
     # @return the name of the specified node ID.
    ###
    def getNodeName(self,app_ID,nodeID):
        if nodeID <= 0: return 0
        if str(app_ID) in self.nodeDict:
            for node in self.nodeDict[str(app_ID)]:
                if node['id'] == nodeID:
                    return node['name']
        return ""
