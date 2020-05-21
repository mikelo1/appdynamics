#!/usr/bin/python
import requests
import json
import csv
import sys

scheduleList = []
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
    start    = "" # i.e.: "06:00" or "0 0 8 ? * 2-6"
    end      = "" # i.e.: "18:00" or "0 0 12 ? * 2-6"
    startDate= "" # i.e.: "01/01/2019"
    endDate  = "" # i.e.: "01/01/2019"
    days     = [] # i.e.: ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]
    def __init__(self,frequency,start,end,startDate=None,endDate=None,days=None):
        self.frequency= frequency
        self.start    = start
        self.end      = end
        self.startDate= startDate
        self.endDate  = endDate
        self.days     = days
    def __str__(self):
        return "({0},{1},{2},{3},{4},{5})".format(self.frequency,self.start,self.end,self.startDate,self.endDate,self.days)


def fetch_schedules(baseUrl,userName,password,app_ID):
    print ("Fetching schedules for App " + app_ID + "...")
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
    parse_schedules(schedules,app_ID)

    for schedule in scheduleList:
        schedule.config=fetch_schedule_spec(baseUrl,userName,password,app_ID,schedule.Id)


def fetch_schedule_spec(baseUrl,userName,password,app_ID,schedule_ID):
#    print ("Fetching schedule "+str(schedule_ID)+" for App " + app_ID + "...")
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
    return parse_schedule_spec(schedule_spec)


def load_schedules_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    schedules = json.load(json_file)
    parse_schedules(schedules)

def parse_schedules(schedules,app_ID=None):
    for schedule in schedules:
        scheduleList.append(Schedule(schedule['id'],schedule['name'],app_ID,schedule['description'],schedule['timezone']))
#    print "Number of schedules:" + str(len(scheduleList))
#    for schedule in scheduleList:
#        print str(schedule)

def parse_schedule_spec(schedule_spec):
    scheduleconfig = schedule_spec['scheduleConfiguration']
    if 'scheduleFrequency' in scheduleconfig:
        if scheduleconfig['scheduleFrequency'] == "CUSTOM":
            return ScheduleConfiguration(scheduleconfig['scheduleFrequency'],
                                         scheduleconfig['startCron'],
                                         scheduleconfig['endCron'] )
        #### TO DO: scheduleconfig['scheduleFrequency'] == "DAILY":
        elif scheduleconfig['scheduleFrequency'] == "WEEKLY":
            dayList = []
            for day in scheduleconfig['days']:
                dayList.append(day)
            return ScheduleConfiguration(scheduleconfig['scheduleFrequency'],
                                         scheduleconfig['startTime'],
                                         scheduleconfig['endTime'],
                                         None,
                                         None,
                                         dayList )
        #### TO DO: scheduleconfig['scheduleFrequency'] == "MONTHLY":
        elif scheduleconfig['scheduleFrequency'] == "ONE_TIME":
            return ScheduleConfiguration(scheduleconfig['scheduleFrequency'],
                                         scheduleconfig['startTime'],
                                         scheduleconfig['endTime'],
                                         scheduleconfig['startDate'],
                                         scheduleconfig['endDate'] )

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
            try:
                if schedule.config:
                    filewriter.writerow({'Name': schedule.name,
                                     'Application': schedule.appName,
                                     'Description': schedule.description,
                                     'Timezone': schedule.timezone,
                                     'Frequency': schedule.config.frequency,
                                     'Start': schedule.config.start,
                                     'End': schedule.config.end })
                else:
                    filewriter.writerow({'Name': schedule.name,
                                     'Application': schedule.appName,
                                     'Description': schedule.description,
                                     'Timezone': schedule.timezone })                    
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()

def export_schedules_CSV(outFileName,inFileName=None,baseUrl=None,userName=None,password=None,app_ID=None):
    if inFileName:
        load_schedules_JSON(inFileName)
    elif userName and password and baseUrl and app_ID:
        fetch_schedules(baseUrl,userName,password,app_ID)
    else:
        print "Missing arguments"
        return
    write_schedules_CSV(outFileName)

#### TO DO:
####        update_schedules_timezone(baseUrl,userName,password,app_ID,timezone)
