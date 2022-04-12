import requests
import json
import sys
from getpass import getpass
import time
#from requests_toolbelt.utils import dump


class RESTfulAPI:
    basicAuth   = dict()
    appD_Config = None
    target = {

        'ApplicationDict':  {'fetch':    {  'RESTfulPath': '/controller/restui/applicationManagerUiBean/getApplicationsAllTypes',
                                            'method': requests.get, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'apmApplications' }
                            },

        'DashboardDict':    {'fetch':    {  'RESTfulPath': '/controller/restui/dashboards/getAllDashboardsByType/false',
                                            'method': requests.get, 'headers': {}, 'params': {"output": "JSON"}, 'data': '', 'keyword': 'widgets' },
                             'fetchByID':{  'RESTfulPath': '/controller/CustomDashboardImportExportServlet?dashboardId={entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'widgetTemplates' },
                             'import':   {  'RESTfulPath': '/controller/CustomDashboardImportExportServlet',
                                            'method': requests.post, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'widgetTemplates' }
                            },

        'ConfigurationDict':{'fetch':    {  'RESTfulPath': '/controller/rest/configuration',
                                            'method': requests.get, 'headers': {}, 'params': {"output": "JSON"}, 'data': '', 'keyword': 'updateable' }
                            },

        'RBACDict':         {'fetch':    {  'RESTfulPath': '/controller/restui/userAdministrationUiService/users',
                                            'method': requests.get, 'headers': {}, 'params': {"output": "JSON"}, 'data': '', 'keyword': 'securityProviderType' },
                             'fetchByID':{  'RESTfulPath': '/controller/api/rbac/v1/users/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'security_provider_type' }
                            },

        'AccountDict':      {'fetch':    {  'RESTfulPath': '/controller/restui/licenseRule/getAllLicenseModuleProperties',
                                            'method': requests.post, 'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'}, 'params': {},
                                            'data': '{{"type": "BEFORE_NOW","durationInMinutes": 5}}', 'keyword': 'usageType' }
                            },

        'TierDict':         {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/tiers',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'numberOfNodes' },
                             'fetchByID':{  'RESTfulPath': '/controller/rest/applications/{app_ID}/tiers/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'numberOfNodes' }
                            },

        'NodeDict':         {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/nodes',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'nodeUniqueLocalId' },
                             'fetchByID':{  'RESTfulPath': '/controller/rest/applications/{app_ID}/nodes/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'nodeUniqueLocalId' }
                            },

        'DetectionruleDict':{'fetch':    {  'RESTfulPath': '/controller/transactiondetection/{app_ID}/custom',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'XML'}, 'data': '', 'keyword': 'rule-list' },
                             'import':   {  'RESTfulPath': '/controller/transactiondetection/{app_ID}/custom?overwrite=true',
                                            'method': requests.post, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'rule-list' }
                            },

        'BusinessTransactionDict':{'fetch':{'RESTfulPath': '/controller/rest/applications/{app_ID}/business-transactions',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'entryPointType' }
                            },

        'BackendDict':      {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/backends',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'exitPointType' }
                            },

        'EntrypointDict':   {'fetchByID':{  'RESTfulPath': '/controller/restui/serviceEndpoint/getAll',
                                            'method': requests.post, 'headers': {"Content-Type": "application/json","Accept": "application/json"}, 'params': {},
                                            'data': '{{"agentType": "APP_AGENT","attachedEntity": {{"entityId": {entity_ID},"entityType": "APPLICATION_COMPONENT"}} }}',
                                            'keyword': 'hierarchicalConfigKey'
                                         }
                            },

        'HealthRuleDict':   {'fetch':    {  'RESTfulPath': '/controller/restui/policy2/policies/{app_ID}',
                                            'method': requests.get, 'headers': {},
                                            'params': {"Content-Type": "application/json","resultColumns":
                                                ["LAST_APP_SERVER_RESTART_TIME", "VM_RUNTIME_VERSION", "MACHINE_AGENT_STATUS", "APP_AGENT_VERSION", "APP_AGENT_STATUS", "HEALTH"] },
                                            'data': '', 'keyword': 'affectedEntityDefinitionRule' },
                             #'fetchList':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/health-rules',
                             #               'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '' },
                             'fetchByID':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/health-rules/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'affects' },
                             'create':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/health-rules',
                                            'method': requests.post, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'affects' },
                             'update':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/health-rules/{entity_ID}',
                                            'method': requests.put, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'affects' },
                             'import':   {  'RESTfulPath': '/controller/healthrules/{app_ID}?overwrite=true',
                                            'method': requests.post, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'health-rules' }
                            },

        'PolicyDict':       {'fetch':    {  'RESTfulPath': '/controller/policies/{app_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'reactorType' },
                             #'fetchList':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/policies',
                             #               'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '' },
                             'fetchByID':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/policies/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'executeActionsInBatch' },
                             'create':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/policies',
                                            'method': requests.post, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'executeActionsInBatch' },
                             'update':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/policies/{entity_ID}',
                                            'method': requests.put, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'executeActionsInBatch' },
                             'import':   {  'RESTfulPath': '/controller/policies/{app_ID}?overwrite=true',
                                            'method': requests.post, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'reactorType' }
                            },

        'ActionDict':       {'fetch':    {  'RESTfulPath': '/controller/actions/{app_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'actionType' },
                             #'fetchList':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/actions',
                             #               'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'actionType' },
                             'fetchByID':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/actions/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'actionType' },
                             'create':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/actions',
                                            'method': requests.post, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'actionType' },
                             'update':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/actions/{entity_ID}',
                                            'method': requests.put, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'actionType' },
                             'import':   {  'RESTfulPath': '/controller/actions/{app_ID}?overwrite=true',
                                            'method': requests.post, 'headers': {}, 'params': {}, 'data': '', 'keyword': 'actionType' }
                            },

        'ScheduleDict':     {'fetch':    {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/schedules',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'timezone' },
                             #'fetchList':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/schedules',
                             #               'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '' },
                             'fetchByID':{  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/schedules/{entity_ID}',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'scheduleConfiguration' },
                             'create':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/schedules/',
                                            'method': requests.post, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'scheduleConfiguration' },
                             'update':   {  'RESTfulPath': '/controller/alerting/rest/v1/applications/{app_ID}/schedules/{entity_ID}',
                                            'method': requests.put, 'headers': {'Content-Type': 'application/json'}, 'params': {}, 'data': '{streamdata}', 'keyword': 'scheduleConfiguration' }
                            },

        'SnapshotDict':     {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/request-snapshots',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'snapshotExitCalls' }
                            },

        'EventDict':        {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/problems/healthrule-violations',
                                            'method': requests.get, 'headers': {}, 'params': {'output': 'JSON'}, 'data': '', 'keyword': 'affectedEntityDefinition' }
                            },

        'MetricDict':       {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/metric-data',
                                            'method': requests.get, 'headers': {}, 'params': {'metric-path': '{metric_path}','rollup': True,'output': 'JSON'}, 'data': '',
                                            'keyword': 'metricPath' }
                            },

        'ErrorDict':        {'fetch':    {  'RESTfulPath': '/controller/rest/applications/{app_ID}/metric-data',
                                            'method': requests.get, 'headers': {}, 'params': {'metric-path': 'Errors|{entity_ID}|*|Errors per Minute','rollup': True,'output': 'JSON'},
                                            'data': '', 'keyword': 'metricPath' }
                            }
    }
    time_range = {  "BEFORE_NOW":   {"time-range-type": "BEFORE_NOW","duration-in-mins": "{duration}"},
                    "BEFORE_TIME":  {"time-range-type": "BEFORE_TIME","duration-in-mins": "{duration}","end-time": "{endEpoch}"},
                    "AFTER_TIME":   {"time-range-type": "AFTER_TIME","duration-in-mins": "{duration}","start-time": "{startEpoch}"},
                    "BETWEEN_TIMES":{"time-range-type": "BETWEEN_TIMES","start-time": "{startEpoch}","end-time": "{endEpoch}"}
                 }

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

        try:
            response = requests.post(serverURL + "/controller/api/oauth/access_token",
                                    auth=(API_username, API_password),
                                    headers={"Content-Type": "application/vnd.appd.cntrl+protobuf", "v":"1"},
                                    data={"grant_type": "client_credentials", "client_id": API_username, "client_secret": API_password})
        except (requests.exceptions.InvalidURL,requests.exceptions.ConnectionError) as error:
            sys.stderr.write("fetch_access_token: "+str(error)+"\n")
            #if 'DEBUG' in locals(): print(dump.dump_all(response).decode("utf-8"))
            return None

        if response.status_code > 399:
            sys.stderr.write("Something went wrong on HTTP request.\n   Status:" + str(response.status_code) + "\n   Header:"+ str(response.headers) + "\n")
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


    def __do_request(self,reqFunction,url,params,data,headers,files,auth):
        """
        Send a request to a RESTful Path from a controller
        :param reqFunction: request function to be executed. Could be one of these: "requests.get", "requests.post", "request.put"
        :param url: URL for the new Request object.
        :param params: (optional) Dictionary, list of tuples or bytes to send in the query string for the Request.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like object to send in the body of the Request.
        :param headers: (optional) Dictionary of HTTP Headers to send with the Request.
        :param files: (optional) Dictionary of 'name': file-like-objects (or {'name': file-tuple}) for multipart encoding upload
        :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
        :returns: the response data. Null if no data was received.
        """
        #DEBUG=True
        try:
            response = reqFunction(url=url,auth=auth,params=params,headers=headers,data=data,files=files)
            #if 'DEBUG' in locals(): print(dump.dump_all(response).decode("utf-8"))
        except requests.exceptions.InvalidURL:
            sys.stderr.write("Invalid URL: " + url + ". Do you have the right controller hostname and RESTful path?\n")
            return None

        if response.status_code > 399:
            sys.stderr.write("[Warn] Something went wrong on HTTP request. Status:" + str(response.status_code) + "\n")
            content = str(response.content)
            message_start = content.find('<b>message</b>')
            if message_start >= 0:
                message_end = content.find("</p>",message_start)
                sys.stderr.write("Message: "+content[message_start+14:message_end] + "\n" )
            description_start = content.find('<b>description</b>')
            if description_start >= 0:
                description_end = content.find("</p>",description_start)
                sys.stderr.write("Description: "+content[description_start+18:description_end] + "\n" )
            elif message_start < 0 and description_start < 0:
                sys.stderr.write(content)
            return None
            if 'DEBUG' in locals(): sys.stderr.write("\nurl: "+str(url)+"\nauth: "+str(auth)+"\nparams: "+str(params)+"\nheaders: "+str(headers)+"\ndata: "+str(data)+"\nfiles:"+str(files)+"\n")
        elif 'DEBUG' in locals():
            sys.stderr.write("HTTP request successful with status:" + str(response.status_code) + "\n")
        return response.content if response.content else response.status_code

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def send_request(self,entityType,verb,**kwargs):
        """
        Send a request to a RESTful Path from a controller. Either provide an username/password or let it get an access token automatically.
        :param entityType: Type of entity to be sent a request
        :param verb: Method to use in the request
        :param app_ID: (optional) the ID number of the application entities to do the request.
        :param entity_ID: (optional) the ID number of the entity to do the request
        :param streamdata: (optional) the stream data in JSON format
        :param filePath: (optional) the path to the file where data is stored
        :param selectors: (optional) send request to only entities filtered by specified selectors
        :param time-range-type: (optional) could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
        :param duration-in-mins: (optional) duration in minutes
        :param start-time: (optional) range start time in Unix Epoch format
        :param end-time: (optional) range end time in Unix Epoch format
        :param serverURL: (optional) Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
        :param userName: (optional) Full username, including account. i.e.: myuser@customer1
        :param password: (optional) password for the specified user and host. i.e.: mypassword
        :returns: the response data. Null if no data was received.
        """
        #DEBUG=True
        # Get parameters from 'kwargs' keyworded variable-length argument list
        app_ID       = str(kwargs['app_ID']) if 'app_ID' in kwargs and type(kwargs['app_ID']) is int else kwargs['app_ID'] if 'app_ID' in kwargs and type(kwargs['app_ID']) is str else ""
        entity_ID    = str(kwargs['entity_ID']) if 'entity_ID' in kwargs else ""
        streamdata   = json.dumps(kwargs['streamdata']) if 'streamdata' in kwargs and type(kwargs['streamdata']) is dict else kwargs['streamdata'] if 'streamdata' in kwargs else ""

        # Variable substitution in URL segments, request data and params
        urlSegments  = self.target[entityType][verb]['RESTfulPath'].format(app_ID=app_ID,entity_ID=entity_ID,streamdata=streamdata)
        data         = self.target[entityType][verb]['data'].format(app_ID=app_ID,entity_ID=entity_ID,streamdata=streamdata)
        params       = self.target[entityType][verb]['params']
        if 'time-range-type' in kwargs:
            time_range = self.time_range[kwargs['time-range-type']]
            for i in time_range: time_range[i] = kwargs[i] if i in kwargs else ""
            params.update(time_range)
        if 'selectors' in kwargs and kwargs['selectors'] is not None:
            params.update(kwargs['selectors'])

        # Generate request parameters
        if 'serverURL' in kwargs and 'userName' in kwargs and 'password' in kwargs:
            serverURL = kwargs['serverURL']
            auth      = (kwargs['userName'], kwargs['password'])
            headers   = self.target[entityType][verb]['headers']
        else:
            serverURL = self.appD_Config.get_current_context_serverURL()
            token     = self.__get_access_token()
            if token is None: return None
            auth      = None
            headers   = {"Authorization": "Bearer "+token}
            headers.update(self.target[entityType][verb]['headers'])
        fullPath  = serverURL + ''.join( urlSegments )
        files     = {'files': open(kwargs['filePath'],'rb')} if 'filePath' in kwargs else None
        reqMethod = self.target[entityType][verb]['method']
        if 'DEBUG' in locals():
            print ("\nRequest RESTful path:",fullPath,"\nparams:",params,"\nheaders:",headers,"\ndata:",data,"\nfiles:",files,"\nmethod:",reqMethod.__name__)
        return self.__do_request(url=fullPath,reqFunction=reqMethod,auth=auth,params=params,headers=headers,data=data,files=files)

    def get_keyword(self,entityType,verb):
        try:
            return self.target[entityType][verb]['keyword']
        except:
            return None

    def get_keywords(self,verb):
        try:
            return [ (key,value[verb]['keyword']) for key,value in iter(self.target.items()) if verb in value and 'keyword' in value[verb] ]
        except:
            return None


