#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath

rbacDict = dict()

###
 # Fetch users from a controller then add them to the users dictionary. Provide either an username/password or an access token.
 # @param selectors fetch specific user filtered by specified user name or ID
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched users. Zero if no user was found.
###
def fetch_users(selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching users list...")    
    # Get All Users
    # GET <controller_url>/controller/rest/users
    restfulPath = "/controller/api/rbac/v1/users"
    params = {"output": "JSON"}
    if selectors: restfulPath = restfulPath + selectors

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        data = json.loads(response)
    except JSONDecodeError:
        print ("fetch_users: Could not process JSON content.")
        return 0

    if loadData:
        index = 0
        for user in data['users']:
            if 'DEBUG' in locals(): print ("Fetching user " + user['name'] + "...")
            # Get User by ID
            # GET /controller/api/rbac/v1/users/userId
            restfulPath = "/controller/api/rbac/v1/users/" + str(user['id'])
            if serverURL and userName and password:
                response = fetch_RESTfulPath(restfulPath,params=params,userName=userName,password=password)
            else:
                response = fetch_RESTfulPath(restfulPath,params=params)
            try:
                userJSON = json.loads(response)
            except JSONDecodeError:
                print ("fetch_users: Could not process JSON content.")
                return 0
            data['users'][index] = userJSON
            index = index + 1

    # Add loaded users to the RBAC dictionary
    rbacDict.update(data)

    if 'DEBUG' in locals():
        print "fetch_users: Loaded " + str(len(data['users'])) + " users."
        for user in data['users']:
            print str(user)

    return len(rbacDict['users'])

###
 # Generate CSV output from rbac data, either from the local dictionary or from streamed data
 # @param rbac_Dict dictionary containing rbac data
 # @param fileName output file name
 # @return None
###
def generate_users_CSV(rbac_Dict=None,fileName=None):
    if rbac_Dict is None and len(rbacDict) == 0:
        print "generate_users_CSV: AppDynamics users not loaded."
        return
    elif rbac_Dict is None:
        rbac_Dict = rbacDict

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
    filewriter.writeheader()
         
    for user in rbac_Dict['users']:
        if 'id' not in user: continue
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
 # Generate JSON output from rbac data, either from the local dictionary or from streamed data
 # @param usrDict dictionary of rbac data
 # @param fileName output file name
 # @return None
###
def generate_users_JSON(rbac_Dict=None,fileName=None):
    if rbac_Dict is None and len(rbacDict) == 0:
        print "generate_users_JSON: Config settings not loaded."
        return
    elif rbac_Dict is None:
        rbac_Dict = rbacDict

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(rbac_Dict, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(rbac_Dict)


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display users from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_users_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        rbac_Dict = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_users_from_stream: Could not process JSON data.")
        return 0

    if outputFormat and outputFormat == "JSON":
        generate_users_JSON(rbac_Dict=rbac_Dict)
    else:
        generate_users_CSV(rbac_Dict=rbac_Dict)

###
 # Display users for a list of applications.
 # @param selectors fetch specific users filtered by specified user name
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched users. Zero if no user was found.
###
def get_users(selectors=None,outputFormat=None):
    sys.stderr.write("get users ...\n")
    numUsers = fetch_users(selectors=selectors,loadData=True)
    if numUsers == 0:
        sys.stderr.write("get_users: Could not fetch any users setting.\n")
    elif outputFormat and outputFormat == "JSON":
        generate_users_JSON()
    elif not outputFormat or outputFormat == "CSV":
        generate_users_CSV()
    return numUsers