#!/usr/bin/python
import xml.etree.ElementTree as ET
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName

detectionruleDict = dict()

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
    # https://docs.appdynamics.com/display/PRO45/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportTransactionDetectionRulesExportTransactionDetectionRules
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
 # Update transaction detection rule from a controller.
 # @param app_ID the ID number of the transaction detection rule to update
 # @param detectRule_ID the ID number of the transaction detection rule to update
 # @return True if the update was successful. False if no transaction detection rule was updated.
###
def update_transactiondetection(app_ID,detectRule_ID):
    for detectionrule in detectionruleDict[str(app_ID)]:
        if detectionrule['id'] == detectRule_ID: break
    else:
        print "No detectionrule " + str(detectRule_ID) + " was found in application " + str(app_ID)
        return False 
    if 'DEBUG' in locals(): print ("Updating schedule " + str(sched_ID) + " for App " + str(app_ID) + "...")
    # Updates an existing schedule with a specified JSON payload
    # POST /controller/transactiondetection/application_id/{scope_name}/rule_type/{entry_point_type}/{rule_name} -F file=@exported_file_name.xml
    # https://docs.appdynamics.com/display/PRO45/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ImportTransactionDetectionRules
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(sched_ID)
    return update_RESTful_JSON(restfulPath,detectionrule)



###
 # toString method, extracts Match Rule List from transaction detection rule
 # @param txMatchRuleData JSON data containing match rules
 # @return string with a comma separated list of Match Rules
###
def str_transactiondetection_matchrules(txMatchRuleData):
    mRuleList = ""
    if txMatchRuleData['type'] == "CUSTOM":
        for mCondition in txMatchRuleData['txcustomrule']['matchconditions']:
            if mCondition['type'] == "HTTP":
                httpmatch = mCondition['httpmatch']
                for HTTPRequestCriteria in httpmatch:
                    if len(mRuleList) > 0: mRuleList = mRuleList + "\n"
                    if HTTPRequestCriteria == 'httpmethod':
                        criteria = httpmatch['httpmethod']
                        strings  = ""
                        mRuleList = mRuleList + HTTPRequestCriteria + " " + criteria + " " + strings
                    elif HTTPRequestCriteria in ['uri','hostname','port','servlet']:
                        criteria = httpmatch[HTTPRequestCriteria]['type']
                        if 'isnot' in httpmatch[HTTPRequestCriteria] and httpmatch[HTTPRequestCriteria]['isnot'] == True:
                            criteria = "NOT_"+criteria
                        strings = " ".join(httpmatch['uri']['matchstrings'])
                        mRuleList = mRuleList + HTTPRequestCriteria + " " + criteria + " " + strings
                    elif HTTPRequestCriteria == 'classmatch':
                        criteria = httpmatch['classmatch']['type']
                        if 'isnot' in httpmatch['classmatch']['classnamecondition'] and httpmatch['classmatch']['classnamecondition']['isnot'] == True:
                            criteria = criteria +"_NOT_"+httpmatch['classmatch']['classnamecondition']['type']
                        else:
                            criteria = criteria +"_"+httpmatch['classmatch']['classnamecondition']['type']
                        strings = " ".join(httpmatch['classmatch']['classnamecondition']['matchstrings'])
                        mRuleList = mRuleList + HTTPRequestCriteria + " " + criteria + " " + strings
                    elif HTTPRequestCriteria in ['parameters','headers','cookies']:
                        addNewLine = False
                        for parameter in httpmatch[HTTPRequestCriteria]:
                            if not addNewLine: addNewLine = True
                            else: mRuleList = mRuleList + "\n"
                            criteria = parameter['comparisontype']
                            strings  = "name " + parameter['name']['type'] + " " + " ".join(parameter['name']['matchstrings'])
                            if parameter['comparisontype'] == "CHECK_VALUE" and 'isnot' in parameter['value'] and parameter['value']['isnot'] == True:
                                strings = strings + " AND value NOT " + parameter['value']['type'] + " " + " ".join(parameter['value']['matchstrings'])
                            elif parameter['comparisontype'] == "CHECK_VALUE":
                                strings = strings + " AND value " + parameter['value']['type'] + " " + " ".join(parameter['value']['matchstrings'])
                            mRuleList = mRuleList + HTTPRequestCriteria + " " + criteria + " " + strings
                    else:
                        print ("HTTP Request Match criteria unknown: " + HTTPRequestCriteria)
            elif mCondition['type'] == "INSTRUMENTATION_PROBE":
                #### TO DO: POJO instrumentation parsing
                return "INSTRUMENTATION_PROBE not supported yet"
            else:
                return "Match condition "+mCondition['type']+" not implemented yet."
    elif txMatchRuleData['type'] == "AUTOMATIC_DISCOVERY":
        #### TO DO: Automatic discovery rules
        return "Automatic discovery rules not supported yet"
    else:
        return "Uknown rule type: "+txMatchRuleData['type']

    return mRuleList

###
 # toString method, extracts actions from transaction detection rule
 # @param txMatchRuleData JSON data containing transaction detection rule actions
 # @return string with a comma separated list of actions
