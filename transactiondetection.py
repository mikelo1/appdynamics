#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import json
import csv
import sys

detectionruleList = []
class DetectionRule:
    name     = ""
    ruleType = ""
    matchRule= ""
    def __init__(self,name,ruleType,matchRule):
        self.name     = name
        self.ruleType = ruleType
        self.matchRule= matchRule
    def __str__(self):
        return "({0},{1},{2})".format(self.name,self.ruleType,self.matchRule)


def fetch_transactiondetection(baseUrl,userName,password,app_ID):
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
    parse_transactiondetection_XML(root)

def load_transactiondetection_XML(fileName):
    print "Parsing file " + fileName + "..."
    tree = ET.parse(fileName)
    root = tree.getroot()
    parse_transactiondetection_XML(root)

def parse_transactiondetection_XML(root):
    ruleList = root.find('rule-list')
    if ruleList is None:
        print "No Detection Rules defined"
        for child in root:
            print(child.tag, child.attrib, child.text)
            print ("\n")
        return None
    
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
        detectionruleList.append(DetectionRule(ruleName,ruleType,matchRule))
#    print "Number of detection rules:" + str(len(detectionruleList))
#    for detectionrule in detectionruleList:
#        print str(detectionrule) 

def write_transactiondetection_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Name', 'Type', 'MatchRule']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    if len(detectionruleList) > 0:
        for detectionrule in detectionruleList:
            try:
                filewriter.writerow({'Name': detectionrule.name,
                                    'Type': detectionrule.ruleType,
                                    'MatchRule': detectionrule.matchRule})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                exit(1)
        csvfile.close()