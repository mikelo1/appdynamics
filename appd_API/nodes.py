import json
import csv
import sys
from datetime import datetime, timedelta
import time
from .entities import AppEntity

class NodeDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_nodes,
                                    'fetchByID': self.controller.RESTfulAPI.fetch_node_by_ID }
        self.entityKeywords = ["nodeUniqueLocalId"]


    def __update_availability_nodes(self,app_ID):
        """
        Update nodes availability with the last hour availability percentage
        https://community.appdynamics.com/t5/Controller-SaaS-On-Premise/Export-app-and-machine-agent-status-by-Rest-Api/m-p/38378#M1983
        :param app_ID: the application ID number where to look for node availability
        :returns: the number of updated nodes. Zero if no node was updated.
        """
        updated = 0
        if str(app_ID) in self.entityDict:
            nodeList = [ node['id'] for node in self.entityDict[str(app_ID)] ]
            end_time   = datetime.today()-timedelta(minutes=5)
            start_time = end_time-timedelta(minutes=60)
            start_epoch= int(time.mktime(start_time.timetuple())*1000)
            end_epoch  = int(time.mktime(end_time.timetuple())*1000)
            response = self.controller.RESTfulAPI.fetch_agent_status(nodeList=nodeList,start_epoch=start_epoch,end_epoch=end_epoch)
            if response is not None:
                nodesHealth = json.loads(response)
                for node in self.entityDict[str(app_ID)]:
                    for i in range(0, len(nodeList), 1):
                        if nodesHealth['data'][i]['nodeId'] == node['id']:
                            percentage = nodesHealth['data'][i]['healthMetricStats']['appServerAgentAvailability']['percentage']
                            node.update({"availability": percentage})
                            #self.entityDict[str(app_ID)] = node
                            updated = updated +1
                            continue
        return updated


    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from nodes data
        :param appID_List: list of application IDs, in order to obtain nodes from local nodes dictionary
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

        fieldnames = ['Node', 'Tier', 'Application', 'AgentVersion', 'MachineName', 'OSType']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print ("Application "+appID +" is not loaded in dictionary.")
                continue
            for node in self.entityDict[appID]:
                if  'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'Node': node['name'],
                                         'Tier': node['tierName'],
                                         'Application': self.controller.applications.getAppName(appID),
                                         'AgentVersion': node['appAgentVersion'] if node['agentType']=="APP_AGENT" else node['agentType'],
                                         'MachineName': node['machineName'],
                                         'OSType': node['machineOSType']})
                except ValueError as valError:
                    sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()

    def drain(self,appID_List,selectors=None):
        """
        Update node status and if the availability equals to zero -during the last hour-, mark them as historical.
        :param appID_List: list of application IDs to update node status
        :param selectors: fetch only nodes filtered by specified selectors
        :returns: the number of nodes marked as historical. Zero if no unavailable node was found.
        """
        DEBUG=True
        updated = 0
        for appID in appID_List:
            sys.stderr.write("drain_nodes: [INFO] update nodes status for application "+self.controller.applications.getAppName(appID)+"...\n")
            if str(appID) not in self.entityDict:
                if self.load(self.controller.RESTfulAPI.fetch_nodes(appID,selectors=selectors),appID) == 0: continue
            self.__update_availability_nodes(appID)
            unavailNodeList = [ node['id'] for node in self.entityDict[str(appID)] if node['availability'] == 0.0 ]
            for i in range(0,len(unavailNodeList),25):
                if 'DEBUG' in locals(): sys.stdout.write("drain_nodes: [INFO] Unavailable node list: "+str(unavailNodeList)+"\n")
                response = self.controller.RESTfulAPI.mark_nodes_as_historical(unavailNodeList[i:i+25])
            self.controller.RESTfulAPI.fetch_nodes(appID,selectors=selectors)
            if 'DEBUG' in locals(): sys.stdout.write("drain_nodes: [INFO] Nodes marked as historical in application "+ \
                                                    self.controller.applications.getAppName(appID)+": "+str(len(unavailNodeList))+"\n")
            updated += len(unavailNodeList)
        return updated


    def getTierName(self,app_ID,tierID):
        """
        Get the name for a tier ID. Fetch tiers data if not loaded yet.
        :param appID: the ID of the application
        :param tierID: the ID of the tier
        :returns: the name of the specified tier ID.
        """
        if tierID <= 0: return 0
        if str(app_ID) in self.entityDict:
            for node in self.entityDict[str(app_ID)]:
                if node['tierId'] == tierID:
                    return node['tierName']
        return ""


    def getNodeName(self,app_ID,nodeID):
        """
        Get the name for a node ID. Fetch nodes data if not loaded yet.
        :param appID: the ID of the application
        :param nodeID: the ID of the node
        :returns: the name of the specified node ID.
        """
        if nodeID <= 0: return 0
        if str(app_ID) in self.entityDict:
            for node in self.entityDict[str(app_ID)]:
                if node['id'] == nodeID:
                    return node['name']
        return ""
