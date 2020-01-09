#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import csv
import sys

healthruleList = []
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

def fetch_health_rules(baseUrl,userName,password,app_ID):
    print ("Fetching Health Rules for application " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "healthrules/" + app_ID, auth=(userName, password))
    except:
       print ("Could not get the health rules of application " + app_ID + ".")
       return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    elif 'DEBUG' in locals():
        file1 = open("response.txt","w") 
        file1.write(response.content)
    try:
        root = ET.fromstring(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_health_rules_XML(root)

def load_health_rules_XML(fileName):
    print "Parsing file " + fileName + "..."
    tree = ET.parse(fileName)
    root = tree.getroot()
    parse_health_rules_XML(root)

def parse_health_rules_XML(root):

    if root.find('health-rule') is None:
        print "No Health rules defined"
        for child in root:
            print(child.tag, child.attrib, child.text)
            print ("\n")
        return None

    for healthrule in root.findall('health-rule'):

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

        healthruleList.append(HealthRule(HRname,Duration,Schedule,Enabled,EntityType,EntityCriteria,CritCondition))
#    print "Number of health rules:" + str(len(healthruleList))
#    for healthrule in healthruleList:
#        print str(healthrule)

def write_health_rules_CSV(fileName=None):
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

    if len(healthruleList) > 0:
        for healthrule in healthruleList:
            Entity_Criteria = healthrule.entityType
            for criteria in healthrule.entityCriteria:
                Entity_Criteria = Entity_Criteria + "\n  " + criteria

            try:
                filewriter.writerow({'HealthRule': healthrule.name,
                                    'Duration': healthrule.duration,
                                    'Schedule': healthrule.schedule,
                                    'Enabled': healthrule.enabled,
                                    'Entity_Criteria': Entity_Criteria,
                                    'Critical_Condition':healthrule.critCondition})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()