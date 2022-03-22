import json
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
        self.CSVfields = {  'Node':         self.__str_node_name,
                            'Tier':         self.__str_node_tierName,
                            'AgentVersion': self.__str_node_agentVersion,
                            'MachineName':  self.__str_node_machineName,
                            'OSType':       self.__str_node_machineOSType }


    def __str_node_name(self,node):
        return node['name'] if sys.version_info[0] >= 3 else node['name'].encode('ASCII', 'ignore')

    def __str_node_tierName(self,node):
        return node['tierName'] if sys.version_info[0] >= 3 else node['tierName'].encode('ASCII', 'ignore')

    def __str_node_agentVersion(self,node):
        return node['appAgentVersion'] if node['agentType']=="APP_AGENT" else node['agentType']

    def __str_node_machineName(self,node):
        return node['machineName']

    def __str_node_machineOSType(self,node):
        return node['machineOSType']

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
                if self.fetch(appID=appID,selectors=selectors) == 0: continue
            self.__update_availability_nodes(appID)
            unavailNodeList = [ node['id'] for node in self.entityDict[str(appID)] if node['availability'] == 0.0 ]
            for i in range(0,len(unavailNodeList),25):
                if 'DEBUG' in locals(): sys.stdout.write("drain_nodes: [INFO] Unavailable node list: "+str(unavailNodeList)+"\n")
                response = self.controller.RESTfulAPI.mark_nodes_as_historical(unavailNodeList[i:i+25])
            self.fetch(appID=appID,selectors=selectors)
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


class TierDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_tiers,
                                    'fetchByID': self.controller.RESTfulAPI.fetch_tier_nodes }
        self.entityKeywords = ['numberOfNodes','agentType']
        self.CSVfields = {  'Tier':            self.__str_tier_name,
                            'Type':            self.__str_tier_type,
                            'Number of nodes': self.__str_tier_number_of_nodes }

    def __str_tier_name(self,tier):
        return tier['name']

    def __str_tier_type(self,tier):
        return tier['type']

    def __str_tier_number_of_nodes(self,tier):
        return tier['numberOfNodes']

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def fetch(self,appID,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        if self.controller.applications.hasTiers(appID):
            data = self.entityAPIFunctions['fetch'](app_ID=appID,selectors=selectors)
            return self.load(streamdata=data,appID=appID)
        return 0

    def getTiers_ID_List(self,appID):
        """
        Get a list of tier IDs for an application.
        :returns: a list with all tier IDs for an application. None if no tier was found.
        """
        if type(appID) is int: appID = str(appID)
        if appID not in self.entityDict:
            self.fetch(appID=appID)
        return [ tier['id'] for tier in self.entityDict[appID] ]

    def getTierName(self,tierID,appID=None):
        """
        Get the name for a tier ID.
        :param appID: the ID of the application
        :param tierID: the ID of the tier
        :returns: the name of the specified tier ID. Empty string if the tier was not found.
        """
        if appID and appID not in self.entityDict:
            self.fetch(appID=appID)
        keys = self.entityDict.keys() if not appID else [str(appID)]
        for key in keys:
            for tier in self.entityDict[key]:
                if tier['id'] == tierID:
                    return tier['name']
        return None