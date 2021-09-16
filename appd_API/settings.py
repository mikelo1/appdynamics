import json
import csv
import sys
from .entities import ControllerEntity

class ConfigurationDict(ControllerEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_configuration }
        self.entityKeywords = ['updateable']

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,fileName=None):
        """
        Generate CSV output from config data
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['Name', 'Value', 'Scope', 'Updateable', 'Description']
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
             
        for setting in self.entityDict:
            if 'header_is_printed' not in locals():
                filewriter.writeheader()
                header_is_printed=True
            try:
                filewriter.writerow({'Name': setting['name'],
                                     'Value': setting['value'],
                                     'Scope': setting['scope'],
                                     'Updateable': setting['updateable'],
                                     'Description': setting['description']})
            except ValueError as valError:
                sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()
