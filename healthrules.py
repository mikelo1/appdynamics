#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import libxml2
import csv

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
        #xml2Doc = libxml2.parseDoc(response.content)
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
    #xml2Doc.freeDoc()

def load_health_rules_XML(fileName):
    print "Parsing file " + fileName + "..."
    tree = ET.parse(fileName)
    root = tree.getroot()
    parse_health_rules_XML(root)

def load_health_rules_XML2(fileName):
    xml2Doc = libxml2.parseFile(fileName)
    parse_health_rules_XML2(xml2Doc)
    xml2Doc.freeDoc()

def parse_health_rules_XML(root):
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

def parse_health_rules_XML2(xml2Doc):
    ctxt = xml2Doc.xpathNewContext()
    #### SELECT HEALTH RULE TYPE
    # 1) Overall Application Performance (load,response time,num slow calls)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"OVERALL_APPLICATION\"]]"):
        ctxt.setContextNode(health_rule)
        Name = str(ctxt.xpathEval("./name/text()")[0])
        Duration = str(ctxt.xpathEval("./duration-min/text()")[0])
        Enabled = ( str(ctxt.xpathEval("./enabled/text()")[0]) == "true" )
        AlwaysEnabled = str(ctxt.xpathEval("./always-enabled/text()")[0])
        Schedule = "24x7" if AlwaysEnabled == "true" else str(ctxt.xpathEval("schedule/text()")[0])
        HR_ALL_type = ctxt.xpathEval("./affected-entities-match-criteria/overall-affected-entities-match-criteria[type[text()=\"APPLICATION\"]]")
        if (len(HR_ALL_type) > 0):
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"OVERALL_APPLICATION",["APPLICATION"]))

    # 2) Business Transaction Performance (load,response time,slow calls)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"BUSINESS_TRANSACTION\"]]"):
        ctxt.setContextNode(health_rule)
        Name = str(ctxt.xpathEval("./name/text()")[0])
        Duration = str(ctxt.xpathEval("./duration-min/text()")[0])
        Enabled = ( str(ctxt.xpathEval("./enabled/text()")[0]) == "true" )
        AlwaysEnabled = str(ctxt.xpathEval("./always-enabled/text()")[0])
        Schedule = "24x7" if AlwaysEnabled == "true" else str(ctxt.xpathEval("schedule/text()")[0])
        #### SELECT BUSINESS TRANSACTIONS THIS HEALTH RULE AFFECTS:
        # 2.1) All Business Transactions in the Application
        HR_ALL_type = ctxt.xpathEval("./affected-entities-match-criteria/affected-bt-match-criteria[type[text()=\"ALL\"]]")
        if (len(HR_ALL_type) > 0):
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"ALL",[]))
        # 2.2) Business Transactions within the specified Tiers
        HR_SPECIFIC_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-bt-match-criteria[type[text()=\"BTS_OF_SPFICIC_TIERS\"]]/application-components/application-component/text()")
        if (len(HR_SPECIFIC_Tiers) > 0):
            PatternList = []
            for specificTier in HR_SPECIFIC_Tiers:
                PatternList.append(str(specificTier))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"BTS_OF_SPFICIC_TIERS",PatternList))
        # 2.3) These specified Business Transactions
        HR_SPECIFIC_BTs = ctxt.xpathEval("./affected-entities-match-criteria/affected-bt-match-criteria[type[text()=\"SPECIFIC\"]]/business-transactions/business-transaction/text()")
        if (len(HR_SPECIFIC_BTs) > 0):
            PatternList = []
            for specificBT in HR_SPECIFIC_BTs:
                PatternList.append(str(specificBT))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"SPECIFIC_BT",PatternList))
        # 2.4) Business Transactions matching the following criteria
        HR_CUSTOM_type = ctxt.xpathEval("./affected-entities-match-criteria/affected-bt-match-criteria[type[text()=\"CUSTOM\"]]/match-type/text()")
        if (len(HR_CUSTOM_type) > 0):
            HR_CUSTOM_pattern = ctxt.xpathEval("./affected-entities-match-criteria/affected-bt-match-criteria[type[text()=\"CUSTOM\"]]/match-pattern/text()")
            PatternList = []
            for custPattern in HR_CUSTOM_pattern:
                PatternList.append(str(custPattern))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,str(HR_CUSTOM_type[0]),PatternList))

    # 3) Tier / Node Health - Transaction Performance (load,response time,slow calls)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"NODE_HEALTH_TRANSACTION_PERFORMANCE\"]]"):
        ctxt.setContextNode(health_rule)
        Name = str(ctxt.xpathEval("./name/text()")[0])
        Duration = str(ctxt.xpathEval("./duration-min/text()")[0])
        Enabled = ( str(ctxt.xpathEval("./enabled/text()")[0]) == "true" )
        AlwaysEnabled = str(ctxt.xpathEval("./always-enabled/text()")[0])
        Schedule = "24x7" if AlwaysEnabled == "true" else str(ctxt.xpathEval("schedule/text()")[0])
        #### WHAT DOES THIS HEALTH RULE AFFECT:
        # 3.1) All Tiers in the Application
        HR_ALL_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"ALL_TIERS\"]]")
        if (len(HR_ALL_Tiers) > 0):
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"ALL_TIERS",[]))
        # 3.2) These specific Tiers
        HR_SPECIFIC_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"SPECIFIC_TIERS\"]]/application-components/application-component/text()")
        if (len(HR_SPECIFIC_Tiers) > 0):
            PatternList = []
            for specificTier in HR_SPECIFIC_Tiers:
                PatternList.append(str(specificTier))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"SPECIFIC_Tier",PatternList))
        # 3.3) All Nodes in the Application
        HR_NODES_ANY = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"ANY\"]]")
        if (len(HR_NODES_ANY) > 0):
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"ALL_NODES",[]))
        # 3.4) Nodes within the specified Tiers
        HR_NODES_SPECIFC_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"NODES_OF_SPECIFC_TIERS\"]]/../components/application-component/text()")
        if (len(HR_NODES_SPECIFC_Tiers) > 0):
            PatternList = []
            for specificTier in HR_NODES_SPECIFC_Tiers:
                PatternList.append(str(specificTier))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"NODE_SPECIFIC_Tier",PatternList))
        # 3.5) These specific Nodes
        HR_NODES_SPECIFIC = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"SPECIFC\"]]/nodes/application-component-node/text()")
        if (len(HR_NODES_SPECIFIC) > 0):
            PatternList = []
            for specificNode in HR_NODES_SPECIFIC:
                PatternList.append(str(specificNode))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"SPECIFIC_Node",PatternList))
        # 3.6) Nodes matching the following criteria (Node name)
        HR_CUSTOM_type = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"CUSTOM\"]]/match-type/text()")
        if (len(HR_CUSTOM_type) > 0):
            HR_CUSTOM_pattern = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"CUSTOM\"]]/match-pattern/text()")
            PatternList = []
            for custPattern in HR_CUSTOM_pattern:
                PatternList.append(str(custPattern))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,str(HR_CUSTOM_type[0]),PatternList))
        # 3.7) Nodes matching the following criteria (Node properties/variables)
        HR_CUSTOM_meta_info = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"CUSTOM\"]]/node-meta-info-match-criteria/name-value")
        if (len(HR_CUSTOM_meta_info) > 0):
            PatternList = []
            for meta_info in HR_CUSTOM_meta_info:
                ctxt.setContextNode(meta_info)
                meta_var_name = ctxt.xpathEval("./name/text()")
                meta_var_value = ctxt.xpathEval("./value/text()")
                PatternList.append(str(meta_var_name[0])+"="+str(meta_var_value[0]))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"CUSTOM_META_INFO",PatternList))

    # 4) Tier / Node Health - Hardware, JVM, CLR (cpu,heap,disk,IO)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"INFRASTRUCTURE\"]]"):
        ctxt.setContextNode(health_rule)
        Name = str(ctxt.xpathEval("./name/text()")[0])
        Duration = str(ctxt.xpathEval("./duration-min/text()")[0])
        Enabled = ( str(ctxt.xpathEval("./enabled/text()")[0]) == "true" )
        AlwaysEnabled = str(ctxt.xpathEval("./always-enabled/text()")[0])
        Schedule = "24x7" if AlwaysEnabled == "true" else str(ctxt.xpathEval("schedule/text()")[0])
        #### WHAT DOES THIS HEALTH RULE AFFECT:
        # 3.1) All Tiers in the Application
        HR_ALL_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"ALL_TIERS\"]]")
        if (len(HR_ALL_Tiers) > 0):
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"ALL_TIERS",[]))
        # 3.2) These specific Tiers
        HR_SPECIFIC_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"SPECIFIC_TIERS\"]]/application-components/application-component/text()")
        if (len(HR_SPECIFIC_Tiers) > 0):
            PatternList = []
            for specificTier in HR_SPECIFIC_Tiers:
                PatternList.append(str(specificTier))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"SPECIFIC_Tier",PatternList))
        # 3.3) All Nodes in the Application
        HR_NODES_ANY = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"ANY\"]]")
        if (len(HR_NODES_ANY) > 0):
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"ALL_NODES",[]))
        # 3.4) Nodes within the specified Tiers
        HR_NODES_SPECIFC_Tiers = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"NODES_OF_SPECIFC_TIERS\"]]/../components/application-component/text()")
        if (len(HR_NODES_SPECIFC_Tiers) > 0):
            PatternList = []
            for specificTier in HR_NODES_SPECIFC_Tiers:
                PatternList.append(str(specificTier))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"NODE_SPECIFIC_Tier",PatternList))
        # 3.5) These specific Nodes
        HR_NODES_SPECIFIC = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"SPECIFC\"]]/nodes/application-component-node/text()")
        if (len(HR_NODES_SPECIFIC) > 0):
            PatternList = []
            for specificNode in HR_NODES_SPECIFIC:
                PatternList.append(str(specificNode))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"SPECIFIC_Node",PatternList))
            print ("New SPECIFIC_NODE health rule added")
        # 3.6) Nodes matching the following criteria (Node name)
        HR_CUSTOM_type = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"CUSTOM\"]]/match-type/text()")
        if (len(HR_CUSTOM_type) > 0):
            HR_CUSTOM_pattern = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"CUSTOM\"]]/match-pattern/text()")
            PatternList = []
            for custPattern in HR_CUSTOM_pattern:
                PatternList.append(str(custPattern))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,str(HR_CUSTOM_type[0]),PatternList))
        # 3.7) Nodes matching the following criteria (Node properties/variables)
        HR_CUSTOM_meta_info = ctxt.xpathEval("./affected-entities-match-criteria/affected-infra-match-criteria[type[text()=\"NODES\"]]/node-match-criteria[type[text()=\"CUSTOM\"]]/node-meta-info-match-criteria/name-value")
        if (len(HR_CUSTOM_meta_info) > 0):
            PatternList = []
            for meta_info in HR_CUSTOM_meta_info:
                ctxt.setContextNode(meta_info)
                meta_var_name = ctxt.xpathEval("./name/text()")
                meta_var_value = ctxt.xpathEval("./value/text()")
                PatternList.append(str(meta_var_name[0])+"="+str(meta_var_value[0]))
            healthruleList.append(HealthRule(Name,Duration,Schedule,Enabled,"CUSTOM_META_INFO",PatternList))
        
    # 5) Tier / Node Health - JMX (connection pools,thread pools)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"JMX\"]]"):
        ctxt.setContextNode(health_rule)
        Name = str(ctxt.xpathEval("./name/text()")[0])
        Duration = str(ctxt.xpathEval("./duration-min/text()")[0])
        Enabled = ( str(ctxt.xpathEval("./enabled/text()")[0]) == "true" )
        AlwaysEnabled = str(ctxt.xpathEval("./always-enabled/text()")[0])
        Schedule = "24x7" if AlwaysEnabled == "true" else str(ctxt.xpathEval("schedule/text()")[0])
        #### FIND JMX INSTANCES BY:
        # 5.1) JMX instance names
        HR_JMX = ctxt.xpathEval("./affected-entities-match-criteria/affected-jmx-match-criteria[type[text()=\"JMX_INSTANCE_NAME\"]]")


    # 6) Advanced Network
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"NETVIZ\"]]"):
        pass
    # 7) Servers
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"SIM\"]]"):
        pass
    # 8) Databases & Remote Services
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"BACKEND\"]]"):
        pass
    # 9) Error Rates (exceptions,return codes)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"ERROR\"]]"):
        pass
    # 10) Service Endpoints
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"SERVICEENDPOINTS\"]]"):
        pass
    # 11) Information Points
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"INFORMATION_POINT\"]]"):
        pass
    # 12) Custom (use any metrics)
    for health_rule in ctxt.xpathEval("//health-rules/health-rule[type[text()=\"OTHER\"]]"):
        pass        

    #healthruleList.append(HealthRule(HRname,Duration,Schedule,Enabled,EntityName,CritCondition))
    ctxt.xpathFreeContext()

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