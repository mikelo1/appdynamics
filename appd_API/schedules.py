#!/usr/bin/python
import json
import csv
import sys
from entities import AppEntity

class ScheduleDict(AppEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_schedules,
                                    'fetchByID': self.controller.RESTfulAPI.fetch_schedule_by_ID,
                                    'create': self.controller.RESTfulAPI.create_schedule,
                                    'update': self.controller.RESTfulAPI.update_schedule }
        self.entityJSONKeyword = "scheduleConfiguration"

    def __build_test_schedules(app_ID):
        schedules1=json.loads('[{"timezone":"Europe/Brussels","description":"This schedule is active Monday through Friday, during business hours","id":30201,"scheduleConfiguration":{"scheduleFrequency":"WEEKLY","endTime":"17:00","days":["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],"startTime":"08:00"},"name":"Weekdays:8am-5pm,Mon-Fri"}]')
        schedules2=json.loads('[{"timezone":"Europe/Brussels","description":"This schedule is active Monday through Friday, during business hours","id":30201,"scheduleConfiguration":{"scheduleFrequency":"WEEKLY","endTime":"17:00","days":["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],"startTime":"08:00"},"name":"Weekdays:8am-5pm,Mon-Fri"}]')
        # Add loaded schedules to the schedule dictionary
        entityDict.update({str(app_ID):schedules1})
        entityDict.update({str(app_ID+1):schedules2})
        if 'DEBUG' in locals():
            print "Number of entries: " + str(len(entityDict))
            if str(app_ID) in entityDict:
                print (entityDict[str(app_ID)])


    def __str_schedule_start(self,schedule):
        """
        toString private method, extracts start time from schedule
        :param schedule: JSON data containing a schedule
        :returns: string with a start time
        """
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


    def __str_schedule_end(self,schedule):
        """
        toString private method, extracts end time from schedule
        :param schedule: JSON data containing a schedule
        :returns: string with a end time
        """
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


    ###### FROM HERE PUBLIC FUNCTIONS ######


    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from schedules data
        :param appID_List: list of application IDs, in order to obtain schedules from local schedules dictionary
        :param fileName: output file name
        :returns: None
        """
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

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print "Application "+appID +" is not loaded in dictionary."
                continue
            for schedule in self.entityDict[appID]:
                # Check if data belongs to a schedule
                if 'timezone' not in schedule: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True
                try:
                    filewriter.writerow({'Name': schedule['name'],
                                         'Description': schedule['description'],
                                         'Application': self.controller.applications.getAppName(appID),
                                         'Timezone': schedule['timezone'],
                                         'Frequency': schedule['scheduleConfiguration']['scheduleFrequency'] if 'scheduleConfiguration' in schedule else "",
                                         'Start': self.__str_schedule_start(schedule),
                                         'End':  self.__str_schedule_end(schedule) })
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()
