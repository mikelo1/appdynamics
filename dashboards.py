#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from entities import ControllerEntity

class DashboardDict(ControllerEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_dashboards}
    entityKeyword = 'canvasType'

    def __init__(self):
        self.entityDict = dict()

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


    def load_details(self):
        """
        Load dashboards details for all dashboards from a controller
        :param app_ID: the ID number of the application dashboards to fetch
        :returns: the number of fetched dashboards. Zero if no dashboard was found.
        """
        count = 0
        for dashboard in self.entityDict:
            response = RESTfulAPI().fetch_custom_dashboard(dashboard['id'])
            if response is not None:
                try:
                    dashboardData = json.loads(response)
                except TypeError as error:
                    print ("load_dashboard_details: "+str(error))
                    continue
                self.entityDict[count]=dashboardData
                count += 1
        return count

# Global object that works as Singleton
dashboards = DashboardDict()