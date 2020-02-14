#!/usr/bin/python
import requests
import json
import sys
from datetime import datetime, timedelta
import time

access_token = None
class AccessToken:
    token    = ""
    startDate= None
    expires  = 0
    def __init__(self,token,startDate,expires):
        self.token    = token
        self.startDate= startDate
        self.expires  = expires
    def __str__(self):
        return "({0},{1},{2})".format(self.token,self.startDate,self.expires)

# https://docs.appdynamics.com/display/PRO45/API+Clients#APIClients-using-the-access-token
# https://docs.appdynamics.com/display/PRO45/API+Clients
def fetch_access_token(baseUrl,userName,password,API_Client,Client_Secret):
    # Fetch Controller schema version
    try:
        response = requests.get(baseUrl + "rest/configuration", auth=(userName, password), params={"name": "schema.version","output": "JSON"})
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        return None
    if response.status_code > 399:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        return None

    schemaVersion = json.loads(response.content)
    controllerVersion = schemaVersion[0]['value'].replace("-","")
    if controllerVersion < 4005009001: # Controller version lower than 4.5.9
        response = requests.post(baseUrl + "api/oauth/access_token", 
                                auth=(API_Client, Client_Secret), 
                                headers={"Content-Type": "application/vnd.appd.cntrl+protobuf", "v":"1"},
                                data={"grant_type": "client_credentials", "client_id": API_Client, "client_secret": Client_Secret})
    else: # Controller version higher than 4.5.9
        response = requests.post(baseUrl + "api/oauth/access_token",
                                auth=(userName, password),
                                headers={"Content-Type": "application/vnd.appd.cntrl+protobuf", "v":"1"},
                                data={"grant_type": "client_credentials", "client_id": API_Client, "client_secret": Client_Secret})
    if response.status_code > 399:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "   content:", response.content
        return None
    data = json.loads(response.content)
    access_token = AccessToken(data['access_token'],datetime.today(),data['expires_in'])
    return access_token.token

# TO DO: get_access_token
def get_access_token(baseUrl,userName,password,API_Client,Client_Secret):
    fetch_access_token(baseUrl,userName,password,API_Client,Client_Secret)
    expire_date=access_token.startDate + access_token.expires
    print "Today:",datetime.today(),"Expires:",expire_date
    if access_token is not None and datetime.today() < expire_date:
        return access_token.token
    else:
        print "Token expired. Creating a new one..."
        return #fetch_access_token(baseUrl,userName,password,API_Client,Client_Secret)