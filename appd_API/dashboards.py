import json
import sys
from .entities import ControllerEntity

class DashboardDict(ControllerEntity):

    def __init__(self,controller):
        super(DashboardDict,self).__init__(controller)
        self['CSVfields'] = {'Name':       self.__str_dashboard_name,
                             'Height':     self.__str_dashboard_height,
                             'Width':      self.__str_dashboard_width,
                             'CanvasType': self.__str_dashboard_canvasType }

    def __str_dashboard_name(self,dashboard):
        return dashboard['name'] if sys.version_info[0] >= 3 else dashboard['name'].encode('ASCII', 'ignore')

    def __str_dashboard_height(self,dashboard):
        return dashboard['height']

    def __str_dashboard_width(self,dashboard):
        return dashboard['width']

    def __str_dashboard_canvasType(self,dashboard):
        return dashboard['canvasType']

    ###### FROM HERE PUBLIC FUNCTIONS ######

