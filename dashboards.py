#!/usr/bin/python
import requests
import json
import csv
import sys
from appdRESTfulAPI import fetch_access_token

dashboardList = []
class Dashboard:
    name      = ""
    height    = 0
    width     = 0
    canvasType= ""
    def __init__(self,name,height,width,canvasType):
        self.name      = name
        self.height    = height
        self.width     = width
        self.canvasType= canvasType
    def __str__(self):
        return "({0},{1},{2},{3})".format(self.name,self.height,self.width,self.canvasType)


def fetch_dashboards(baseUrl,userName,password,apiClientName,apiClientSecret):
    
    token = fetch_access_token(baseUrl,userName,password,apiClientName,apiClientSecret)

    print ("Fetching dashboards list...")
    try:
        response = requests.get(baseUrl + "restui/dashboards/getAllDashboardsByType/false",
                                 headers={"Authorization": "Bearer "+token})
    except:
        print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
        return None

    if response.status_code != 200:
        print "Something went wrong on HTTP request:"
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None

    try:
        dashboards = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_dashboards(dashboards)

def load_dashboards_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    dashboards = json.load(json_file)
    parse_dashboards(dashboards)

def parse_dashboards(dashboards):
    for dashboard in dashboards:      
        dashboardList.append(Dashboard(dashboard['name'],dashboard['height'],dashboard['width'],dashboard['canvasType']))
#    print "Number of dashboards:" + str(len(dashboardList))
#    for dashboard in dashboardList:
#        print str(dashboard)    

def write_dashboards_CSV(fileName=None):
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

    if len(dashboardList) > 0:           
        for dashboard in dashboardList:
            try:
                filewriter.writerow({'Name': dashboard.name,
                                     'Height': dashboard.height,
                                     'Width': dashboard.width,
                                     'CanvasType': dashboard.canvasType})
            except:
                print ("Could not write to the output.")
                csvfile.close()
                return (-1)
        csvfile.close()