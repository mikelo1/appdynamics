#!/usr/bin/python
import requests
import json
import csv
import sys

scheduleList = []

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

def fetch_schedules(baseUrl,userName,password,app_ID):
    if 'DEBUG' in locals(): print ("Fetching schedules for App " + app_ID + "...")
    try:
        # Retrieve a List of Schedules for a Given Application
        # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules
        response = requests.get(baseUrl + "alerting/rest/v1/applications/" + app_ID + "/schedules", auth=(userName, password), params={"output": "JSON"})
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    try:
        schedulesJSON = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    appScheduleList = []
    for schedule in schedulesJSON:
        if 'DEBUG' in locals(): print ("Fetching schedule "+str(schedule['id'])+" for App " + app_ID + "...")
        try:
            # Retrieve the Details of a Specified Schedule with a specified ID
            # GET <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
            response = requests.get(baseUrl + "alerting/rest/v1/applications/" + app_ID + "/schedules/" + str(schedule['id']), auth=(userName, password), params={"output": "JSON"})
        except:
            print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            continue

        try:
            scheduleJSON = json.loads(response.content)
        except:
            print ("Could not process authentication token for user " + userName + ". Did you mess up your username/password?")
            print "   status:", response.status_code
            print "   header:", response.headers
            print "Writing content to file: response.txt"
            file1 = open("response.txt","w") 
            file1.write(response.content)
            file1.close() 
            continue
        appScheduleList.append(ScheduleElement(appID=app_ID,schedID=scheduleJSON['id'],data=scheduleJSON))
    if 'DEBUG' in locals():
        print "Number of fetched schedules:" + str(len(appScheduleList))
        for schedule in appScheduleList:
            print str(schedule)
    return appScheduleList

def update_schedule(baseUrl,userName,password,schedElement):
    # Updates an existing schedule with a specified JSON payload
    # PUT <controller_url>/controller/alerting/rest/v1/applications/<application_id>/schedules/{schedule-id}
    #if 'DEBUG' in locals(): 
    print ("Updating schedule " + str(schedElement.schedID) + " for App " + str(schedElement.appID) + "...")
    try:
        response = requests.put(baseUrl + "alerting/rest/v1/applications/" + str(schedElement.appID) + "/schedules/" + str(schedElement.schedID),
                                headers={"Content-Type": "application/json"},
                                auth=(userName, password), data=json.dumps(schedElement.data))
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

def load_schedules_JSON(fileName,app_ID=0):
    if 'DEBUG' in locals(): print "Processing file " + fileName + "..."
    try:
        json_file = open(fileName)
        schedulesJSON = json.load(json_file)
    except:
        print ("Could not process JSON file " + fileName)
        return None

    appScheduleList = []
    for schedule in schedulesJSON:
        if 'DEBUG' in locals(): print ("Fetching schedule "+str(schedule['id'])+" for App " + app_ID + "...")
        schedFileName=fileName[:fileName.find('.json')]+"/"+str(schedule['id'])+".json"
        try:
            sched_json_file = open(schedFileName)
            scheduleJSON = json.load(sched_json_file)
        except:
            print ("Could not process JSON file " + schedFileName)
            continue
        appScheduleList.append(ScheduleElement(appID=app_ID,schedID=scheduleJSON['id'],data=scheduleJSON))

    if 'DEBUG' in locals():
        print "Number of fetched schedules:" + str(len(appScheduleList))
        for schedule in appScheduleList:
            print str(schedule)
    return appScheduleList

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

def write_schedules_CSV(fileName=None):
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

    if len(scheduleList) > 0:           
        for schedule in scheduleList:
            scheduleConfig = schedule.data['scheduleConfiguration']

            if scheduleConfig and 'startCron' in scheduleConfig:
                start=scheduleConfig['startCron']
            elif scheduleConfig and 'startDate' in scheduleConfig:
                start=scheduleConfig['startDate']+" "+scheduleConfig['startTime']
            elif scheduleConfig and 'occurrence' in scheduleConfig:
                start=scheduleConfig['occurrence']+" "+scheduleConfig['day']+" "+scheduleConfig['startTime']
            elif scheduleConfig and 'startTime' in scheduleConfig:
                start=scheduleConfig['startTime']

            if scheduleConfig and 'endCron' in scheduleConfig:
                end=scheduleConfig['endCron']
            elif scheduleConfig and 'endDate' in scheduleConfig:
                end=scheduleConfig['endDate']+" "+scheduleConfig['endTime']
            elif scheduleConfig and 'occurrence' in scheduleConfig:
                end=scheduleConfig['occurrence']+" "+scheduleConfig['day']+" "+scheduleConfig['endTime']
            elif scheduleConfig and 'endTime' in scheduleConfig:
                end=scheduleConfig['endTime']

            try:
                filewriter.writerow({'Name': schedule.data['name'],
                                     'Application': schedule.appID,
                                     'Description': schedule.data['description'],
                                     'Timezone': schedule.data['timezone'],
                                     'Frequency': scheduleConfig['scheduleFrequency'] if scheduleConfig else "",
                                     'Start': start if scheduleConfig else "",
                                     'End':  end if scheduleConfig else "" })
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()

def export_schedules_CSV(outFileName, *args):
    if len(args)==1:
        list = load_schedules_JSON(args[0])
    elif len(args)==4:
        list = fetch_schedules(args[0],args[1],args[2],args[3])
    else:
        print "Missing or wrong arguments"

    if list is not None:
        scheduleList.extend(list)
        write_schedules_CSV(outFileName)
        if 'DEBUG' in locals(): print "Data stored in file " + outFileName        

    return

def update_schedules(baseUrl,userName,password,app_ID,source):
    if source[-5:] == ".json":
        schedList = load_schedules_JSON(source,app_ID)
        for schedElement in schedList:
            update_schedule(baseUrl,userName,password,schedElement)        
    else:
        try:
            changesJSON = json.loads(source)
        except:
            print ("Could not process source data.")
            return None
            
        # Load data for the application
        list = fetch_schedules(baseUrl,userName,password,app_ID)
        if list is not None:
            scheduleList.extend(list)
            for schedElement in scheduleList:
                if schedElement.appID == app_ID:
                    if 'timezone' in changesJSON:
                        schedElement.data['timezone'] = changesJSON['timezone']
                        update_schedule(baseUrl,userName,password,schedElement)