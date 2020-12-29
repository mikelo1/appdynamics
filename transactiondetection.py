#!/usr/bin/python
import xml.etree.ElementTree as ET
import json
import csv
import sys
from applications import ApplicationDict
from entities import AppEntity

class DetectionruleDict(AppEntity):
    detectionruleDict = dict()

    def __init__(self):
        self.detectionruleDict = self.entityDict

    ###
     # toString private method, extracts Match Rule List from transaction detection rule
     # @param txMatchRuleData JSON data containing match rules
     # @return string with a comma separated list of Match Rules
    ###
    def __str_transactiondetection_matchrules(self,txMatchRuleData):
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
     # toString private method, extracts actions from transaction detection rule
     # @param txMatchRuleData JSON data containing transaction detection rule actions
     # @return string with a comma separated list of actions
    ###
    def __str_transactiondetection_actions(self,txMatchRuleData):
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

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from transaction detection rules data
     # @param appID_List list of application IDs, in order to obtain transaction detection rules from local transaction detection rules dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
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
        fieldnames = ['Name', 'Application', 'MatchRuleList', 'HttpSplit']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.detectionruleDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue        
            detectionRules = self.detectionruleDict[str(appID)]

            # Verify this ElementTree contains transaction detection rule data
            if detectionRules.find('rule-list') is None: continue
            elif 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True

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
                        matchRuleList = self.__str_transactiondetection_matchrules(txMatchRuleData)
                        httpSplit     = self.__str_transactiondetection_actions(txMatchRuleData)
                else:
                    matchRuleList = "Uknown rule type: " + ruleType
                    httpSplit     = "Uknown rule type: " + ruleType

                try:
                    filewriter.writerow({'Name': ruleName,
                                         'Application': ApplicationDict().getAppName(appID),
                                         'MatchRuleList': matchRuleList,
                                         'HttpSplit': httpSplit})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)

        if fileName is not None: csvfile.close()

    ###
     # Generate JSON output from transaction detection rules data
     # @param appID_List list of application IDs, in order to obtain transaction detection rules from local transaction detection rules dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,appID_List,fileName=None):
        print "generate_transactiondetection_JSON: feature not implemented yet."
    # TODO: generate JSON output format

    ###
     # Load transaction detection rules from a stream data in XML format.
     # @param streamdata the stream data in JSON format
     # @param appID the ID number of the application where to load the detection rules data.
     # @return the number of loaded detection rules. Zero if no detection rule was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            root = ET.fromstring(streamdata)
        except TypeError as error:
            print ("load_transaction_detection: "+str(error))
            return 0
        # Add loaded detection rules to the transaction detection rules dictionary
        if str(appID) in self.detectionruleDict:
            # Merge new and existing detection rules
            for new_rule in root.find("rule-list"):
                self.detectionruleDict[str(appID)].find("rule-list").append(new_rule)
        else:
            # Add loaded detection rules to the detectrules dictionary
            self.detectionruleDict.update({str(appID):root})
        return len(root.find("rule-list").getchildren())

    ###
     # Get transaction detection rules matching a given URL. Fetch transaction detection data if not loaded yet.
     # @param app_ID the ID of the application
     # @return a list of transaction detection names.
    ###
    def get_transactiondetections_matching_URL(self,app_ID,URL):
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