#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import libxml2
import csv
import sys
from optparse import OptionParser

userName = ""
password = ""
fileName = ""
port = ""

usage = "usage: %prog [options] controller username@account password Application_ID"
epilog= "example: %prog -s -p 443 ad-financial.saas.appdynamics.com johndoe@ad-financial s3cr3tp4ss 1001"

parser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
parser.add_option("-i", "--inputfile", action="store", dest="inFileName",
                  help="read source data from FILE.  If not provided, read from URL", metavar="FILE")
parser.add_option("-o", "--outfile", action="store", dest="outFileName",
                  help="write report to FILE.  If not provided, output to STDOUT", metavar="FILE")
parser.add_option("-p", "--port",
                  action="store", dest="port",
                  help="Controller port")
parser.add_option("-s", "--ssl",
                  action="store_true", dest="ssl",
                  help="Use SSL")

(options, args) = parser.parse_args()


if options.inFileName:
    print "Parsing file " + options.inFileName + "..."
    tree = ET.parse(options.inFileName)
    root = tree.getroot()
else:
    if len(args) != 4:
        parser.error("incorrect number of arguments")

    controller = args[0]
    userName = args[1]
    password = args[2]
    app_ID = args[3]

    if options.port:
        port = options.port

    baseUrl = "http"

    if options.ssl:
        baseUrl = baseUrl + "s"
        if (port == "") :
            port = "443"
    else:
        if (port == "") :
            port = "80"

    baseUrl = baseUrl + "://" + controller + ":" + port + "/controller/"

    print ("Fetching Auto Detection Rules for App " + app_ID + "...")
    try: ## //${App_ID}/auto -o autodetection-${App_Name}.xml
        response = requests.get(baseUrl + "transactiondetection/" + app_ID + "/auto", auth=(userName, password))
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        exit(1)

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
        exit(1)

    print ("Fetching Custom Detection Rules for App " + app_ID + "...")
    try: ## //${App_ID}/auto -o autodetection-${App_Name}.xml
        response = requests.get(baseUrl + "transactiondetection/" + app_ID + "/custom", auth=(userName, password))
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        exit(1)

    try:
        rootCustom = ET.fromstring(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "status:", response.status_code
        print "single header:", response.headers['content-type']
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        exit(1)
 
    auto_data_rule_list = root.find("rule-list")
    custom_data_rule_list = rootCustom.find("rule-list")
    for custom_data_rule in custom_data_rule_list:
        auto_data_rule_list.append(custom_data_rule)

try:
    if options.outFileName:
        csvfile = open(options.outFileName, 'w')
    else:
        csvfile = sys.stdout
except:
    print ("Could not open output file " + options.outFileName + ".")
    exit(1)

# create the csv writer object
fieldnames = ['EntityName', 'HealthRule', 'Duration', 'Schedule', 'Critical_Count', 'Critical_Condition']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

#for health_rule in ctxt.xpathEval("/health-rules/health-rule[type[text()="BUSINESS_TRANSACTION"] and enabled[text()="true"] and is-default[text()="false"]]"):
#	BT = health_rule.xpathEval("/affected-entities-match-criteria/affected-bt-match-criteria")

count = 0
for healthrule in root.findall('health-rule'):

    Enabled = healthrule.find('enabled').text
#    if Enabled == "false":
#        continue

    IsDefault = healthrule.find('is-default').text
#    if IsDefault == "true":
#        continue

    Type = healthrule.find('type').text
    if Type == "BUSINESS_TRANSACTION":
        aEntitymc = healthrule.find('affected-entities-match-criteria')
        amc = aEntitymc.find('affected-bt-match-criteria')
        matchType = amc.find('type')
        if matchType.text == "ALL":
            BTname = matchType.text
        else:
            BTS = amc.find('business-transactions')
            EntityName = BTS.find('business-transaction').text
    elif Type == "MOBILE_APPLICATION":
        aEntitymc = healthrule.find('affected-entities-match-criteria')
        amc = aEntitymc.find('affected-mobile-application-match-criteria')
        matchType = amc.find('type')
        if matchType.text == "ALL_MOBILE_APPLICATIONS":
            EntityName = matchType.text
        else:
            EntityName = matchType.text
    elif Type == "APPLICATION_DIAGNOSTIC_DATA" or Type == "MOBILE_NETWORK_REQUESTS":
        aEntitymc = healthrule.find('affected-entities-match-criteria')
        amc = aEntitymc.find('affected-add-match-criteria')
        matchType = amc.find('type')
        if matchType.text == "ALL_ADDS":
            EntityName = "ALL " + Type
        else:
            EntityName = matchType.text
    elif Type == "INFRASTRUCTURE" or Type == "NETVIZ":
        aEntitymc = healthrule.find('affected-entities-match-criteria')
        amc = aEntitymc.find('affected-infra-match-criteria')
        matchType = amc.find('type')
        if matchType.text == "NODES":
            nodeMatchCrit = amc.find('node-match-criteria')
            nodeMatchType = nodeMatchCrit.find('type')
            EntityName = matchType.text + " " + nodeMatchType.text
        elif matchType.text == "TIERS":
            tierMatchCrit = amc.find('tier-match-criteria')
            tierMatchType = tierMatchCrit.find('type')
            EntityName = matchType.text + " " + tierMatchType.text
        else:
            EntityName = matchType.text
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
        print ("No critical-execution-criteria for health-rule: "+healthrule.find('name').text)
        CritCondition = "NULL"
    else:
        policyCondition = cec.find('policy-condition')
        for num in range(1,9):
            condition = policyCondition.find('condition'+str(num))
            if condition is not None and condition.find('type').text == 'leaf':
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
            elif condition is not None:
                CritCondition = condition.find('type').text
            else:
                continue
               
#    wec = healthrule.find('warning-execution-criteria')
#    if wec is None:
#        WarnCondition = "NULL"
#    else:
#        print ("No warning-execution-criteria for health-rule: "+healthrule.find('name').text)

    try:
        filewriter.writerow({'EntityName': EntityName,
                            'HealthRule': HRname,
                            'Duration': Duration,
                            'Schedule': Schedule,
                            'Critical_Count': CECcount,
                            'Critical_Condition':CritCondition})
    except:
        print ("Could not write to the output file " + fileName + ".")
        csvfile.close()
        exit(1)

#doc.freeDoc()
#ctxt.xpathFreeContext()
