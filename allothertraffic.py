#!/usr/bin/python
import requests
import json
import csv
import sys
from businesstransactions import get_business_transaction_ID
from datetime import datetime, timedelta
import time

OverflowBT_List = []

class OverflowBT:
    URL= ""
    count = 0
    BTtype= None
    def __init__(self,URL,count,BTtype=None):
        self.URL= URL
        self.count = count
        self.BTtype= BTtype
    def __str__(self):
        return "({0},{1},{2})".format(self.URL,self.count,self.BTtype)


def fetch_allothertraffic(baseUrl,userName,password,app_ID,time_range_type,range_param1,range_param2):
   # time_range_type="AFTER_TIME" # {"BEFORE_NOW","BEFORE_TIME","AFTER_TIME","BETWEEN_TIMES"
   # duration_in_mins: {1day:"1440" 1week:"10080" 1month:"43200"}
   # range_param1=datetime.today()-timedelta(days=1)
    MAX_RESULTS="9999"
    AllOtherTraffic_ID = get_business_transaction_ID("_APPDYNAMICS_DEFAULT_TX_")
    if AllOtherTraffic_ID is None:
        return None

    if time_range_type == "BEFORE_NOW" and range_param1 > 0:
        duration_in_mins = range_param1
        print ("Fetching all other traffic snapshots for App "+app_ID+", "+time_range_type+", "+range_param1+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots/", auth=(userName, password),\
                                    params={"business-transaction-ids": AllOtherTraffic_ID,"time-range-type": time_range_type,"duration-in-mins": duration_in_mins, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BEFORE_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching all other traffic for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                params={"business-transaction-ids": AllOtherTraffic_ID,"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"end-time": end_time, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "AFTER_TIME" and range_param1 > 0 and range_param2 is not None:
        duration_in_mins = range_param1
        start_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching all other traffic for App "+app_ID+", "+time_range_type+", "+range_param1+", "+str(range_param2)+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                params={"business-transaction-ids": AllOtherTraffic_ID,"time-range-type": time_range_type,"duration-in-mins": duration_in_mins,"start-time": start_time, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    elif time_range_type == "BETWEEN_TIMES" and range_param1 is not None and range_param2 is not None:
        start_time = long(time.mktime(range_param1.timetuple())*1000)
        end_time = long(time.mktime(range_param2.timetuple())*1000)
        print ("Fetching all other traffic for App "+app_ID+", "+time_range_type+", "+range_param1+", "+range_param2+"...")
        try:
            response = requests.get(baseUrl + "rest/applications/" + app_ID + "/request-snapshots", auth=(userName, password),\
                                params={"business-transaction-ids": AllOtherTraffic_ID,"time-range-type": time_range_type,"start-time": start_time,"end-time": end_time, "output": "JSON", "maximum-results": MAX_RESULTS})
        except:
            #print ("Could not get authentication token from " + baseUrl + ".  Do you have the right controller hostname?")
            return None
    else:
        print ("Unknown time range or missing arguments. Exiting...")
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
        snapshots = json.loads(response.content)
    except:
        print ("Could not process authentication token for user " + userName + ".  Did you mess up your username/password?")
        print "   status:", response.status_code
        print "   header:", response.headers
        print "Writing content to file: response.txt"
        file1 = open("response.txt","w") 
        file1.write(response.content)
        file1.close() 
        return None
    parse_allothertraffic(snapshots)
    return snapshots

def load_allothertraffic_JSON(fileName):
    print "Parsing file " + fileName + "..."
    json_file = open(fileName)
    snapshots = json.load(json_file)
    parse_allothertraffic(snapshots)

def parse_allothertraffic(snapshots):
    URL_List  = []
    Count_List= []
    for snapshot in snapshots:
        url=snapshot['URL']
        if URL_List.count(url) == 0:
            URL_List.append(url)
            OverflowBT_List.append(OverflowBT(url,1))
        else:
            OverflowBT_List[URL_List.index(url)].count = OverflowBT_List[URL_List.index(url)].count + 1

  #  print "Number of URLs:" + str(len(OverflowBT_List))
  #  for ovfBT in OverflowBT_List:
  #      print ovfBT.URL, ovfBT.count

def write_allothertraffic_CSV(fileName=None):
    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['URL', 'Count', 'Type']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    for overflowBT in OverflowBT_List:
        try:
            filewriter.writerow({'URL': overflowBT.URL,
                                'Count': overflowBT.count,
                                'Type': overflowBT.BTtype})
        except:
            print ("Could not write to the output file " + fileName + ".")
            csvfile.close()
            exit(1)