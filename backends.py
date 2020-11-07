#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath
from applications import getAppName

backendDict = dict()

###
 # Fetch application backends from a controller then add them to the backends dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application backends to fetch
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched backends. Zero if no backend was found.
###
def fetch_backends(app_ID,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching business transactions for App " + str(app_ID) + "...")

    # Retrieve All Registered Backends in a Business Application With Their Properties
    # GET /controller/rest/applications/application_name/backends
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/backends"
    params = {"output": "JSON"}

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        backends = json.loads(response)
    except JSONDecodeError:
        print ("fetch_backends: Could not process JSON content.")
        return None

    # Add loaded Backends to the Backend dictionary
    backendDict.update({str(app_ID):backends})

    if 'DEBUG' in locals():
        print "fetch_policies: Loaded " + str(len(backends)) + " backends."
        for appID in backendDict:
            print str(backendDict[appID])

    return len(backends)

###
 # Generate CSV output from backends data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain backends from local backends dictionary
 # @param custom_backendDict dictionary containing backends
 # @param fileName output file name
 # @return None
###
def generate_backends_CSV(appID_List,custom_backendDict=None,fileName=None):
    if appID_List is None and custom_backendDict is None:
        return
    elif custom_backendDict is None:
        custom_backendDict = backendDict

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['name', 'Application', 'exitPointType']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for appID in appID_List:
        for BE in custom_backendDict[str(appID)]:
            # Check if data belongs to a backend
            if 'exitPointType' not in BE: continue
            try:
                filewriter.writerow({'name': BE['name'].encode('ASCII', 'ignore'),
                                     'Application': getAppName(appID),
                                     'exitPointType': BE['exitPointType']})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                exit(1)
    if fileName is not None: csvfile.close()

###
 # Generate CSV output from backends data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain backends from local backends dictionary
 # @param custom_backendDict dictionary containing backends
 # @param fileName output file name
 # @return None
###
def generate_backends_JSON(appID_List,custom_backendDict=None,fileName=None):
    if appID_List is None and custom_backendDict is None:
        return
    elif custom_backendDict is None:
        custom_backendDict = backendDict

    backends = []
    for appID in appID_List:
        backends = backends + custom_backendDict[str(appID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(backends, outfile)
            outfile.close()
        except:
            print ("generate_backends_JSON: Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(backends)


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display backends from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_backends_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        backends = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_backends_from_stream: Could not process JSON data.")
        return 0
    custom_backendDict = {"0":[backends]} if type(backends) is dict else {"0":backends}
    if outputFormat and outputFormat == "JSON":
        generate_backends_JSON(appID_List=[0],custom_backendDict=custom_backendDict,fileName=outFilename)
    else:
        generate_backends_CSV(appID_List=[0],custom_backendDict=custom_backendDict,fileName=outFilename)

###
 # Display backends for a list of applications.
 # @param appID_List list of application IDs to fetch backends
 # @param selectors fetch only backends filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched backends. Zero if no backend was found.
###
def get_backends(appID_List,selectors=None,outputFormat=None):
    numBackends = 0
    for appID in appID_List:
        sys.stderr.write("get backends " + getAppName(appID) + "...\n")
        numBackends = numBackends + fetch_backends(appID)
    if numBackends == 0:
        sys.stderr.write("get_backends: Could not fetch any backends.\n")
    elif outputFormat and outputFormat == "JSON":
        generate_backends_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_backends_CSV(appID_List)
    return numBackends