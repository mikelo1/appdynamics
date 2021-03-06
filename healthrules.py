#!/usr/bin/python
import xml.etree.ElementTree as ET
import json
import csv
import sys
from applications import ApplicationDict
from appdRESTfulAPI import RESTfulAPI
from entities import AppEntity

class HealthRuleDict(AppEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_health_rules_legacy}
    #TODO: entityAPIFunctions = {'fetch': RESTfulAPI().fetch_health_rules_with_IDs}

    def __init__(self):
        self.entityDict = dict()


    def __entityXML2JSON(self,XMLentityType):
        """
        private method to translate XML format entity names to JSON format entity names.
        :param entityType: naming of the entity in the XML file format
        :returns: naming of the entity in the JSON file format. Null if provided entity name could not be interpreted.
        """
        switcher = {
            "BUSINESS_TRANSACTION": "BUSINESS_TRANSACTION_PERFORMANCE",
            "NODE_HEALTH_TRANSACTION_PERFORMANCE": "TIER_NODE_TRANSACTION_PERFORMANCE",
            "INFRASTRUCTURE": "TIER_NODE_HARDWARE",
            "JMX_INSTANCE_NAME": "JMX_OBJECT",
            "INFORMATION_POINT": "INFORMATION_POINTS",
            "SIM": "SERVERS_IN_APPLICATION",
            "NETVIZ": "ADVANCED_NETWORK",
            "BACKEND": "BACKENDS",
            "SERVICEENDPOINTS": "SERVICE_ENDPOINTS",
            "ERROR": "ERRORS",
            "OVERALL_APPLICATION": "OVERALL_APPLICATION_PERFORMANCE",
            "EUMPAGES": "EUM_BROWSER_APPS"
        }
        return switcher.get(XMLentityType, XMLentityType)

    def __parse_healthrules_XML(self,streamdata):
        """
        private method to translate stream containing healthrules in XML format, to JSON format structure
        :param streamdata: the stream data in XML format
        :returns: stream data in JSON format.
        """
        try:
            root = ET.fromstring(streamdata)
        except:
            if 'DEBUG' in locals(): print ("parse_healthrules_XML: Could not process XML content.")
            return []

        healthrules = []
        for element in root.findall('health-rule'):
            # print element.find('name').text
            # for child in element:
            #    print(child.tag, child.attrib, child.text)
            # print ("\n")
            #print ET.dump(element)

            healthrule = {}
            #healthrule.update({"id": len(healthrules) })
            healthrule.update({"name": element.find('name').text })
            healthrule.update({"enabled": True if element.find('enabled').text=="true" else False})
            healthrule.update({"useDataFromLastNMinutes": int(element.find('duration-min').text) })
            healthrule.update({"waitTimeAfterViolation": int(element.find('wait-time-min').text) })
            alwaysEnabled = element.find('always-enabled').text
            schedule = "Always" if alwaysEnabled == "true" else element.find('schedule').text
            healthrule.update({"scheduleName": schedule })
            entityType = element.find('type').text
            healthrule.update({"affectedEntityType": self.__entityXML2JSON(entityType)})

            healthrule.update({"affects": self.__parse_affects_from_XML(element.find('affected-entities-match-criteria'),entityType)})

            cec = element.find('critical-execution-criteria')
            criticalCriteria = self.__parse_evalCriterias_from_XML(cec) if cec is not None else None
            wec  = element.find('warning-execution-criteria')
            warningCriteria = self.__parse_evalCriterias_from_XML(wec) if wec is not None else None
            healthrule.update({"evalCriterias": { "criticalCriteria": criticalCriteria, "warningCriteria": warningCriteria }})

            healthrules.append(healthrule)

        return healthrules


    def __parse_affects_from_XML(self,element,entityType):
        """
        private method to translate ElementTree XML object containing affected-entities-match-criteria data to JSON data
        :param element: the ElementTree XML object
        :param entityType: the type of the ElementTree object
        :returns: stream data in JSON format.
        """
        affects = {"affectedEntityType": self.__entityXML2JSON(entityType)}

        # 1) Overall Application Performance (load,response time,num slow calls)
        if entityType == "OVERALL_APPLICATION":
            pass
        # 2) Business Transaction Performance (load,response time,slow calls)
        elif entityType == "BUSINESS_TRANSACTION":
            #### SELECT BUSINESS TRANSACTIONS THIS HEALTH RULE AFFECTS:
            amc = element.find('affected-bt-match-criteria')
            affectScopeType = amc.find('type').text
            if affectScopeType == "ALL":
                # 2.1) All Business Transactions in the Application
                affects.update({"affectedBusinessTransactions":{"businessTransactionScope": "ALL_BUSINESS_TRANSACTIONS"} })
            elif affectScopeType == "BTS_OF_SPFICIC_TIERS":
                # 2.2) Business Transactions within the specified Tiers
                tierList = amc.findall('./application-components/application-component')
                tiers = ','.join(map(lambda x: str(x.text),tierList)) if (len(tierList) > 0) else ""
                affects.update({"affectedBusinessTransactions":{"businessTransactionScope": "BUSINESS_TRANSACTIONS_IN_SPECIFIC_TIERS",
                                                                "SpecificTiers": [tiers]} })                
            elif affectScopeType == "SPECIFIC":
                # 2.3) These specified Business Transactions
                BTList = amc.findall('./business-transactions/business-transaction')
                BTs = ','.join(map(lambda x: str(x.text),BTList)) if (len(BTList) > 0) else ""
                affects.update({"affectedBusinessTransactions":{"businessTransactionScope":"SPECIFIC_BUSINESS_TRANSACTIONS",
                                                                "businessTransactions": [BTs]} })
            elif affectScopeType == "CUSTOM":
                # 2.4) Business Transactions matching the following criteria
                affects.update({"affectedBusinessTransactions":{"businessTransactionScope": "BUSINESS_TRANSACTIONS_MATCHING_PATTERN",
                                                                "patternMatcher": { "matchTo": amc.find('match-type').text,
                                                                                    "matchValue": amc.find('match-pattern').text,
                                                                                    "shouldNot": amc.find('inverse').text } } })
            else: print "parse_healthrules_XML: [WARN] Unknown affectScopeType",affectScopeType
        # 3) Tier / Node Health - Transaction Performance (load,response time,slow calls)
        # 4) Tier / Node Health - Hardware, JVM, CLR (cpu,heap,disk,IO)
        # 6) Advanced Network
        elif entityType in ["NODE_HEALTH_TRANSACTION_PERFORMANCE","INFRASTRUCTURE","NETVIZ"]:
            amc = element.find('affected-infra-match-criteria')
            affectScopeType = amc.find('type').text
            #### WHAT DOES THIS HEALTH RULE AFFECT:
            if affectScopeType == "ALL_TIERS":
                # 3.1) All Tiers in the Application
                affects.update({"affectedEntities":{"tierOrNode": "TIER_AFFECTED_ENTITIES",
                                                    "affectedTiers":{"affectedTierScope":"ALL_TIERS"} } })
            elif affectScopeType == "SPECIFIC_TIERS":
                # 3.2) These specific Tiers
                tierList = amc.findall('./application-components/application-component')
                tiers = ','.join(map(lambda x: str(x.text),tierList)) if (len(tierList) > 0) else ""
                affects.update({"affectedEntities":{"tierOrNode": "TIER_AFFECTED_ENTITIES",
                                                    "affectedTiers":{"affectedTierScope":"SPECIFIC_TIERS","tiers": [tiers]} } })
            elif affectScopeType == "NODES":
                nmc = amc.find('node-match-criteria')
                nodeMatchType = nmc.find('type').text
                if nodeMatchType == "ANY":
                    # 3.3) All Nodes in the Application
                    affects.update({"affectedEntities":{"tierOrNode": "NODE_AFFECTED_ENTITIES",
                                                        "typeofNode": "ALL_NODES","affectedNodes":{"affectedNodeScope":"ALL_NODES"} } })
                elif nodeMatchType == "NODES_OF_SPECIFC_TIERS":
                    # 3.4) Nodes within the specified Tiers
                    tierList = nmc.findall('../components/application-component')
                    tiers = ','.join(map(lambda x: str(x.text),tierList))
                    affects.update({"affectedEntities":{"tierOrNode": "NODE_AFFECTED_ENTITIES",
                                        "typeofNode": "ALL_NODES","affectedNodes":{
                                                                "affectedNodeScope": "NODES_OF_SPECIFIC_TIERS",
                                                                "specificTiers": [tiers]} } })
                elif nodeMatchType == "SPECIFC":
                    # 3.5) These specific Nodes
                    nodesList = nmc.findall('./nodes/application-component-node')
                    nodes = ','.join(map(lambda x: str(x.text),nodesList))
                    affects.update({"affectedEntities":{"tierOrNode": "NODE_AFFECTED_ENTITIES",
                                        "typeofNode": "ALL_NODES","affectedNodes":{
                                                                "affectedNodeScope": "SPECIFIC_NODES",
                                                                "nodes": [nodes]} } })
                elif nodeMatchType == "CUSTOM":
                    if nmc.find('match-type') is not None:
                        # 3.6) Nodes matching the following criteria (Node name)
                        affects.update({"affectedEntities":{"tierOrNode": "NODE_AFFECTED_ENTITIES",
                                        "typeofNode": "ALL_NODES","affectedNodes":{
                                                                "affectedNodeScope": "NODES_MATCHING_PATTERN",
                                                                "patternMatcher": { "matchTo": nmc.find('match-type').text,
                                                                                    "matchValue": nmc.find('match-pattern').text,
                                                                                    "shouldNot": nmc.find('inverse').text } } } })
                    elif nmc.find('env-properties') is not None:
                        # 3.7) Nodes matching the following criteria (Node properties/variables)
                        meta_var_nameList  = nmc.findall('./env-properties/name-value/name')
                        meta_var_valueList = nmc.findall('./env-properties/name-value/value')
                        patternJSON = {}
                        for index in range(0,len(meta_var_nameList)):
                            patternJSON.update({str(meta_var_nameList[index].text):str(meta_var_valueList[index].text)})
                        affects.update({"affectedEntities":{"tierOrNode": "NODE_AFFECTED_ENTITIES",
                                        "typeofNode": "ALL_NODES","affectedNodes":{
                                                                "affectedNodeScope": "NODES_MATCHING_PROPERTY",
                                                                "patternMatcher": patternJSON } } })
                    else: print "parse_healthrules_XML: [WARN] Unknown node matching criteria."
                else: print "parse_healthrules_XML: [WARN] Unknown nodeMatchType",nodeMatchType
            else: print "parse_healthrules_XML: [WARN] Unknown affectScopeType",affectScopeType

        # 5) Tier / Node Health - JMX (connection pools,thread pools)
        elif entityType == "JMX":
            amc = element.find('affected-jmx-match-criteria')
            EntityType = amc.find('metric-path-prefix').text

        elif entityType == "APPLICATION_DIAGNOSTIC_DATA" or entityType == "MOBILE_NETWORK_REQUESTS":
            amc = element.find('affected-add-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "ALL_ADDS":
                EntityType = "ALL " + entityType
            else:
                EntityType = matchType.text
        elif entityType == "MOBILE_APPLICATION":
            amc = element.find('affected-mobile-application-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "ALL_MOBILE_APPLICATIONS":
                EntityType = matchType.text
            else:
                EntityType = matchType.text
        # 9) Error Rates (exceptions,return codes)
        elif entityType == "ERROR":
            #### SELECT WHAT ERRORS THIS HEALTH RULE AFFECTS:
            amc = element.find('affected-errors-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "ALL":
                # 9.1) All Errors in the Application
                affects.update({"affectedErrors":{"errorScope": "ALL_ERRORS"} })
            elif matchType.text == "SPECIFIC":
                # 9.2) These specified Errors
                errorsList = amc.findall('./application-diagnostic-data-list/application-diagnostic-data/name')
                errors = ','.join(map(lambda x: str(x.text),errorsList)) if (len(errorsList) > 0) else ""
                affects.update({"affectedErrors":{"errorScope": "SPECIFIC_ERRORS","errors": [errors]} })
            elif matchType.text == "ERRORS_OF_SPECIFIC_TIERS":
                # 9.3) Errors within the specified Tiers
                tiersList = amc.findall('./application-components/application-component')
                tiers = ','.join(map(lambda x: str(x.text),tiersList)) if (len(tiersList) > 0) else ""
                affects.update({"affectedErrors":{"errorScope": "ERRORS_OF_SPECIFIC_TIERS","specificTiers": [tiers]} })

            elif matchType.text == "CUSTOM":
                # 9.4) Errors matching the following criteria
                affects.update({"affectedErrors":{"errorScope": "ERRORS_MATCHING_PATTERN",
                                                "patternMatcher": { "matchTo": amc.find('match-type').text,
                                                                    "matchValue": amc.find('match-pattern').text,
                                                                    "shouldNot": amc.find('inverse').text } } })
            else: print "parse_healthrules_XML: [WARN] Unknown affectScopeType",affectScopeType
        elif entityType == "OTHER":
            amc = element.find('other-affected-entities-match-criteria')
            EntityType = "Custom metric: " + amc.find('entity').find('entity-type').text
        else:
            print "Unknown type: " + entityType

        return affects


    def __parse_evalCriterias_from_XML(self,element):
        """
        private method to translate ElementTree XML object containing critical or warning execution-criteria data to JSON data
        :param element: the ElementTree XML object
        :param entityType: the type of the ElementTree object
        :returns: stream data in JSON format.
        """
        def go_over_condition_tree(element):
            if element.find('type').text == 'leaf':
                criteria['conditions'].append(parse_condition(element))
            else:
                index = 1
                #conditionExpression = None
                newCondition = element.find('condition'+str(index))
                while newCondition is not None:
                    go_over_condition_tree(newCondition)
                    index = index +1
                    newCondition = element.find('condition'+str(index))

        def parse_condition(element):
            def go_over_MetricExpression_tree(element):
                if element.find('type').text == 'leaf':
                    metricExpressionVariable = {}
                    if element.find('function-type') is not None:
                        metricExpressionVariable.update({"variableName": element.find('display-name').text })
                        metricExpressionVariable.update({"metricAggregateFunction": element.find('function-type').text })
                        metricExpressionVariable.update({"metricPath": element.find('./metric-definition/logical-metric-name').text })
                        evalDetail['metricExpressionVariables'].append(metricExpressionVariable)
                else:
                    index = 1
                    newExpression = element.find('expression'+str(index))
                    while newExpression is not None:
                        go_over_MetricExpression_tree(newExpression)
                        index = index +1
                        newExpression = element.find('expression'+str(index))                
            condition = {}
            condition.update({"name":element.find('display-name').text})
            condition.update({"shortName":element.find('short-name').text}) if element.find('short-name') is not None else condition.update({"shortName":None})
            condition.update({"evaluateToTrueOnNoData": True if element.find('trigger-on-no-data').text=="true" else False})
            condition.update({"triggerEnabled": True if element.find('enable-triggers').text=="true" else False})
            condition.update({"minimumTriggers": int(element.find('min-triggers').text)})
            evalDetail = {}
            if element.find('./metric-expression/type').text == "leaf":
                evalDetail.update({"evalDetailType": "SINGLE_METRIC"})
                evalDetail.update({"metricAggregateFunction": element.find('./metric-expression/function-type').text})
                evalDetail.update({"metricPath": element.find('./metric-expression/metric-definition/logical-metric-name').text})
            else:
                evalDetail.update({"evalDetailType": "METRIC_EXPRESSION"})
                evalDetail.update({"metricExpressionVariables": [] })
                evalDetail.update({"metricExpression": element.find('condition-expression').text })
                go_over_MetricExpression_tree(element.find('metric-expression'))
            metricEvalDetail = {}
            compareCondition = element.find('operator').text
            if element.find('condition-value-type').text in ["BASELINE_PERCENTAGE","BASELINE_STANDARD_DEVIATION"]:
                metricEvalDetail.update({"metricEvalDetailType": "BASELINE_TYPE"})
                if compareCondition == "EQUALS": metricEvalDetail.update({"baselineCondition": "WITHIN_BASELINE"})
                elif compareCondition == "NOT_EQUALS": metricEvalDetail.update({"baselineCondition": "NOT_WITHIN_BASELINE"})
                else: metricEvalDetail.update({"baselineCondition": compareCondition+"_BASELINE"})
                if element.find('use-active-baseline').text == "true":
                    metricEvalDetail.update({"baselineName": "Default Baseline"})
                else:
                    metricEvalDetail.update({"baselineName": element.find('./metric-baseline/name').text})
                if element.find('condition-value-type').text == "BASELINE_PERCENTAGE":
                    metricEvalDetail.update({"baselineUnit": "PERCENTAGE"})
                elif element.find('condition-value-type').text == "BASELINE_STANDARD_DEVIATION":
                    metricEvalDetail.update({"baselineUnit": "STANDARD_DEVIATIONS"})
            elif element.find('condition-value-type').text == "ABSOLUTE":
                metricEvalDetail.update({"metricEvalDetailType": "SPECIFIC_TYPE"})
                metricEvalDetail.update({"baselineCondition": compareCondition+"_SPECIFIC_VALUE"})
            metricEvalDetail.update({"compareValue": float(element.find('condition-value').text)})
            evalDetail.update({"metricEvalDetail": metricEvalDetail})
            condition.update({"evalDetail":evalDetail})
            return condition
            
        if element is None: return None
        criteria = {}

        conditionAggregationType = element.find('condition-aggregation-type').text if element.find('condition-aggregation-type') is not None else "ALL"
        criteria.update({"conditionAggregationType":conditionAggregationType})
        conditionExpression = element.find('condition-expression').text if element.find('condition-expression') is not None else None
        criteria.update({"conditionExpression":conditionExpression})

        evalMatchingCriteria = {}
        if element.find('entity-aggregation-scope/type').text == "ANY":
            evalMatchingCriteria.update({"matchType": "ANY_NODE"})
        elif element.find('entity-aggregation-scope/type').text == "AGGREGATE":
            evalMatchingCriteria.update({"matchType": "AVERAGE"})
        if element.find('entity-aggregation-scope/value').text != "0":
            evalMatchingCriteria.update({"value": int(element.find('entity-aggregation-scope/value').text) })
        else:
            evalMatchingCriteria.update({"value": None })
        criteria.update({"evalMatchingCriteria":evalMatchingCriteria})

        criteria.update({"conditions": []})
        go_over_condition_tree(element.find('policy-condition'))

        #print json.dumps(criteria)
        #print criteria
        return criteria



    def __str_healthrule_affects(self,healthrule):
        """
        toString private method, extracts affects from health rule
        :param healthrule: JSON data containing a health rule
        :returns: string with a comma separated list of affects
        """
        if 'affects' not in healthrule:
            Affects=""
        elif healthrule['affects']['affectedEntityType']=="OVERALL_APPLICATION_PERFORMANCE":
            Affects="Overall application performance"
        elif healthrule['affects']['affectedEntityType']=="BUSINESS_TRANSACTION_PERFORMANCE":
            if healthrule['affects']['affectedBusinessTransactions']['businessTransactionScope']=="ALL_BUSINESS_TRANSACTIONS":
                Affects="All Business Transactions"
            elif healthrule['affects']['affectedBusinessTransactions']['businessTransactionScope']=="BUSINESS_TRANSACTIONS_IN_SPECIFIC_TIERS":
                tierList = healthrule['affects']['affectedBusinessTransactions']['SpecificTiers']
                tiers = ','.join(map(lambda x: str(x),tierList)) if (len(tierList) > 0) else ""
                Affects = "Business Transactions in Tiers " + tiers
            elif healthrule['affects']['affectedBusinessTransactions']['businessTransactionScope']=="SPECIFIC_BUSINESS_TRANSACTIONS":
                BTList = healthrule['affects']['affectedBusinessTransactions']['businessTransactions']
                BTs = ','.join(map(lambda x: str(x),BTList)) if (len(BTList) > 0) else ""
                Affects = "Business Transactions in Tiers " + BTs
            elif healthrule['affects']['affectedBusinessTransactions']['businessTransactionScope']=="BUSINESS_TRANSACTIONS_MATCHING_PATTERN":
                patternMatcher = healthrule['affects']['affectedBusinessTransactions']['patternMatcher']
                if patternMatcher['shouldNot'] == "true":
                    Affects = "Business Transactions " + "NOT" + patternMatcher['matchTo'] + " " + patternMatcher['matchValue']
                else:
                    Affects = "Business Transactions " + patternMatcher['matchTo'] + " " + patternMatcher['matchValue']
            else: Affects=""
        elif healthrule['affects']['affectedEntityType'] in ["TIER_NODE_TRANSACTION_PERFORMANCE","TIER_NODE_HARDWARE","ADVANCED_NETWORK"]:
            if healthrule['affects']['affectedEntities']['tierOrNode']=="TIER_AFFECTED_ENTITIES":
                if healthrule['affects']['affectedEntities']['affectedTiers']['affectedTierScope']=="ALL_TIERS":
                    Affects = "All Tiers"
                elif healthrule['affects']['affectedEntities']['affectedTiers']['affectedTierScope']=="SPECIFIC_TIERS":
                    tierList = healthrule['affects']['affectedEntities']['affectedTiers']['tiers']
                    tiers = ','.join(map(lambda x: str(x),tierList)) if (len(tierList) > 0) else ""
                    Affects = "Specific Tiers " + tiers
            elif healthrule['affects']['affectedEntities']['tierOrNode']=="NODE_AFFECTED_ENTITIES":
                if healthrule['affects']['affectedEntities']['affectedNodes']['affectedNodeScope']=="ALL_NODES":
                    Affects = "All Nodes"
                elif healthrule['affects']['affectedEntities']['affectedNodes']['affectedNodeScope']=="NODES_OF_SPECIFIC_TIERS":
                    tierList = healthrule['affects']['affectedEntities']['affectedNodes']['specificTiers']
                    tiers = ','.join(map(lambda x: str(x),tierList)) if (len(tierList) > 0) else ""
                    Affects = "All nodes from Tiers " + tiers
                elif healthrule['affects']['affectedEntities']['affectedNodes']['affectedNodeScope']=="SPECIFIC_NODES":
                    nodeList = healthrule['affects']['affectedEntities']['affectedNodes']['nodes']
                    nodes = ','.join(map(lambda x: str(x),nodeList)) if (len(nodeList) > 0) else ""
                    Affects = "Specific Nodes " + nodes
                elif healthrule['affects']['affectedEntities']['affectedNodes']['affectedNodeScope']=="NODES_MATCHING_PATTERN":
                    patternMatcher = healthrule['affects']['affectedEntities']['affectedNodes']['patternMatcher']
                    if patternMatcher['shouldNot'] == "true":
                        Affects = "Nodes " + "NOT" + patternMatcher['matchTo'] + " " + patternMatcher['matchValue']
                    else:
                        Affects = "Nodes " + patternMatcher['matchTo'] + " " + patternMatcher['matchValue']
                elif healthrule['affects']['affectedEntities']['affectedNodes']['affectedNodeScope']=="NODES_MATCHING_PROPERTY":
                        patternDict = healthrule['affects']['affectedEntities']['affectedNodes']['patternMatcher']
                        patterns = ','.join(map(lambda x: str(x),patternDict.items())) if (len(patternDict) > 0) else ""
                        Affects = "Nodes matching " + patterns
                else: Affects=""
            else: Affects=""
        elif healthrule['affects']['affectedEntityType']=="ERRORS":
            if healthrule['affects']['affectedErrors']['errorScope']=="ALL_ERRORS":
                Affects = "All Errors"
            elif healthrule['affects']['affectedErrors']['errorScope']=="ERRORS_OF_SPECIFIC_TIERS":
                tierList = healthrule['affects']['affectedErrors']['specificTiers']
                tiers = ','.join(map(lambda x: str(x),tierList)) if (len(tierList) > 0) else ""
                Affects = "Errors from specific Tiers " + tiers
            elif healthrule['affects']['affectedErrors']['errorScope']=="SPECIFIC_ERRORS":
                errorList = healthrule['affects']['affectedErrors']['errors']
                errors = ','.join(map(lambda x: str(x),errorList)) if (len(errorList) > 0) else ""
                Affects = "Specific errors " + errors
            elif healthrule['affects']['affectedErrors']['errorScope']=="ERRORS_MATCHING_PATTERN":
                patternMatcher = healthrule['affects']['affectedErrors']['patternMatcher']
                if patternMatcher['shouldNot'] == "true":
                    Affects = "Errors " + "NOT" + patternMatcher['matchTo'] + " " + patternMatcher['matchValue']
                else:
                    Affects = "Errors " + patternMatcher['matchTo'] + " " + patternMatcher['matchValue']
            else: Affects=""
        else: Affects=""
        return Affects


    def __str_healthrule_critical_conditions(self,healthrule):
        """
        toString private method, extracts critical conditions from health rule
        :param healthrule: JSON data containing a health rule
        :returns: string with a comma separated list of critical conditions
        """
        if 'evalCriterias' not in healthrule or 'criticalCriteria' not in healthrule['evalCriterias'] or healthrule['evalCriterias']['criticalCriteria'] is None:
            CritCondition = ""
        elif 'conditionExpression' in healthrule['evalCriterias']['criticalCriteria']:
            CritCondition = healthrule['evalCriterias']['criticalCriteria']['conditionExpression']
        elif healthrule['evalCriterias']['criticalCriteria']['conditions'][0]['evalDetail']['evalDetailType'] == "METRIC_EXPRESSION":
            CritCondition = healthrule['evalCriterias']['criticalCriteria']['conditions'][0]['evalDetail']['metricExpression']
        elif healthrule['evalCriterias']['criticalCriteria']['conditions'][0]['evalDetail']['evalDetailType'] == "SINGLE_METRIC":
            evalDetail = healthrule['evalCriterias']['criticalCriteria']['conditions'][0]['evalDetail']
            if evalDetail['metricEvalDetail']['metricEvalDetailType']=="BASELINE_TYPE":
                CritCondition = evalDetail['metricPath']+" is "+ \
                                evalDetail['metricEvalDetail']['baselineCondition']+" "+ \
                                evalDetail['metricEvalDetail']['baselineName']+" by "+ \
                                str(evalDetail['metricEvalDetail']['compareValue'])+" "+ \
                                evalDetail['metricEvalDetail']['baselineUnit']
            elif evalDetail['metricEvalDetail']['metricEvalDetailType']=="SPECIFIC_TYPE":
                CritCondition = evalDetail['metricPath']+" is "+ \
                                evalDetail['metricEvalDetail']['baselineCondition']+" "+ \
                                str(evalDetail['metricEvalDetail']['compareValue'])
            else: CritCondition = ""
        else:
            CritCondition = ""
        return CritCondition


    ###### FROM HERE PUBLIC METHODS ######


    def generate_CSV(self,appID_List,fileName=None):
        """
        Generate CSV output from health rules data
        :param appID_List: list of application IDs, in order to obtain health rules from local health rules dictionary
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
        fieldnames = ['HealthRule', 'Application', 'Duration', 'Wait_Time', 'Schedule', 'Enabled', 'Affects', 'Critical_Condition']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.entityDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for healthrule in self.entityDict[str(appID)]:
                # Check if data belongs to a health rule
                if 'affectedEntityType' not in healthrule and 'useDataFromLastNMinutes' not in healthrule: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'HealthRule': healthrule['name'].encode('ASCII', 'ignore'),
                                         'Application': ApplicationDict().getAppName(appID),
                                         'Duration': healthrule['useDataFromLastNMinutes'] if 'useDataFromLastNMinutes' in healthrule else "",
                                         'Wait_Time': healthrule['useDataFromLastNMinutes'] if 'useDataFromLastNMinutes' in healthrule else "",
                                         'Schedule': healthrule['scheduleName'] if 'scheduleName' in healthrule else "",
                                         'Enabled': healthrule['enabled'],
                                         'Affects': self.__str_healthrule_affects(healthrule),
                                         'Critical_Condition': self.__str_healthrule_critical_conditions(healthrule) })
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if 'DEBUG' in locals(): print "INFO: Displayed number of health rules:" + str(len(healthrules))
        if fileName is not None: csvfile.close()


    def load(self,streamdata,appID=None):
        """
        Load health rules from a stream data in JSON or XML format.
        :param streamdata: the stream data in JSON or XML format
        :param appID: the ID number of the application where to load the health rule data.
        :returns: the number of loaded health rules. Zero if no health rule was loaded.
        """
        if appID is None: appID = 0
        healthrules = self.__parse_healthrules_XML(streamdata)
        if len(healthrules) == 0:
            try:
                healthrules = json.loads(streamdata)
            except TypeError as error:
                sys.stderr.write("load_health_rule: "+str(error)+"\n")
                return 0

        if type(healthrules) is dict:
            self.entityDict.update({str(appID):[healthrules]})
        else:
            self.entityDict.update({str(appID):healthrules})

        return len(healthrules)


    def get_health_rules_matching(self,appID,entityName,entityType):
        pass
        #for healthrule in self.entityDict:
        #    if healthrule['affectedEntityType'] == entityType: