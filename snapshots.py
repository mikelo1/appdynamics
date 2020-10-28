#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from appdRESTfulAPI import fetch_RESTfulPath, timerange_to_params
from nodes import getTierName, getNodeName
from applications import getAppName

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

    for i in range(int(minutesBeforeNow),0,-1440): # loop "minutesBeforeNow" minutes in chunks of 180 minutes (3 hours)
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

    # Add loaded snapshots to the snapshot dictionary
    if 'snapshots' in locals():
        snapshotDict.update({str(app_ID):snapshots})
    else:
        return 0

    if 'DEBUG' in locals():
        print "fetch_snapshots: Loaded " + str(len(snapshots)) + " snapshots."

    return len(snapshots)


def fetch_snapshots2(app_ID,minutesBeforeNow,selectors=None,serverURL=None,userName=None,password=None,token=None):
    MAX_RESULTS = RESULTS = 9
    lastSnapshotTimestamp = 0
    snapshots = []
    DEBUG=True
    if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
    #Retrieve Transaction Snapshots
    # GET /controller/rest/applications/application_name/request-snapshots
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"

    while RESULTS == MAX_RESULTS:
        sinceTime = datetime.today()-timedelta(minutes=minutesBeforeNow)
        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
        params = timerange_to_params("BEFORE_NOW",duration=minutesBeforeNow)
        params.update({"output": "JSON","maximum-results": str(MAX_RESULTS)})
        if selectors: params.update(selectors)

        for retry in range(1,4):
            if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", params "+str(params)+"...")
            if serverURL and userName and password:
                response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
            else:
                response = fetch_RESTfulPath(restfulPath,params=params)
            try:
                data_chunck = json.loads(response)
            except TypeError:
                print response
                if retry < 3:
                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
                    continue
                else:
                    print "Giving up."
                    return None
            if "data_chunck" in locals(): break
    
        if 'DEBUG' in locals(): print "fetch_snapshots: Added " + str(len(data_chunck)) + " snapshots."
        lastSnapshotTimestamp = int(data_chunck[len(data_chunck)-1]['serverStartTime'])
        print "last snapshot start time: " + str(lastSnapshotTimestamp)
        epochNow = int(round(time.time()*1000))
        print type(epochNow), epochNow
        minutesBeforeNow = int(round((epochNow - lastSnapshotTimestamp) / 1000 / 60))
        print type(minutesBeforeNow), minutesBeforeNow
        RESULTS = len(data_chunck)
        print "startTime: ",data_chunck[0]['serverStartTime'],",lastTime: ",data_chunck[len(data_chunck)-1]['serverStartTime']
        snapshots = snapshots + data_chunck

    # Add loaded snapshots to the snapshot dictionary
    if 'snapshots' in locals():
        snapshotDict.update({str(app_ID):snapshots})
    else:
        return 0

    if 'DEBUG' in locals():
        print "fetch_snapshots: Loaded " + str(len(snapshots)) + " snapshots."

    return len(snapshots)


###
 # Generate CSV output from snapshots data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain snapshots from local snapshots dictionary
 # @param snapshots data containing snapshots
 # @param fileName output file name
 # @return None
###
def generate_snapshots_CSV(appID_List=None,snapshots=None,fileName=None):
    if appID_List is None and snapshots is None:
        return
    elif snapshots is None:
        snapshots = []
        for appID in appID_List:
            snapshots = snapshots + snapshotDict[str(appID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            sys.stderr.write ("Could not open output file " + fileName + ".\n")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['Time', 'UserExperience', 'URL', 'Summary', 'Application', 'BussinessTransaction', 'Tier', 'Node', 'ExeTime']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for snapshot in snapshots:
        if 'snapshotExitCalls' not in snapshot: continue
        Time = datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        appID= snapshot['applicationId']
        appName = getAppName(appID) 
        Tier = getTierName(appID,snapshot['applicationComponentId'])
        Node = getNodeName(appID,snapshot['applicationComponentNodeId'])
        Summary = snapshot['summary'].encode('ASCII', 'ignore') if 'summary' in snapshot else ""

        try:
            filewriter.writerow({'Time': Time,
                                'UserExperience': snapshot['userExperience'],
                                'URL': snapshot['URL'],
                                'Summary': Summary,
                                'Application': appName,
                                'BussinessTransaction': snapshot['businessTransactionId'],
                                'Tier': Tier,
                                'Node': Node,
                                'ExeTime': snapshot['timeTakenInMilliSecs']})
        except:
            print ("Could not write to the output.")
            continue
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from snapshots data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain snapshots from local snapshots dictionary
 # @param snapshots data containing snapshots
 # @param fileName output file name
 # @return None
###
def generate_snapshots_JSON(appID_List=None,snapshots=None,fileName=None):
    if appID_List is None and snapshots is None:
        return
    elif snapshots is None:
        snapshots = []
        for appID in appID_List:
            snapshots = snapshots + snapshotDict[str(appID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(policies, outfile)
            outfile.close()
        except:
            sys.stderr.write ("Could not open output file " + fileName + ".\n")
            return (-1)
    else:
        print json.dumps(snapshots)



###### FROM HERE PUBLIC FUNCTIONS ######



###
 # Display snapshots from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_snapshots_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        snapshots = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_snapshots_from_stream: Could not process JSON data.")
        return 0
    if outputFormat and outputFormat == "JSON":
        generate_snapshots_JSON(snapshots=snapshots,fileName=outFilename)
    else:
        generate_snapshots_CSV(snapshots=snapshots,fileName=outFilename)

###
 # Display snapshots for a list of applications.
 # @param appID_List list of application IDs to fetch snapshots
 # @param minutesBeforeNow fetch only snapshots newer than a relative duration in minutes
 # @param selectors fetch only snapshots filtered by specified selectors
 # @return the number of fetched snapshots. Zero if no snapshots was found.
###
def get_snapshots(appID_List,minutesBeforeNow,selectors=None,outputFormat=None):
    numSnapshots = 0
    for appID in appID_List:
        sys.stderr.write("get snapshots " + getAppName(appID) + "...\n")
        numSnapshots = numSnapshots + fetch_snapshots(appID,minutesBeforeNow,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_snapshots_JSON(appID_List)
    else:
        generate_snapshots_CSV(appID_List)
    return numSnapshots