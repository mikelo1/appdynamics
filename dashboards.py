#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTful_JSON

dashboardDict = dict()

###
 # Fetch dashboards from a controller then add them to the dashboards dictionary. Provide either an username/password or an access token.
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched dashboards. Zero if no dashboard was found.
###
def fetch_dashboards(serverURL,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching dashboards list...")    
    # Export the list of all Custom Dashboards
    # https://community.appdynamics.com/t5/Dashboards/How-to-export-the-list-of-all-Custom-Dashboards-in-the/td-p/30083
    # HTTP call: /controller/restui/dashboards/getAllDashboardsByType/false
    restfulPath = "/controller/restui/dashboards/getAllDashboardsByType/false"
    dashboards = fetch_RESTful_JSON(restfulPath)

    for dashboard in dashboards:
        if loadData:
            if 'DEBUG' in locals(): print ("Fetching dashboard "+str(dashboard['id']) + "...")
            # Export Custom Dashboards and Templates
            # GET /controller/CustomDashboardImportExportServlet?dashboardId=dashboard_id
            restfulPath = "/controller/CustomDashboardImportExportServlet?dashboardId=" + str(dashboard['id'])
            dashboardJSON = fetch_RESTful_JSON(restfulPath)

        # Add loaded dashboard to the dashboard dictionary
        dashboardID = dashboard['id']
        if 'dashboardJSON' in locals() and dashboardJSON is not None:
            dashboardDict.update({str(dashboardID):dashboardJSON})
        else:
            dashboardDict.update({str(dashboardID):dashboard})

    if 'DEBUG' in locals():
        print "fetch_dashboards: Loaded " + str(len(dashboards)) + " dashboards."
        for appID in dashboardDict:
            print str(dashboardDict[appID])

    return len(dashboards)

def convert_dashboards_JSON_to_CSV(inFileName,outFilename=None):
    json_file = open(inFileName)
    dashboards = json.load(json_file)

    dashboardID = 0
    for dashboard in dashboards:
        # Add loaded dashboard to the dashboard dictionary
        dashboardID = dashboardID +1
        dashboardDict.update({str(dashboardID):dashboard})

    generate_dashboards_CSV(fileName=outFilename)

def generate_dashboards_JSON(dashboards=None,outFileName=None):
    if dashboards is None and len(dashboardDict) == 0:
        print "generate_dashboards_CSV: Dahsboards not loaded."
        return
    elif dashboards is None:
        dashboards = dashboardDict

    if outFileName is not None:
        try:
            JSONfile = open(outFileName, 'w')
        except:
            print ("Could not open output file " + outFileName + ".")
            return (-1)
    else:
        JSONfile = sys.stdout

    data = []
    for dashboardID in dashboards:
        data.append(dashboardDict[dashboardID])
    json.dump(data,JSONfile)

def generate_dashboards_CSV(dashboards=None,fileName=None):
    if dashboards is None and len(dashboardDict) == 0:
        print "generate_dashboards_CSV: Dahsboards not loaded."
        return
    elif dashboards is None:
        dashboards = dashboardDict

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
    filewriter.writeheader()
         
    for dashboardID in dashboards:
        dashboard = dashboardDict[dashboardID]
        if 'success' in dashboard and dashboard['success']==False: continue
        try:
            filewriter.writerow({'Name': dashboard['name'],
                                 'Height': dashboard['height'],
                                 'Width': dashboard['width'],
                                 'CanvasType': dashboard['canvasType']})
        except:
            print ("Could not write to the output.")
            print json.dumps(dashboard)
            if fileName is not None: csvfile.close()
            return (-1)
    if fileName is not None: csvfile.close()

def get_dashboards(serverURL,userName=None,password=None,token=None):
    if userName and password:
        if fetch_dashboards(serverURL,userName=userName,password=password) > 0:
            generate_dashboards_CSV()
    elif token:
        if fetch_dashboards(serverURL,token=token) > 0:
            generate_dashboards_CSV()