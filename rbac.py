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

###
 # Fetch users from a controller then add them to the users dictionary. Provide either an username/password or an access token.
 # @param selectors fetch specific user filtered by specified user name or ID
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched users. Zero if no user was found.
###
#def fetch_users(selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
#    if 'DEBUG' in locals(): print ("Fetching users list...")    
#    # Get All Users
#    # GET <controller_url>/controller/rest/users
#    restfulPath = "/controller/api/rbac/v1/users"
#    params = {"output": "JSON"}
#    if selectors: restfulPath = restfulPath + selectors
#
#    if serverURL and userName and password:
#        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
#    else:
#        response = fetch_RESTfulPath(restfulPath,params=params)
#
#    try:
#        data = json.loads(response)
#    except JSONDecodeError:
#        print ("fetch_users: Could not process JSON content.")
#        return 0
#
#    if loadData:
#        index = 0
#        for user in data['users']:
#            if 'DEBUG' in locals(): print ("Fetching user " + user['name'] + "...")
#            # Get User by ID
#            # GET /controller/api/rbac/v1/users/userId
#            restfulPath = "/controller/api/rbac/v1/users/" + str(user['id'])
#            if serverURL and userName and password:
#                response = fetch_RESTfulPath(restfulPath,params=params,userName=userName,password=password)
#            else:
#                response = fetch_RESTfulPath(restfulPath,params=params)
#            try:
#                userJSON = json.loads(response)
#            except JSONDecodeError:
#                print ("fetch_users: Could not process JSON content.")
#                return 0
#            data['users'][index] = userJSON
#            index = index + 1
#
#    # Add loaded users to the RBAC dictionary
#    rbacDict.update(data)
#
#    if 'DEBUG' in locals():
#        print "fetch_users: Loaded " + str(len(data['users'])) + " users."
#        for user in data['users']:
#            print str(user)
#
#    return len(rbacDict['users'])


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
                                     'Email': user['email'] if 'email' in user else "",
                                     'Roles': json.dumps(user['roles'] if 'roles' in user else ""),
                                     'Groups': json.dumps(user['groups']) if 'groups' in user else ""})
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
            users = json.loads(streamdata)
        except TypeError as error:
            print ("load_users: "+str(error))
            return 0
        for user in users:
            # Add loaded user to the users dictionary
            if 'id' not in user: continue
            userName = user['name']
            self.rbacDict.update({userName:user})
        return len(users)


    ###
     # Load user details for all users from a controller
     # @param app_ID the ID number of the application users to fetch
     # @return the number of fetched users. Zero if no user was found.
    ###
    def load_details(self):
        count = 0
        for userName in self.rbacDict:
            response = RESTfulAPI().fetch_user_by_ID(self.rbacDict[userName]['id'])
            if response is not None:
                try:
                    user = json.loads(response)
                except TypeError as error:
                    print ("load_duser_details: "+str(error))
                    continue
                self.rbacDict.update({userName:user})
                count += 1
        return count