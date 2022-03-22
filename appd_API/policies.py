import json
import sys
from .entities import AppEntity

class PolicyDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_policies_legacy,
                                    'fetchByID': self.controller.RESTfulAPI.fetch_policy_by_ID }
        self.entityKeywords = ["actions","reactorType"]
        self.CSVfields = {  'PolicyName': self.__str_policy_name,
                            'Events':     self.__str_policy_healthrules,
                            'Entities':   self.__str_policy_entities,
                            'Actions':    self.__str_policy_actions }

    def __build_test_policies(self,app_ID):
        policies1=json.loads('[{"id":1854,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
        policies2=json.loads('[{"id":1855,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
        #policies3=json.loads('[{"id":1856,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
        entityDict.update({str(app_ID):policies1})
        entityDict.update({str(app_ID+1):policies2})
        #entityDict.update({str(app_ID+1):policies3})
        print ("Number of entries: " + str(len(entityDict)) )
        if str(app_ID) in entityDict:
            print (entityDict[str(app_ID)])

    def __str_policy_name(self,policy):
        return policy['name'] if sys.version_info[0] >= 3 else policy['name'].encode('ASCII', 'ignore')

    def __str_policy_healthrules(self,policy):
        """
        toString private method, extracts healthrules from policy
        :param policy: JSON data containing a policy
        :returns: string with a comma separated list of health rule names
        """
        if 'eventFilterTemplate' in policy and policy['eventFilterTemplate']['healthRuleNames'] is not None:
            for healthRule in policy['eventFilterTemplate']['healthRuleNames']:
                healthrules = healthrules + "," + healthRule['entityName'] if 'healthrules' in locals() else healthRule['entityName']
            return healthrules
        elif 'events' in policy and policy['events']['healthRuleEvents']['healthRuleScopeType'] == "SPECIFIC_HEALTH_RULES":
            return ",".join(policy['events']['healthRuleEvents']['healthRuleScope']['healthRules'])
        else:
            return "ANY"

    def __str_policy_entities(self,policy):
        """
        toString private method, extracts entities from policy
        :param policy: JSON data containing a policy
        :returns: string with a comma separated list of entity names
        """
        if 'entityFilterTemplates' in policy:
            for entTemplate in policy['entityFilterTemplates']:
                if entTemplate['matchCriteriaType'] == "AllEntities":
                    EntityDescription = "ALL "+entTemplate['entityType']
                elif entTemplate['matchCriteriaType'] == "RelatedEntities":
                    EntityDescription = entTemplate['entityType']+" within the Tiers: "
                    for tier in entTemplate['relatedEntityNames']:
                        EntityDescription = EntityDescription + tier['entityName'] + ", "
                elif entTemplate['matchCriteriaType'] == "SpecificEntities":
                    EntityDescription = "These specific "+ entTemplate['entityType']+": "
                    for entityName in entTemplate['entityNames']:
                        EntityDescription = EntityDescription + entityName['entityName'] + ", "
                elif entTemplate['matchCriteriaType'] == "CustomEntities":
                    EntityDescription = entTemplate['entityType']+" matching the following criteria: "
                    EntityDescription = EntityDescription + " " + entTemplate['stringMatchType'] + " " + entTemplate['stringMatchExpression']
                elif entTemplate['entityType'] == "JMX_INSTANCE_NAME":
                    nodeEntCriteria = entTemplate['nodeEntityMatchCriteria']
                    if nodeEntCriteria['matchCriteriaType'] == "AllEntities":
                        EntityDescription = "JMX Objects from ALL"+nodeEntCriteria['entityType']
                    elif nodeEntCriteria['matchCriteriaType'] == "RelatedEntities":
                        EntityDescription = nodeEntCriteria['entityType']+" within the Tiers: "
                        for tier in entTemplate['relatedEntityNames']:
                            EntityDescription = EntityDescription + tier['entityName'] + ", "
                    elif nodeEntCriteria['matchCriteriaType'] == "SpecificEntities":
                        EntityDescription = "These specific "+ nodeEntCriteria['entityType']+": "
                        for entityName in entTemplate['entityNames']:
                            EntityDescription = EntityDescription + entityName['entityName'] + ", "
                    elif nodeEntCriteria['matchCriteriaType'] == "CustomEntities":
                        EntityDescription = nodeEntCriteria['entityType']+" matching the following criteria: "
                        EntityDescription = EntityDescription + " " + nodeEntCriteria['stringMatchType'] + " " + nodeEntCriteria['stringMatchExpression']
                entities = entities + " " + EntityDescription if 'entities' in locals() else EntityDescription
        elif 'selectedEntities' in policy and policy['selectedEntities']['selectedEntityType'] == "SPECIFIC_ENTITIES":
            for entity in policy['selectedEntities']['entities']:
                entities = entities + "\n" if 'entities' in locals() else ""
                if entity['entityType']   == "BUSINESS_TRANSACTION":
                    if entity['selectedBusinessTransactions']['businessTransactionScope'] == "ALL_BUSINESS_TRANSACTIONS":
                        entities = entities + "\nAll Business Transactions" if 'entities' in locals() else "All Business Transactions"
                    elif entity['selectedBusinessTransactions']['businessTransactionScope'] == "SPECIFIC_BUSINESS_TRANSACTIONS":
                        entities = entities + ",".join(entity['selectedBusinessTransactions']['businessTransactions'])
                    else:
                        pass
                # TO DO: print out rest of entities
                elif entity['entityType'] == "DATABASES_IN_APPLICATION":
                    entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
                elif entity['entityType'] == "TIER_NODE":
                    entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
                elif entity['entityType'] == "INFORMATION_POINTS":
                    entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
                elif entity['entityType'] == "SERVERS_IN_APPLICATION":
                    entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
                elif entity['entityType'] == "ERRORS":
                    entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
                elif entity['entityType'] == "PAGE":
                    entities = entities + "\n" + entity['entityType'] + " Output not implemented yet."
        else:
            return "ANY"
        if 'entities' in locals(): return entities
        else: return "ANY"

    def __str_policy_actions(self,policy):
        """
        toString private method, extracts actions from policy
        :param policy: JSON data containing a policy
        :returns: string with a comma separated list of action names
        """
        if 'actionWrapperTemplates' in policy:
            for action in policy['actionWrapperTemplates']:
                actions = actions + " " + action['actionTag'] if 'actions' in locals() else action['actionTag']
            if 'actions' in locals(): return actions
            else: return "ANY"
        elif 'actions' in policy:
            return "Output not implemented yet."
        else:
            return "ANY"


    ###### FROM HERE PUBLIC FUNCTIONS ######


    def get_policies_matching_action(self,app_ID,name):
        MatchList = []
        if str(app_ID) in self.entityDict:
            for policy in self.entityDict[str(app_ID)]:
                for policy_action in policy['actions']:
                    if policy_action['actionName'] == name:
                        MatchList.append(policy.name)
        return MatchList
	
#### TO DO:
####        get_policies_matching_health_rule(app_ID,name)
####        get_policies_matching_business_transaction
####        get_policies_matching_tiers_and_nodes
####        get_policies_matching_JMX
####        get_policies_matching_Information_Point
####        get_policies_matching_Server
####        get_policies_matching_Database
####        get_policies_matching_Service_Endpoint
####        get_policies_matching_Error
