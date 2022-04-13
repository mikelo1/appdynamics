import json
import csv
import sys
from .entities import ControllerEntity

class ConfigurationDict(ControllerEntity):

    def __init__(self,controller):
        super(ConfigurationDict,self).__init__(controller)
        self['CSVfields'] = {'Name':        self.__str_setting_name,
                             'Value':       self.__str_setting_value,
                             'Scope':       self.__str_setting_scope,
                             'Updateable':  self.__str_setting_updateable,
                             'Description': self.__str_setting_description }


    def __str_setting_name(self,setting):
        return setting['name']

    def __str_setting_value(self,setting):
        return setting['value']

    def __str_setting_scope(self,setting):
        return setting['scope']

    def __str_setting_updateable(self,setting):
        return setting['updateable']

    def __str_setting_description(self,setting):
        return setting['description']

    ###### FROM HERE PUBLIC FUNCTIONS ######

