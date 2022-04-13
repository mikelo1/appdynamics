import json
import sys
from datetime import datetime, timedelta
import time
from .entities import AppEntity

class EventDict(AppEntity):

    def __init__(self,controller):
        super(EventDict,self).__init__(controller)
        self['CSVfields']= {'PolicyName':  self.__str_event_policy,
                            'EntityName':  self.__str_event_entity,
                            'Severity':    self.__str_event_severity,
                            'Status':      self.__str_event_status,
                            'Start_Time':  self.__str_event_start_time,
                            'End_Time':    self.__str_event_end_time,
                            'Description': self.__str_event_description }


    def __str_event_policy(self,event):
        """
        toString private method, extracts policy from event
        :param event: JSON data containing an event
        :returns: string with a comma separated list of policy names
        """
        triggeredEntitytype = event['triggeredEntityDefinition']['entityType']
        if triggeredEntitytype == "POLICY":
            if 'name' in event['triggeredEntityDefinition']:
                return event['triggeredEntityDefinition']['name'] if sys.version_info[0] >= 3 else event['triggeredEntityDefinition']['name'].encode('ASCII', 'ignore')
            else:
                return event['triggeredEntityDefinition']['entityId']
        else:
            return ""


    def __str_event_entity(self,event):
        """
        toString private method, extracts policy from event
        :param event: JSON data containing an event
        :returns: string with a comma separated list of entity names
        """
        affectedEntityType = event['affectedEntityDefinition']['entityType']
        if affectedEntityType in ["BUSINESS_TRANSACTION","APPLICATION_DIAGNOSTIC_DATA","MOBILE_APPLICATION"]:
            if 'name' in event['affectedEntityDefinition']:
                return event['affectedEntityDefinition']['name'].encode('ASCII', 'ignore')
            else:
                return event['affectedEntityDefinition']['entityId']
        else:
            return ""


    def __str_event_severity(self,event):
        return event['severity'] if 'severity' in event else "Undefined"


    def __str_event_status(self,event):
        return event['incidentStatus']


    def __str_event_description(self,event):
        """
        toString private method, extracts description from event
        :param event: JSON data containing an event
        :returns: string with the description of the event
        """
        desc_pos = event['description'].find("All of the following conditions were found to be violating")
        Description = event['description'][desc_pos+58:] if desc_pos > 0 else event['description']
        Description = Description.replace("<br>","\n")
        return Description


    def __str_event_start_time(self,event):
        """
        toString private method, extracts starting time from event
        :param event: JSON data containing an event
        :returns: date
        """
        Start_Time_Epoch = event['startTimeInMillis']
        return datetime.fromtimestamp(float(Start_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')


    def __str_event_end_time(self,event):
        """
        toString private method, extracts ending time from event
        :param event: JSON data containing an event
        :returns: date
        """
        Status = event['incidentStatus']
        if Status != "OPEN":
            End_Time_Epoch = event['endTimeInMillis']
            return datetime.fromtimestamp(float(End_Time_Epoch)/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return ""


    ###### FROM HERE PUBLIC FUNCTIONS ######


class MetricDict(AppEntity):

    def __init__(self,controller):
        super(MetricDict,self).__init__(controller)
        self['CSVfields']= {'ErrorCode': self.__str_metric_start_time,
                            'Value':     self.__str_metric_value,
                            'Max':       self.__str_metric_max,
                            'Min':       self.__str_metric_min,
                            'Sum':       self.__str_metric_sum,
                            'Count':     self.__str_metric_count }

    def __str_metric_start_time(self,metric):
        return metric['metricPath'].split("|")[2]

    def __str_metric_value(self,metric):
        return metric['metricValues'][0]['value'] if len(metric['metricValues']) > 0 else "-"

    def __str_metric_max(self,metric):
        return metric['metricValues'][0]['max'] if len(metric['metricValues']) > 0 else "-"

    def __str_metric_min(self,metric):
        return metric['metricValues'][0]['min'] if len(metric['metricValues']) > 0 else "-"

    def __str_metric_sum(self,metric):
        return metric['metricValues'][0]['sum'] if len(metric['metricValues']) > 0 else "-"

    def __str_metric_count(self,metric):
        return metric['metricValues'][0]['count'] if len(metric['metricValues']) > 0 else "-"


class ErrorDict(MetricDict, object):

    def __init__(self,controller):
        super(ErrorDict,self).__init__(controller)

    def fetch_after_time(self,appID,duration,sinceEpoch,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        count = 0
        for tierName in self['controller'].tiers.getTiers_Name_List(appID=appID):
            selectors.update({'metric-path':'Errors|'+tierName+'|*|Errors per Minute'})
            #data = self.entityAPIFunctions['fetch'](app_ID=appID,entity_ID=tierName,time_range_type="AFTER_TIME",
            #                                        **{"duration-in-mins":duration,"start-time":sinceEpoch,"selectors":selectors})
            data = self['controller'].RESTfulAPI.send_request( entityType=self.__class__.__name__,verb="fetch",app_ID=appID,selectors=selectors,
                                                            **{"time-range-type":"AFTER_TIME","duration-in-mins":duration,"start-time":sinceEpoch})
            count += self.load(streamdata=data,appID=appID)
        return count