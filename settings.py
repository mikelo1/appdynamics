#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath

configDict = dict()

###
 # Fetch config from a controller then add them to the config dictionary. Provide either an username/password or an access token.
 # @param selectors fetch specific configuration filtered by specified configuration name
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched config settings. Zero if no setting was found.
###
def fetch_config(selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching config list...")    
    # Retrieve All Controller Settings
    # GET <controller_url>/controller/rest/configuration
    restfulPath = "/controller/rest/configuration?name="
    params = {"output": "JSON"}
    if selectors: restfulPath = restfulPath + selectors

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        config = json.loads(response)
    except JSONDecodeError:
        print ("fetch_config: Could not process JSON content.")
        return 0

    # Add loaded settings to the configuration settings dictionary
    for setting in config:
        configDict.update({setting['name']:setting})

    if 'DEBUG' in locals():
        print "fetch_config: Loaded " + str(len(config)) + " settings."
        for setting in config:
            print str(setting)

    return len(configDict)

###
 # Generate CSV output from config data, either from the local dictionary or from streamed data
 # @param cfgDict dictionary of config settings, containing settings data
 # @param fileName output file name
 # @return None
###
def generate_config_CSV(cfgDict=None,fileName=None):
    if cfgDict is None and len(configDict) == 0:
        print "generate_config_CSV: Config settings not loaded."
        return
    elif cfgDict is None:
        cfgDict = configDict

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Name', 'Value', 'Scope', 'Updateable', 'Description']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()
         
    for setting in cfgDict:
        if 'updateable' not in cfgDict[setting]: continue
        try:
            filewriter.writerow({'Name': cfgDict[setting]['name'],
                                 'Value': cfgDict[setting]['value'],
                                 'Scope': cfgDict[setting]['scope'],
                                 'Updateable': cfgDict[setting]['updateable'],
                                 'Description': cfgDict[setting]['description']})
        except ValueError as valError:
            print (valError)
            if fileName is not None: csvfile.close()
            return (-1)
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from config data, either from the local dictionary or from streamed data
 # @param cfgDict dictionary of config settings, containing settings data
 # @param fileName output file name
 # @return None
###
def generate_config_JSON(cfgDict=None,fileName=None):
    if cfgDict is None and len(configDict) == 0:
        print "generate_config_JSON: Config settings not loaded."
        return
    elif cfgDict is None:
        cfgDict = configDict

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(cfgDict, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(cfgDict)


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display config from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_config_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        cfgDict = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_config_from_stream: Could not process JSON data.")
        return 0

    if outputFormat and outputFormat == "JSON":
        generate_config_JSON(cfgDict=cfgDict)
    else:
        generate_config_CSV(cfgDict=cfgDict)

###
 # Display config for a list of applications.
 # @param selectors fetch specific configuration filtered by specified configuration name
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched config settings. Zero if no setting was found.
###
def get_config(selectors=None,outputFormat=None):
    sys.stderr.write("get configuration ...\n")
    numSettings = fetch_config(selectors=selectors)
    if numSettings == 0:
        sys.stderr.write("get_config: Could not fetch any config setting.\n")
    elif outputFormat and outputFormat == "JSON":
        generate_config_JSON()
    elif not outputFormat or outputFormat == "CSV":
        generate_config_CSV()
    return numSettings