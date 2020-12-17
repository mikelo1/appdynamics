#!/usr/bin/python
import json
import csv
import sys
from datetime import datetime, timedelta
import time
from nodes import NodeDict
from applications import ApplicationDict

class SnapshotDict:
    snapshotDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.snapshotDict)

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
#def fetch_snapshots(app_ID,minutesBeforeNow,selectors=None,serverURL=None,userName=None,password=None,token=None):
#    MAX_RESULTS="9999"
#    if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
#    #Retrieve Transaction Snapshots
#    # GET /controller/rest/applications/application_name/request-snapshots
#    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"

#    for i in range(int(minutesBeforeNow),0,-1440): # loop "minutesBeforeNow" minutes in chunks of 180 minutes (3 hours)
#        sinceTime = datetime.today()-timedelta(minutes=i)
#        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
#        params = timerange_to_params("AFTER_TIME",duration="180",startEpoch=sinceEpoch)
#        params.update({"output": "JSON"})
#        if selectors: params.update(selectors)

#        for retry in range(1,4):
#            if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", params "+str(params)+"...")
#            if serverURL and userName and password:
#                response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
#            else:
#                response = fetch_RESTfulPath(restfulPath,params=params)

#            try:
#                data_chunck = json.loads(response)
#            except JSONDecodeError:
#                if retry < 3:
#                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
#                else:
#                    print "Giving up."
#                    return None
#            if data_chunck is not None: break
#    
#        if 'snapshots' not in locals():
#            snapshots = data_chunck
#            if 'DEBUG' in locals(): print "fetch_snapshots: Added " + str(len(snapshots)) + " snapshots."
#        else:
#            # Append retrieved data to root
#            for new_snapshot in data_chunck:
#                snapshots.append(new_snapshot)
#            if 'DEBUG' in locals(): print "fetch_snapshots: Added " + str(len(snapshots)) + " snapshots."

#    # Add loaded snapshots to the snapshot dictionary
#    if 'snapshots' in locals():
#        snapshotDict.update({str(app_ID):snapshots})
#    else:
#        return 0

#    if 'DEBUG' in locals():
#        print "fetch_snapshots: Loaded " + str(len(snapshots)) + " snapshots."

#    return len(snapshots)


#def fetch_snapshots2(app_ID,minutesBeforeNow,selectors=None,serverURL=None,userName=None,password=None,token=None):
#    MAX_RESULTS = RESULTS = 9
#    lastSnapshotTimestamp = 0
#    snapshots = []
#    DEBUG=True
#    if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", for the last "+str(minutesBeforeNow)+" minutes...")
#    #Retrieve Transaction Snapshots
#    # GET /controller/rest/applications/application_name/request-snapshots
#    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"
#
#    while RESULTS == MAX_RESULTS:
#        sinceTime = datetime.today()-timedelta(minutes=minutesBeforeNow)
#        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
#        params = timerange_to_params("BEFORE_NOW",duration=minutesBeforeNow)
#        params.update({"output": "JSON","maximum-results": str(MAX_RESULTS)})
#        if selectors: params.update(selectors)
#
#        for retry in range(1,4):
#            if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + ", params "+str(params)+"...")
#            if serverURL and userName and password:
#                response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
#            else:
#                response = fetch_RESTfulPath(restfulPath,params=params)
#            try:
#                data_chunck = json.loads(response)
#            except TypeError:
#                print response
#                if retry < 3:
#                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
#                    continue
#                else:
#                    print "Giving up."
#                    return None
#            if "data_chunck" in locals(): break
    #
#        if 'DEBUG' in locals(): print "fetch_snapshots: Added " + str(len(data_chunck)) + " snapshots."
#        lastSnapshotTimestamp = int(data_chunck[len(data_chunck)-1]['serverStartTime'])
#        print "last snapshot start time: " + str(lastSnapshotTimestamp)
#        epochNow = int(round(time.time()*1000))
#        print type(epochNow), epochNow
#        minutesBeforeNow = int(round((epochNow - lastSnapshotTimestamp) / 1000 / 60))
#        print type(minutesBeforeNow), minutesBeforeNow
#        RESULTS = len(data_chunck)
#        print "startTime: ",data_chunck[0]['serverStartTime'],",lastTime: ",data_chunck[len(data_chunck)-1]['serverStartTime']
#        snapshots = snapshots + data_chunck
#
#    # Add loaded snapshots to the snapshot dictionary
#    if 'snapshots' in locals():
#        snapshotDict.update({str(app_ID):snapshots})
#    else:
#        return 0
#
#    if 'DEBUG' in locals():
#        print "fetch_snapshots: Loaded " + str(len(snapshots)) + " snapshots."
#
#    return len(snapshots)


    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from snapshots data
     # @param appID_List list of application IDs, in order to obtain snapshots from local snapshots dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

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

        for appID in appID_List:
            if str(appID) not in self.snapshotDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for snapshot in self.snapshotDict[str(appID)]:
                # Check if data belongs to an event
                if 'snapshotExitCalls' not in snapshot: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True
                Time = datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
                appID= snapshot['applicationId']
                appName = ApplicationDict().getAppName(appID) 
                Tier = NodeDict().getTierName(appID,snapshot['applicationComponentId'])
                Node = NodeDict().getNodeName(appID,snapshot['applicationComponentNodeId'])
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
     # Generate JSON output from snapshots data
     # @param appID_List list of application IDs, in order to obtain snapshots from local snapshots dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return
        snapshots = [ self.snapshotDict[str(appID)] for appID in appID_List ]
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(snapshots, outfile)
                outfile.close()
            except:
                sys.stderr.write ("Could not open output file " + fileName + ".\n")
                return (-1)
        else:
            print json.dumps(snapshots)

    ###
     # Load snapshots from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID the ID number of the application where to load the snapshots data.
     # @return the number of loaded snapshots. Zero if no snapshot was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            snapshots = json.loads(streamdata)
        except TypeError as error:
            print ("load_snapshots: "+str(error))
            return 0
        # Add loaded snapshots to the snapshots dictionary
        if type(snapshots) is dict:
            self.snapshotDict.update({str(appID):[snapshots]})
        else:
            self.snapshotDict.update({str(appID):snapshots})
        return len(snapshots)