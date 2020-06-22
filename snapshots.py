#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from appdRESTfulAPI import fetch_RESTful_JSON, timerange_to_params
from applications import getTierName, getNodeName

snapshotDict = dict()

###
 # Fetch snapshot from a controller then add them to the snapshot dictionary. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param app_ID the ID number of the application snapshot to fetch
 # @param minutesBeforeNow fetch only snapshots newer than a relative duration in minutes
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched snapshots. Zero if no snapshot was found.
###
def fetch_snapshots(serverURL,app_ID,minutesBeforeNow,userName=None,password=None,token=None):
    MAX_RESULTS="9999"
    if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
    #Retrieve Transaction Snapshots
    # GET /controller/rest/applications/application_name/request-snapshots
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"

    for i in range(int(minutesBeforeNow),0,-180): # loop "minutesBeforeNow" minutes in chunks of 180 minutes (3 hours)
        sinceTime = datetime.today()-timedelta(minutes=i)
        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
        params = timerange_to_params("AFTER_TIME",duration="1440",startEpoch=sinceEpoch)

        for retry in range(1,4):
            if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + "params "+str(params)+"...")
            if userName and password:
                data_chunck = fetch_RESTful_JSON(restfulPath,params=params,userName=userName,password=password)
            elif token:
                data_chunck = fetch_RESTful_JSON(restfulPath,params=params)

            if data_chunck is not None:
                break
            elif retry < 3:
                print "Failed to fetch snapshots. Retrying (",retry," of 3)..."
            else:
                print "Giving up."
                return None
    
        if 'snapshots' not in locals():
            snapshots = data_chunck
            if 'DEBUG' in locals(): print "fetch_snapshots: Added " + str(len(snapshots)) + " snapshots."
        else:
            # Append retrieved data to root
            for new_snapshot in data_chunck:
                snapshots.append(new_snapshot)
            if 'DEBUG' in locals(): print "fetch_snapshots: Added " + str(len(snapshots)) + " snapshots."

    # Add loaded events to the event dictionary
    if 'snapshots' in locals():
        snapshotDict.update({str(app_ID):snapshots})
    else:
        return 0

    if 'DEBUG' in locals():
        print "fetch_snapshots: Loaded " + str(len(snapshots)) + " snapshots."

    return len(snapshots)

def convert_snapshots_JSON_to_CSV(inFileName,outFilename=None):
    json_file = open(inFileName)
    snapshots = json.load(json_file)
    generate_snapshots_CSV(app_ID=0,snapshots=snapshots,fileName=outFilename)

def generate_snapshots_CSV(app_ID,snapshots=None,fileName=None):
    if snapshots is None and str(app_ID) not in snapshotDict:
        print "Snapshots for application "+str(app_ID)+" not loaded."
        return
    elif snapshots is None and str(app_ID) in snapshotDict:
        snapshots = snapshotDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Time', 'URL', 'BussinessTransaction', 'Tier', 'Node', 'ExeTime']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for snapshot in snapshots:
        Time = datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        Tier = getTierName(snapshot['applicationComponentId'])
        Node = getNodeName(snapshot['applicationComponentNodeId'])

        try:
            filewriter.writerow({'Time': Time,
                                'URL': snapshot['URL'],
                                'BussinessTransaction': snapshot['businessTransactionId'],
                                'Tier': Tier,
                                'Node': Node,
                                'ExeTime': snapshot['timeTakenInMilliSecs']})
        except:
            print ("Could not write to the output file " + fileName + ".")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()

def get_snapshots(serverURL,app_ID,minutesBeforeNow,userName=None,password=None,token=None):
    if serverURL == "dummyserver":
        build_test_events(app_ID)
    elif userName and password:
        if fetch_snapshots(serverURL,app_ID,minutesBeforeNow,userName=userName,password=password) == 0:
            print "get_snapshots: Failed to retrieve snapshots for application " + str(app_ID)
            return None
    elif token:
        if fetch_snapshots(serverURL,app_ID,minutesBeforeNow,token=token) == 0:
            print "get_snapshots: Failed to retrieve snapshots for application " + str(app_ID)
            return None
    generate_snapshots_CSV(app_ID)