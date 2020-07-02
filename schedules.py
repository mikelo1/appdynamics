#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath, update_RESTful_JSON

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
            if userName and password:
                scheduleJSON = fetch_RESTful_JSON(restfulPath,userName=userName,password=password)
            else:
                scheduleJSON = fetch_RESTful_JSON(restfulPath)

            if scheduleJSON is None:
                "fetch_schedules: Failed to retrieve schedule " + str(schedule['id']) + " for application " + str(app_ID)
                continue
            schedules[index] = scheduleJSON
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
def update_schedule(app_ID,sched_ID,serverURL=None,userName=None,password=None,token=None):
    for schedule in scheduleDict[str(app_ID)]:
        if schedule['id'] == sched_ID: break
    if schedule['id'] != sched_ID:
        print "No schedule " + str(sched_ID) + " was found in application " + str(app_ID)
        return False 
    if 'DEBUG' in locals(): print ("Updating schedule " + str(sched_ID) + " for App " + str(app_ID) + "...")
    # Updates an existing schedule with a specified JSON payload
    # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
    restfulPath = "/controller/alerting/rest/v1/applications/" + str(app_ID) + "/schedules/" + str(sched_ID)
    if serverURL and userName and password:
        return update_RESTful_JSON(restfulPath,schedule,serverURL=serverURL,userName=userName,password=password)
    else:
        return update_RESTful_JSON(restfulPath,schedule)

def schedules_JSON_to_structure(app_ID=None):
    for schedule in scheduleList:
        schedConfigData = schedule.data['scheduleConfiguration']
        if 'scheduleFrequency' in schedConfigData:
            if schedConfigData['scheduleFrequency'] == "CUSTOM":
                scheduleConfiguration = ScheduleConfiguration(frequency=schedConfigData['scheduleFrequency'],
                                             startCron=schedConfigData['startCron'],
                                             endCron  =schedConfigData['endCron'] )
            elif schedConfigData['scheduleFrequency'] == "DAILY":
                scheduleConfiguration = ScheduleConfiguration(frequency=schedConfigData['scheduleFrequency'],
                                             startTime=schedConfigData['startTime'],
                                             endTime  =schedConfigData['endTime'] )
            elif schedConfigData['scheduleFrequency'] == "WEEKLY":
                dayList = []
                for day in schedConfigData['days']:
                    dayList.append(day)
                scheduleConfiguration = ScheduleConfiguration(frequency=schedConfigData['scheduleFrequency'],
                                             startTime=schedConfigData['startTime'],
                                             endTime  =schedConfigData['endTime'],
                                             days     =dayList )
            elif schedConfigData['scheduleFrequency'] == "MONTHLY_SPECIFIC_DAY":
                scheduleConfiguration = ScheduleConfiguration(frequency=schedConfigData['scheduleFrequency'],
                                             startTime=schedConfigData['startTime'],
                                             endTime  =schedConfigData['endTime'],
                                             occurrenc=schedConfigData['occurrence'],
                                             day      =schedConfigData['day'] )
            elif schedConfigData['scheduleFrequency'] == "ONE_TIME" or schedConfigData['scheduleFrequency'] == "MONTHLY_SPECIFIC_DATE":
                scheduleConfiguration = ScheduleConfiguration(frequency=schedConfigData['scheduleFrequency'],
                                             startTime=schedConfigData['startTime'],
                                             endTime  =schedConfigData['endTime'],
                                             startDate=schedConfigData['startDate'],
                                             endDate  =schedConfigData['endDate'] )
            else:
                print "Unknown schedule frequency:" + schedConfigData['scheduleFrequency']
        schedule.data = Schedule(schedule['id'],schedule['name'],app_ID,schedule['description'],schedule['timezone'],scheduleConfiguration)
    if 'DEBUG' in locals():
        print "Number of schedules:" + str(len(scheduleList))
        for schedule in scheduleList:
            print str(schedule)

def generate_schedules_CSV(app_ID,schedules=None,fileName=None):
    if schedules is None and str(app_ID) not in scheduleDict:
        print "Schedules for application "+str(app_ID)+" not loaded."
        return
    elif schedules is None and str(app_ID) in scheduleDict:
        schedules = scheduleDict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    # create the csv writer object
    fieldnames = ['Name', 'Application', 'Description', 'Timezone', 'Frequency', 'Start', 'End']
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
                                 'Application': str(app_ID),
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

def generate_schedules_JSON(app_ID,schedules=None,fileName=None):
    if schedules is None and str(app_ID) not in scheduleDict:
        print "Schedules for application "+str(app_ID)+" not loaded."
        return
    elif schedules is None and str(app_ID) in scheduleDict:
        schedules = scheduleDict[str(app_ID)]

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


def get_schedules_from_stream(streamData,outputFormat=None,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        schedules = json.loads(streamData)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
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
        generate_schedules_JSON(app_ID=0,schedules=schedules,fileName=outFilename)
    else:
        generate_schedules_CSV(app_ID=0,schedules=schedules,fileName=outFilename)

def get_schedules(app_ID,selectors=None,outputFormat=None,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_schedules(app_ID)
    elif serverURL and userName and password:
        if fetch_schedules(app_ID,selectors=selectors,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_schedules: Failed to retrieve schedules for application " + str(app_ID)
            return None
    else:
        if fetch_schedules(app_ID,selectors=selectors,token=token) == 0:
            print "get_schedules: Failed to retrieve schedules for application " + str(app_ID)
            return None
    if outputFormat and outputFormat == "JSON":
        generate_schedules_JSON(app_ID)
    else:
        generate_schedules_CSV(app_ID)

def patch_schedules(app_ID,source,serverURL=None,userName=None,password=None,token=None):
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
            return None

    ### TODO: patch for one specific scheduleID (name|description|scheduleConfiguration)
    if 'name' in changesJSON or 'description' in changesJSON or 'scheduleConfiguration' in changesJSON:
        print "Warn: schedule (name|description|scheduleConfiguration) patching not implemented yet."

    if 'timezone' not in changesJSON:
        print "Nothing to be changed."
        return

    # Load schedules data for provided application
    if serverURL == "dummyserver":
        build_test_schedules(app_ID)
    elif userName and password:
        if fetch_schedules(serverURL,app_ID,userName=userName,password=password,loadData=True) == 0:
            print "update_schedules: Failed to retrieve schedules for application " + str(app_ID)
            return None
    elif token:
        if fetch_schedules(serverURL,app_ID,token=token,loadData=True) == 0:
            print "update_schedules: Failed to retrieve schedules for application " + str(app_ID)
            return None

    for schedule in scheduleDict[str(app_ID)]:
        # Do the replacement in loaded data
        if 'timezone' in changesJSON:
            schedule['timezone'] = changesJSON['timezone']
        # Update controller data
        if serverURL != "dummyserver":
            update_schedule(serverURL,app_ID,schedule['id'],userName,password,token)
        else:
            generate_schedules_CSV(app_ID)