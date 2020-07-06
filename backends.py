#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath

backendDict = dict()

class Backend:
    name          = ""
    exitPointType = ""
    def __init__(self,name,exitPointType):
        self.name          = name
        self.exitPointType = exitPointType
    def __str__(self):
        return "({0},{1}".format(self.name,self.entryPointType)

###
 # Fetch application backends from a controller then add them to the backends dictionary. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param app_ID the ID number of the application backends to fetch
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched backends. Zero if no backend was found.
###
def fetch_backends(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None):
    if 'DEBUG' in locals(): print ("Fetching business transactions for App " + str(app_ID) + "...")

    # Retrieve All Registered Backends in a Business Application With Their Properties
    # GET /controller/rest/applications/application_name/backends
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/backends"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

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

def generate_backends_CSV(app_ID,backends=None,fileName=None):
    if backends is None and str(app_ID) not in backendDict:
        print "Backends for application "+str(app_ID)+" not loaded."
        return
    elif backends is None and str(app_ID) in backendDict:
        backends = backendDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['name', 'exitPointType']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for BE in backends:
        if 'exitPointType' not in BE: continue
        try:
            filewriter.writerow({'name': BE['name'].encode('ASCII', 'ignore'),
                                 'exitPointType': BE['exitPointType']})
        except:
            print ("Could not write to the output file. Backend: " + Backend['name'] + ", " + Backend['exitPointType'])
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

def generate_backends_JSON(app_ID,backends=None,fileName=None):
    if backends is None and str(app_ID) not in backendDict:
        print "Backends for application "+str(app_ID)+" not loaded."
        return
    elif backends is None and str(app_ID) in backendDict:
        backends = backendDict[str(app_ID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(backends, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(backends)


###### FROM HERE PUBLIC FUNCTIONS ######


def get_backends_from_stream(streamdata,outputFormat=None,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        BEs = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_backends_JSON(app_ID=0,backends=BEs,fileName=outFilename)
    else:
        generate_backends_CSV(app_ID=0,backends=BEs,fileName=outFilename)

def get_backends(app_ID,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_policies(app_ID)
    elif serverURL and userName and password:
        number = fetch_backends(app_ID,selectors=selectors,serverURL=serverURL,userName=userName,password=password)
        if number == 0:
            print "get_backends: Failed to retrieve backends for application " + str(app_ID)
            return None
    else:
        number = fetch_backends(app_ID,selectors=selectors,token=token)
        if number == 0:
            print "get_backends: Failed to retrieve backends for application " + str(app_ID)
            return None
    if 'DEBUG' in locals(): print "get_backends: [INFO] Loaded",number,"backends"
    if outputFormat and outputFormat == "JSON":
        generate_backends_JSON(app_ID)
    elif not outputFormat or outputFormat == "CSV":
        generate_backends_CSV(app_ID)