#    def fetch_applicationsAllTypes(self):
#        """
#        Fetch applications from a controller.
#        :returns: the fetched data. Null if no data was received.
#        """
#        restfulPath = "/controller/restui/applicationManagerUiBean/getApplicationsAllTypes"
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params={},data='',headers={},files=None,auth=None)
#
#    def fetch_applications(self):
#        """
#        Fetch applications from a controller.
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve All Business Applications
#        # GET /controller/rest/applications
#        restfulPath = "/controller/rest/applications/"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_application(self,app_ID):
#        """
#        Fetch application from a controller.
#        :param app_ID: name or ID number of the application to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve a specific Business Application
#        # GET /controller/rest/applications/application_name
#        restfulPath = "/controller/rest/applications/" + str(app_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_tiers(self,app_ID,selectors=None):
#        """
#        Fetch tiers for an application.
#        :param app_ID: name or ID number of the application to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve All Tiers in a Business Application
#        # GET /controller/rest/applications/application_name/tiers
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/tiers"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_tier_nodes(self,app_ID,entity_ID):
#        """
#        Fetch nodes for an application tier
#        :param app_ID: name or ID number of the application to fetch nodes
#        :param entity_ID: name or ID of the tier to fetch nodes
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve Node Information for All Nodes in a Tier
#        # GET /controller/rest/applications/application_name/tiers/tier_name/nodes
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/tiers/" + str(entity_ID) + "/nodes"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_nodes(self,app_ID,selectors=None):
#        """
#        Fetch application nodes from a controller
#        :param app_ID: the ID number of the nodes to fetch
#        :param selectors: fetch only nodes filtered by specified selectors
#        :returns: the number of fetched nodes. Zero if no node was found.
#        """
#        # Retrieve Node Information for All Nodes in a Business Application
#        # GET /controller/rest/applications/application_name/nodes
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/nodes"
#        params = {"output": "JSON"}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_node_by_ID(self,app_ID,entity_ID):
#        """
#        Fetch node details from a controller.
#        :param app_ID: the ID number of the application nodes to fetch
#        :param entity_ID: the ID number of the node to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve Node Information by Node Name
#        # GET /controller/rest/applications/application_name/nodes/node_name
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/nodes/" + str(entity_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)

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
        token = self.__get_access_token()
        if token is None: return None
        headers = {"Authorization": "Bearer "+token,"Content-Type": "application/json","Accept": "application/json"}
        serverURL = self.appD_Config.get_current_context_serverURL()
        restfulPath = serverURL + restfulPath
        data       = json.dumps( {  "requestFilter":nodeList,"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[],
                                    "resultColumns":["APP_AGENT_STATUS","HEALTH"],
                                    "timeRangeStart":start_epoch,"timeRangeEnd":end_epoch} )
        return self.__do_request(reqFunction=requests.post,url=restfulPath,params={},data=data,headers=headers,files=None,auth=None)

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
        token = self.__get_access_token()
        if token is None: return None
        headers = {"Authorization": "Bearer "+token,"Content-Type": "application/json","Accept": "application/json"}
        serverURL = self.appD_Config.get_current_context_serverURL()
        restfulPath = serverURL + restfulPath
        return self.__do_request(reqFunction=requests.post,url=restfulPath,params={},data='',headers=headers,files=None,auth=None)

