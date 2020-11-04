#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath, update_RESTful_JSON
from applications import getAppName

scheduleDict = dict()

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
 # @param app_ID the ID number of the application schedule to update
 # @param sched_ID the ID number of the schedule to update
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
 # toString method, extracts start time from schedule
 # @param schedule JSON data containing a schedule
 # @return string with a start time
###
def str_schedule_start(schedule):
    if 'scheduleConfiguration' in schedule:
        scheduleConfig = schedule['scheduleConfiguration']
        if 'startCron' in scheduleConfig:
            return scheduleConfig['startCron']
        elif 'startDate' in scheduleConfig:
            return scheduleConfig['startDate']+" "+scheduleConfig['startTime']
        elif 'occurrence' in scheduleConfig:
            return scheduleConfig['occurrence']+" "+scheduleConfig['day']+" "+scheduleConfig['startTime']
        elif 'startTime' in scheduleConfig:
            return scheduleConfig['startTime']
    return ""

###
 # toString method, extracts end time from schedule
 # @param schedule JSON data containing a schedule
 # @return string with a end time
###
def str_schedule_end(schedule):
    if 'scheduleConfiguration' in schedule:
        scheduleConfig = schedule['scheduleConfiguration']
        if 'endCron' in scheduleConfig:
            return scheduleConfig['endCron']
        elif 'endDate' in scheduleConfig:
            return scheduleConfig['endDate']+" "+scheduleConfig['endTime']
        elif 'occurrence' in scheduleConfig:
            return scheduleConfig['occurrence']+" "+scheduleConfig['day']+" "+scheduleConfig['endTime']
        elif 'endTime' in scheduleConfig:
            return scheduleConfig['endTime']
    return ""

###
 # Generate CSV output from schedules data, either from the local dictionary or from streamed data
 # @param appID_List list of application IDs, in order to obtain schedules from local schedules dictionary
 # @param schedules data stream containing schedules
 # @param fileName output file name
 # @return None
###
def generate_schedules_CSV(appID_List,custom_scheduleDict=None,fileName=None):
    if appID_List is None and custom_scheduleDict is None:
        return
    elif custom_scheduleDict is None:
        custom_scheduleDict = scheduleDict

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Name', 'Description', 'Application', 'Timezone', 'Frequency', 'Start', 'End']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for appID in appID_List:
        for schedule in custom_scheduleDict[str(appID)]:
            # Check if data belongs to a schedule
            if 'timezone' not in schedule: continue
            try:
                filewriter.writerow({'Name': schedule['name'],
                                     'Description': schedule['description'],
                                     'Application': getAppName(appID),
                                     'Timezone': schedule['timezone'],
                                     'Frequency': schedule['scheduleConfiguration']['scheduleFrequency'] if 'scheduleConfiguration' in schedule else "",
                                     'Start': str_schedule_start(schedule),
                                     'End':  str_schedule_end(schedule) })
            except ValueError as valError:
                print (valError)
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
def generate_schedules_JSON(appID_List,custom_scheduleDict=None,fileName=None):
    if appID_List is None and custom_scheduleDict is None:
        return
    elif custom_scheduleDict is None:
        custom_scheduleDict = scheduleDict

    schedules = []
    for appID in appID_List:
        schedules = schedules + custom_scheduleDict[str(appID)]

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
    custom_scheduleDict = {"0":[schedules]} if type(schedules) is dict else {"0":schedules}
    if outputFormat and outputFormat == "JSON":
        generate_schedules_JSON(appID_List=[0],custom_scheduleDict=custom_scheduleDict,fileName=outFilename)
    else:
        generate_schedules_CSV(appID_List=[0],custom_scheduleDict=custom_scheduleDict,fileName=outFilename)

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