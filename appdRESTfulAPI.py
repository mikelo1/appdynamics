#!/usr/bin/python
import requests
import json
import sys
from getpass import getpass
from appdconfig import AppD_Configuration, BasicAuth

basicAuth=None
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
 # Get access token from a controller. If no credentials provided it will try to get them from config file.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param API_Client Full username, including account. i.e.: myuser@customer1
 # @param basicAuthFile name of the source CSV file
 # @return the access token string. Null if there was a problem getting the access token.
###
def get_access_token(serverURL=None,API_Client=None,basicAuthFile=None):
    global basicAuth
    if serverURL is None or API_Client is None:
        # If controller was not provided, try to find in the configuration file
        serverURL  = appD_Config.get_current_context_serverURL()
        API_Client = appD_Config.get_current_context_username()
        if serverURL is None or API_Client is None:
            if 'DEBUG' in locals(): print "Cannot get context data. Did you login to any controller machine?"
            return None

    appD_Config.create_or_select_user(serverURL,API_Client)
    token = appD_Config.get_current_context_token()
    if token is None:
        if basicAuthFile is not None:
            basicAuth = BasicAuth(basicAuthFile=basicAuthFile)
        if basicAuth is not None:
            Client_Secret = basicAuth.get_password(API_Client)
        else:
            sys.stderr.write("Authentication required for " + serverURL + "\n")
            Client_Secret = getpass(prompt='Password: ')
        token_data = fetch_access_token(serverURL,API_Client,Client_Secret)
        if token_data is None:
            sys.stderr.write("Authentication failed. Did you mistype the password?\n") 
            return None
        appD_Config.set_new_token(API_Client,token_data['access_token'],token_data['expires_in'])
        token = token_data['access_token']
    return token

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
    if 'DEBUG' in locals(): print ("Fetching JSON from RESTful path " + RESTfulPath + "with params " + json.dumps(params) + " ...")
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