#    def fetch_transactiondetection(self,app_ID,selectors=None):
#        """
#        Fetch transaction detection rules from a controller.
#        :param app_ID: the ID number of the detection rules to fetch
#        :param selectors: fetch only snapshots filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Export Transaction Detection Rules for All Entry Point Types
#        # GET /controller/transactiondetection/application_id/[tier_name/]rule_type
#        # https://docs.appdynamics.com/display/PRO45/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportTransactionDetectionRulesExportTransactionDetectionRules
#        restfulPath = "/controller/transactiondetection/" + str(app_ID) + "/custom"
#        params = {"output": "XML"}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def import_transactiondetection(self,app_ID,filePath):
#        """
#        Import application transaction detection rules to a controller.
#        :param app_ID: the ID number of the application where to import transaction detection rules
#        :param filePath: path to the datasource file
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Import automatic detection rules in XML format
#        # POST /controller/transactiondetection/application_id/[scope_name]/rule_type/[entry_point_type]/[rule_name] -F file=@exported_file_name.xml
#        # https://docs.appdynamics.com/display/PRO45/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ImportTransactionDetectionRules
#        restfulPath = "/controller/transactiondetection/" + str(app_ID) + "/custom?overwrite=true"
#        files={'files': open(filePath,'rb')}
#        return self.__do_request(reqFunction=requests.post,url=restfulPath,params={},data='',headers={},files=files,auth=None)
#
#    def fetch_business_transactions(self,app_ID,selectors=None):
#        """
#        Fetch application business transactions from a controller.
#        :param app_ID: the ID number of the application business transactions to fetch
#        :param selectors: fetch only business transactions filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve All Business Transactions in a Business Application
#        # GET /controller/rest/applications/application_name/business-transactions
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/business-transactions"
#        params = {"output": "JSON"}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_backends(self,app_ID,selectors=None):
#        """
#        Fetch application backends from a controller.
#        :param app_ID: the ID number of the application backends to fetch
#        :param selectors: fetch only backends filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve All Registered Backends in a Business Application With Their Properties
#        # GET /controller/rest/applications/application_name/backends
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/backends"
#        params = {"output": "JSON"}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_entrypoints_TierRules(self,entity_ID,selectors=None):
#        """
#        Fetch tier entrypoints from a controller.
#        :param entity_ID: the ID number of the tier endpoints to fetch
#        :param selectors: fetch only endpoints filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        #GetAPMSEPTierRules
#        restfulPath = "/controller/restui/serviceEndpoint/getAll"
#        data = json.dumps( {"agentType": "APP_AGENT","attachedEntity": {"entityId": entity_ID,"entityType": "APPLICATION_COMPONENT"} } )
#        headers={"Content-Type": "application/json","Accept": "application/json"}
#        params = {"output": "JSON"}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.post,url=restfulPath,params=params,data=data,headers=headers,files=None,auth=None)

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
        token = self.__get_access_token()
        if token is None: return None
        headers = {"Authorization": "Bearer "+token,"Content-Type": "application/json","Accept": "application/json"}
        serverURL = self.appD_Config.get_current_context_serverURL()
        restfulPath = serverURL + restfulPath
        params = {"output": "XML"}
        if selectors: params.update(selectors)
        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers=headers,files=None,auth=None)

