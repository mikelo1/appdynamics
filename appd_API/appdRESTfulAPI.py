#!/usr/bin/python
import requests
import json
import sys
from getpass import getpass
import time


class RESTfulAPI:
    basicAuth   = dict()
    appD_Config = None

    def __init__(self,appD_Config,basicAuth=None):
        #self._session   = None
        self.basicAuth   = basicAuth
        self.appD_Config = appD_Config

    ### TO DO: Implement sessions
#    def _get_session(self):
#        if not self._session:
#            from requests.sessions import Session
#            self._session = Session()
#            self._session.verify = self.verify
#        return self._session

    def __fetch_access_token(self,serverURL,API_username,API_password):
        """
        Fetch access token from a controller. Provide an username/password.
        :param serverURL: Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
        :param userName: Full username, including account. i.e.: myuser@customer1
        :param password: password for the specified user and host. i.e.: mypassword
        :returns: the access token string. Null if there was a problem getting the access token.
        """
        if 'DEBUG' in locals(): print ("Fetching access token for controller " + serverURL + "...")
        # https://docs.appdynamics.com/display/PRO45/API+Clients#APIClients-using-the-access-token
        response = requests.post(serverURL + "/controller/api/oauth/access_token",
                                    auth=(API_username, API_password),
                                    headers={"Content-Type": "application/vnd.appd.cntrl+protobuf", "v":"1"},
                                    data={"grant_type": "client_credentials", "client_id": API_username, "client_secret": API_password})
        if response.status_code > 399:
            sys.stderr.write("Something went wrong on HTTP request. Status:" + str(response.status_code) + " ")
            if response.content.find("<b>description</b>"):
                sys.stderr.write("Description: "+response.content[response.content.find("<b>description</b>")+18:response.content.rfind("</p>")] + "\n" )
            else:
                sys.stderr.write("Description not available\n")
            if 'DEBUG' in locals():
                print ("   header:", response.headers)
                print ("Writing content to file: response.txt")
                file1 = open("response.txt","w") 
                file1.write(response.content)
                file1.close()
            return None
        token_data = json.loads(response.content)
        return token_data

    def __get_access_token(self):
        """
        Get access token from a controller. If no credentials provided it will try to get them from basic auth file.
        :param contextName: name of context
        :returns: the access token string. Null if there was a problem getting the access token.
        """
        if self.appD_Config.get_current_context(output=None) is None:
            if 'DEBUG' in locals(): print ("Cannot get context data. Did you login to any controller machine?")
            return None

        token     = self.appD_Config.get_current_context_token()
        serverURL = self.appD_Config.get_current_context_serverURL()
        API_Client= self.appD_Config.get_current_context_user()
        if token is None:
            if 'DEBUG' in locals(): print ("Current context "+ self.appD_Config.get_current_context(output=None) + " has no valid token.")
            if self.basicAuth and len(self.basicAuth) > 0 and API_Client in self.basicAuth:
                Client_Secret = self.basicAuth[API_Client]
            elif self.appD_Config.get_credentials(self.appD_Config.get_current_context(output=None)):
                Client_Secret = self.appD_Config.get_credentials(self.appD_Config.get_current_context(output=None))
            else:
                sys.stderr.write("Authentication required for " + serverURL + "\n")
                Client_Secret = getpass(prompt='Password: ')
            API_Client= self.appD_Config.get_current_context_username()
            token_data = self.__fetch_access_token(serverURL,API_Client,Client_Secret)
            if token_data is None:
                sys.stderr.write("Authentication failed. Did you mistype the password?\n") 
                return None
            self.appD_Config.set_current_context_token(token_data['access_token'],token_data['expires_in'])
            token = token_data['access_token']
            if 'DEBUG' in locals(): print ("New token obtained for current context "+ self.appD_Config.get_current_context(output=None) + ": "+token)
        else:
            if 'DEBUG' in locals(): print ("Current context "+ self.appD_Config.get_current_context(output=None) + " has valid token: "+token)
        return token

    def __fetch_RESTfulPath(self,RESTfulPath,params=None,serverURL=None,userName=None,password=None):
        """
        Fetch RESTful Path from a controller. Either provide an username/password or let it get an access token automatically.
        :param RESTfulPath: RESTful path to retrieve data
        :param params: additional HTTP parameters (if any)
        :param serverURL: Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
        :param userName: Full username, including account. i.e.: myuser@customer1
        :param password: password for the specified user and host. i.e.: mypassword
        :returns: the response data. Null if no data was received.
        """
        if 'DEBUG' in locals(): print ("Fetching JSON from RESTful path " + RESTfulPath + " with params " + json.dumps(params) + " ...")
        if serverURL is None: serverURL = self.appD_Config.get_current_context_serverURL()
        if userName and password:
            try:
                response = requests.get(serverURL + RESTfulPath,
                                        auth=(userName, password), params=params)
            except requests.exceptions.InvalidURL:
                sys.stderr.write("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
                return None
        else:
            token = self.__get_access_token()
            if token is None: return None
            try:
                response = requests.get(serverURL + RESTfulPath,
                                    headers={"Authorization": "Bearer "+token}, params=params)
            except requests.exceptions.InvalidURL:
                sys.stderr.write("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
                return None

        if response.status_code != 200:
            sys.stderr.write("Something went wrong on HTTP request. Status:" + str(response.status_code) + " ")
            if response.content.find("<b>description</b>"):
                sys.stderr.write("Description: "+response.content[response.content.find("<b>description</b>")+18:response.content.rfind("</p>")] + "\n" )
            else:
                sys.stderr.write("Description not available\n")
            if 'DEBUG' in locals():
                print ("   header:", response.headers)
                print ("Writing content to file: response.txt")
                file1 = open("response.txt","w") 
                file1.write(response.content)
                file1.close()
            return None
        return response.content


    def __update_RESTfulPath(self,RESTfulPath,streamdata,method,headers=None,serverURL=None,userName=None,password=None):
        """
        Update data from a controller. Either provide an username/password or let it get an access token automatically.
        :param RESTfulPath: RESTful path to upload data
        :param streamdata: the data to be updated, in JSON or XML format
        :param method: HTTP method, could be either POST or PUT.
        :param headers: additional request headers. i.e: Content-Type:application/json, Accept:text/xml, ...
        :param serverURL: Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
        :param userName: Full username, including account. i.e.: myuser@customer1
        :param password: password for the specified user and host. i.e.: mypassword
        :returns: response of the update request, if request was OK. None, if request failed.
        """
        if 'DEBUG' in locals(): print ("Updating RESTful path " + RESTfulPath + " with provided stream data...")
        data = json.dumps(streamdata) if type(streamdata) is dict else streamdata
        requestMethod = requests.post if method=="POST" else requests.put
        if serverURL is None: serverURL = self.appD_Config.get_current_context_serverURL()
        if userName and password:
            try:
                response = requestMethod(serverURL + RESTfulPath, headers=headers, auth=(userName, password), data=data)
            except requests.exceptions.InvalidURL:
                sys.stderr.write ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
                return None
        else:
            token = self.__get_access_token()
            if token is None: return None
            if headers is not None: headers.update({"Authorization": "Bearer "+token})
            else: headers = {"Authorization": "Bearer "+token}
            try:
                response = requestMethod(serverURL + RESTfulPath, headers=headers, data=data)
            except requests.exceptions.InvalidURL:
                sys.stderr.write ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
                return None

        if 'DEBUG' in locals() and response.status_code > 399:
            sys.stderr.write("Something went wrong on HTTP request. Status:" + str(response.status_code) + " ")
            if response.content.find("<b>description</b>"):
                sys.stderr.write("Description: "+response.content[response.content.find("<b>description</b>")+18:response.content.rfind("</p>")] + "\n" )
            else:
                sys.stderr.write("Description not available\n")
        elif 'DEBUG' in locals():
            sys.stderr.write("HTTP request successful with status:" + str(response.status_code) + " ")
        return response

    def __import_RESTfulPath(self,RESTfulPath,filePath,method,headers=None,serverURL=None,userName=None,password=None):
        """
        Update data from a controller. Either provide an username/password or let it get an access token automatically.
        :param RESTfulPath: RESTful path to upload data
        :param filePath: path to the datasource file
        :param method: HTTP method, could be either POST or PUT.
        :param headers: additional request headers. i.e: Content-Type:application/json, Accept:text/xml, ...
        :param serverURL: Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
        :param userName: Full username, including account. i.e.: myuser@customer1
        :param password: password for the specified user and host. i.e.: mypassword
        :returns: True if the update was successful. False if no data was updated.
        """
        if 'DEBUG' in locals(): print ("Importing RESTful path " + RESTfulPath + " with provided datasource file...")
        requestMethod = requests.post if method=="POST" else requests.put
        files={'files': open(filePath,'rb')}
        if serverURL is None: serverURL = self.appD_Config.get_current_context_serverURL()
        if userName and password:
            try:
                response = requestMethod(serverURL + RESTfulPath, headers=headers, auth=(userName, password), files=files)
            except requests.exceptions.InvalidURL:
                sys.stderr.write ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
                return False
        else:
            token = self.__get_access_token()
            if token is None: return None
            if headers is not None: headers.update({"Authorization": "Bearer "+token})
            else: headers = {"Authorization": "Bearer "+token}
            try:
                response = requestMethod(serverURL + RESTfulPath, headers=headers, files=files)
            except requests.exceptions.InvalidURL:
                sys.stderr.write ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
                return False

        if response.status_code != 200:
            sys.stderr.write("Something went wrong on HTTP request. Status:" + str(response.status_code) + " ")
            if response.content.find("<b>description</b>"):
                sys.stderr.write("Description: "+response.content[response.content.find("<b>description</b>")+18:response.content.rfind("</p>")] + "\n" )
            else:
                sys.stderr.write("Description not available\n")
            if 'DEBUG' in locals():
                print ("   header:", response.headers)
                print (response.content)
            return False
        return True


       ###### FROM HERE PUBLIC FUNCTIONS ######


    def fetch_applicationsAllTypes(self):
        """
        Fetch applications from a controller.
        :returns: the fetched data. Null if no data was received.
        """
        restfulPath = "/controller/restui/applicationManagerUiBean/getApplicationsAllTypes"
        return self.__fetch_RESTfulPath(restfulPath)

    def fetch_applications(self):
        """
        Fetch applications from a controller.
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve All Business Applications
        # GET /controller/rest/applications
        restfulPath = "/controller/rest/applications/"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_application(self,appKey):
        """
        Fetch application from a controller.
        :param appKey: name or ID number of the application to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve a specific Business Application
        # GET /controller/rest/applications/application_name
        restfulPath = "/controller/rest/applications/" + str(appKey)
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_tiers(self,appKey):
        """
        Fetch tiers for an application.
        :param appKey: name or ID number of the application to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve All Tiers in a Business Application
        # GET /controller/rest/applications/application_name/tiers
        restfulPath = "/controller/rest/applications/" + str(appKey) + "/tiers"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_tier_nodes(self,appKey,tierKey):
        """
        Fetch nodes for an application
        :param appKey: name or ID number of the application to fetch nodes
        :param tierName: name or ID of the tier to fetch nodes
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve Node Information for All Nodes in a Tier
        # GET /controller/rest/applications/application_name/tiers/tier_name/nodes
        restfulPath = "/controller/rest/applications/" + str(appKey) + "/tiers/" + str(tierKey) + "/nodes"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_nodes(self,app_ID,selectors=None):
        """
        Fetch application nodes from a controller
        :param app_ID: the ID number of the nodes to fetch
        :param selectors: fetch only nodes filtered by specified selectors
        :returns: the number of fetched nodes. Zero if no node was found.
        """
        # Retrieve Node Information for All Nodes in a Business Application
        # GET /controller/rest/applications/application_name/nodes
        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/nodes"
        params = {"output": "JSON"}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_node_by_ID(self,app_ID,node_ID):
        """
        Fetch node details from a controller.
        :param app_ID: the ID number of the application nodes to fetch
        :param node_ID: the ID number of the node to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve Node Information by Node Name
        # GET /controller/rest/applications/application_name/nodes/node_name
        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/nodes/" + str(node_ID)
        return self.__fetch_RESTful_JSON(restfulPath)

    def fetch_agent_status(self,nodeList,start_epoch,end_epoch):
        """
        Fetch agent status from a controller.
        :param nodeList: a list of node IDs to fetch agent status
        :param start_epoch: the time range start time in unix epoch format
        :param end_epoch: the time range end time in unix epoch format
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve app and machine agent status by Rest API
        # POST /controller/restui/v1/nodes/list/health/ids
        # BODY {"requestFilter":[<comma seperated list of node id's>],"resultColumns":["LAST_APP_SERVER_RESTART_TIME","VM_RUNTIME_VERSION","MACHINE_AGENT_STATUS","APP_AGENT_VERSION","APP_AGENT_STATUS","HEALTH"],"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[],"timeRangeStart":<start_time>,"timeRangeEnd":<end_time>}
        restfulPath= "/controller/restui/v1/nodes/list/health/ids"
        params     = {"requestFilter":nodeList,"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[],
                      "resultColumns":["APP_AGENT_STATUS","HEALTH"],
                      "timeRangeStart":start_epoch,"timeRangeEnd":end_epoch}
        response = self.__update_RESTfulPath(restfulPath,streamdata=params,method="POST",headers={"Content-Type": "application/json","Accept": "application/json"})
        return response.content if response.status_code < 400 else None

    def mark_nodes_as_historical(self,nodeList):
        """
        Mark nodes as historical
        @source https://docs.appdynamics.com/display/PRO45/Configuration+API#ConfigurationAPI-MarkNodesasHistorical
        :param nodeList: the list of node IDs to be maked as historical
        :returns: the fetched data. Null if no data was received.
        """
        # Mark Nodes as Historical.Pass one or more identifiers of the node to be marked as historical, up to a maximum of 25 nodes.
        # POST /controller/rest/mark-nodes-historical?application-component-node-ids=value
        nodeList_str = ','.join(map(lambda x: str(x),nodeList))
        restfulPath= "/controller/rest/mark-nodes-historical?application-component-node-ids="+nodeList_str
        response = self.__update_RESTfulPath(restfulPath,streamdata="",method="POST",headers={"Content-Type": "application/json","Accept": "application/json"})
        return response.content if response.status_code < 400 else None

    def fetch_transactiondetection(self,app_ID,selectors=None):
        """
        Fetch transaction detection rules from a controller.
        :param app_ID: the ID number of the detection rules to fetch
        :param selectors: fetch only snapshots filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # Export Transaction Detection Rules for All Entry Point Types
        # GET /controller/transactiondetection/application_id/[tier_name/]rule_type
        # https://docs.appdynamics.com/display/PRO45/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportTransactionDetectionRulesExportTransactionDetectionRules
        restfulPath = "/controller/transactiondetection/" + str(app_ID) + "/custom"
        params = {"output": "XML"}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def import_transactiondetection(self,app_ID,filePath):
        """
        Import application transaction detection rules to a controller.
        :param app_ID: the ID number of the application where to import transaction detection rules
        :param filePath: path to the datasource file
        :returns: the fetched data. Null if no data was received.
        """
        # Import automatic detection rules in XML format
        # POST /controller/transactiondetection/application_id/[scope_name]/rule_type/[entry_point_type]/[rule_name] -F file=@exported_file_name.xml
        # https://docs.appdynamics.com/display/PRO45/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ImportTransactionDetectionRules
        restfulPath = "/controller/transactiondetection/" + str(app_ID) + "/custom?overwrite=true"
        return self.__import_RESTfulPath(restfulPath,method="POST",filePath=filePath)

    def fetch_business_transactions(self,app_ID,selectors=None):
        """
        Fetch application business transactions from a controller.
        :param app_ID: the ID number of the application business transactions to fetch
        :param selectors: fetch only business transactions filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve All Business Transactions in a Business Application
        # GET /controller/rest/applications/application_name/business-transactions
        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/business-transactions"
        params = {"output": "JSON"}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_backends(self,app_ID,selectors=None):
        """
        Fetch application backends from a controller.
        :param app_ID: the ID number of the application backends to fetch
        :param selectors: fetch only backends filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve All Registered Backends in a Business Application With Their Properties
        # GET /controller/rest/applications/application_name/backends
        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/backends"
        params = {"output": "JSON"}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)


    def fetch_entrypoints_TierRules(self,tier_ID,selectors=None):
        """
        Fetch tier entrypoints from a controller.
        :param tier_ID: the ID number of the tier endpoints to fetch
        :param selectors: fetch only endpoints filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        #GetAPMSEPTierRules
        restfulPath = "/controller/restui/serviceEndpoint/getAll"
        data = {"agentType": "APP_AGENT","attachedEntity": {"entityId": tier_ID,"entityType": "APPLICATION_COMPONENT"} }
        if selectors: params.update(selectors)
        return self.__update_RESTfulPath(restfulPath,streamdata=data,method="POST",headers={"Content-Type": "application/json","Accept": "application/json"})

    def fetch_health_rules_XML(self,app_ID,selectors=None):
        """
        Fetch health rules from a controller - Using the legacy API call
        :param app_ID: the ID number of the health rules to fetch
        :param selectors: fetch only health rules filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # Export Health Rules from an Application
        # GET /controller/healthrules/application_id?name=health_rule_name
        restfulPath = "/controller/healthrules/" + str(app_ID)
        params = {"output": "XML"}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_health_rules_JSON(self,app_ID,selectors=None):
        """
        Fetch health rules from a controller - Using the RESTUI API call
        :param app_ID: the ID number of the health rules to fetch
        :param selectors: fetch only health rules filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        restfulPath = "/controller/restui/policy2/policies/" + str(app_ID)
        params = {"Content-Type": "application/json","resultColumns": ["LAST_APP_SERVER_RESTART_TIME", "VM_RUNTIME_VERSION", "MACHINE_AGENT_STATUS", "APP_AGENT_VERSION", "APP_AGENT_STATUS", "HEALTH"]}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_health_rule_by_ID(self,app_ID,entityID):
        """
        Fetch health rules from a controller - Using the new API call
        :param app_ID: the ID number of the health rules to fetch
        :param entityID: the ID number of the health rule to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve complete details of the health rule for the specified application ID
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/health-rules/{health-rule-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/health-rules/" + str(entityID)
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def import_health_rules_XML(self,app_ID,filePath):
        """
        Import application healthrules to a controller.
        :param app_ID: the ID number of the application where to import healthrules
        :param filePath: path to the datasource file
        :returns: the fetched data. Null if no data was received.
        """
        # Import Health Rules into an Application
        # You can import health rules defined in an XML file into a business application.
        # POST /controller/healthrules/application_id?overwrite=true_or_false
        restfulPath = "/controller/healthrules/" + str(app_ID) + "?overwrite=true"
        return self.__import_RESTfulPath(restfulPath,method="POST",filePath=filePath)

    def update_health_rule(self,app_ID,healthrule_ID,healthruleJSON):
        """
        Update application healthrule from a controller. Provide either an username/password or an access token.
        :param app_ID: the ID number or name of the application where to update the healthrule
        :param healthrule_ID: the ID number of the healthrule to update
        :param healthruleJSON: the JSON data of the healthrule to update
        :returns: the fetched data. Null if no data was received.
        """
        # Updates an existing health rule (required fields) with details from the specified health rule ID. See Property Details
        # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/health-rules/{health-rule-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/health-rules/" + str(healthrule_ID)
        return self.__update_RESTful_JSON(restfulPath,streamdata=healthruleJSON,method="PUT",headers={"Content-Type": "application/json"})

    def fetch_policies(self,app_ID):
        """
        Fetch application policies from a controller - Using the new API call
        :param app_ID: the ID number of the application policies to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve a list of Policies associated with an Application
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_policy_by_ID(self,app_ID,policy_ID):
        """
        Fetch policy details from a controller.
        :param app_ID: the ID number of the application policies to fetch
        :param policy_ID: the ID number of the policy to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve Details of a Specified Policy
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies/{policy-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies/" + str(policy_ID)
        return self.__fetch_RESTfulPath(restfulPath)

    def fetch_policies_legacy(self,app_ID,selectors=None):
        """
        Fetch application policies from a controller - Using the legacy API call
        :param app_ID: the ID number of the application policies to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportPolicies
        # export policies to a JSON file.
        # GET /controller/policies/application_id
        restfulPath = "/controller/policies/" + str(app_ID)
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_actions(self,app_ID):
        """
        Fetch application actions from a controller - Using the new API call
        :param app_ID: the ID number of the application actions to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve a List of Actions for a Given Application
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_action_by_ID(self,app_ID,action_ID):
        """
        Fetch action details from a controller.
        :param app_ID: the ID number of the application actions to fetch
        :param action_ID: the ID number of the action to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve Details of a Specified Action
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions/{action-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions/" + str(action_ID)
        return self.__fetch_RESTfulPath(restfulPath)

    def fetch_actions_legacy(self,app_ID,selectors=None):
        """
        Fetch application actions from a controller - Using the legacy API call
        :param app_ID: the ID number of the application actions to fetch
        :param selectors: fetch only actions filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportActionsfromanApplication
        # Exports all actions in the specified application to a JSON file.
        # GET /controller/actions/application_id
        restfulPath = "/controller/actions/" + str(app_ID)
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_schedules(self,app_ID,selectors=None):
        """
        Fetch application schedules from a controller then add them to the policies dictionary. Provide either an username/password or an access token.
        :param app_ID: the ID number or name of the application schedules to fetch
        :param selectors: fetch only snapshots filtered by specified selectors
        :returns: the number of fetched schedules. Zero if no schedule was found.
        """
        if type(app_ID) is str: app_ID = ApplicationDict().getAppID(app_ID)
        # Retrieve a List of Schedules for a Given Application
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_schedule_by_ID(self,app_ID,schedule_ID):
        """
        Fetch schedule details from a controller.
        :param app_ID: the ID number of the application schedule to fetch
        :param schedule_ID: the ID number of the schedule to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve the Details of a Specified Schedule with a specified ID
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(schedule_ID)
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def create_schedule(self,app_ID,dataJSON):
        """
        Update application schedule from a controller. Provide either an username/password or an access token.
        :param app_ID: the ID number or name of the application where to update the schedule
        :param entity_ID: the ID number of the schedule to update
        :param dataJSON: the JSON data of the schedule to update
        :returns: True if schedule was created. False otherwise.
        """
        # Creates a new schedule with the specified JSON payload
        # POST <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/"
        response = self.__update_RESTfulPath(restfulPath,streamdata=dataJSON,method="POST",headers={"Content-Type": "application/json"})
        return response is not None and response.status_code == 201

    def update_schedule(self,app_ID,entity_ID,dataJSON):
        """
        Update application schedule from a controller. Provide either an username/password or an access token.
        :param app_ID: the ID number or name of the application where to update the schedule
        :param entity_ID: the ID number of the schedule to update
        :param dataJSON: the JSON data of the schedule to update
        :returns: the fetched data. Null if no data was received.
        """
        # Updates an existing schedule with a specified JSON payload
        # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(entity_ID)
        response = self.__update_RESTfulPath(restfulPath,streamdata=dataJSON,method="PUT",headers={"Content-Type": "application/json"})
        return response is not None and response.status_code == 200

    def fetch_metric_hierarchy(self,app_ID,metric_path):
        """
        Fetch metrics hierarchy from a controller.
        :param app_ID: the ID number of the application metrics to fetch
        :param metric_path: The path to the metric in the metric hierarchy.
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve Metric Hierarchy
        # GET /controller/rest/applications/application_name/metrics
        restfulPath = "/controller/rest/applications/"+ str(app_ID) + "/metrics"
        params.update({'metric-path': metric_path,'output':'JSON'})
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_metric_data(self,app_ID,metric_path,time_range_type,duration=None,startEpoch=None,endEpoch=None):
        """
        Fetch metric data from a controller.
        :param app_ID: the ID number of the application metrics to fetch
        :param metric_path: The path to the metric in the metric hierarchy.
        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
        :param duration: duration in minutes
        :param startEpoch: range start time in Unix Epoch format
        :param endEpoch: range end time in Unix Epoch format
        :param selectors: fetch only errors filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        MAX_RESULTS="9999"
        # Retrieve Metric Data
        # GET /controller/rest/applications/application_name/metric-data
        restfulPath = "/controller/rest/applications/"+ str(app_ID) + "/metric-data"
        if time_range_type == "BEFORE_NOW" and duration is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration}
        elif time_range_type == "BEFORE_TIME" and duration is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"end-time": endEpoch}
        elif time_range_type == "AFTER_TIME" and duration is not None and startEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"start-time": startEpoch}
        elif time_range_type == "BETWEEN_TIMES" and startEpoch is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"start-time": startEpoch,"end-time": endEpoch}
        else:
            return None
        params.update({'metric-path': metric_path,'rollup': True,'output':'JSON'})
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_healthrule_violations(self,app_ID,time_range_type,duration=None,startEpoch=None,endEpoch=None,selectors=None):
        """
        Fetch healtrule violations from a controller.
        :param app_ID: the ID number of the application healtrule violations to fetch
        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
        :param duration: duration in minutes
        :param startEpoch: range start time in Unix Epoch format
        :param endEpoch: range end time in Unix Epoch format
        :param selectors: fetch only events filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # https://docs.appdynamics.com/display/PRO45/Events+and+Action+Suppression+API
        # Retrieve All Health Rule Violations that have occurred in an application within a specified time frame. 
        # URI /controller/rest/applications/application_id/problems/healthrule-violations
        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/problems/healthrule-violations"
        if time_range_type == "BEFORE_NOW" and duration is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"output": "JSON"}
        elif time_range_type == "BEFORE_TIME" and duration is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"end-time": endEpoch,"output": "JSON"}
        elif time_range_type == "AFTER_TIME" and duration is not None and startEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"start-time": startEpoch,"output": "JSON"}
        elif time_range_type == "BETWEEN_TIMES" and startEpoch is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"start-time": startEpoch,"end-time": endEpoch,"output": "JSON"}
        else:
            return None
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_snapshots(self,app_ID,time_range_type,duration=None,startEpoch=None,endEpoch=None,selectors=None):
        """
        Fetch snapshot from a controller.
        :param app_ID: the ID number of the application healtrule violations to fetch
        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
        :param duration: duration in minutes
        :param startEpoch: range start time in Unix Epoch format
        :param endEpoch: range end time in Unix Epoch format
        :param selectors: fetch only events filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        MAX_RESULTS="9999"
        #Retrieve Transaction Snapshots
        # GET /controller/rest/applications/application_name/request-snapshots
        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"
        if time_range_type == "BEFORE_NOW" and duration is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"output": "JSON"}
        elif time_range_type == "BEFORE_TIME" and duration is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"end-time": endEpoch,"output": "JSON"}
        elif time_range_type == "AFTER_TIME" and duration is not None and startEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"start-time": startEpoch,"output": "JSON"}
        elif time_range_type == "BETWEEN_TIMES" and startEpoch is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"start-time": startEpoch,"end-time": endEpoch,"output": "JSON"}
        else:
            return None
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_errors(self,app_ID,tier_ID,time_range_type,duration=None,startEpoch=None,endEpoch=None,selectors=None):
        """
        Fetch errors from a controller.
        :param app_ID: the ID number of the application errors to fetch
        :param tier_ID: the ID number of the application tier errors to fetch
        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
        :param duration: duration in minutes
        :param startEpoch: range start time in Unix Epoch format
        :param endEpoch: range end time in Unix Epoch format
        :param selectors: fetch only errors filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        MAX_RESULTS="9999"
        # "controller/rest/applications/{applicationName}/metrics?metric-path=Errors|{tierName}&time-range-type=BEFORE_NOW&duration-in-mins=15&output=JSON"
        restfulPath = "/controller/rest/applications/"+ str(app_ID) + "/metric-data"#?metric-path=Errors%7CAPIManager%7CSocketException%7CErrors per Minute&time-range-type=BEFORE_NOW&duration-in-mins=60"
        if time_range_type == "BEFORE_NOW" and duration is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration}
        elif time_range_type == "BEFORE_TIME" and duration is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"end-time": endEpoch}
        elif time_range_type == "AFTER_TIME" and duration is not None and startEpoch is not None:
            params={"time-range-type": time_range_type,"duration-in-mins": duration,"start-time": startEpoch}
        elif time_range_type == "BETWEEN_TIMES" and startEpoch is not None and endEpoch is not None:
            params={"time-range-type": time_range_type,"start-time": startEpoch,"end-time": endEpoch}
        else:
            return None
        params.update({"metric-path":"Errors|"+str(tier_ID)+"|*|Errors per Minute",'rollup': True,"output":"JSON"})
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_dashboards(self,selectors=None):
        """
        Fetch dashboards from a controller.
        :param selectors: fetch only dashboards filtered by specified selectors
        :returns: the fetched data. Null if no data was received.
        """
        # Export the list of all Custom Dashboards
        # https://community.appdynamics.com/t5/Dashboards/How-to-export-the-list-of-all-Custom-Dashboards-in-the/td-p/30083
        # HTTP call: /controller/restui/dashboards/getAllDashboardsByType/false
        restfulPath = "/controller/restui/dashboards/getAllDashboardsByType/false"
        params = {"output": "JSON"}
        if selectors: params.update(selectors)
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_dashboard_by_ID(self,dashboard_id):
        """
        Fetch custom dashboards from a controller.
        :param dashboard_id: the ID number of the dashboards to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Export Custom Dashboards and Templates
        # GET /controller/CustomDashboardImportExportServlet?dashboardId=dashboard_id
        restfulPath = "/controller/CustomDashboardImportExportServlet?dashboardId=" + str(dashboard_id)
        return self.__fetch_RESTfulPath(restfulPath)


    def fetch_configuration(self,selectors=None):
        """
        Fetch config from a controller.
        :param selectors: fetch specific configuration filtered by specified configuration name
        :returns: the fetched data. Null if no data was received.
        """
        # Retrieve All Controller Settings
        # GET <controller_url>/controller/rest/configuration
        restfulPath = "/controller/rest/configuration"
        params = {"output": "JSON"}
        if selectors: restfulPath = restfulPath + "?name=" + selectors
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_users(self,selectors=None):
        """
        Fetch users from a controller.
        :param selectors: fetch specific user filtered by specified user name or ID
        :returns: the fetched data. Null if no data was received.
        """
        # Get All Users
        # GET <controller_url>/controller/rest/users
        restfulPath = "/controller/api/rbac/v1/users"
        params = {"output": "JSON"}
        if selectors: restfulPath = restfulPath + selectors
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_users_extended(self):
        """
        Fetch users with extended info from a controller.
        :returns: the fetched data. Null if no data was received.
        """
        restfulPath = "/controller/restui/userAdministrationUiService/users"
        params = {"output": "JSON"}
        return self.__fetch_RESTfulPath(restfulPath,params=params)

    def fetch_user_by_ID(self,userID):
        """
        Fetch specific user from a controller.
        :param userID: the ID number of the user to fetch
        :returns: the fetched data. Null if no data was received.
        """
        # Get User by ID
        # GET /controller/api/rbac/v1/users/userId
        restfulPath = "/controller/api/rbac/v1/users/" + str(userID)
        return self.__fetch_RESTfulPath(restfulPath)

    def get_controller_version(self):
        """
        Get the controller version. Either provide an username/password or let it get an access token automatically.
        :returns: the controller release version number. Null if no data was received.
        """
        # Retrieve All Controller Settings
        # GET /controller/rest/configuration
        restfulPath = "/controller/rest/configuration",
        params={"name": "schema.version","output": "JSON"}
        response = self.__fetch_RESTfulPath(restfulPath)
        if response is not None:
            schemaVersion = json.loads(response.content)
            return schemaVersion[0]['value'].replace("-","")
