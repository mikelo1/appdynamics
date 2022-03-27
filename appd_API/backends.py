import json
import sys
from .entities import AppEntity

class BackendDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        #self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_backends }
        self.entityKeywords = ["exitPointType"]
        self.CSVfields = {  'name':          self.__str_backend_name,
                            'exitPointType': self.__str_backend_exitPointType }

    def __str_backend_name(self,backend):
        return backend['name'] if sys.version_info[0] >= 3 else backend['name'].encode('ASCII', 'ignore')

    def __str_backend_exitPointType(self,backend):
        return backend['exitPointType']


    ###### FROM HERE PUBLIC FUNCTIONS ######



class EntrypointDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        #self.entityAPIFunctions = {'fetchByID': self.controller.RESTfulAPI.fetch_entrypoints_TierRules}
        self.entityKeywords = ["hierarchicalConfigKey"]
        self.CSVfields = {  'name':           self.__str_backend_name,
                            'Tier':           self.__str_backend_tierName,
                            'matchCondition': self.__str_backend_matchCondition,
                            'priority':       self.__str_backend_priority }

    def __str_backend_name(self,entrypoint):
        return entrypoint['definitionName'] if sys.version_info[0] >= 3 else entrypoint['definitionName'].encode('ASCII', 'ignore')

    def __str_backend_tierName(self,entrypoint):
        return self.controller.tiers.getTierName(tierID=entrypoint['hierarchicalConfigKey']['attachedEntity']['entityId'])

    def __str_backend_matchCondition(self,entrypoint):
        matchCondition = entrypoint['matchPointRule']['uri']['matchType']+"  "+entrypoint['matchPointRule']['uri']['matchPattern']
        if entrypoint['matchPointRule']['uri']['inverse'] == True: matchCondition = "NOT "+matchCondition 
        return matchCondition

    def __str_backend_priority(self,entrypoint):
        return entrypoint['matchPointRule']['priority']



    ###### FROM HERE PUBLIC FUNCTIONS ######

    def fetch(self,appID,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        self.controller.tiers.fetch(appID=appID)
        count = 0
        for tierID in self.controller.tiers.getTiers_ID_List(appID=appID):
            #data = self.entityAPIFunctions['fetchByID'](entity_ID=tierID,selectors=selectors)
            data = self.controller.RESTfulAPI.send_request(entityType=self.__class__.__name__,verb="fetchByID",app_ID=appID,entity_ID=tierID,selectors=selectors)
            count += self.load(streamdata=data,appID=appID)
        return count
