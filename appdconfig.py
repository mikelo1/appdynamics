#!/usr/bin/python
import yaml
import csv
from datetime import datetime, timedelta
import time

AppD_configfile="appdconfig.yaml"

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

def build_test_config_yaml():
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


###### FROM HERE PUBLIC FUNCTIONS ######

def get_current_context_serverURL():
    data = read_config_yaml()
    if 'current-context' in data and len(data['current-context']) > 0:
        for context in data['contexts']:
            if context['name'] == data['current-context']:
             return context['context']['server']

def get_current_context_servername():
    data = read_config_yaml()
    if 'current-context' in data and len(data['current-context']) > 0:
        return data['current-context'].split('/')[0]
    else:
        if 'DEBUG' in locals(): print "Cannot get context data. Did you login to any controller machine?"
        return None

def get_current_context_username():
    data = read_config_yaml()
    if 'current-context' in data and len(data['current-context']) > 0:
        return data['current-context'].split('/')[1]
    else:
        if 'DEBUG' in locals(): print "Cannot get context data. Did you login to any controller machine?"
        return None

def get_current_context_token():
    data = read_config_yaml()
    if 'current-context' in data and len(data['current-context']) > 0:
        context = data['current-context'].split('/')
        for user in data['users']:
            username = context[1] + "/" + context[0]
            if user['name'] == username:
                if 'expire' in user['user'] and datetime.today() < user['user']['expire']:
                    if 'DEBUG' in locals(): print "Found valid token in config YAML file."
                    return user['user']['token']
                else:
                    if 'DEBUG' in locals(): print "Token expired or invalid in config YAML file."
                    return None
    else:
        print "Cannot get context data. Did you login to any controller machine?"
        return None

def set_new_token(API_Client,access_token,expires_in):
    data = read_config_yaml()
    for user in data['users']:
        username = user['name'].split('/')[0]
        if username == API_Client:
            user['user']['token']  = str(access_token)
            user['user']['expire'] = datetime.now()+timedelta(seconds=expires_in)
            if 'DEBUG' in locals(): print "Saving new token..."
            with open(AppD_configfile, "w") as outfile:
                yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)
            return True
    return False

def create_or_select_user(serverURL,API_Client):
    servername = serverURL.split('/')[2]
    username = API_Client + "/" + servername
    contextname = servername + "/" + API_Client

    data = read_config_yaml()
    # Check whether provided user does exist or not
    for user in data['users']:
        if user['name'] == username:
            break

    if 'user' not in locals() or user['name'] != username:
        # Create the new user
        data['users'].append({'name': username,'user': {}})
        data['contexts'].append({'name': contextname,'context': { 'server': serverURL, 'user': username}})
        changes = True
    
    # Set this one as current-context, if not already
    if data['current-context'] != contextname:
        data['current-context'] = contextname
        changes = True
    
    # Save changes, if any
    if 'changes' in locals():
        if 'DEBUG' in locals(): print "Saving changes..."
        with open(AppD_configfile, "w") as outfile:
            yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)

def get_password(basicAuthFile,API_Client):
    with open(basicAuthFile, mode='r') as csv_file:
        auth_dict = csv.DictReader(csv_file,fieldnames=['password','apiClient'])
        for credential in auth_dict:
            if credential['apiClient'] == API_Client:
                return credential['password']