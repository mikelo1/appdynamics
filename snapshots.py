#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from appdRESTfulAPI import fetch_RESTfulPath, timerange_to_params
from nodes import getTierName, getNodeName

snapshotDict = dict()

###
 # Fetch snapshot from a controller then add them to the snapshot dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application snapshot to fetch
 # @param minutesBeforeNow fetch only snapshots newer than a relative duration in minutes
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched snapshots. Zero if no snapshot was found.
###
def fetch_snapshots(app_ID,minutesBeforeNow,selectors=None,serverURL=None,userName=None,password=None,token=None):
    MAX_RESULTS="9999"
    if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
    #Retrieve Transaction Snapshots
    # GET /controller/rest/applications/application_name/request-snapshots
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"

    for i in range(int(minutesBeforeNow),0,-180): # loop "minutesBeforeNow" minutes in chunks of 180 minutes (3 hours)
        sinceTime = datetime.today()-timedelta(minutes=i)
        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
        params = timerange_to_params("AFTER_TIME",duration="180",startEpoch=sinceEpoch)
        params.update({"output": "JSON"})
        if selectors: params.update(selectors)

        for retry in range(1,4):
            if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", params "+str(params)+"...")
            if serverURL and userName and password:
                response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
            else:
                response = fetch_RESTfulPath(restfulPath,params=params)

            try:
                data_chunck = json.loads(response)
            except JSONDecodeError:
                if retry < 3:
                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
                else:
                    print "Giving up."
                    return None
            if data_chunck is not None: break
    
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

    fieldnames = ['Time', 'UserExperience', 'URL', 'Summary', 'BussinessTransaction', 'Tier', 'Node', 'ExeTime']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for snapshot in snapshots:
        if 'snapshotExitCalls' not in snapshot: continue
        Time = datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        AppID= snapshot['applicationId']
        Tier = getTierName(AppID,snapshot['applicationComponentId'])
        Node = getNodeName(AppID,snapshot['applicationComponentNodeId'])
        Summary = snapshot['summary'].encode('ASCII', 'ignore') if 'summary' in snapshot else ""

        try:
            filewriter.writerow({'Time': Time,
                                'UserExperience': snapshot['userExperience'],
                                'URL': snapshot['URL'],
                                'Summary': Summary,
                                'BussinessTransaction': snapshot['businessTransactionId'],
                                'Tier': Tier,
                                'Node': Node,
                                'ExeTime': snapshot['timeTakenInMilliSecs']})
        except:
            print ("Could not write to the output.")
            continue
    if fileName is not None: csvfile.close()

def generate_snapshots_JSON(app_ID,snapshots=None,fileName=None):
    if snapshots is None and str(app_ID) not in snapshotDict:
        print "Snapshots for application "+str(app_ID)+" not loaded."
        return
    elif snapshots is None and str(app_ID) in snapshotDict:
        snapshots = snapshotDict[str(app_ID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(policies, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(snapshots)


###### FROM HERE PUBLIC FUNCTIONS ######


def get_snapshots_from_stream(streamdata,outputFormat=None,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        snapshots = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_snapshots_JSON(app_ID=0,snapshots=snapshots,fileName=outFilename)
    else:
        generate_snapshots_CSV(app_ID=0,snapshots=snapshots,fileName=outFilename)

def get_snapshots(app_ID,minutesBeforeNow,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_events(app_ID)
    elif serverURL and userName and password:
        if fetch_snapshots(app_ID,minutesBeforeNow,selectors=selectors,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_snapshots: Failed to retrieve snapshots for application " + str(app_ID)
            return None
    else:
        if fetch_snapshots(app_ID,minutesBeforeNow,selectors=selectors,token=token) == 0:
            print "get_snapshots: Failed to retrieve snapshots for application " + str(app_ID)
            return None
    if outputFormat and outputFormat == "JSON":
        generate_snapshots_JSON(app_ID)
    else:
        generate_snapshots_CSV(app_ID)