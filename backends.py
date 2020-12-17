#!/usr/bin/python
import json
import csv
import sys
from applications import ApplicationDict


class BackendDict:
    backendDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.backendDict)

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from backends data
     # @param appID_List list of application IDs, in order to obtain backends from local backends dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        fieldnames = ['name', 'Application', 'exitPointType']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in appID_List:
            if str(appID) not in self.backendDict:
                if 'DEBUG' in locals(): print "Application "+str(appID) +" is not loaded in dictionary."
                continue
            for BE in self.backendDict[str(appID)]:
                # Check if data belongs to a backend
                if 'exitPointType' not in BE: continue
                elif 'header_is_printed' not in locals(): 
                    filewriter.writeheader()
                    header_is_printed=True

                try:
                    filewriter.writerow({'name': BE['name'].encode('ASCII', 'ignore'),
                                         'Application': ApplicationDict().getAppName(appID),
                                         'exitPointType': BE['exitPointType']})
                except ValueError as valError:
                    print (valError)
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()

    ###
     # Generate CSV output from backends data, either from the local dictionary or from streamed data
     # @param appID_List list of application IDs, in order to obtain backends from local backends dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return

        backends = []
        for appID in appID_List:
            backends = backends + self.backendDict[str(appID)]

        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(backends, outfile)
                outfile.close()
            except:
                print ("generate_backends_JSON: Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(backends)


    ###
     # Load backends from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID the ID number of the application where to load the health rule data.
     # @return the number of loaded backends. Zero if no backend was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            backends = json.loads(streamdata)
        except TypeError as error:
            print ("load_backends: "+str(error))
            return 0
        # Add loaded Backends to the Backend dictionary
        if type(backends) is dict:
            self.backendDict.update({str(appID):[backends]})
        else:
            self.backendDict.update({str(appID):backends})
        return len(backends)