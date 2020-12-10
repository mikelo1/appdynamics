#!/usr/bin/python
import requests
import json
import yaml
import csv
import sys
from getpass import getpass
from datetime import datetime, timedelta
from urlparse import urlparse
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

    def get_help(self,output=sys.stdout):
        if output in [sys.stdout,sys.stderr]:
            output.write ("Modify appdconfig files using subcommands like \"appdctl config set current-context my-context\"\n\n" + \
                        " The loading order follows these rules:\n\n" + \
                        "  1.  If the --kubeconfig flag is set, then only that file is loaded. The flag may only be set once and no merging takes place.\n" + \
                        "  2.  If $KUBECONFIG environment variable is set, then it is used as a list of paths (normal path delimiting rules for your system). These paths are merged. When a value is modified, it is modified the file that defines the stanza. When a value is created, it is created in the first file that exists. If no files in the chain exist, then it creates the last file in the list.\n" + \
                        "  3.  Otherwise, ${HOME}/.kube/config is used and no merging takes place.\n\n" + \
                        "Available Commands:\n" + \
                        "  current-context Displays the current-context\n" + \
                        "  delete-context  Delete the specified context from the kubeconfig\n" + \
                        "  get-contexts    Describe one or many contexts\n" + \
                        "  rename-context  Renames a context from the kubeconfig file.\n" + \
                        "  set-context     Sets a context entry in kubeconfig\n" + \
                        "  set-credentials Sets a user entry in kubeconfig\n" + \
                        "  unset           Unsets an individual value in a kubeconfig file\n" + \
                        "  use-context     Sets the current-context in a kubeconfig file\n" + \
                        "  view            Display merged kubeconfig settings or a specified kubeconfig file\n\n" + \
                        "Usage:\n" + \
                        "  appdctl config SUBCOMMAND [options]\n\n")

    def view(self):
        try:
            with open(self.configFile, 'r') as stream:
                print stream.readlines()
        except EnvironmentError as exc:
            print(exc)

    def save(self):
        if 'DEBUG' in locals(): print "Saving changes..."
        try:
            with open(self.configFile, "w") as outfile:
                yaml.dump(self.data, outfile, default_flow_style=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            print(exc)

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
                if 'DEBUG' in locals(): print "Found valid token in config YAML file."
                return user['user']['token']
            else:
                if 'DEBUG' in locals(): print "Token expired or invalid in config YAML file."
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

basicAuth   = None #BasicAuth(basicAuthFile="auth_file.csv")
appD_Config = AppD_Configuration()

###
 # Fetch access token from a controller. Provide an username/password.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return the access token string. Null if there was a problem getting the access token.
###
def fetch_access_token(serverURL,API_username,API_password):
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
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w") 
            file1.write(response.content)
            file1.close()
        return None
    token_data = json.loads(response.content)
    return token_data

###
 # Get access token from a controller. If no credentials provided it will try to get them from basic auth file.
 # @param contextName name of context
 # @return the access token string. Null if there was a problem getting the access token.
###
def get_access_token(contextName=None):
    global basicAuth
    if contextName is not None:
        if appD_Config.select_context(contextName) is None:
            if 'DEBUG' in locals(): print "Cannot get context data. Did you type correctly the context name?"
            return None
    elif appD_Config.get_current_context(output=None) is None:
        if 'DEBUG' in locals(): print "Cannot get context data. Did you login to any controller machine?"
        return None

    token     = appD_Config.get_current_context_token()
    serverURL = appD_Config.get_current_context_serverURL()
    API_Client= appD_Config.get_current_context_username()
    if token is None:
        if basicAuth is not None:
            Client_Secret = basicAuth.get_password(API_Client)
        elif appD_Config.get_credentials(appD_Config.get_current_context(output=None)):
            Client_Secret = appD_Config.get_credentials(appD_Config.get_current_context(output=None))
        else:
            sys.stderr.write("Authentication required for " + serverURL + "\n")
            Client_Secret = getpass(prompt='Password: ')
        token_data = fetch_access_token(serverURL,API_Client,Client_Secret)
        if token_data is None:
            sys.stderr.write("Authentication failed. Did you mistype the password?\n") 
            return None
        appD_Config.set_current_context_token(token_data['access_token'],token_data['expires_in'])
        token = token_data['access_token']
    return token


###### FROM HERE PUBLIC FUNCTIONS ######

###
 # Fetch RESTful Path from a controller. Either provide an username/password or let it get an access token automatically.
 # @param RESTfulPath RESTful path to retrieve data
 # @param params additional HTTP parameters (if any)
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return the response data. Null if no data was received.
###
def fetch_RESTfulPath(RESTfulPath,params=None,serverURL=None,userName=None,password=None):
    if 'DEBUG' in locals(): print ("Fetching JSON from RESTful path " + RESTfulPath + " with params " + json.dumps(params) + " ...")
    if serverURL is None: serverURL = appD_Config.get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.get(serverURL + RESTfulPath,
                                    auth=(userName, password), params=params)
        except requests.exceptions.InvalidURL:
            sys.stderr.write("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
            return None
    else:
        token = get_access_token()
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
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w") 
            file1.write(response.content)
            file1.close()
        return None
    return response.content


###
 # Update data from a controller. Either provide an username/password or let it get an access token automatically.
 # @param RESTfulPath RESTful path to upload data
 # @param JSONdata the data to be updated in JSON format
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return True if the update was successful. False if no schedule was updated.
###
def create_RESTful_JSON(RESTfulPath,JSONdata,serverURL=None,userName=None,password=None):
    if 'DEBUG' in locals(): print ("Creating RESTful path " + RESTfulPath + " with provided JSON data...")
    if serverURL is None: serverURL = appD_Config.get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.post(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json","Accept": "application/json"},
                                    auth=(userName, password), data=json.dumps(JSONdata))
        except requests.exceptions.InvalidURL:
            sys.stderr.write ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
            return None
    else:
        token = get_access_token()
        if token is None: return None
        try:
            response = requests.post(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer "+token},
                                    data=json.dumps(JSONdata))
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
            print "   header:", response.headers
            print response.content
            #print "Writing content to file: response.txt"
            #file1 = open("response.txt","w")
            #file1.write(response.content)
            #file1.close()
        return None
    return response.content

###
 # Update data from a controller. Either provide an username/password or let it get an access token automatically.
 # @param RESTfulPath RESTful path to upload data
 # @param JSONdata the data to be updated in JSON format
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return True if the update was successful. False if no schedule was updated.
###
def update_RESTful_JSON(RESTfulPath,JSONdata,serverURL=None,userName=None,password=None):
    if 'DEBUG' in locals(): print ("Updating RESTful path " + RESTfulPath + " with provided JSON data...")
    if serverURL is None: serverURL = appD_Config.get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.put(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json"},
                                    auth=(userName, password), data=json.dumps(JSONdata))
        except requests.exceptions.InvalidURL:
            sys.stderr.write ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?\n")
            return False
    else:
        token = get_access_token()
        if token is None: return False
        try:
            response = requests.put(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json", "Authorization": "Bearer "+token},
                                    data=json.dumps(JSONdata))
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
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w")
            file1.write(response.content)
            file1.close()
        return False
    return True

###
 # Get the controller version. Either provide an username/password or let it get an access token automatically.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return the controller release version number. Null if no data was received.
###
def get_controller_version(serverURL=None,userName=None,password=None):
    if serverURL is None: serverURL = appD_Config.get_current_context_serverURL() 
    if 'DEBUG' in locals(): print ("Fetching controller version for controller " + serverURL + "...")
    if userName and password:
        try:
            response = requests.get(serverURL + "/controller/rest/configuration",
                                    auth=(userName, password), params={"name": "schema.version","output": "JSON"})
        except requests.exceptions.InvalidURL:
            sys.stderr.write ("Invalid URL: " + serverURL + "/controller/rest/configuration. Do you have the right controller hostname?\n")
            return None
    else:
        token = get_access_token()
        if token is None: return None
        try:
            response = requests.get(serverURL + "/controller/rest/configuration",
                                headers={"Authorization": "Bearer "+token}, params={"name": "schema.version","output": "JSON"})
        except requests.exceptions.InvalidURL:
            sys.stderr.write ("Invalid URL: " + serverURL + "/controller/rest/configuration. Do you have the right controller hostname?\n")
            return None

    if response.status_code > 399:
        sys.stderr.write("Something went wrong on HTTP request. Status:" + str(response.status_code) + " ")
        if response.content.find("<b>description</b>"):
            sys.stderr.write("Description: "+response.content[response.content.find("<b>description</b>")+18:response.content.rfind("</p>")] + "\n" )
        else:
            sys.stderr.write("Description not available\n")
        if 'DEBUG' in locals():
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w")
            file1.write(response.content)
            file1.close()
        return None

    schemaVersion = json.loads(response.content)
    return schemaVersion[0]['value'].replace("-","")

###
 # Translates start/end time range into HTTP param compliant string.
 # @param time_range_type time range type, which could be one of these: {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"}
 # @param duration duration in minutes
 # @param startEpoch range start time in Epoch format
 # @param endEpoch range end time in Epoch format
 # @return HTTP param compliant string. Null if provided data could not be interpreted.
###
def timerange_to_params(time_range_type,duration=None,startEpoch=None,endEpoch=None):
    if time_range_type == "BEFORE_NOW" and duration is not None:
        params={"time-range-type": time_range_type,"duration-in-mins": duration}
    elif time_range_type == "BEFORE_TIME" and duration is not None and endEpoch is not None:
        params={"time-range-type": time_range_type,"duration-in-mins": duration,"end-time": endEpoch}
    elif time_range_type == "AFTER_TIME" and duration is not None and startEpoch is not None:
        params={"time-range-type": time_range_type,"duration-in-mins": duration,"start-time": startEpoch}
    elif time_range_type == "BETWEEN_TIMES" and startEpoch is not None and endEpoch is not None:
        params={"time-range-type": time_range_type,"start-time": startEpoch,"end-time": endEpoch}
    else:
        print ("Unknown time range or missing arguments.")
        return None
    return params

###
 # Translates XML format entity names to JSON format entity names.
 # @param entityType naming of the entity in the XML file format
 # @return naming of the entity in the JSON file format. Null if provided entity name could not be interpreted.
###
def entityXML2JSON(XMLentityType):
    switcher = {
        "BUSINESS_TRANSACTION": "BUSINESS_TRANSACTION_PERFORMANCE",
        "NODE_HEALTH_TRANSACTION_PERFORMANCE": "TIER_NODE_TRANSACTION_PERFORMANCE",
        "INFRASTRUCTURE": "TIER_NODE_HARDWARE",
        "JMX_INSTANCE_NAME": "JMX_OBJECT",
        "INFORMATION_POINT": "INFORMATION_POINTS",
        "SIM": "SERVERS_IN_APPLICATION",
        "NETVIZ": "ADVANCED_NETWORK",
        "BACKEND": "BACKENDS",
        "SERVICEENDPOINTS": "SERVICE_ENDPOINTS",
        "ERROR": "ERRORS",
        "OVERALL_APPLICATION": "OVERALL_APPLICATION_PERFORMANCE",
        "EUMPAGES": "EUM_BROWSER_APPS"
    }
    return switcher.get(XMLentityType, XMLentityType)