#!/usr/bin/python
import xml.etree.ElementTree as ET
import csv
import sys
from applications import getName
from appdRESTfulAPI import fetch_RESTful_XML

healthruleDict = dict()

class HealthRule:
    name          = ""
    duration      = 0
    schedule      = ""
    enabled       = None
    entityType    = ""
    entityCriteria= []
    critCondition = ""
    warnCondition = ""
    def __init__(self,name,duration,schedule,enabled,entityType,entityCriteria,critCondition=None,warnCondition=None):
        self.name          = name
        self.duration      = duration
        self.schedule      = schedule
        self.enabled       = enabled
        self.entityType    = entityType
        self.entityCriteria= entityCriteria
        self.critCondition = critCondition
        self.warnCondition = warnCondition
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5},{6},{7})".format(self.name,self.duration,self.schedule,self.enabled,self.entityType,self.entityCriteria,self.critCondition,self.warnCondition)

###
 # Fetch health rules from a controller then add them to the healthrule dictionary. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param app_ID the ID number of the health rules to fetch
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched health rules. Zero if no health rule was found.
###
def fetch_health_rules(serverURL,app_ID,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching Health Rules for application " + str(app_ID) + "...")

    # Export Health Rules from an Application
    # GET /controller/healthrules/application_id?name=health_rule_name
    restfulPath = "/controller/healthrules/" + str(app_ID)
    if userName and password:
        root = fetch_RESTful_XML(restfulPath,userName=userName,password=password)
    elif token:
        root = fetch_RESTful_XML(restfulPath)

    if root is None:
        print "fetch_health_rules: Failed to retrieve health rules for application " + str(app_ID)
        return None

    # Add loaded events to the event dictionary
    healthruleDict.update({str(app_ID):root})

    if 'DEBUG' in locals():
        print "fetch_health_rules: Loaded " + str(len(root.getchildren())) + " health rules."

    return len(root.getchildren())

def convert_health_rules_XML_to_CSV(inFileName,outFilename=None):
    tree = ET.parse(inFileName)
    root = tree.getroot()
    generate_health_rules_CSV(app_ID=0,healthrules=root,fileName=outFilename)

def generate_health_rules_CSV(app_ID,healthrules=None,fileName=None):
    if healthrules is None and str(app_ID) not in healthruleDict:
        print "Health Rules for application "+str(app_ID)+" not loaded."
        return
    elif healthrules is None and str(app_ID) in healthruleDict:
        healthrules = healthruleDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['HealthRule', 'Duration', 'Schedule', 'Enabled', 'Entity_Criteria', 'Critical_Condition']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    if healthrules.find('health-rule') is None:
        print "No Health rules defined"
        for child in healthrules:
            print(child.tag, child.attrib, child.text)
            print ("\n")
        return None

    for healthrule in healthrules.findall('health-rule'):

        Enabled = ( healthrule.find('enabled').text == "true" )
    #    if Enabled == "false":
    #        continue

        IsDefault = healthrule.find('is-default').text
    #    if IsDefault == "true":
    #        continue

        EntityCriteria = []
        Type = healthrule.find('type').text
        if Type == "BUSINESS_TRANSACTION":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('affected-bt-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "SPECIFIC":
                EntityType = "Specific business transactions"
                BTS = amc.find('business-transactions')
                for BT in BTS.findall('business-transaction'):
                    EntityCriteria.append(BT.text)
            elif matchType.text == "BTS_OF_SPFICIC_TIERS":
                EntityType = "BTs of specific tiers"
                componentList = amc.find('application-components')
                for component in componentList.findall('application-component'):
                    EntityCriteria.append(component.text)
            elif matchType.text == "CUSTOM":
                if amc.find('inverse').text == "true":
                    EntityType = "Business Transactions NOT " + amc.find('match-type').text
                else:
                    EntityType = "Business Transactions " + amc.find('match-type').text
                EntityCriteria.append(amc.find('match-pattern').text)
            else: # matchType.text == "ALL":
                EntityType = "All business transactions"
        elif Type == "MOBILE_APPLICATION":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('affected-mobile-application-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "ALL_MOBILE_APPLICATIONS":
                EntityType = matchType.text
            else:
                EntityType = matchType.text
        elif Type == "APPLICATION_DIAGNOSTIC_DATA" or Type == "MOBILE_NETWORK_REQUESTS":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('affected-add-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "ALL_ADDS":
                EntityType = "ALL " + Type
            else:
                EntityType = matchType.text
        elif Type == "INFRASTRUCTURE" or Type == "NODE_HEALTH_TRANSACTION_PERFORMANCE" or Type == "NETVIZ":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('affected-infra-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "NODES":
                nodeMatchCrit = amc.find('node-match-criteria')
                nodeMatchType = nodeMatchCrit.find('type')
                if nodeMatchType == "SPECIFC" or nodeMatchType == "NODES_OF_SPECIFC_TIERS":
                    EntityType = Type + ": " + matchType.text
                    componentList = nodeMatchCrit.find('nodes')
                    for component in componentList.findall('application-component-node'):
                        EntityCriteria.append(component.text)
                elif nodeMatchType == "CUSTOM":
                    EntityType = Type + ": " + matchType.text
                    if amc.find('inverse').text == "true":
                        EntityType = EntityType + " NOT matching: " + amc.find('match-type').text
                    else:
                        EntityType = EntityType + " matching: " + amc.find('match-type').text
                    EntityCriteria.append(amc.find('match-pattern').text)
                else: # nodeMatchType == "ANY"
                    EntityType = Type + ": " + nodeMatchType.text + " " + matchType.text 
            elif matchType.text == "SPECIFIC_TIERS":
                EntityType = Type + ": " + matchType.text
                componentList = amc.find('application-components')
                for component in componentList.findall('application-component'):
                    EntityCriteria.append(component.text)
            else: # matchType.text == "ALL_TIERS"
                pass
        elif Type == "JMX":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('affected-jmx-match-criteria')
            EntityType = amc.find('metric-path-prefix').text
        elif Type == "ERROR":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('affected-errors-match-criteria')
            matchType = amc.find('type')
            if matchType.text == "SPECIFIC":
                EntityType = "Specific errors"
                diagDataList = amc.find('application-diagnostic-data-list')
                for diagData in diagDataList.findall('application-diagnostic-data'):
                    EntityCriteria.append(diagData.find('name').text)
            elif matchType.text == "ERRORS_OF_SPECIFIC_TIERS":
                EntityType = "Errors of specific tiers:"
                componentList = amc.find('application-components')
                for component in componentList.findall('application-component'):
                    EntityCriteria.append(component.text)
            elif matchType.text == "CUSTOM":
                EntityType = "Errors "
                if amc.find('inverse').text == "true":
                    EntityType = "Errors NOT " + amc.find('match-type').text
                else:
                    EntityType = "Errors " + amc.find('match-type').text
                EntityCriteria.append(amc.find('match-pattern').text)
            elif matchType.text == "ALL":
                EntityType = "ALL_ERRORS"
            else:
                print "Unknown error entity: " + matchType.text
                continue
        elif Type == "OVERALL_APPLICATION":
            EntityType = Type
        elif Type == "OTHER":
            aEntitymc = healthrule.find('affected-entities-match-criteria')
            amc = aEntitymc.find('other-affected-entities-match-criteria')
            EntityType = "Custom metric: " + amc.find('entity').find('entity-type').text
        else:
            print "Unknown type: " + Type
            continue

        Entity_Criteria = EntityType
        for criteria in EntityCriteria:
            Entity_Criteria = Entity_Criteria + "\n  " + criteria

        HRname = healthrule.find('name').text
        Duration = healthrule.find('duration-min').text

        AlwaysEnabled = healthrule.find('always-enabled').text
        if AlwaysEnabled == "false":
            Schedule = healthrule.find('schedule').text
        else:
            Schedule = "24x7"

    #   print healthrule.find('name').text
    #   for child in healthrule:
    #      print(child.tag, child.attrib, child.text)
    #   print ("\n")

        CECcount = 0
        CritCondition = ""
        cec = healthrule.find('critical-execution-criteria')
        if cec is None:
            print ("Warn: No critical-execution-criteria for health-rule: "+healthrule.find('name').text)
            CritCondition = "None"
        else:
            policyCondition = cec.find('policy-condition')
            num = 1
            condition = policyCondition.find('condition'+str(num))
            if condition is not None:
                while condition is not None:
                    if condition.find('type').text == 'leaf':
                        CECcount = CECcount + 1
                        if CECcount > 1: CritCondition = CritCondition + "\n"
                        ConditionExp = condition.find('condition-expression')
                        if ConditionExp is not None and ConditionExp.text is not None:
                            CritCondition = CritCondition + ConditionExp.text
                        else:
                            MetricDef = condition.find('metric-expression').find('metric-definition')
                            MetricName = MetricDef.find('logical-metric-name')
                            CritCondition = CritCondition + MetricName.text
                        ConditionOpe = condition.find('operator')
                        ConditionVal = condition.find('condition-value')
                        CritCondition = CritCondition + " " + ConditionOpe.text + " " + ConditionVal.text
                        if condition.find('condition-value-type').text == "BASELINE_STANDARD_DEVIATION":
                            CritCondition = CritCondition + " Baseline Standard Deviations"
                    else:
                        CritCondition = condition.find('type').text
                    num += 1
                    condition = policyCondition.find('condition'+str(num))
            else:
                ConditionExp = policyCondition.find('condition-expression')
                if ConditionExp is not None and ConditionExp.text is not None:
                    CritCondition = CritCondition + ConditionExp.text
                else:
                    MetricDef = policyCondition.find('metric-expression').find('metric-definition')
                    MetricName = MetricDef.find('logical-metric-name')
                    CritCondition = CritCondition + MetricName.text
                ConditionOpe = policyCondition.find('operator')
                ConditionVal = policyCondition.find('condition-value')
                CritCondition = CritCondition + " " + ConditionOpe.text + " " + ConditionVal.text
                if policyCondition.find('condition-value-type').text == "BASELINE_STANDARD_DEVIATION":
                    CritCondition = CritCondition + " Baseline Standard Deviations"

    #    wec = healthrule.find('warning-execution-criteria')
    #    if wec is None:
    #        WarnCondition = "NULL"
    #    else:
    #        print ("No warning-execution-criteria for health-rule: "+healthrule.find('name').text)

            try:
                filewriter.writerow({'HealthRule': HRname,
                                    'Duration': Duration,
                                    'Schedule': Schedule,
                                    'Enabled': Enabled,
                                    'Entity_Criteria': Entity_Criteria,
                                    'Critical_Condition':CritCondition})
            except:
                print ("Could not write to the output.")
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()

def get_health_rules(serverURL,app_ID,userName=None,password=None,token=None):
    if serverURL == "dummyserver":
        build_test_health_rules(app_ID)
    elif userName and password:
        if fetch_health_rules(serverURL,app_ID,userName=userName,password=password) == 0:
            print "get_health_rules: Failed to retrieve health rules for application " + str(app_ID)
            return None
    elif token:
        if fetch_health_rules(serverURL,app_ID,token=token) == 0:
            print "get_health_rules: Failed to retrieve health rules for application " + str(app_ID)
            return None
    generate_health_rules_CSV(app_ID)