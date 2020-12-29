#!/usr/bin/python
import json
import sys

class AppEntity:
    entityDict = dict()

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.entityDict)

    def generate_CSV(self,appID_List,fileName=None):
        pass

    ###
     # Generate JSON output from dictionary data
     # @param appID_List list of application IDs, in order to obtain entities from local entities dictionary
     # @param fileName output file name
     # @return None
    ###
    def generate_JSON(self,appID_List,fileName=None):
        if type(appID_List) is not list or len(appID_List)==0: return
        entityList = [ self.entityDict[str(appID)]  for appID in appID_List ]
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(entityList, outfile)
                outfile.close()
            except:
                print ("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(entityList)

    ###
     # Load entities from a JSON stream data.
     # @param streamdata the stream data in JSON format
     # @param appID the ID number of the application where to load the entities data.
     # @return the number of loaded entities. Zero if no entity was loaded.
    ###
    def load(self,streamdata,appID=None):
        if appID is None: appID = 0
        try:
            entities = json.loads(streamdata)
        except TypeError as error:
            print ("load_entities: "+str(error))
            return 0
        # Add loaded entities to the entities dictionary
        if type(entities) is dict:
            self.entityDict.update({str(appID):[entities]})
        else:
            self.entityDict.update({str(appID):entities})
        return len(entities)