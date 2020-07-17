#!/usr/bin/python
import requests
import json
import xml.etree.ElementTree as ET
from getpass import getpass
from appdconfig import get_current_context_serverURL, get_current_context_username, get_current_context_token, create_or_select_user, set_new_token


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
        if 'DEBUG' in locals():
            print "Something went wrong on HTTP request:"
            print "   status:", response.status_code
            print "   header:", response.headers
            print "   content:", response.content
        return None
    token_data = json.loads(response.content)
    return token_data

###
 # Get access token from a controller. If no credentials provided it will try to get them from config file.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return the access token string. Null if there was a problem getting the access token.
###
def get_access_token(serverURL=None,API_Client=None,Client_Secret=None):
    if serverURL is None or API_Client is None:
        # If controller was not provided, try to find in the configuration file
        serverURL  = get_current_context_serverURL()
        API_Client = get_current_context_username()
        if serverURL is None or API_Client is None:
            print "Cannot get context data. Did you login to any controller machine?"
            return None

    create_or_select_user(serverURL,API_Client)
    token = get_current_context_token()
    if token is None:
        if Client_Secret is None:
            print "Authentication required for " + serverURL
            Client_Secret = getpass(prompt='Password: ')
        token_data = fetch_access_token(serverURL,API_Client,Client_Secret)
        if token_data is None:
            print "Authentication failed. Did you mistype the password?"
            return None
        set_new_token(API_Client,token_data['access_token'],token_data['expires_in'])
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
    if 'DEBUG' in locals(): print ("Fetching JSON from RESTful path " + RESTfulPath + "with params " + params + " ...")
    if serverURL is None: serverURL = get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.get(serverURL + RESTfulPath,
                                    auth=(userName, password), params=params)
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return None
    else:
        token = get_access_token()
        if token is None: return None
        try:
        	response = requests.get(serverURL + RESTfulPath,
                                headers={"Authorization": "Bearer "+token}, params=params)
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request. Status:", response.status_code
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
    if serverURL is None: serverURL = get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.post(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json","Accept": "application/json"},
                                    auth=(userName, password), data=json.dumps(JSONdata))
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return None
    else:
        token = get_access_token()
        if token is None: return None
        try:
            response = requests.post(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer "+token},
                                    data=json.dumps(JSONdata))
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request. Status:", response.status_code
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
    if serverURL is None: serverURL = get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.put(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json"},
                                    auth=(userName, password), data=json.dumps(JSONdata))
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return False
    else:
        token = get_access_token()
        if token is None: return False
        try:
            response = requests.put(serverURL + RESTfulPath,
                                    headers={"Content-Type": "application/json", "Authorization": "Bearer "+token},
                                    data=json.dumps(JSONdata))
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return False

    if response.status_code != 200:
        print "Something went wrong on HTTP request. Status:", response.status_code
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
    if serverURL is None: serverURL = get_current_context_serverURL() 
    if 'DEBUG' in locals(): print ("Fetching controller version for controller " + serverURL + "...")
    if userName and password:
        try:
            response = requests.get(serverURL + "/controller/rest/configuration",
                                    auth=(userName, password), params={"name": "schema.version","output": "JSON"})
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + "/controller/rest/configuration. Do you have the right controller hostname?")
            return None
    else:
        token = get_access_token()
        if token is None: return None
        try:
            response = requests.get(serverURL + "/controller/rest/configuration",
                                headers={"Authorization": "Bearer "+token}, params={"name": "schema.version","output": "JSON"})
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + "/controller/rest/configuration. Do you have the right controller hostname?")
            return None

    if response.status_code > 399:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
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
def to_JSONentityName(XMLentityType):
    switcher = {
        "APPLICATION_COMPONENT": "TIER",
        "APPLICATION_COMPONENT_NODE": "NODE",
        "JMX_INSTANCE_NAME": "JMX_OBJECT",
        "INFO_POINT": "INFORMATION_POINT",
        "MACHINE_INSTANCE": "SERVER",
        "BACKEND": "DATABASES",
        "SERVICE_END_POINT": "SERVICE_ENDPOINTS"
    }
    return switcher.get(XMLentityType, XMLentityType)