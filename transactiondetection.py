#!/usr/bin/python
import requests
import xml.etree.ElementTree as ET
import json
import csv
import sys

detectionruleList = []
class DetectionRule:
    name         = ""
    matchRuleList= []
    httpSplitList= []
    def __init__(self,name,matchRuleList,httpSplitList):
        self.name         = name
        self.matchRuleList= matchRuleList
        self.httpSplitList= httpSplitList
    def __str__(self):
        return "({0},{1},{2},{3})".format(self.name,self.matchRuleList,self.httpSplitList)

class MatchCriteria:
    dataType= ""   # Method|URI|HTTP_Parameter|Header|Hostname|Port|Class_Name|Servlet_Name|Cookie
    criteria= ""   # Equals|Starts_With|Ends_With|Contains|Matches_Regex|Is_In_List|Is_Not_Empty
    strings = []   # Match criteria strings
    field   = None # data field (only for HTTP_Parameter|Header|Cookie)
    def __init__(self,dataType,criteria,strings,field=None):
        self.dataType = dataType
        self.criteria = criteria
        self.strings  = strings
        self.field    = field
    def __str__(self):
        if self.field is None:
            return "({0},{1},{2})".format(self.dataType,self.criteria,self.strings)
        else:
            return "({0},{1},{2},{3})".format(self.dataType,self.field,self.criteria,self.strings)


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
                txMatchRuleData = json.loads(txMatchRule.text)
            except:
                print ("Could not process JSON content:\n"+txMatchRule.text)
                return None
            parse_tx_match_rule(ruleName,txMatchRuleData)
            
        else:
            print ("Uknown rule type: "+ruleType)
            matchRule = txMatchRule.text
            return None
#    print "Number of detection rules:" + str(len(detectionruleList))
#    for detectionrule in detectionruleList:
#        print str(detectionrule) 

def parse_tx_match_rule(ruleName,txMatchRuleData):
    mRuleList = []
    httpSplit = []

    matchRuleType = txMatchRuleData['type']

    if matchRuleType == "CUSTOM":
        matchconditions = txMatchRuleData['txcustomrule']['matchconditions']
        for mCondition in matchconditions:
            if mCondition['type'] == "HTTP":
                httpmatch = mCondition['httpmatch']
                for HTTPRequestCriteria in httpmatch:

                    if HTTPRequestCriteria == 'httpmethod':
                        matchCriteria = MatchCriteria(HTTPRequestCriteria,httpmatch['httpmethod'],[])

                    elif HTTPRequestCriteria == 'uri' or HTTPRequestCriteria == 'hostname' or HTTPRequestCriteria == 'port' or HTTPRequestCriteria == 'servlet':
                        criteria = httpmatch[HTTPRequestCriteria]['type']
                        if 'isnot' in httpmatch[HTTPRequestCriteria] and httpmatch[HTTPRequestCriteria]['isnot'] == True:
                            criteria = "NOT_"+criteria
                        strings = []
                        for matchstring in httpmatch['uri']['matchstrings']: 
                            strings.append(matchstring)
                        matchCriteria = MatchCriteria(HTTPRequestCriteria,criteria,strings)

                    elif HTTPRequestCriteria == 'classmatch':
                        criteria = httpmatch['classmatch']['type']
                        if 'isnot' in httpmatch['classmatch']['classnamecondition'] and httpmatch['classmatch']['classnamecondition']['isnot'] == True:
                            criteria = criteria +"_NOT_"+httpmatch['classmatch']['classnamecondition']['type']
                        else:
                            criteria = criteria +"_"+httpmatch['classmatch']['classnamecondition']['type']
                        strings = []
                        for matchstring in httpmatch['classmatch']['classnamecondition']['matchstrings']: 
                            strings.append(matchstring)
                        matchCriteria = MatchCriteria(HTTPRequestCriteria,criteria,strings)

                    #### TO DO: Parameters | Headers | Cookies
