#!/usr/bin/python
import json
import csv
import sys


class ConfigurationDict:
    configDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.configDict)

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

    ###
     # Generate JSON output from config data
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,fileName=None):
        data = [ self.configDict[settingName] for settingName in self.configDict ]

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
     # Load config from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID
     # @return None
    ###
    def load(self,streamdata,appID=None):
        try:
            configurations = json.loads(streamdata)
        except TypeError as error:
            print ("load_settings: "+str(error))
            return 0
        for setting in configurations:
            # Add loaded setting to the configurations dictionary
            if 'updateable' not in setting: continue
            settingName = setting['name']
            self.configDict.update({settingName:setting})
        return len(configurations)