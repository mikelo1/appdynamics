#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath, update_RESTful_JSON
from applications import getAppName

scheduleDict = dict()

class ScheduleElement:
    appID  = 0
    schedID= 0
    data   = None
    def __init__(self,appID,schedID,data=None):
        self.appID  = appID
        self.schedID= schedID
        self.data   = data
    def __str__(self):
        return "({0},{1},{2})".format(self.appID,self.schedID,self.data)

class Schedule:
    Id         = 0
    name       = "" # i.e.: "End of Business Hour: 5pm-6pm, Mon-Fri"
    appName    = "" 
    description= "" # i.e.: "This schedule is active Monday through Friday, during end of business hour"
    timezone   = "" # i.e.: "Asia/Kolkata"
    config     = None
    def __init__(self,Id,name,appName,description,timezone,config=None):
        self.Id         = Id
        self.name       = name
        self.appName    = appName
        self.description= description
        self.timezone   = timezone
        self.config     = config
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5})".format(self.Id,self.name,self.appName,self.description,self.timezone,self.config)

class ScheduleConfiguration:
    frequency= "" # i.e.: "WEEKLY", "ONE_TIME" or "CUSTOM"
    startTime= "" # i.e.: "06:00"
    endTime  = "" # i.e.: "18:00"
    startCron= "" # i.e.: "0 0 8 ? * 2-6"
    endCron  = "" # i.e.: "0 0 12 ? * 2-6"
    startDate= "" # i.e.: "01/01/2019"
    endDate  = "" # i.e.: "01/01/2019"
    occurrenc= "" # i.e.: "FIRST"
    day      = "" # i.e.: "SUNDAY"
    days     = [] # i.e.: ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]
    def __init__(self,frequency,startTime=None,endTime=None,startCron=None,endCron=None,startDate=None,endDate=None,occurrenc=None,day=None,days=None):
        self.frequency= frequency
        self.startTime= startTime
        self.endTime  = endTime
        self.startCron= startCron
        self.endCron  = endCron
        self.startDate= startDate
        self.endDate  = endDate
        self.occurrenc= occurrenc
        self.day      = day
        self.days     = days
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5})".format(self.frequency,self.startTime,self.endTime,self.startCron,self.endCron,self.startDate,self.endDate,self.occurrenc,self.day,self.days)


def build_test_schedules(app_ID):
    schedules1=json.loads('[{"timezone":"Europe/Brussels","description":"This schedule is active Monday through Friday, during business hours","id":30201,"scheduleConfiguration":{"scheduleFrequency":"WEEKLY","endTime":"17:00","days":["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],"startTime":"08:00"},"name":"Weekdays:8am-5pm,Mon-Fri"}]')
    schedules2=json.loads('[{"timezone":"Europe/Brussels","description":"This schedule is active Monday through Friday, during business hours","id":30201,"scheduleConfiguration":{"scheduleFrequency":"WEEKLY","endTime":"17:00","days":["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],"startTime":"08:00"},"name":"Weekdays:8am-5pm,Mon-Fri"}]')
    # Add loaded schedules to the schedule dictionary
    scheduleDict.update({str(app_ID):schedules1})
    scheduleDict.update({str(app_ID+1):schedules2})
    if 'DEBUG' in locals():
        print "Number of entries: " + str(len(scheduleDict))
        if str(app_ID) in scheduleDict:
            print (scheduleDict[str(app_ID)])

