#!/usr/bin/python
import xml.etree.ElementTree as ET
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName

detectionruleDict = dict()
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

###
 # Fetch transaction detection rules from a controller then add them to the detectionrule dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the detection rules to fetch
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched transaction detection rules. Zero if no detection rule was found.
###
def fetch_transactiondetection(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching Auto Detection Rules for App " + str(app_ID) + "...")
    # Export Transaction Detection Rules for All Entry Point Types
    # GET /controller/transactiondetection/application_id/[tier_name/]rule_type  
    restfulPath = "/controller/transactiondetection/" + str(app_ID) + "/auto"
    params = {"output": "XML"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        root = ET.fromstring(response)
    except:
        print ("fetch_health_rules: Could not process XML content.")
        return None

    if root is None:
        print "fetch_transactiondetection: Failed to retrieve transaction detection rules for application " + str(app_ID)
        return None

    if 'DEBUG' in locals(): print ("Fetching Custom Detection Rules for App " + str(app_ID) + "...")
    restfulPath = "/controller/transactiondetection/" + str(app_ID) + "/custom"

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        rootCustom = ET.fromstring(response)
    except:
        print ("fetch_health_rules: Could not process XML content.")
        return None

    if rootCustom is None:
        print "fetch_transactiondetection: Failed to retrieve transaction detection rules for application " + str(app_ID)
        return None

    # Merge auto and custom detection rules
    for custom_data_rule in rootCustom.find("rule-list"):
        root.find("rule-list").append(custom_data_rule)

    # Add loaded detection rules to the detectrules dictionary
    detectionruleDict.update({str(app_ID):root})

    if 'DEBUG' in locals():
        print "fetch_transactiondetection: Loaded " + str(len(root.find("rule-list").getchildren())) + " transaction detection rules."

    return len(root.find("rule-list").getchildren())

###
 # Load JSON object containing tx-match-rule data to local DetectionRule class
 # @param ruleName the name of the rule
 # @param txMatchRuleData tx-match-rule data in JSON format
 # @return DetectionRule object
###
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
                    # elif (HTTPRequestCriteria == 'parameters' and httpmatch['parameters']) or (HTTPRequestCriteria == 'headers' and httpmatch['headers']) or (HTTPRequestCriteria == 'cookies' and httpmatch['cookies']):
                    #    if matchRule is not "":
                    #        matchRule = matchRule + "\n"
                    #    matchRule = matchRule + "HTTP_" + HTTPRequestCriteria + ": "
                    #    for parameter in httpmatch[HTTPRequestCriteria]:
                    #        for matchstring in parameter['name']['matchstrings']: 
                    #            matchRule = matchRule + "Name " + parameter['name']['type'] + ": " + matchstring + ", "
                    #        for matchstring in parameter['value']['matchstrings']: 
                    #            matchRule = matchRule + "Value " + parameter['value']['type'] + ": " + matchstring
                    #    matchCriteria = MatchCriteria(HTTPRequestCriteria,criteria,strings,field)

                    else:
                        continue
                mRuleList.append(matchCriteria)
            elif mCondition['type'] == "INSTRUMENTATION_PROBE":
                #### TO DO: POJO instrumentation parsing
                print ("INSTRUMENTATION_PROBE not supported yet")
            else:
                print ("Match condition "+mCondition['type']+" not implemented yet.")
        
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
                    print ("httpsplitonpayload not supported yet")
                else: 
                    print action['httpsplit']
            elif action['type'] == "POJO_SPLIT":
                #### TO DO: POJO split
                print ("POJO split not supported yet")
                pass
            else: 
                print action['type']
                print action['httpsplit']

    elif matchRuleType == "AUTOMATIC_DISCOVERY":
        #### TO DO: Automatic discovery rules
        print ("Automatic discovery rules not supported yet")
    else:
        print ("Uknown rule type: "+matchRuleType)

    return DetectionRule(ruleName,mRuleList,httpSplit)

###
 # Generate CSV output from transaction detection rules data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain transaction detection rules from local transaction detection rules dictionary
 # @param detectionRules data stream containing transaction detection rules
 # @param fileName output file name
 # @return None
###
def generate_transactiondetection_CSV(appID_List=None,detectionRules=None,fileName=None):
    print "generate_transactiondetection_CSV: feature not finished yet."
    return
    # TODO: generate CSV output format

    if detectionRules is None and str(app_ID) not in detectionruleDict:
        print "Detection Rules for application "+str(app_ID)+" not loaded."
        return
    elif detectionRules is None and str(app_ID) in detectionruleDict:
        detectionRules = detectionruleDict[str(app_ID)]

    # Verify this ElementTree contains transaction detection rule data
    if detectionRules.find('rule-list') is None: return 0

    # for child in detectionRules:
    #     print(child.tag, child.attrib, child.text)
    #     print ("\n")

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

    for detectrule in detectionRules.find('rule-list').findall('rule'):

        # for child in detectrule:
        #    print(child.tag, child.attrib, child.text)
        # print ("\n")

        ruleName = detectrule.attrib['rule-name'].encode('ASCII', 'ignore')
        ruleType = detectrule.attrib['rule-type']

        if ruleType == "TX_MATCH_RULE":
            txMatchRule = detectrule.find('tx-match-rule')
            try:
                txMatchRuleData = json.loads(txMatchRule.text)
            except:
                print ("generate_transactiondetection_CSV: Could not process JSON content:\n"+txMatchRule.text)
                continue
            match_rule = parse_tx_match_rule(ruleName,txMatchRuleData)
        else:
            print ("Uknown rule type: "+ruleType)
            continue

        ruleList_str = ""
        for matchrule in match_rule.matchRuleList:
            if ruleList_str != "":
                ruleList_str = ruleList_str + "\n" + str(matchrule)
            else:
                ruleList_str = str(matchrule)
        splitList_str = ""
        for httpSplit in match_rule.httpSplitList:
            if splitList_str != "":
                splitList_str = splitList_str + "\n" + str(httpSplit)
            else:
                splitList_str = str(httpSplit)

        try:
            filewriter.writerow({'Name': match_rule.name,
                             'MatchRuleList': ruleList_str,
                             'HttpSplit': splitList_str})
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from transaction detection rules data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain transaction detection rules from local transaction detection rules dictionary
 # @param detectionRules data stream containing transaction detection rules
 # @param fileName output file name
 # @return None
###
def generate_transactiondetection_JSON(app_ID,detectionRules=None,fileName=None):
    print "generate_transactiondetection_JSON: feature not implemented yet."
# TODO: generate JSON output format


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display transaction detection rules from a stream data in JSON or XML format.
 # @param streamdata the stream data in JSON or XML format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_detection_rules_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        root = ET.fromstring(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process XML data.")
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_transactiondetection_JSON(detectionRules=root,fileName=outFilename)
    else:
        generate_transactiondetection_CSV(detectionRules=root,fileName=outFilename)

###
 # Display transaction detection rules for a list of applications.
 # @param appID_List list of application IDs to fetch transaction detection rules
 # @param selectors fetch only transaction detection rules filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched transaction detection rules. Zero if no transaction detection rule was found.
###
def get_detection_rules(appID_List,selectors=None,outputFormat=None):
    numTransactionRules = 0
    for appID in appID_List:
        sys.stderr.write("get transaction-rules " + getAppName(appID) + "...\n")
        numTransactionRules = numTransactionRules + fetch_transactiondetection(appID,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_transactiondetection_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_transactiondetection_CSV(appID_List)
    return numTransactionRules

###
 # Get transaction detection rules matching a given URL. Fetch transaction detection data if not loaded yet.
 # @param app_ID the ID of the application
 # @return a list of transaction detection names.
###
def get_transactiondetections_matching_URL(app_ID,URL):
    pass 
    TD_List = []
    if len(detectionruleList) > 0:
        for detectionrule in detectionruleList:
            #### TO DO: Automatic discovery rules
            pass
    else:
        return None

# TODO: Get Scopes
# You can use the following endpoint as a start to query the scope within an application
# https://<controller url>/controller/restui/transactionConfigProto/getScopes/<applicationid>