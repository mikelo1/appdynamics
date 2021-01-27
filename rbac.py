#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from entities import ControllerEntity

class RBACDict(ControllerEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_users_extended}

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from rbac data
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self, fileName=None):
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

        for userName in self.entityDict:
            user = self.entityDict[userName]
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

    ###
     # Load user details for all users from a controller
     # @param app_ID the ID number of the application users to fetch
     # @return the number of fetched users. Zero if no user was found.
    ###
    def load_details(self):
        count = 0
        for userName in self.entityDict:
            response = RESTfulAPI().fetch_user(self.entityDict[userName]['id'])
            if response is not None:
                try:
                    user = json.loads(response)
                except TypeError as error:
                    print ("load_duser_details: "+str(error))
                    continue
                self.entityDict.update({userName:user})
                count += 1
        return count