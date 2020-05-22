#!/usr/bin/python
import requests
import json
import csv
import sys

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
        schedules = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    return schedules

def fetch_schedule_spec(baseUrl,userName,password,app_ID,schedule_ID):
    if 'DEBUG' in locals(): print ("Fetching schedule "+str(schedule_ID)+" for App " + app_ID + "...")
    try:
        response = requests.get(baseUrl + "alerting/rest/v1/applications/" + app_ID + "/schedules/" + str(schedule_ID), auth=(userName, password), params={"output": "JSON"})
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
    elif 'DEBUG' in locals():
        file1 = open("response.txt","w") 
        file1.write(response.content)

    try:
        schedule_spec = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    return schedule_spec

def load_schedules_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    schedules = json.load(json_file)
    return schedules

def parse_schedules(schedules,app_ID=None):
    scheduleList = []
    for schedule in schedules:
        scheduleList.append(Schedule(schedule['id'],schedule['name'],app_ID,schedule['description'],schedule['timezone']))
    if 'DEBUG' in locals():
        print "Number of schedules:" + str(len(scheduleList))
        for schedule in scheduleList:
            print str(schedule)
    return scheduleList

def parse_schedule_spec(schedule_spec):
    scheduleconfig = schedule_spec['scheduleConfiguration']
    if 'scheduleFrequency' in scheduleconfig:
        if scheduleconfig['scheduleFrequency'] == "CUSTOM":
            return ScheduleConfiguration(frequency=scheduleconfig['scheduleFrequency'],
                                         startCron=scheduleconfig['startCron'],
                                         endCron  =scheduleconfig['endCron'] )
        elif scheduleconfig['scheduleFrequency'] == "DAILY":
            return ScheduleConfiguration(frequency=scheduleconfig['scheduleFrequency'],
                                         startTime=scheduleconfig['startTime'],
                                         endTime  =scheduleconfig['endTime'] )
        elif scheduleconfig['scheduleFrequency'] == "WEEKLY":
            dayList = []
            for day in scheduleconfig['days']:
                dayList.append(day)
            return ScheduleConfiguration(frequency=scheduleconfig['scheduleFrequency'],
                                         startTime=scheduleconfig['startTime'],
                                         endTime  =scheduleconfig['endTime'],
                                         days     =dayList )
        elif scheduleconfig['scheduleFrequency'] == "MONTHLY_SPECIFIC_DAY":
            return ScheduleConfiguration(frequency=scheduleconfig['scheduleFrequency'],
                                         startTime=scheduleconfig['startTime'],
                                         endTime  =scheduleconfig['endTime'],
                                         occurrenc=scheduleconfig['occurrence'],
                                         day      =scheduleconfig['day'] )
        elif scheduleconfig['scheduleFrequency'] == "ONE_TIME" or scheduleconfig['scheduleFrequency'] == "MONTHLY_SPECIFIC_DATE":
            return ScheduleConfiguration(frequency=scheduleconfig['scheduleFrequency'],
                                         startTime=scheduleconfig['startTime'],
                                         endTime  =scheduleconfig['endTime'],
                                         startDate=scheduleconfig['startDate'],
                                         endDate  =scheduleconfig['endDate'] )
        else:
            print "Unknown schedule frequency:" + scheduleconfig['scheduleFrequency']

def write_schedules_CSV(scheduleList,fileName=None):
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
            if schedule.config and schedule.config.startCron:
                start=schedule.config.startCron
            elif schedule.config and schedule.config.startDate:
                start=schedule.config.startDate+" "+schedule.config.startTime
            elif schedule.config and schedule.config.occurrenc:
                start=schedule.config.occurrenc+" "+schedule.config.day+" "+schedule.config.startTime
            elif schedule.config and schedule.config.startTime:
                start=schedule.config.startTime

            if schedule.config and schedule.config.endCron:
                end=schedule.config.endCron
            elif schedule.config and schedule.config.endDate:
                end=schedule.config.endDate+" "+schedule.config.endTime
            elif schedule.config and schedule.config.occurrenc:
                end=schedule.config.occurrenc+" "+schedule.config.day+" "+schedule.config.endTime
            elif schedule.config and schedule.config.endTime:
                end=schedule.config.endTime

            try:
                filewriter.writerow({'Name': schedule.name,
                                     'Application': schedule.appName,
                                     'Description': schedule.description,
                                     'Timezone': schedule.timezone,
                                     'Frequency': schedule.config.frequency if schedule.config else "",
                                     'Start': start if schedule.config else "",
                                     'End':  end if schedule.config else "" })
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()

def export_schedules_CSV(outFileName,inFileName=None,baseUrl=None,userName=None,password=None,app_ID=None):
    if inFileName:
        schedules = load_schedules_JSON(inFileName)
        scheduleList = parse_schedules(schedules)
    elif userName and password and baseUrl and app_ID:
        schedules = fetch_schedules(baseUrl,userName,password,app_ID)
        scheduleList = parse_schedules(schedules,app_ID)
    else:
        print "Missing arguments"
        return
    
    for schedule in scheduleList:
        schedule_spec=fetch_schedule_spec(baseUrl,userName,password,app_ID,schedule.Id)
        schedule.config=parse_schedule_spec(schedule_spec)

    write_schedules_CSV(scheduleList,outFileName)

#### TO DO:
####        update_schedules_timezone(baseUrl,userName,password,app_ID,timezone)
