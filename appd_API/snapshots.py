import json
import sys
from datetime import datetime, timedelta
import time
from .entities import AppEntity

class SnapshotDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = {'fetch': self.controller.RESTfulAPI.fetch_snapshots}
        self.entityKeywords = ["snapshotExitCalls"]
        self.CSVfields = {  'Time':                 self.__str_snapshot_time,
                            'UserExperience':       self.__str_snapshot_userExperience,
                            'URL':                  self.__str_snapshot_URL,
                            'Summary':              self.__str_snapshot_summary,
                            'BussinessTransaction': self.__str_snapshot_BT,
                            'Tier':                 self.__str_snapshot_tier,
                            'Node':                 self.__str_snapshot_node,
                            'ExeTime':              self.__str_snapshot_exeTime}


    def __str_snapshot_time(self,snapshot):
        return datetime.fromtimestamp(float(snapshot['localStartTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')

    def __str_snapshot_userExperience(self,snapshot):
        return snapshot['userExperience']

    def __str_snapshot_URL(self,snapshot):
        return snapshot['URL']

    def __str_snapshot_summary(self,snapshot):
        return snapshot['summary'] if 'summary' in snapshot and sys.version_info[0] >= 3 else snapshot['summary'].encode('ASCII', 'ignore') if 'summary' in snapshot else ""

    def __str_snapshot_BT(self,snapshot):
        return snapshot['businessTransactionId']

    def __str_snapshot_tier(self,snapshot):
        return snapshot['applicationComponentId']

    def __str_snapshot_node(self,snapshot):
        return snapshot['applicationComponentNodeId']

    def __str_snapshot_exeTime(self,snapshot):
        return snapshot['timeTakenInMilliSecs']

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
#        entityDict.update({str(app_ID):snapshots})
#    else:
#        return 0
#
#    if 'DEBUG' in locals():
#        print "fetch_snapshots: Loaded " + str(len(snapshots)) + " snapshots."
#
#    return len(snapshots)


    ###### FROM HERE PUBLIC FUNCTIONS ######

