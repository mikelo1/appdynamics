#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from applications import ApplicationDict

class ScheduleDict:
    scheduleDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.scheduleDict)

    def __build_test_schedules(app_ID):
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
     # toString private method, extracts start time from schedule
     # @param schedule JSON data containing a schedule
     # @return string with a start time
    ###
    def __str_schedule_start(self,schedule):
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
     # toString private method, extracts end time from schedule
     # @param schedule JSON data containing a schedule
     # @return string with a end time
    ###
    def __str_schedule_end(self,schedule):
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


    ###
     # Generate CSV output from schedules data
     # @param appID_List list of application IDs, in order to obtain schedules from local schedules dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

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


        for appID in appID_List:
            if str(appID) not in self.scheduleDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for schedule in self.scheduleDict[str(appID)]:
                # Check if data belongs to a schedule
                if 'timezone' not in schedule: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True
                try:
                    filewriter.writerow({'Name': schedule['name'],
                                         'Description': schedule['description'],
                                         'Application': ApplicationDict().getAppName(appID),
                                         'Timezone': schedule['timezone'],
                                         'Frequency': schedule['scheduleConfiguration']['scheduleFrequency'] if 'scheduleConfiguration' in schedule else "",
                                         'Start': self.__str_schedule_start(schedule),
                                         'End':  self.__str_schedule_end(schedule) })
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()

    ###
     # Generate JSON output from schedules data
     # @param appID_List list of application IDs, in order to obtain schedules from local schedules dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        schedules = []
        for appID in appID_List:
            schedules = schedules + self.scheduleDict[str(appID)]

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

    ###
     # Load schedules from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param outFilename output file name
     # @return the number of loaded schedules. Zero if no schedule was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            schedules = json.loads(streamdata)
        except TypeError as error:
            print ("load_schedules: "+str(error))
            return 0
        # Add loaded schedules to the schedules dictionary
        if type(schedules) is dict:
            self.scheduleDict.update({str(appID):[schedules]})
        else:
            self.scheduleDict.update({str(appID):schedules})

        return len(schedules)


    ###
     # Load schedule details for all schedules from an application
     # @param app_ID the ID number of the application schedules to fetch
     # @return the number of fetched schedules. Zero if no schedule was found.
    ###
    def load_details(self,app_ID):
        if str(app_ID) in self.scheduleDict:
            index = 0
            for schedule in self.scheduleDict[str(app_ID)]:
                streamdata = RESTfulAPI().fetch_schedule_details(app_ID,schedule['id'])
                if streamdata is None:
                    print "load_schedule_details: Failed to retrieve schedule " + str(schedule['id']) + " for application " + str(app_ID)
                    continue
                try:
                    scheduleJSON = json.loads(streamdata)
                except TypeError as error:
                    print ("load_schedule_detail: "+str(error))
                    continue
                self.scheduleDict[str(app_ID)][index] = scheduleJSON
                index = index + 1
            return index
        else:
            print self
        return 0

    ###
     # Patch schedules for a list of applications, using a schedule data input.
     # @param appID_List list of application IDs to update schedules
     # @param source schedule data input in JSON format.
     # @param selectors update only schedules filtered by specified selectors
     # @return the number of updated schedules. Zero if no schedule was updated.
    ###
    def patch(self,appID_List,source,selectors=None):
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
            if self.load(RESTfulAPI().fetch_schedules(appID,selectors=selectors),appID=appID) == 0 or self.load_details(appID) == 0:
                sys.stderr.write("update_schedules: Failed to retrieve schedules for application " + str(appID) + "...\n")
                continue
            sys.stderr.write("update schedules " + ApplicationDict().getAppName(appID) + "...\n")
            for schedule in self.scheduleDict[str(appID)]:
                # Do the replacement in loaded data
                schedule.update({"timezone": changesJSON['timezone']})
                # Update controller data
                if RESTfulAPI().update_schedule(app_ID=appID,sched_ID=schedule['id'],scheduleJSON=schedule) == True:
                    numSchedules = numSchedules + 1
        return numSchedules