#!/usr/bin/python
import json
import csv
import sys
from entities import ControllerEntity

class RBACDict(ControllerEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_users_extended,
                                    'fetchByID': self.controller.RESTfulAPI.fetch_user_by_ID }
        self.entityJSONKeyword = "providerUniqueName"

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self, fileName=None):
        """
        Generate CSV output from rbac data
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['Name', 'Email', 'Roles', 'Groups']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for user in self.entityDict:
            # Check if data belongs to a user
            if 'providerUniqueName' not in user: continue
            elif 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True
            try:
                filewriter.writerow({'Name': user['name'],
                                     'Email': user['email'] if 'email' in user else None,
                                     'Roles': json.dumps(user['roles'] if 'roles' in user else None),
                                     'Groups': json.dumps(user['groups']) if 'groups' in user else None})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()
