#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import libxml2
import json
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

#mydata = ET.tostring(root)
#myfile = open("items.xml", "w")
#myfile.write(mydata)
#exit

# create the csv writer object
fieldnames = ['Name', 'Type', 'MatchRule']
filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
filewriter.writeheader()

ruleList = root.find('rule-list')
for detectrule in ruleList.findall('rule'):

#    for child in detectrule:
#       print(child.tag, child.attrib, child.text)
#    print ("\n")

    ruleName = detectrule.attrib['rule-name'].encode('ASCII', 'ignore')
    ruleType = detectrule.attrib['rule-type']

    if ruleType == "TX_MATCH_RULE":
        txMatchRule = detectrule.find('tx-match-rule')

        try:
            matchRuleData = json.loads(txMatchRule.text)
        except:
            print ("Could not process JSON content:\n"+txMatchRule.text)

        matchRuleType = matchRuleData['type']
        ruleType = matchRuleType
        if matchRuleType == "AUTOMATIC_DISCOVERY":
            matchRule = ''
            autoDiscoveryConfigs = matchRuleData['txautodiscoveryrule']['autodiscoveryconfigs']
            for discoveryconfig in autoDiscoveryConfigs:
                if matchRule is not "":
                    matchRule = matchRule + "\n" 
                matchRule = matchRule + discoveryconfig['txentrypointtype']
        elif matchRuleType == "CUSTOM":
            matchRule = ''
            matchconditions = matchRuleData['txcustomrule']['matchconditions']
            for mCondition in matchconditions:
                if mCondition['type'] == "HTTP":
                    httpmatch = mCondition['httpmatch']
                    for HTTPRequestCriteria in httpmatch:
                        if HTTPRequestCriteria == 'uri':
                            mConditionHTTP = httpmatch['uri']
                            if matchRule is not "":
                                matchRule = matchRule + "\n"
                            matchRule = matchRule + "URI " + mConditionHTTP['type'] + ": "
                            for matchstring in mConditionHTTP['matchstrings']: 
                                matchRule = matchRule + matchstring
                        elif HTTPRequestCriteria == 'classmatch':
                            mConditionHTTP = httpmatch['classmatch']['classnamecondition']
                            classMatchType = httpmatch['classmatch']['type']
                            if matchRule is not "":
                                matchRule = matchRule + "\n"
                            matchRule = matchRule + classMatchType + " " + mConditionHTTP['type'] + ": "
                            for matchstring in mConditionHTTP['matchstrings']: 
                                matchRule = matchRule + matchstring
                        elif HTTPRequestCriteria == 'httpmethod':
                            if matchRule is not "":
                                matchRule = matchRule + "\n"
                            matchRule = matchRule + "HTTP_Method: " + httpmatch['httpmethod']
                        elif (HTTPRequestCriteria == 'parameters' and httpmatch['parameters']) or (HTTPRequestCriteria == 'headers' and httpmatch['headers']) or (HTTPRequestCriteria == 'cookies' and httpmatch['cookies']):
                            if matchRule is not "":
                                matchRule = matchRule + "\n"
                            matchRule = matchRule + "HTTP_" + HTTPRequestCriteria + ": "
                            for parameter in httpmatch[HTTPRequestCriteria]:
                                paramName = parameter['name']
                                for matchstring in paramName['matchstrings']: 
                                    matchRule = matchRule + "Name " + paramName['type'] + ": " + matchstring + ", "
                                paramValue = parameter['value']
                                for matchstring in paramValue['matchstrings']: 
                                    matchRule = matchRule + "Value " + paramValue['type'] + ": " + matchstring
                        elif HTTPRequestCriteria == 'hostname' or HTTPRequestCriteria == 'port' or HTTPRequestCriteria == 'servlet':
                            if matchRule is not "":
                                matchRule = matchRule + "\n"
                            matchRule = matchRule + HTTPRequestCriteria + " "
                            paramName = httpmatch[HTTPRequestCriteria]
                            for matchstring in paramName['matchstrings']: 
                                matchRule = matchRule + paramName['type'] + ": " + matchstring
                        else:
                            continue
        else:
            print ("Uknown rule type: "+matchRuleType)
            matchRule = txMatchRule.text
    else:
        print ("Uknown rule type: "+ruleType)
        matchRule = txMatchRule.text

    try:
        filewriter.writerow({'Name': ruleName,
                            'Type': ruleType,
                            'MatchRule': matchRule})
    except:
        print ("Could not write to the output file " + fileName + ".")
        csvfile.close()
        exit(1)

#doc.freeDoc()
#ctxt.xpathFreeContext()