###
 # Fetch application schedules from a controller then add them to the policies dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the application schedules to fetch
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched schedules. Zero if no schedule was found.
###
def fetch_schedules(app_ID,selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching schedules for App " + str(app_ID) + "...")
    # Retrieve a List of Schedules for a Given Application
    # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        schedules = json.loads(response)
    except JSONDecodeError:
        print ("fetch_schedules: Could not process JSON content.")
        return None

    if loadData:
        index = 0
        for schedule in schedules:
            if 'DEBUG' in locals(): print ("Fetching schedule "+str(schedule['id'])+" for App " + str(app_ID) + "...")
            # Retrieve the Details of a Specified Schedule with a specified ID
            # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
            restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(schedule['id'])
            params = {"output": "JSON"}
            if userName and password:
                response = fetch_RESTfulPath(restfulPath,params=params,userName=userName,password=password)
            else:
                response = fetch_RESTfulPath(restfulPath,params=params)

            if response is None:
                "fetch_schedules: Failed to retrieve schedule " + str(schedule['id']) + " for application " + str(app_ID)
                continue
            try:
                scheduleData = json.loads(response)
            except JSONDecodeError:
                print ("fetch_schedules: Could not process JSON content.")
                return None
            schedules[index] = scheduleData
            index = index + 1
    
    # Add loaded schedules to the schedule dictionary
    scheduleDict.update({str(app_ID):schedules})

    if 'DEBUG' in locals():
        print "fetch_schedules: Loaded " + str(len(schedules)) + " schedules:"
        for appID in scheduleDict:
            print str(scheduleDict[appID])

    return len(schedules)

###
 # Update application schedule from a controller. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param app_ID the ID number of the application schedule to update
 # @param sched_ID the ID number of the schedule to update
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return True if the update was successful. False if no schedule was updated.
###
def update_schedule(app_ID,sched_ID):
    for schedule in scheduleDict[str(app_ID)]:
        if schedule['id'] == sched_ID: break
    if schedule['id'] != sched_ID:
        print "No schedule " + str(sched_ID) + " was found in application " + str(app_ID)
        return False 
    if 'DEBUG' in locals(): print ("Updating schedule " + str(sched_ID) + " for App " + str(app_ID) + "...")
    # Updates an existing schedule with a specified JSON payload
    # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(sched_ID)
    return update_RESTful_JSON(restfulPath,schedule)

###
 # Generate CSV output from schedules data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain schedules from local schedules dictionary
 # @param schedules data stream containing schedules
 # @param fileName output file name
 # @return None
###
def generate_schedules_CSV(appID_List=None,schedules=None,fileName=None):
    if appID_List is None and schedules is None:
        return
    elif schedules is None:
        schedules = []
        for appID in appID_List:
            schedules = schedules + scheduleDict[str(appID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Name', 'Description', 'Timezone', 'Frequency', 'Start', 'End']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for schedule in schedules:
        if 'timezone' not in schedule: continue
        if 'scheduleConfiguration' in schedule:
            scheduleConfig = schedule['scheduleConfiguration']

            if 'startCron' in scheduleConfig:
                start=scheduleConfig['startCron']
            elif 'startDate' in scheduleConfig:
                start=scheduleConfig['startDate']+" "+scheduleConfig['startTime']
            elif 'occurrence' in scheduleConfig:
                start=scheduleConfig['occurrence']+" "+scheduleConfig['day']+" "+scheduleConfig['startTime']
            elif 'startTime' in scheduleConfig:
                start=scheduleConfig['startTime']

            if 'endCron' in scheduleConfig:
                end=scheduleConfig['endCron']
            elif 'endDate' in scheduleConfig:
                end=scheduleConfig['endDate']+" "+scheduleConfig['endTime']
            elif 'occurrence' in scheduleConfig:
                end=scheduleConfig['occurrence']+" "+scheduleConfig['day']+" "+scheduleConfig['endTime']
            elif 'endTime' in scheduleConfig:
                end=scheduleConfig['endTime']

        try:
            filewriter.writerow({'Name': schedule['name'],
                                 'Description': schedule['description'],
                                 'Timezone': schedule['timezone'],
                                 'Frequency': scheduleConfig['scheduleFrequency'] if 'scheduleConfig' in locals() else "",
                                 'Start': start if 'start' in locals() else "",
                                 'End':  end if 'end' in locals() else "" })
        except:
            print ("Could not write to the output.")
            if fileName is not None: csvfile.close()
            return (-1)
    if fileName is not None: csvfile.close()

###
 # Generate JSON output from schedules data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain schedules from local schedules dictionary
 # @param schedules data stream containing schedules
 # @param fileName output file name
 # @return None
###
def generate_schedules_JSON(appID_List=None,schedules=None,fileName=None):
    if appID_List is None and schedules is None:
        return
    elif schedules is None:
        schedules = []
        for appID in appID_List:
            schedules = schedules + scheduleDict[str(appID)]

    if fileName is not None:
        try:
            with open(fileName, 'w') as outfile:
                json.dump(schedules, outfile)
            outfile.close()
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        print json.dumps(schedules)


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display schedules from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_schedules_from_stream(streamData,outputFormat=None,outFilename=None):
    try:
        schedules = json.loads(streamData)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON data.")
        return 0

    if 'loadData' in locals():
        index = 0
        for schedule in schedules:
            if 'DEBUG' in locals(): print ("Fetching schedule "+str(schedule['id'])+" for App " + app_ID + "...")
            schedFileName=inFileName[:inFileName.find('.json')]+"/"+str(schedule['id'])+".json"
            try:
                sched_json_file = open(schedFileName)
                scheduleJSON = json.load(sched_json_file)
            except:
                print ("Could not process JSON file " + schedFileName)
                continue

            if scheduleJSON is None:
                "get_schedules_from_server: Failed to retrieve schedule " + str(schedule['id']) + " for application " + str(app_ID)
                continue
            schedules[index] = scheduleJSON
            index = index + 1
    if outputFormat and outputFormat == "JSON":
        generate_schedules_JSON(schedules=schedules,fileName=outFilename)
    else:
        generate_schedules_CSV(schedules=schedules,fileName=outFilename)

###
 # Display schedules for a list of applications.
 # @param appID_List list of application IDs to fetch schedules
 # @param selectors fetch only schedules filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched schedules. Zero if no schedule was found.
###
def get_schedules(appID_List,selectors=None,outputFormat=None):
    numSchedules = 0
    for appID in appID_List:
        sys.stderr.write("get schedules " + getAppName(appID) + "...\n")
        numSchedules = numSchedules + fetch_schedules(appID,selectors=selectors)
    if outputFormat and outputFormat == "JSON":
        generate_schedules_JSON(appID_List)
    elif not outputFormat or outputFormat == "CSV":
        generate_schedules_CSV(appID_List)
    return numSchedules

###
 # Patch schedules for a list of applications, using a schedule data input.
 # @param appID_List list of application IDs to update schedules
 # @param source schedule data input in JSON format.
 # @param selectors update only schedules filtered by specified selectors
 # @return the number of updated schedules. Zero if no schedule was updated.
###
def patch_schedules(appID_List,source,selectors=None):
    # Verify if the source is a file or stream JSON data
    try:
        # Load data from stream
        changesJSON = json.loads(source)
    except:
        try:
            # Load data from file
            json_file = open(source)
            changesJSON = json.load(json_file)
            json_file.close()
        except IOError:
            print("Could not process source data.")
            return 0

    ### TODO: patch for one specific scheduleID (name|description|scheduleConfiguration)
    if 'name' in changesJSON or 'description' in changesJSON or 'scheduleConfiguration' in changesJSON:
        print "Warn: schedule (name|description|scheduleConfiguration) patching not implemented yet."

    if 'timezone' not in changesJSON:
        print "Only timezone patch is currently supported."
        return 0

    numSchedules = 0
    for appID in appID_List:
        # Reload schedules data for provided application
        if fetch_schedules(appID,selectors=selectors,loadData=True) == 0:
            sys.stderr.write("update_schedules: Failed to retrieve schedules for application " + str(appID) + "...\n")
            continue
        sys.stderr.write("update schedules " + getAppName(appID) + "...\n")
        for schedule in scheduleDict[str(appID)]:
            # Do the replacement in loaded data
            schedule.update({"timezone": changesJSON['timezone']})
            # Update controller data
            if update_schedule(appID,schedule['id']) == True:
                numSchedules = numSchedules + 1
    return numSchedules