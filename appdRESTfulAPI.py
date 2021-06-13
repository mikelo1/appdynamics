#!/usr/bin/python
import requests
import json
import yaml
import csv
import sys
from getpass import getpass
from datetime import datetime, timedelta
if sys.version_info.major < 3:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse
import base64
import time

class AppD_Configuration:
    data       = {
        'Kind': 'Config',
        'contexts': [ ],
        'users': [ ],
        'current-context': ''
    }
    configFile = "appdconfig.yaml"

    def __init__(self,dataFile=None):
        if dataFile is not None:
            self.configFile = dataFile
        try:
            stream = open(self.configFile)
        except IOError as exc:
            print(exc)
            return None
        with open(self.configFile, 'r') as stream:
            try:
                self.data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def __str__(self):
        return "({0},{1})".format(self.configFile,self.data)

    def view(self):
        try:
            with open(self.configFile, 'r') as stream:
                print (stream.readlines())
        except EnvironmentError as exc:
            print(exc)

    def save(self):
        if 'DEBUG' in locals(): print ("Saving changes...")
        try:
            with open(self.configFile, "w") as outfile:
                yaml.dump(self.data, outfile, default_flow_style=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            print(exc)

    def get_configFileName(self):
        return self.configFile

    def get_contexts(self,output=sys.stdout):
        fieldnames = ['CURRENT', 'NAME', 'AUTHINFO']
        filewriter = csv.DictWriter(output, fieldnames=fieldnames, delimiter=',', quotechar='"')
        filewriter.writeheader()

        for context in self.data['contexts']:
            try:
                filewriter.writerow({'CURRENT': "*" if 'current-context' in self.data and context['name'] == self.data['current-context'] else "",
                                     'NAME': context['name'],
                                     'AUTHINFO': context['context']['user']})
            except ValueError as valError:
                print (valError)
                return (-1)

    def get_current_context(self,output=sys.stdout):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            if output in [sys.stdout,sys.stderr]:
                output.write(self.data['current-context']+"\n")
            return self.data['current-context']
        else:
            return None

    def get_current_context_serverURL(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            return [context for context in self.data['contexts'] if context['name']==self.data['current-context']][0]['context']['server']

    def get_current_context_user(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            return [context for context in self.data['contexts'] if context['name']==self.data['current-context']][0]['context']['user']

    def get_current_context_username(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            return [context for context in self.data['contexts'] if context['name']==self.data['current-context']][0]['context']['user'].split('/')[0]

    def get_current_context_token(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            current_user = self.get_current_context_user()
            userdata = [user for user in self.data['users'] if user['name']==current_user][0]['user']
            if userdata is not None and 'expire' in userdata and datetime.today() < userdata['expire']:
                if 'DEBUG' in locals(): print ("Found valid token in config YAML file.")
                return userdata['token']
            else:
                if 'DEBUG' in locals(): print ("Token expired or invalid in config YAML file.")
                return None

    def set_current_context_token(self,access_token,expires_in):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            current_user = self.get_current_context_user()
            userdata = [user for user in self.data['users'] if user['name']==current_user][0]['user']
            if userdata is not None:
                userdata['token']  = str(access_token)
                userdata['expire'] = datetime.now()+timedelta(seconds=expires_in)
                self.save()
                return True
        return False

    def select_context(self,contextname):
        if 'current-context' in self.data and self.data['current-context'] == contextname:
            sys.stdout.write("Context " + contextname + " already selected.\n")
            return contextname
        for context in self.data['contexts']:
            if context['name'] == contextname:
                self.data['current-context'] = contextname
                self.save()
                sys.stdout.write("Context changed to "+contextname+"\n")
                return contextname
        sys.stderr.write("Context "+contextname+" does not exist.\n")
        return None

    # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
    # @param API_Client Full username, including account. i.e.: myuser@customer1
    def create_context(self,contextname,serverURL,API_Client):
        url = urlparse(serverURL)
        if len(url.scheme) == 0 or len(url.netloc) == 0 is None:
            sys.stderr.write("URL is not correctly formatted. <protocol>://<host>:<port>\n")
            return
        servername = url.netloc
        username = API_Client + "/" + servername
        if contextname is None: contextname = servername + "/" + API_Client

        # Check whether provided user does exist or not
        if username in self.data['users'] or contextname in self.data['contexts']:
            sys.stderr.write("User or context already exists.\n")
        else:
            # Create the new user and set this one as current-context
            self.data['users'].append({'name': username,'user': {}})
            self.data['contexts'].append({'name': contextname,'context': { 'server': serverURL, 'user': username}})
            self.data['current-context'] = contextname
            self.save()

    def delete_context(self,contextname):
        context_index = 0
        for context in self.data['contexts']:
            if context['name'] == contextname:
                context_user = context['context']['user']
                user_index = 0
                for user in self.data['users']:
                    if user['name'] == context_user: break
                    else: user_index += 1
                if user_index < len (self.data['users']):
                    self.data['users'].pop(user_index)
                break
            else: context_index += 1
        if context_index < len(self.data['contexts']): 
            self.data['contexts'].pop(context_index)
            if 'current-context' in self.data and self.data['current-context'] == contextname:
                self.data.pop('current-context')
            self.save()
        else:
            sys.stderr.write("Context does not exist.\n")

    def rename_context(self,contextname,new_contextname):
        for context in self.data['contexts']:
            if context['name'] == contextname:
                context['name'] = new_contextname
                self.save()
                sys.stdout.write("Context changed to "+new_contextname+"\n")
                return new_contextname
        sys.stderr.write("Context "+contextname+" does not exist.\n")
        return None

    def set_credentials(self,contextname):
        context = [context for context in self.data['contexts'] if context['name']==contextname]
        if not context:
            sys.stdout.write("Context "+contextname+" does not exist.\n")
        else:
            API_Client = context[0]['context']['user']
            user = [user for user in self.data['users'] if user['name']==API_Client][0]
            sys.stderr.write("Authentication required for " + API_Client + "\n")
            Client_Secret = getpass(prompt='Password: ')
            user['user'].update({'password': base64.b64encode(Client_Secret.encode('ascii'))})
            self.save()

    def get_credentials(self,contextname):
        context = [context for context in self.data['contexts'] if context['name']==contextname]
        if not context:
            sys.stdout.write("Context "+contextname+" does not exist.\n")
        else:
            API_Client = context[0]['context']['user']
            user = [user for user in self.data['users'] if user['name']==API_Client][0]
            if 'password' in user['user']:
                return base64.b64decode(user['user']['password'].encode('ascii')).decode('ascii')


class BasicAuth:
    authFile  = ""

    def __init__(self,basicAuthFile=None):
        if basicAuthFile is not None:
            try:
                stream = open(basicAuthFile)
            except IOError as exc:
                print("BasicAuth init: "+str(exc))
                return None
            self.authFile = basicAuthFile

    def __str__(self):
        return "({0})".format(self.authFile)

    def get_authFileName(self):
        return self.authFile

    def get_password(self,API_Client):
        auth_dict = dict()
        with open(self.authFile, mode='r') as csv_file:
            try:
                auth_dict = csv.DictReader(csv_file,fieldnames=['password','apiClient'])
            except IOError as exc:
                print(exc)
            for credential in auth_dict:
                if credential['apiClient'] == API_Client:
                    return credential['password']


class RESTfulAPI:
    basicAuth   = None #BasicAuth(basicAuthFile="auth_file.csv")

    def __init__(self):
        pass
        #self._session = None

    def __str__(self):
        return json.dumps(self.BTDict)

    def __str__(self):
        return "({0},{1})".format(self.appD_Config.get_configFileName,self.basicAuth)

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

    def __get_access_token(self,contextName=None):
        """
        Get access token from a controller. If no credentials provided it will try to get them from basic auth file.
        :param contextName: name of context
        :returns: the access token string. Null if there was a problem getting the access token.
        """
        appD_Config=AppD_Configuration()
        if contextName is not None:
            if appD_Config.select_context(contextName) is None:
                if 'DEBUG' in locals(): print ("Cannot get context data. Did you type correctly the context name?")
                return None
        elif appD_Config.get_current_context(output=None) is None:
            if 'DEBUG' in locals(): print ("Cannot get context data. Did you login to any controller machine?")
            return None

        token     = appD_Config.get_current_context_token()
        serverURL = appD_Config.get_current_context_serverURL()
        API_Client= appD_Config.get_current_context_username()
        if token is None:
            if 'DEBUG' in locals(): print ("Current context "+ appD_Config.get_current_context(output=None) + " has no valid token.")
            if self.basicAuth is not None:
                Client_Secret = self.basicAuth.get_password(API_Client)
            elif appD_Config.get_credentials(appD_Config.get_current_context(output=None)):
                Client_Secret = appD_Config.get_credentials(appD_Config.get_current_context(output=None))
            else:
                sys.stderr.write("Authentication required for " + serverURL + "\n")
                Client_Secret = getpass(prompt='Password: ')
            token_data = self.__fetch_access_token(serverURL,API_Client,Client_Secret)
            if token_data is None:
                sys.stderr.write("Authentication failed. Did you mistype the password?\n") 
                return None
            appD_Config.set_current_context_token(token_data['access_token'],token_data['expires_in'])
            token = token_data['access_token']
            if 'DEBUG' in locals(): print ("New token obtained for current context "+ appD_Config.get_current_context(output=None) + ": "+token)
        else:
            if 'DEBUG' in locals(): print ("Current context "+ appD_Config.get_current_context(output=None) + " has valid token: "+token)
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
        if serverURL is None: serverURL = AppD_Configuration().get_current_context_serverURL()
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
        :returns: response of the update request. None if no data was updated.
        """
        if 'DEBUG' in locals(): print ("Updating RESTful path " + RESTfulPath + " with provided stream data...")
        data = json.dumps(streamdata) if type(streamdata) is dict else streamdata
        requestMethod = requests.post if method=="POST" else requests.put
        if serverURL is None: serverURL = AppD_Configuration().get_current_context_serverURL()
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

        if response.status_code != 200:
            sys.stderr.write("Something went wrong on HTTP request. Status:" + str(response.status_code) + " ")
            if response.content.find("<b>description</b>"):
                sys.stderr.write("Description: "+response.content[response.content.find("<b>description</b>")+18:response.content.rfind("</p>")] + "\n" )
            else:
                sys.stderr.write("Description not available\n")
            if 'DEBUG' in locals():
                print ("   header:", response.headers)
                print (response.content)
            return None
        return response.content

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
        :returns: True if the update was successful. False if no schedule was updated.
        """
        if 'DEBUG' in locals(): print ("Importing RESTful path " + RESTfulPath + " with provided datasource file...")
        requestMethod = requests.post if method=="POST" else requests.put
        files={'files': open(filePath,'rb')}
        if serverURL is None: serverURL = AppD_Configuration().get_current_context_serverURL()
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
        return self.__update_RESTfulPath(restfulPath,streamdata=params,method="POST",headers={"Content-Type": "application/json","Accept": "application/json"})

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
        return self.__update_RESTfulPath(restfulPath,streamdata="",method="POST",headers={"Content-Type": "application/json","Accept": "application/json"})


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

    def update_schedule(self,app_ID,sched_ID,scheduleJSON):
        """
        Update application schedule from a controller. Provide either an username/password or an access token.
        :param app_ID: the ID number or name of the application where to update the schedule
        :param sched_ID: the ID number of the schedule to update
        :param scheduleJSON: the JSON data of the schedule to update
        :returns: the fetched data. Null if no data was received.
        """
        # Updates an existing schedule with a specified JSON payload
        # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
        restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(sched_ID)
        return self.__update_RESTfulPath(restfulPath,streamdata=scheduleJSON,method="PUT",headers={"Content-Type": "application/json"})

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
