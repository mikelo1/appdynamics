#!/usr/bin/python
import requests
import json
import yaml
import sys
from datetime import datetime, timedelta
from getpass import getpass
import time

AppD_configfile="appdconfig.yaml"

# https://docs.appdynamics.com/display/PRO45/API+Clients#APIClients-using-the-access-token
# https://docs.appdynamics.com/display/PRO45/API+Clients
def fetch_access_token(serverURL,API_username,API_password):
    response = requests.post(serverURL + "/controller/api/oauth/access_token",
                                auth=(API_username, API_password),
                                headers={"Content-Type": "application/vnd.appd.cntrl+protobuf", "v":"1"},
                                data={"grant_type": "client_credentials", "client_id": API_username, "client_secret": API_password})
    if response.status_code > 399:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "   content:", response.content
        return None
    token_data = json.loads(response.content)
    return token_data

def get_current_context_server():
    data = read_config_yaml()
    if 'current-context' in data and len(data['current-context']) > 0:
        for context in data['contexts']:
            if context['name'] == data['current-context']:
             return context['context']['server']

def get_current_context_user():
    data = read_config_yaml()
    if 'current-context' in data and len(data['current-context']) > 0:
        return data['current-context'].split('/')[1]

def get_access_token(serverURL,API_Client,Client_Secret=None):
    servername = serverURL.split('/')[2]
    username = API_Client + "/" + servername
    contextname = servername + "/" + API_Client
    data = read_config_yaml()
    # Check if user already exists in config YAML file
    # If the user exists and token is not expired, return token from file. Otherwise get a new token
    for user in data['users']:
        if user['name'] == username:
            if datetime.today() < user['user']['expire']:
                if 'DEBUG' in locals(): print "Found valid token in config YAML file."
                if data['current-context'] != contextname:
                    data['current-context'] = contextname
                    if 'DEBUG' in locals(): print "Saving context selection change..."
                    with open(AppD_configfile, "w") as outfile:
                        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)
                return user['user']['token']
            else:
                if 'DEBUG' in locals(): print "Token expired in config YAML file. Fetching new token..."
                if Client_Secret is None:
                    print "Authentication required for " + serverURL
                    Client_Secret = getpass(prompt='Password: ')
                token_data = fetch_access_token(serverURL,API_Client,Client_Secret)
                user['user']['token']  = str(token_data['access_token'])
                user['user']['expire'] = datetime.now()+timedelta(seconds=token_data['expires_in'])
                data['current-context'] = contextname
                break
            
    # If the user does not exist, get a new token and create user
    if 'user' not in locals() or user['name'] != username:
        if 'DEBUG' in locals(): print "User not found in config YAML file. Fetching new token..."
        if Client_Secret is None:
            print "Authentication required for " + serverURL
            Client_Secret = getpass(prompt='Password: ')
        token_data = fetch_access_token(serverURL,API_Client,Client_Secret)
        expire = datetime.now()+timedelta(seconds=token_data['expires_in'])
        token = str(token_data['access_token'])
        data['users'].append({'name': username,'user': { 'token': token, 'expire': expire}})
        data['contexts'].append({'name': contextname,'context': { 'server': serverURL, 'user': username}})
        data['current-context'] = contextname

    # Save the new token to the config YAML file
    if 'DEBUG' in locals(): print "Saving new user/token..."
    with open(AppD_configfile, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)
    return token_data['access_token']

def read_config_yaml():
    try:
        stream = open(AppD_configfile)
    except IOError:
        create_new_config_yaml()

    with open(AppD_configfile, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def create_new_config_yaml():
    if 'DEBUG' in locals(): print "Create default YAML file"
    data = {
        'Kind': 'Config',
        'contexts': [ ],
        'users': [ ],
        'current-context': ''
    }

    # Write YAML file
    with open(AppD_configfile, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)

def create_sample_config_yaml():
    if 'DEBUG' in locals(): print "Create sample YAML file"
    data = {
        'Kind': 'Config',
        'contexts': [ {
            'context': {
                'server': 'localhost:8090',
                'user': 'admin/localhost:8090'
            },
            'name': 'localhost:8090/admin' 
        } ],
        'users': [ {
            'name': 'admin/localhost:8090',
            'user': { 
                'token': 'abcdef',
                'expire': '2099-12-31 23:59:59.9999999' }
        } ],
        'current-context': 'localhost:8090/admin'
    }

    # Write YAML file
    with open(AppD_configfile, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)