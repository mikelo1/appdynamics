#!/usr/bin/pythons
import json
import csv
import sys
from businesstransactions import get_business_transaction_ID
from appdRESTfulAPI import fetch_RESTful_JSON, timerange_to_params
from datetime import datetime, timedelta
import time

appdDefaultTX_Dict = dict()

class OverflowBT:
    URL= ""
    count = 0
    def __init__(self,URL,count):
        self.URL= URL
        self.count = count
    def __str__(self):
        return "({0},{1})".format(self.URL,self.count)

###
 # Fetch AllOtherTraffic snapshots from a controller then add them to the AllOtherTraffic dictionary. Provide either an username/password or an access token.
 # @param app_ID the ID number of the AllOtherTraffic snapshots to fetch
 # @param minutesBeforeNow fetch only snapshots newer than a relative duration in minutes
 # @param serverURL Full hostname of the Appdynamics controller. i.e.: https://demo1.appdynamics.com:443
 # @param userName Full username, including account. i.e.: myuser@customer1
 # @param password password for the specified user and host. i.e.: mypassword
 # @param token API acccess token
 # @return the number of fetched snapshots. Zero if no snapshot was found.
###
def fetch_allothertraffic(app_ID,minutesBeforeNow,serverURL=None,userName=None,password=None,token=None):
    MAX_RESULTS="9999"
    AllOtherTraffic_ID = get_business_transaction_ID(app_ID,"_APPDYNAMICS_DEFAULT_TX_")
    if AllOtherTraffic_ID == 0: return None

    if 'DEBUG' in locals(): print ("Fetching all other traffic snapshots for App "+str(app_ID)+"...")
    # Retrieving All Other Traffic Business Transaction Metrics
    # The All Other Traffic business transaction uses a special identifier in API URI paths, _APPDYNAMICS_DEFAULT_TX_
    restfulPath = "/controller/rest/applications/" + str(app_ID) + "/request-snapshots"

    for i in range(int(minutesBeforeNow),0,-180): # loop "minutesBeforeNow" minutes in chunks of 180 minutes (3 hours)
        sinceTime = datetime.today()-timedelta(minutes=i)
        sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
        params = timerange_to_params("AFTER_TIME",duration="180",startEpoch=sinceEpoch)
        params.update({"business-transaction-ids": AllOtherTraffic_ID})

        for retry in range(1,4):
            if 'DEBUG' in locals(): print ("Fetching snapshots for App " + str(app_ID) + "params "+str(params)+"...")
            if serverURL and userName and password:
                data_chunck = fetch_RESTful_JSON(restfulPath,params=params,serverURL=serverURL,userName=userName,password=password)
            else:
                data_chunck = fetch_RESTful_JSON(restfulPath,params=params)

            if data_chunck is not None:
                break
            elif retry < 3:
                print "Failed to fetch snapshots. Retrying (",retry," of 3)..."
            else:
                print "Giving up."
                return None
    
        if 'snapshots' not in locals():
            snapshots = data_chunck
            if 'DEBUG' in locals(): print "fetch_allothertraffic: Added " + str(len(snapshots)) + " snapshots."
        else:
            # Append retrieved data to root
            for new_snapshot in data_chunck:
                snapshots.append(new_snapshot)
            if 'DEBUG' in locals(): print "fetch_allothertraffic: Added " + str(len(snapshots)) + " snapshots."

    # Add loaded events to the event dictionary
    if 'snapshots' in locals():
        appdDefaultTX_Dict.update({str(app_ID):snapshots})
    else:
        return 0

    if 'DEBUG' in locals():
        print "fetch_allothertraffic: Loaded " + str(len(snapshots)) + " snapshots."

    return len(snapshots)

def generate_allothertraffic_CSV(app_ID,snapshots=None,fileName=None):
    if snapshots is None and str(app_ID) not in appdDefaultTX_Dict:
        print "AllOtherTraffic snapshots for application "+str(app_ID)+" not loaded."
        return
    elif snapshots is None and str(app_ID) in appdDefaultTX_Dict:
        snapshots = appdDefaultTX_Dict[str(app_ID)]

    if fileName is not None:
        try:
            csvfile = open(fileName, 'w')
        except:
            print ("Could not open output file " + fileName + ".")
            return (-1)
    else:
        csvfile = sys.stdout

    fieldnames = ['URL', 'Count']
    filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
    filewriter.writeheader()

    # Count distinct URLs and store in a dictionary
    URL_Count = dict()
    for snapshot in snapshots:
        if snapshot['URL'] in URL_Count:
            URL_Count[snapshot['URL']] = URL_Count[snapshot['URL']] + 1
        else:
            URL_Count.update({snapshot['URL']:0})

    # Add URLs and counts to CSV
    for URL in URL_Count:
        try:
            filewriter.writerow({'URL': URL,
                                'Count': URL_Count[URL]})
        except:
            print ("Could not write to the output file " + fileName + ".")
            if fileName is not None: csvfile.close()
            exit(1)
    if fileName is not None: csvfile.close()


###### FROM HERE PUBLIC FUNCTIONS ######


def get_allothertraffic_from_server(inFileName,outFilename=None):
    if 'DEBUG' in locals(): print "Processing file " + inFileName + "..."
    try:
        json_file = open(fileName)
        snapshots = json.load(json_file)
    except:
        if 'DEBUG' in locals(): print ("Could not process JSON file " + inFileName)
        return 0
    generate_allothertraffic_CSV(app_ID=0,snapshots=snapshots,fileName=outFilename)

def get_allothertraffic(app_ID,minutesBeforeNow,serverURL=None,userName=None,password=None,token=None):
    if serverURL and serverURL == "dummyserver":
        build_test_events(app_ID)
    elif serverURL and userName and password:
        if fetch_allothertraffic(app_ID,minutesBeforeNow,serverURL=serverURL,userName=userName,password=password) == 0:
            print "get_allothertraffic: Failed to retrieve snapshots for application " + str(app_ID)
            return None
    else:
        if fetch_allothertraffic(app_ID,minutesBeforeNow,token=token) == 0:
            print "get_allothertraffic: Failed to retrieve snapshots for application " + str(app_ID)
            return None
    generate_allothertraffic_CSV(app_ID)