#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import fetch_RESTfulPath

dashboardDict = dict()

###
 # Fetch dashboards from a controller then add them to the dashboards dictionary. Provide either an username/password or an access token.
 # @param selectors fetch only snapshots filtered by specified selectors
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched dashboards. Zero if no dashboard was found.
###
def fetch_dashboards(selectors=None,serverURL=None,userName=None,password=None,token=None,loadData=False):
    if 'DEBUG' in locals(): print ("Fetching dashboards list...")    
    # Export the list of all Custom Dashboards
    # https://community.appdynamics.com/t5/Dashboards/How-to-export-the-list-of-all-Custom-Dashboards-in-the/td-p/30083
    # HTTP call: /controller/restui/dashboards/getAllDashboardsByType/false
    restfulPath = "/controller/restui/dashboards/getAllDashboardsByType/false"
    params = {"output": "JSON"}
    if selectors: params.update(selectors)

    if serverURL and userName and password:
        response = fetch_RESTfulPath(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
    else:
        response = fetch_RESTfulPath(restfulPath,params=params)

    try:
        dashboards = json.loads(response)
    except JSONDecodeError:
        print ("fetch_dashboards: Could not process JSON content.")
        return 0

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

###
 # Generate CSV output from dashboards data, either from the local dictionary or from streamed data
 # @param dashbDict dictionary of dashboards, containing dashboard data
 # @param fileName output file name
 # @return None
###
def generate_dashboards_CSV(dashbDict=None,fileName=None):
    if dashbDict is None and len(dashboardDict) == 0:
        print "generate_dashboards_CSV: Dashboards not loaded."
        return
    elif dashbDict is None:
        dashbDict = dashboardDict

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
         
    for dashboardID in dashbDict:
        dashboard = dashbDict[dashboardID]
        if 'success' in dashboard and dashboard['success']==False: continue
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
 # Generate JSON output from dashboards data, either from the local dictionary or from streamed data
 # @param dashbDict dictionary of dashboards, containing dashboard data
 # @param fileName output file name
 # @return None
###
def generate_dashboards_JSON(dashbDict=None,fileName=None):
    if dashbDict is None and len(dashboardDict) == 0:
        print "generate_dashboards_JSON: Dahsboards not loaded."
        return
    elif dashbDict is None:
        dashbDict = dashboardDict

    data = []
    for dashboardID in dashbDict:
        data.append(dashbDict[dashboardID])

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


###### FROM HERE PUBLIC FUNCTIONS ######


###
 # Display dashboards from a JSON stream data.
 # @param streamdata the stream data in JSON format
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @param outFilename output file name
 # @return None
###
def get_dashboards_from_stream(streamdata,outputFormat=None,outFilename=None):
    try:
        dashboards = json.loads(streamdata)
    except:
        if 'DEBUG' in locals(): print ("get_dashboards_from_stream: Could not process JSON data.")
        return 0

    dashbDict = dict()
    for dashboard in dashboards:
        # Add loaded dashboard to the dashboard dictionary
        if 'canvasType' not in dashboard: continue
        dashboardID = dashboard['id']
        dashbDict.update({str(dashboardID):dashboard})

    if outputFormat and outputFormat == "JSON":
        generate_dashboards_JSON(dashbDict=dashbDict)
    else:
        generate_dashboards_CSV(dashbDict=dashbDict)

###
 # Display dashboards for a list of applications.
 # @param selectors fetch only dashboards filtered by specified selectors
 # @param outputFormat output format. Accepted formats are CSV or JSON.
 # @return the number of fetched dashboards. Zero if no dashboard was found.
###
def get_dashboards(selectors=None,outputFormat=None):
    sys.stderr.write("get dashboards ...\n")
    numDashboards = fetch_dashboards(selectors=selectors)
    if numDashboards == 0:
        sys.stderr.write("get_dashboards: Could not fetch any dashboards.\n")
    elif outputFormat and outputFormat == "JSON":
        generate_dashboards_JSON()
    elif not outputFormat or outputFormat == "CSV":
        generate_dashboards_CSV()
    return numDashboards