###
def str_transactiondetection_actions(txMatchRuleData):
    httpSplit = ""
    if txMatchRuleData['type'] == "CUSTOM":
        for action in txMatchRuleData['txcustomrule']['actions']:
            if action['type'] == "HTTP_SPLIT":
                if not action['httpsplit']: # HTTPSplit definition is empty
                    continue
                elif 'httpsplitonreqdata' in action['httpsplit']:
                    if len(httpSplit) > 0: httpSplit = httpSplit + "\n"
                    httpsplitonreqdata = action['httpsplit']['httpsplitonreqdata']
                    if 'customexpression' in httpsplitonreqdata:
                        httpSplit = httpSplit + "Split Transactions using custom expression: "+httpsplitonreqdata['customexpression']['stringvalue']
                    elif 'segments' in httpsplitonreqdata:
                        if httpsplitonreqdata['segments']['type'] == "FIRST":
                            httpSplit = httpSplit + "Split Transactions using first "+str(httpsplitonreqdata['segments']['numsegments'])+" URI segments"
                        elif httpsplitonreqdata['segments']['type'] == "LAST":
                            httpSplit = httpSplit + "Split Transactions using last "+str(httpsplitonreqdata['segments']['numsegments'])+" URI segments"
                        elif httpsplitonreqdata['segments']['type'] == "SELECTED":
                            httpSplit = httpSplit + "Split Transactions using URI segments " + str(httpsplitonreqdata['segments']['selectedsegments'])
                    elif 'parametername' in httpsplitonreqdata:
                        httpSplit = httpSplit + "Split Transactions using parameter value "+httpsplitonreqdata['parametername']
                    elif 'headername' in httpsplitonreqdata:
                        httpSplit = httpSplit + "Split Transactions using header value "+httpsplitonreqdata['headername']
                    elif 'cookiename' in httpsplitonreqdata:
                        httpSplit = httpSplit + "Split Transactions using cookie value "+httpsplitonreqdata['cookiename']
                    elif 'sessionattributename' in httpsplitonreqdata:
                        httpSplit = httpSplit + "Split Transactions using session attribute value "+httpsplitonreqdata['sessionattributename']
                    elif 'usehttpmethod' in httpsplitonreqdata and httpsplitonreqdata['usehttpmethod'] == True:
                        httpSplit = httpSplit + "Split Transactions using the request method (GET/POST/PUT)"
                    elif 'usehost' in httpsplitonreqdata and httpsplitonreqdata['usehost'] == True:
                        httpSplit = httpSplit + "Split Transactions using the request host"
                    elif 'useoriginatingaddr' in httpsplitonreqdata and httpsplitonreqdata['useoriginatingaddr'] == True:
                        httpSplit = httpSplit + "Split Transactions using the request originating address"
                    else:
                        return "Request data split criteria unknown."
                elif 'httpsplitonpayload' in action['httpsplit']:
                    #### TO DO: Actions (Split Using Payload)
                    return "httpsplitonpayload not supported yet"
                else:
                    print action['httpsplit']
            elif action['type'] == "POJO_SPLIT":
                #### TO DO: POJO split
                return "POJO split not supported yet"
                pass
            else:
                return action['type']
                return action['httpsplit']
    elif txMatchRuleData['type'] == "AUTOMATIC_DISCOVERY":
        #### TO DO: Automatic discovery rules
        return "Automatic discovery rules not supported yet"
    else:
        return "Uknown rule type: "+txMatchRuleData['type']
    return httpSplit
###
 # Generate CSV output from transaction detection rules data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain transaction detection rules from local transaction detection rules dictionary
 # @param custom_detectruleDict dictionary containing transaction detection rules
 # @param fileName output file name
 # @return None
###
def generate_transactiondetection_CSV(appID_List,custom_detectruleDict=None,fileName=None):
    if appID_List is None and custom_detectruleDict is None:
        return
    elif custom_detectruleDict is None:
        custom_detectruleDict = detectionruleDict

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Name', 'Application', 'MatchRuleList', 'HttpSplit']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()


    for appID in appID_List:
        detectionRules = custom_detectruleDict[str(appID)]

        # Verify this ElementTree contains transaction detection rule data
        if detectionRules.find('rule-list') is None: return 0

        for detectrule in detectionRules.find('rule-list').findall('rule'):
            # for child in detectrule:
            #    print(child.tag, child.attrib, child.text)
            #    print ("\n")
            ruleName = detectrule.attrib['rule-name'].encode('ASCII', 'ignore')
            ruleType = detectrule.attrib['rule-type']

            if ruleType == "TX_MATCH_RULE":
                txMatchRule = detectrule.find('tx-match-rule')
                try:
                    txMatchRuleData = json.loads(txMatchRule.text)
                except:
                    matchRuleList = "Could not process JSON content"
                    httpSplit     = "Could not process JSON content"
                else:
                    matchRuleList = str_transactiondetection_matchrules(txMatchRuleData)
                    httpSplit     = str_transactiondetection_actions(txMatchRuleData)
            else:
                matchRuleList = "Uknown rule type: " + ruleType
                httpSplit     = "Uknown rule type: " + ruleType

            try:
                filewriter.writerow({'Name': ruleName,
                                     'Application': getAppName(appID),
                                     'MatchRuleList': matchRuleList,
                                     'HttpSplit': httpSplit})
            except ValueError as valError:
                print (valError)
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
def generate_transactiondetection_JSON(appID_List,custom_detectruleDict=None,fileName=None):
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
    custom_detectruleDict = {"0":root}
    if outputFormat and outputFormat == "JSON":
        generate_transactiondetection_JSON(appID_List=[0],custom_detectruleDict=custom_detectruleDict,fileName=outFilename)
    else:
        generate_transactiondetection_CSV(appID_List=[0],custom_detectruleDict=custom_detectruleDict,fileName=outFilename)

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
    if numTransactionRules == 0:
        sys.stderr.write("get_detection_rules: Could not fetch any transaction detection rules.\n")
    elif outputFormat and outputFormat == "JSON":
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