#    def fetch_health_rules_JSON(self,app_ID,selectors=None):
#        """
#        Fetch health rules from a controller - Using the RESTUI API call
#        :param app_ID: the ID number of the health rules to fetch
#        :param selectors: fetch only health rules filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        restfulPath = "/controller/restui/policy2/policies/" + str(app_ID)
#        params = {"Content-Type": "application/json","resultColumns": ["LAST_APP_SERVER_RESTART_TIME", "VM_RUNTIME_VERSION", "MACHINE_AGENT_STATUS", "APP_AGENT_VERSION", "APP_AGENT_STATUS", "HEALTH"]}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_health_rule_by_ID(self,app_ID,entityID):
#        """
#        Fetch health rules from a controller - Using the new API call
#        :param app_ID: the ID number of the health rules to fetch
#        :param entityID: the ID number of the health rule to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve complete details of the health rule for the specified application ID
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/health-rules/{health-rule-id}
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/health-rules/" + str(entityID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)

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
        token = self.__get_access_token()
        if token is None: return None
        headers = {"Authorization": "Bearer "+token,"Content-Type": "application/json","Accept": "application/json"}
        serverURL = self.appD_Config.get_current_context_serverURL()
        restfulPath = serverURL + restfulPath
        files={'files': open(filePath,'rb')}
        return self.__do_request(reqFunction=requests.post,url=restfulPath,params={},data='',headers=headers,files=files,auth=None)


