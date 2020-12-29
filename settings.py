#!/usr/bin/python
import json
import csv
import sys
from entities import ControllerEntity

class ConfigurationDict(ControllerEntity):
    configDict = dict()

    def __init__(self):
        self.configDict = self.entityDict

    ###### FROM HERE PUBLIC FUNCTIONS ######

    ###
     # Generate CSV output from config data
     # @param fileName output file name
     # @return None
    ###
    def generate_CSV(self,fileName=None):
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['Name', 'Value', 'Scope', 'Updateable', 'Description']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
             
        for settingName in self.configDict:
            setting = self.configDict[settingName]
            # Check if data belongs to a controller setting
            if 'updateable' not in setting: continue
            elif 'header_is_printed' not in locals(): 
                filewriter.writeheader()
                header_is_printed=True
            try:
                filewriter.writerow({'Name': setting['name'],
                                     'Value': setting['value'],
                                     'Scope': setting['scope'],
                                     'Updateable': setting['updateable'],
                                     'Description': setting['description']})
            except ValueError as valError:
                print (valError)
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()