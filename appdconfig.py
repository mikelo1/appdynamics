#!/usr/bin/python
import yaml
import csv
from datetime import datetime, timedelta
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
        return "({0})".format(self.data)

    def get_current_context_serverURL(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            for context in self.data['contexts']:
                if context['name'] == self.data['current-context']:
                 return context['context']['server']

    def get_current_context_servername(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            return self.data['current-context'].split('/')[0]
        else:
            return None

    def get_current_context_username(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            return self.data['current-context'].split('/')[1]
        else:
            return None

    def get_current_context_token(self):
        if 'current-context' in self.data and len(self.data['current-context']) > 0:
            context = self.data['current-context'].split('/')
            for user in self.data['users']:
                username = context[1] + "/" + context[0]
                if user['name'] == username:
                    if 'expire' in user['user'] and datetime.today() < user['user']['expire']:
                        if 'DEBUG' in locals(): print "Found valid token in config YAML file."
                        return user['user']['token']
                    else:
                        if 'DEBUG' in locals(): print "Token expired or invalid in config YAML file."
                        return None
        else:
            if 'DEBUG' in locals(): print "get_current_context_token: Cannot get context data. Did you login to any controller machine?"
            return None

    def set_new_token(self,API_Client,access_token,expires_in):
        for user in self.data['users']:
            username = user['name'].split('/')[0]
            if username == API_Client:
                user['user']['token']  = str(access_token)
                user['user']['expire'] = datetime.now()+timedelta(seconds=expires_in)
                if 'DEBUG' in locals(): print "Saving new token..."
                with open(self.configFile, "w") as outfile:
                    yaml.dump(self.data, outfile, default_flow_style=False, allow_unicode=True)
                return True
        return False

    def create_or_select_user(self,serverURL,API_Client):
        servername = serverURL.split('/')[2]
        username = API_Client + "/" + servername
        contextname = servername + "/" + API_Client

        # Check whether provided user does exist or not
        for user in self.data['users']:
            if user['name'] == username:
                break

        if 'user' not in locals() or user['name'] != username:
            # Create the new user
            self.data['users'].append({'name': username,'user': {}})
            self.data['contexts'].append({'name': contextname,'context': { 'server': serverURL, 'user': username}})
            changes = True
        
        # Set this one as current-context, if not already
        if self.data['current-context'] != contextname:
            self.data['current-context'] = contextname
            changes = True
        
        # Save changes, if any
        if 'changes' in locals():
            if 'DEBUG' in locals(): print "Saving changes..."
            with open(self.configFile, "w") as outfile:
                yaml.dump(self.data, outfile, default_flow_style=False, allow_unicode=True)

class BasicAuth:
    authFile  = ""

    def __init__(self,basicAuthFile=None):
        if basicAuthFile is not None:
            try:
                stream = open(self.authFile)
            except IOError as exc:
                print(exc)
                return None
            self.authFile = basicAuthFile

    def __str__(self):
        return "({0})".format(self.authFile)

    def get_password(self,API_Client):
        auth_dict = dict()
        print self.authFile
        with open(self.authFile, mode='r') as csv_file:
            try:
                auth_dict = csv.DictReader(csv_file,fieldnames=['password','apiClient'])
            except IOError as exc:
                print(exc)
            for credential in auth_dict:
                if credential['apiClient'] == API_Client:
                    return credential['password']