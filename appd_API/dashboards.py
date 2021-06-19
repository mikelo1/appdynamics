#!/usr/bin/python
import json
import csv
import sys
from entities import ControllerEntity

class DashboardDict(ControllerEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_dashboards,
                                    'fetchByID': self.controller.RESTfulAPI.fetch_dashboard_by_ID }
        self.entityJSONKeyword = 'canvasType'

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self, fileName=None):
        """
        Generate CSV output from dashboards data
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
        fieldnames = ['Name', 'Height', 'Width', 'CanvasType']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
             
        for dashboard in self.entityDict:
            # Check if data belongs to a dashboard
            if 'canvasType' not in dashboard: continue
            elif 'success' in dashboard and dashboard['success']==False: continue
            elif 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True
            try:
                filewriter.writerow({'Name': dashboard['name'],
                                     'Height': dashboard['height'],
                                     'Width': dashboard['width'],
                                     'CanvasType': dashboard['canvasType']})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()
