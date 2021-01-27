#!/usr/bin/python
import json
import csv
import sys
from appdRESTfulAPI import RESTfulAPI
from entities import ControllerEntity

class ConfigurationDict(ControllerEntity):
    entityAPIFunctions = {'fetch': RESTfulAPI().fetch_configuration}

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
             
        for settingName in self.entityDict:
            setting = self.entityDict[settingName]
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

    ###
     # Load entities from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @return the number of loaded entities. Zero if no entity was loaded.
    ###
    def load(self,streamdata):
        try:
            entities = json.loads(streamdata)
        except TypeError as error:
            sys.stderr.write("load_entities: "+str(error))
            return 0
        for entity in entities:
            # Add loaded entities to the entity dictionary
            entityID = entity['name']
            self.entityDict.update({str(entityID):entity})
        return len(entities)