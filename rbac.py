#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI

class RBACDict:
    rbacDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.rbacDict)

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

        for userName in self.rbacDict:
            user = self.rbacDict[userName]
            if 'id' not in user: continue
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
     # Generate JSON output from rbac data
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,fileName=None):
        data = [ self.rbacDict[userName] for userName in self.rbacDict ]
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(data, outfile)
                outfile.close()
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(data)

    ###
     # Load users from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID
     # @return the number of loaded users. Zero if no user was loaded.
    ###
    def load(self,streamdata,appID=None):
        try:
            usersJSON = json.loads(streamdata)
        except TypeError as error:
            print ("load_users: "+str(error))
            return 0
        print json.dumps(usersJSON)
        for user in usersJSON:
            # Add loaded user to the users dictionary
            if 'providerUniqueName' not in user: continue
            userName = user['name']
            self.rbacDict.update({userName:user})
        return len(usersJSON)


    ###
     # Load user details for all users from a controller
     # @param app_ID the ID number of the application users to fetch
     # @return the number of fetched users. Zero if no user was found.
    ###
    def load_details(self):
        count = 0
        for userName in self.rbacDict:
            response = RESTfulAPI().fetch_user(self.rbacDict[userName]['id'])
            if response is not None:
                try:
                    user = json.loads(response)
                except TypeError as error:
                    print ("load_duser_details: "+str(error))
                    continue
                self.rbacDict.update({userName:user})
                count += 1
        return count