import json
import sys
from .entities import AppEntity

class ScheduleDict(AppEntity):

    def __init__(self,controller):
        super(ScheduleDict,self).__init__(controller)
        self['CSVfields']= {'Name':        self.__str_schedule_name,
                            'Description': self.__str_schedule_description,
                            'Timezone':    self.__str_schedule_timezone,
                            'Frequency':   self.__str_schedule_frequency,
                            'Start':       self.__str_schedule_start,
                            'End':         self.__str_schedule_end }


    def __build_test_schedules(app_ID):
        schedules1=json.loads('[{"timezone":"Europe/Brussels","description":"This schedule is active Monday through Friday, during business hours","id":30201,"scheduleConfiguration":{"scheduleFrequency":"WEEKLY","endTime":"17:00","days":["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],"startTime":"08:00"},"name":"Weekdays:8am-5pm,Mon-Fri"}]')
        schedules2=json.loads('[{"timezone":"Europe/Brussels","description":"This schedule is active Monday through Friday, during business hours","id":30201,"scheduleConfiguration":{"scheduleFrequency":"WEEKLY","endTime":"17:00","days":["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"],"startTime":"08:00"},"name":"Weekdays:8am-5pm,Mon-Fri"}]')
        # Add loaded schedules to the schedule dictionary
        entityDict.update({app_ID:schedules1})
        entityDict.update({app_ID+1:schedules2})
        if 'DEBUG' in locals():
            print ("Number of entries: " + str(len(self['entities'])) )
            if str(app_ID) in self['entities']:
                print (self['entities'][app_ID])


    def __str_schedule_name(self,schedule):
        return schedule['name'] if sys.version_info[0] >= 3 else schedule['name'].encode('ASCII', 'ignore')

    def __str_schedule_description(self,schedule):
        return schedule['description'] if sys.version_info[0] >= 3 else schedule['description'].encode('ASCII', 'ignore')

    def __str_schedule_timezone(self,schedule):
        return schedule['timezone']

    def __str_schedule_frequency(self,schedule):
        return schedule['scheduleConfiguration']['scheduleFrequency'] if 'scheduleConfiguration' in schedule else ""

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

