#!/usr/bin/python
import json
import csv
import sys

from appdRESTfulAPI import RESTfulAPI

class DashboardDict:
    dashboardDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.dashboardDict)

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from dashboards data
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self, fileName=None):
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
             
        for dashboardID in self.dashboardDict:
            dashboard = self.dashboardDict[dashboardID]
            if 'success' in dashboard and dashboard['success']==False: continue
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

    ###
     # Generate JSON output from dashboards data
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,fileName=None):
        data = [ self.dashboardDict[dashboardID] for dashboardID in self.dashboardDict ]
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(data, outfile)
                outfile.close()
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(data)

    ###
     # Load dashboards from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID
     # @return the number of loaded dashboards. Zero if no dashboard was loaded.
    ###
    def load(self,streamdata,appID=None):
        try:
            dashboards = json.loads(streamdata)
        except TypeError as error:
            print ("load_dashboards: "+str(error))
            return 0
        for dashboard in dashboards:
            # Add loaded dashboard to the dashboards dictionary
            if 'canvasType' not in dashboard: continue
            dashboard_ID = dashboard['id']
            self.dashboardDict.update({str(dashboard_ID):dashboard})
        return len(dashboards)

    ###
     # Load dashboards details for all dashboards from a controller
     # @param app_ID the ID number of the application dashboards to fetch
     # @return the number of fetched dashboards. Zero if no dashboard was found.
    ###
    def load_details(self):
        count = 0
        for dashboardID in self.dashboardDict:
            response = RESTfulAPI().fetch_custom_dashboard(dashboardID)
            if response is not None:
                try:
                    dashboard = json.loads(response)
                except TypeError as error:
                    print ("load_dashboard_details: "+str(error))
                    continue
                self.dashboardDict.update({str(dashboardID):dashboard})
                count += 1
        return count