#    def create_health_rule(self,app_ID,dataJSON):
#        """
#        Create a new application healthrule from a controller.
#        :param app_ID: the ID number or name of the application where to create the healthrule
#        :param dataJSON: the JSON data of the healthrule to create
#        :returns: True if healthrule was created. False otherwise.
#        """
#        # Creates a new health rule from the specified JSON payload.
#        # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/health-rules
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/health-rules"
#        data = json.dumps(dataJSON)
#        headers={"Content-Type": "application/json"}
#        response = self.__do_request(reqFunction=requests.post,url=restfulPath,params={},data=data,headers=headers,files=None,auth=None)
#        return response == "201"
#
#    def update_health_rule(self,app_ID,entity_ID,dataJSON):
#        """
#        Update application healthrule from a controller.
#        :param app_ID: the ID number or name of the application where to update the healthrule
#        :param entity_ID: the ID number of the healthrule to update
#        :param dataJSON: the JSON data of the healthrule to update
#        :returns: True if healthrule was updated. False otherwise.
#        """
#        # This API updates an existing health rule (required fields) with details from the specified health rule ID.
#        # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/health-rules/{health-rule-id}
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/health-rules/" + str(entity_ID)
#        data = json.dumps(dataJSON)
#        headers={"Content-Type": "application/json"}
#        response = self.__do_request(reqFunction=requests.put,url=restfulPath,params=params,data=data,headers=headers,files=None,auth=None)
#        return response == "200"
#
#    def fetch_policies(self,app_ID):
#        """
#        Fetch application policies from a controller - Using the new API call
#        :param app_ID: the ID number of the application policies to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve a list of Policies associated with an Application
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_policy_by_ID(self,app_ID,entity_ID):
#        """
#        Fetch policy details from a controller.
#        :param app_ID: the ID number of the application policies to fetch
#        :param entity_ID: the ID number of the policy to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve Details of a Specified Policy
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/policies/{policy-id}
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/policies/" + str(entity_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_policies_legacy(self,app_ID,selectors=None):
#        """
#        Fetch application policies from a controller - Using the legacy API call
#        :param app_ID: the ID number of the application policies to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportPolicies
#        # export policies to a JSON file.
#        # GET /controller/policies/application_id
#        restfulPath = "/controller/policies/" + str(app_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_actions(self,app_ID):
#        """
#        Fetch application actions from a controller - Using the new API call
#        :param app_ID: the ID number of the application actions to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve a List of Actions for a Given Application
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_action_by_ID(self,app_ID,entity_ID):
#        """
#        Fetch action details from a controller.
#        :param app_ID: the ID number of the application actions to fetch
#        :param entity_ID: the ID number of the action to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve Details of a Specified Action
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/actions/{action-id}
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/actions/" + str(entity_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_actions_legacy(self,app_ID,selectors=None):
#        """
#        Fetch application actions from a controller - Using the legacy API call
#        :param app_ID: the ID number of the application actions to fetch
#        :param selectors: fetch only actions filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API#ConfigurationImportandExportAPI-ExportActionsfromanApplication
#        # Exports all actions in the specified application to a JSON file.
#        # GET /controller/actions/application_id
#        restfulPath = "/controller/actions/" + str(app_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_schedules(self,app_ID,selectors=None):
#        """
#        Fetch application schedules from a controller then add them to the policies dictionary. Provide either an username/password or an access token.
#        :param app_ID: the ID number or name of the application schedules to fetch
#        :param selectors: fetch only snapshots filtered by specified selectors
#        :returns: the number of fetched schedules. Zero if no schedule was found.
#        """
#        if type(app_ID) is str: app_ID = ApplicationDict().getAppID(app_ID)
#        # Retrieve a List of Schedules for a Given Application
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_schedule_by_ID(self,app_ID,entity_ID):
#        """
#        Fetch schedule details from a controller.
#        :param app_ID: the ID number of the application schedule to fetch
#        :param entity_ID: the ID number of the schedule to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve the Details of a Specified Schedule with a specified ID
#        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(entity_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def create_schedule(self,app_ID,dataJSON):
#        """
#        Create a new application schedule from a controller.
#        :param app_ID: the ID number or name of the application where to update the schedule
#        :param entity_ID: the ID number of the schedule to update
#        :param dataJSON: the JSON data of the schedule to update
#        :returns: True if schedule was created. False otherwise.
#        """
#        # Creates a new schedule with the specified JSON payload
#        # POST <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/"
#        data = json.dumps(dataJSON)
#        headers={"Content-Type": "application/json"}
#        params = {"output": "JSON"}
#        response = self.__do_request(reqFunction=requests.post,url=restfulPath,params=params,data=data,headers=headers,files=None,auth=None)
#        return response == "201"
#
#    def update_schedule(self,app_ID,entity_ID,dataJSON):
#        """
#        Update application schedule from a controller.
#        :param app_ID: the ID number or name of the application where to update the schedule
#        :param entity_ID: the ID number of the schedule to update
#        :param dataJSON: the JSON data of the schedule to update
#        :returns: True if schedule was updated. False otherwise.
#        """
#        # Updates an existing schedule with a specified JSON payload
#        # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
#        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(entity_ID)
#        data = json.dumps(dataJSON)
#        headers={"Content-Type": "application/json"}
#        params = {"output": "JSON"}
#        response = self.__do_request(reqFunction=requests.put,url=restfulPath,params=params,data=data,headers=headers,files=None,auth=None)
#        return response == "200"

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
        token = self.__get_access_token()
        if token is None: return None
        headers = {"Authorization": "Bearer "+token,"Content-Type": "application/json","Accept": "application/json"}
        serverURL = self.appD_Config.get_current_context_serverURL()
        restfulPath = serverURL + restfulPath
        params={'metric-path': metric_path,'output':'JSON'}
        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers=headers,files=None,auth=None)

