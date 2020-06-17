#!/usr/bin/python
import requests
import json
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
 # Fetch RESTful Path from a controller. Either provide an username/password or gets an access token automatically.
 # @param RESTfulPath RESTful path to retrieve data
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @return the response JSON data. Null if no JSON data was received.
###
def fetch_RESTful_JSON(RESTfulPath,userName=None,password=None):
    if 'DEBUG' in locals(): print ("Fetching JSON for RESTful path " + RESTfulPath + "...")
    serverURL = get_current_context_serverURL()
    if userName and password:
        try:
            response = requests.get(serverURL + "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules",
                                    auth=(userName, password), params={"output": "JSON"})
        except requests.exceptions.InvalidURL:
            print ("Invalid URL: " + serverURL + RESTfulPath + ". Do you have the right controller hostname and RESTful path?")
            return None
    else:
    	token = get_access_token()
        if token is None: return None
        try:
        	response = requests.get(serverURL + RESTfulPath,
                                headers={"Authorization": "Bearer "+token}, params={"output": "JSON"})
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

    try:
        responseJSON = json.loads(response.content)
    except:
        print ("Could not process JSON content")
        return None
    return responseJSON

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