#                    elif (HTTPRequestCriteria == 'parameters' and httpmatch['parameters']) or (HTTPRequestCriteria == 'headers' and httpmatch['headers']) or (HTTPRequestCriteria == 'cookies' and httpmatch['cookies']):
#                        if matchRule is not "":
#                            matchRule = matchRule + "\n"
#                        matchRule = matchRule + "HTTP_" + HTTPRequestCriteria + ": "
#                        for parameter in httpmatch[HTTPRequestCriteria]:
#                            for matchstring in parameter['name']['matchstrings']: 
#                                matchRule = matchRule + "Name " + parameter['name']['type'] + ": " + matchstring + ", "
#                            for matchstring in parameter['value']['matchstrings']: 
#                                matchRule = matchRule + "Value " + parameter['value']['type'] + ": " + matchstring
#                        matchCriteria = MatchCriteria(HTTPRequestCriteria,criteria,strings,field)

                    else:
                        continue
                mRuleList.append(matchCriteria)
            elif mCondition['type'] == "INSTRUMENTATION_PROBE":
                #### TO DO: POJO instrumentation parsing
                print "INSTRUMENTATION_PROBE not supported yet"
            else:
                print "Match condition "+mCondition['type']+" not implemented yet."
        
        actions = txMatchRuleData['txcustomrule']['actions']
        for action in actions:
            if action['type'] == "HTTP_SPLIT":
                if not action['httpsplit']: # HTTPSplit definition is empty
                    continue
                elif 'httpsplitonreqdata' in action['httpsplit']:
                    httpsplitonreqdata = action['httpsplit']['httpsplitonreqdata']
                    if 'customexpression' in httpsplitonreqdata:
                        httpSplit.append("Split Transactions using custom expression: "+httpsplitonreqdata['customexpression']['stringvalue'])
                    elif 'segments' in httpsplitonreqdata:
                        segments = str(httpsplitonreqdata['segments']['selectedsegments'])
                        httpSplit.append("Split Transactions using URI segment "+segments)
                    elif 'usehttpmethod' in httpsplitonreqdata:
                        if httpsplitonreqdata['usehttpmethod'] == True:
                            httpSplit.append("Split Transactions using the request method (GET/POST/PUT)")
                        else: # Split Transactions using request method is disabled
                            pass
                    else: #### TO DO: Implement rest of actions (Split Transactions Using Request Data)
                        print action['httpsplit']['httpsplitonreqdata']
                        pass
                elif 'httpsplitonpayload' in action['httpsplit']:
                    #### TO DO: Actions (Split Using Payload)
                    print "httpsplitonpayload not supported yet"
                else: 
                    print action['httpsplit']
            elif action['type'] == "POJO_SPLIT":
                #### TO DO: POJO split
                print "POJO split not supported yet"
                pass
            else: 
                print action['type']
                print action['httpsplit']

    elif matchRuleType == "AUTOMATIC_DISCOVERY":
        #### TO DO: Automatic discovery rules
        print "Automatic discovery rules not supported yet"
    else:
        print ("Uknown rule type: "+matchRuleType)

#    print "Number of detection rules:" + str(len(mRuleList))
#    for mRule in mRuleList:
#        print str(mRule)
    detectionruleList.append(DetectionRule(ruleName,mRuleList,httpSplit))

def get_transactiondetections_matching_URL(URL):
    pass 
    TD_List = []
    if len(detectionruleList) > 0:
        for detectionrule in detectionruleList:
            #### TO DO: Automatic discovery rules
            pass
    else:
        return None

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
    fieldnames = ['Name', 'MatchRuleList', 'HttpSplit']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    if len(detectionruleList) > 0:
        for detectionrule in detectionruleList:
            ruleList_str = ""
            for matchrule in detectionrule.matchRuleList:
                if ruleList_str != "":
                    ruleList_str = ruleList_str + "\n" + str(matchrule)
                else:
                    ruleList_str = str(matchrule)
            splitList_str = ""
            for httpSplit in detectionrule.httpSplitList:
                if splitList_str != "":
                    splitList_str = splitList_str + "\n" + str(httpSplit)
                else:
                    splitList_str = str(httpSplit)

            try:
                filewriter.writerow({'Name': detectionrule.name,
                                 'MatchRuleList': ruleList_str,
                                 'HttpSplit': splitList_str})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                exit(1)
        csvfile.close()