#    def fetch_metric_data(self,app_ID,time_range_type,**kwargs):
#        """
#        Fetch metric data from a controller.
#        :param app_ID: the ID number of the application metrics to fetch
#        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
#        :param duration-in-mins: (optional) duration in minutes
#        :param start-time: (optional) range start time in Unix Epoch format
#        :param end-time: (optional) range end time in Unix Epoch format
#        :param selectors: Must contain the path to the metric in the metric hierarchy
#        :returns: the fetched data. Null if no data was received.
#        """
#        MAX_RESULTS="9999"
#        # Retrieve Metric Data
#        # GET /controller/rest/applications/application_name/metric-data
#        if 'selectors' not in kwargs or kwargs['selectors'] is None: return None # selectors must contain the path to the metric in the metric hierarchy
#        restfulPath = "/controller/rest/applications/"+ str(app_ID) + "/metric-data"
#        params = self.time_range[time_range_type]
#        for i in params: params[i] = kwargs[i] if i in kwargs else ""
#        params.update({'time-range-type':time_range_type,'rollup': True,'output':'JSON'})
#        params.update(kwargs['selectors'])
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_healthrule_violations(self,app_ID,time_range_type,**kwargs):
#        """
#        Fetch healtrule violations from a controller.
#        :param app_ID: the ID number of the application healtrule violations to fetch
#        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
#        :param duration-in-mins: (optional) duration in minutes
#        :param start-time: (optional) range start time in Unix Epoch format
#        :param end-time: (optional) range end time in Unix Epoch format
#        :param selectors: (optional) fetch only events filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        # https://docs.appdynamics.com/display/PRO45/Events+and+Action+Suppression+API
#        # Retrieve All Health Rule Violations that have occurred in an application within a specified time frame. 
#        # URI /controller/rest/applications/application_id/problems/healthrule-violations
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/problems/healthrule-violations"
#        params = self.time_range[time_range_type]
#        for i in params: params[i] = kwargs[i] if i in kwargs else ""
#        params.update({"time-range-type":time_range_type, "output": "JSON"})
#        if 'selectors' in kwargs and kwargs['selectors'] is not None: params.update(kwargs['selectors'])
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_snapshots(self,app_ID,time_range_type,**kwargs):
#        """
#        Fetch snapshot from a controller.
#        :param app_ID: the ID number of the application healtrule violations to fetch
#        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
#        :param duration-in-mins: (optional) duration in minutes
#        :param start-time: (optional) range start time in Unix Epoch format
#        :param end-time: (optional) range end time in Unix Epoch format
#        :param selectors: (optional) fetch only errors filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        MAX_RESULTS="9999"
#        #Retrieve Transaction Snapshots
#        # GET /controller/rest/applications/application_name/request-snapshots
#        restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"
#        params = self.time_range[time_range_type]
#        for i in params: params[i] = kwargs[i] if i in kwargs else ""
#        params.update({"time-range-type":time_range_type, "output": "JSON"})
#        if 'selectors' in kwargs and kwargs['selectors'] is not None: params.update(kwargs['selectors'])
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_errors(self,app_ID,entity_ID,time_range_type,**kwargs):
#        """
#        Fetch errors from a controller.
#        :param app_ID: the ID number of the application errors to fetch
#        :param entity_ID: the ID number of the application tier errors to fetch
#        :param time_range_type: could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
#        :param duration-in-mins: (optional) duration in minutes
#        :param start-time: (optional) range start time in Unix Epoch format
#        :param end-time: (optional) range end time in Unix Epoch format
#        :param selectors: (optional) fetch only errors filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        MAX_RESULTS="9999"
#        # "controller/rest/applications/{applicationName}/metrics?metric-path=Errors|{tierName}&time-range-type=BEFORE_NOW&duration-in-mins=15&output=JSON"
#        restfulPath = "/controller/rest/applications/"+ str(app_ID) + "/metric-data"#?metric-path=Errors%7CAPIManager%7CSocketException%7CErrors per Minute&time-range-type=BEFORE_NOW&duration-in-mins=60"
#        params = self.time_range[time_range_type]
#        for i in params: params[i] = kwargs[i] if i in kwargs else ""
#        params.update({"time-range-type":time_range_type, "output": "JSON"})
#        params.update({"metric-path":"Errors|"+str(entity_ID)+"|*|Errors per Minute",'rollup': True,"output":"JSON"})
#        if 'selectors' in kwargs and kwargs['selectors'] is not None: params.update(kwargs['selectors'])
#        #print ("params:",params)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_dashboards(self,selectors=None):
#        """
#        Fetch dashboards from a controller.
#        :param selectors: fetch only dashboards filtered by specified selectors
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Export the list of all Custom Dashboards
#        # https://community.appdynamics.com/t5/Dashboards/How-to-export-the-list-of-all-Custom-Dashboards-in-the/td-p/30083
#        # HTTP call: /controller/restui/dashboards/getAllDashboardsByType/false
#        restfulPath = "/controller/restui/dashboards/getAllDashboardsByType/false"
#        params = {"output": "JSON"}
#        if selectors: params.update(selectors)
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_dashboard_by_ID(self,entity_ID):
#        """
#        Fetch custom dashboards from a controller.
#        :param entity_ID: the ID number of the dashboards to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Export Custom Dashboards and Templates
#        # GET /controller/CustomDashboardImportExportServlet?dashboardId=dashboard_id
#        restfulPath = "/controller/CustomDashboardImportExportServlet?dashboardId=" + str(entity_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_configuration(self,selectors=None):
#        """
#        Fetch config from a controller.
#        :param selectors: fetch specific configuration filtered by specified configuration name
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Retrieve All Controller Settings
#        # GET <controller_url>/controller/rest/configuration
#        restfulPath = "/controller/rest/configuration"
#        params = {"output": "JSON"}
#        if selectors: restfulPath = restfulPath + "?name=" + selectors
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_users(self,selectors=None):
#        """
#        Fetch users from a controller.
#        :param selectors: fetch specific user filtered by specified user name or ID
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Get All Users
#        # GET <controller_url>/controller/rest/users
#        restfulPath = "/controller/api/rbac/v1/users"
#        params = {"output": "JSON"}
#        if selectors: restfulPath = restfulPath + selectors
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_users_extended(self):
#        """
#        Fetch users with extended info from a controller.
#        :returns: the fetched data. Null if no data was received.
#        """
#        restfulPath = "/controller/restui/userAdministrationUiService/users"
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#    def fetch_user_by_ID(self,entity_ID):
#        """
#        Fetch specific user from a controller.
#        :param entity_ID: the ID number of the user to fetch
#        :returns: the fetched data. Null if no data was received.
#        """
#        # Get User by ID
#        # GET /controller/api/rbac/v1/users/userId
#        restfulPath = "/controller/api/rbac/v1/users/" + str(entity_ID)
#        params = {"output": "JSON"}
#        return self.__do_request(reqFunction=requests.get,url=restfulPath,params=params,data='',headers={},files=None,auth=None)
#
#
#    def get_account_usage_summary(self):
#        """
#        Get the account license usage summary.
#        :returns: the ysage summary in JSON data format. Null if no data was received.
#        """
#        # Retrieve account license usage summary
#        # POST /controller/restui/licenseRule/getAccountUsageSummary
#        restfulPath = "/controller/restui/licenseRule/getAccountUsageSummary"
#        data        = json.dumps({"type": "BEFORE_NOW","durationInMinutes": 5})
#        return self.__do_request(reqFunction=requests.post,url=restfulPath,params={},data=data,headers={},files=None,auth=None)


    def get_controller_version(self):
        """
        Get the controller version. Either provide an username/password or let it get an access token automatically.
        :returns: the controller release version number. Null if no data was received.
        """
        # Retrieve All Controller Settings
        # GET /controller/rest/configuration
        restfulPath = "/controller/rest/configuration"
        token = self.__get_access_token()
        if token is None: return None
        headers = {"Authorization": "Bearer "+token,"Content-Type": "application/json","Accept": "application/json"}
        serverURL = self.appD_Config.get_current_context_serverURL()
        restfulPath = serverURL + restfulPath
        params      = {"name": "schema.version","output": "JSON"}
        response = self.__do_request(reqFunction=requests.get,url=restfulPath,params={},data='',headers=headers,files=None,auth=None)
        if response is not None:
            schemaVersion = json.loads(response.content)
            return schemaVersion[0]['value'].replace("-","")