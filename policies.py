#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class PolicyDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_policies_legacy}

    def __init__(self):
        self.entityDict = dict()

    def __build_test_policies(self,app_ID):
        policies1=json.loads('[{"id":1854,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
        policies2=json.loads('[{"id":1855,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
        #policies3=json.loads('[{"id":1856,"name":"POLICY_SANDBOX","enabled":true,"executeActionsInBatch":true,"frequency":null,"actions":[{"actionName":"gogs@acme.com","actionType":"EMAIL","notes":""}],"events":{"healthRuleEvents":null,"otherEvents":[],"anomalyEvents":["ANOMALY_OPEN_CRITICAL"],"customEvents":[]},"selectedEntities":{"selectedEntityType":"ANY_ENTITY"}]')
        entityDict.update({str(app_ID):policies1})
        entityDict.update({str(app_ID+1):policies2})
    #    entityDict.update({str(app_ID+1):policies3})
        print "Number of entries: " + str(len(entityDict))
        if str(app_ID) in entityDict:
            print (entityDict[str(app_ID)])


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
        elif 'events' in policy and policy['events']['healthRuleEvents']['healthRuleScope']['healthRuleScopeType'] == "SPECIFIC_HEALTH_RULES":
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


    def generate_CSV(self,appID_List,fileName=None):
        """
        Generate CSV output from policies data
        :param appID_List: list of application IDs, in order to obtain policies from local policies dictionary
        :param fileName: output file name
        :returns: None
        """
        if type(appID_List) is not list or len(appID_List)==0: return

        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['Policy', 'Application', 'Events', 'Entities', 'Actions']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for policy in self.entityDict[str(appID)]:
                # Check if data belongs to a policy
                if 'reactorType' not in policy and 'selectedEntities' not in policy: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True
                try:
                    filewriter.writerow({'Policy': policy['name'].encode('ASCII', 'ignore'),
                                         'Application': ApplicationDict().getAppName(appID),
                                         'Events': self.__str_policy_healthrules(policy),
                                         'Entities': self.__str_policy_entities(policy),
                                         'Actions': self.__str_policy_actions(policy)})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()



    def load_details(self,app_ID):
        """
        Load action details for all actions from an application
        :param app_ID: the ID number of the application actions to fetch
        :returns: the number of fetched actions. Zero if no action was found.
        """
        index = 0
        for policy in self.entityDict[str(app_ID)]:
            try:
                policyJSON = json.loads(RESTfulAPI().fetch_policy_details(app_ID,policy['id']))
            except JTypeError as error:
                print ("load_policy: "+str(error))
                return None
            self.entityDict[str(appID)][index] = policyJSON
            index = index + 1

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