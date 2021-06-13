#!/usr/bin/python
import json
import xml.etree.ElementTree as ET
import sys

class AppEntity:
    entityDict = dict()
    entityAPIFunctions = {} # {'fetch':     RESTfulAPI().fetch_entity
                            #  'fetchByID': RESTfulAPI().fetch_entity_by_ID,
                            #  'import':    RESTfulAPI().import_entity}
    entityJSONKeyword = ""
    entityXMLKeyword = ""

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.entityDict)

    def count(self):
        count = 0
        for appID in self.entityDict:
            count += len(self.entityDict[str(appID)])
        return count

    def info(self):
        return "Class ",self.__class__,"Number of entities in ", hex(id(self.entityDict)), self.count()

    def fetch(self,appID,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self.entityAPIFunctions['fetch'](app_ID=appID,selectors=selectors)
        return self.load(streamdata=data,appID=appID)

    def fetch_with_details(self,appID,selectors=None):
        """
        Fetch entities with details from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self.entityAPIFunctions['fetch'](app_ID=appID,selectors=selectors)
        return self.load_with_details(streamdata=data,appID=appID)

    def fetch_after_time(self,appID,duration,sinceEpoch,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self.entityAPIFunctions['fetch'](app_ID=appID,time_range_type="AFTER_TIME",duration=duration,startEpoch=sinceEpoch,selectors=selectors)
        return self.load(streamdata=data,appID=appID)

    def load(self,streamdata,appID=None):
        """
        Load entities from a JSON stream data.
        :param streamdata: the stream data in JSON format
        :param appID: the ID number of the application where to load the entities data.
        :returns: the number of loaded entities. Zero if no entity was loaded.
        """
        if appID is None: appID = 0
        try:
            entities = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("load_AppEntity("+str(appID)+"): "+str(error)+"\n")
            return 0
        # Add loaded entities to the entities dictionary
        if type(entities) is dict:
            entities = [entities]
        if str(appID) not in self.entityDict:
            self.entityDict.update({str(appID):entities})
        else:
            self.entityDict[str(appID)].extend(entities)
        return len(entities)

    def load_with_details(self,streamdata,appID=None):
        """
        Load entities with details for all entities within an application
        :param streamdata: the stream data with the entity list, in JSON format
        :param app_ID: the ID number of the application to fetch entities
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        if appID is None: appID = 0
        self.load(streamdata,appID)
        index = 0
        for entity in self.entityDict[str(appID)]:
            streamdata = self.entityAPIFunctions['fetchByID'](appID,entity['id'])
            if streamdata is None:
                sys.stderr.write("load_AppEntity_with_details("+str(appID)+"): Failed to retrieve entity.\n")
                continue
            try:
                entityJSON = json.loads(streamdata)
            except TypeError as error:
                sys.stderr.write("load_AppEntity_with_details("+str(appID)+"): "+str(error)+"\n")
                continue
            self.entityDict[str(appID)][index] = entityJSON
            index = index + 1
        return index

    def verify(self,streamdata):
        """
        Verify that input stream contains entity data.
        :param streamdata: the stream data
        :returns: True if the stream data contains an entity. False otherwise.
        """
        try:
            dataJSON = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("verify "+ str(self.__class__) +": "+str(error)+"\n")
            try:
                root = ET.fromstring(streamdata)
            except (TypeError,ET.ParseError) as error:
                if 'DEBUG' in locals(): sys.stderr.write("verify "+ str(self.__class__)+": "+str(error)+"\n")
                return False
            # Input data is XML format
            return root.find(self.entityXMLKeyword) is not None
        # Input data is JSON format
        if dataJSON is not None and type(dataJSON) is list:
            return self.entityJSONKeyword in dataJSON[0]
        elif dataJSON is not None and type(dataJSON) is dict:
            return self.entityJSONKeyword in dataJSON
        return False

    def apply(self,appID,filePath):
        return self.entityAPIFunctions['import'](app_ID=appID,filePath=filePath)

    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
        :param fileName: output file name
        :returns: None
        """
        raise NotImplementedError("Don't forget to implement the generate_CSV function!")

    def generate_JSON(self,appID_List=None,fileName=None):
        """
        Generate JSON output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
        :param fileName: output file name
        :returns: None
        """
        if appID_List is not None and type(appID_List) is list and len(appID_List) > 0:
            entities = [ self.entityDict[str(appID)] for appID in appID_List ]
        else:
            entities = self.entityDict

        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(entities, outfile)
                outfile.close()
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(entities)


class ControllerEntity:
    entityDict = dict()
    entityAPIFunctions = {} # {'fetch': RESTfulAPI().fetch_entity}
    entityJSONKeyword = ""
    entityXMLKeyword = ""

    def __init__(self):
        pass

    def __str__(self):
        return json.dumps(self.entityDict)

    def count(self):
        return len(self.entityDict)


    def info(self):
        return "Class ",self.__class__,"Number of entities in ", hex(id(self.entityDict)), self.count()

    def fetch(self,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self.entityAPIFunctions['fetch']()
        return self.load(streamdata=data)

    def fetch_with_details(self,selectors=None):
        """
        Fetch entities with details from controller RESTful API.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self.entityAPIFunctions['fetch']()
        return self.load_with_details(streamdata=data)

    def load(self,streamdata):
        """
        Load entities from a JSON stream data.
        :param streamdata: the stream data in JSON format
        :returns: the number of loaded entities. Zero if no entity was loaded.
        """
        try:
            entities = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("load_ControllerEntity("+str(appID)+"): "+str(error)+"\n")
            return 0
        self.entityDict=entities
        return len(entities)

    def load_with_details(self,streamdata):
        """
        Load entities with details
        :param streamdata: the stream data with the entity list, in JSON format
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        self.load(streamdata)
        count = 0
        for entity in self.entityDict:
            response = RESTfulAPI().fetch_custom_dashboard(dashboard['id'])
            if streamdata is None:
                sys.stderr.write("load_AppEntity_with_details("+str(appID)+"): Failed to retrieve entity.\n")
                continue
            try:
                entityJSON = json.loads(response)
            except TypeError as error:
                sys.stderr.write("load_AppEntity_with_details: "+str(error)+"\n")
                continue
            self.entityDict[count]=entityJSON
            count += 1
        return count

    def verify(self,streamdata):
        """
        Verify that input stream contains entity data.
        :param streamdata: the stream data
        :returns: True if the stream data contains an entyty. False otherwise.
        """
        try:
            dataJSON = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("verify "+ str(self.__class__) +": "+str(error)+"\n")
            try:
                root = ET.fromstring(streamdata)
            except (TypeError,ET.ParseError) as error:
                if 'DEBUG' in locals(): sys.stderr.write("verify "+ str(self.__class__)+": "+str(error)+"\n")
                return False
            # Input data is XML format
            return root.find(self.entityXMLKeyword) is not None
        # Input data is JSON format
        if dataJSON is not None and type(dataJSON) is list:
            return self.entityJSONKeyword in dataJSON[0]
        elif dataJSON is not None and type(dataJSON) is dict:
            return self.entityJSONKeyword in dataJSON
        return False

    def apply(self,filePath):
        return self.entityAPIFunctions['import'](filePath=filePath)

    def generate_CSV(self,fileName=None):
        """
        Generate CSV output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
        :param fileName: output file name
        :returns: None
        """
        raise NotImplementedError("Don't forget to implement the generate_CSV function!")

    def generate_JSON(self,fileName=None):
        """
        Generate JSON output from dictionary data
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(self.entityDict, outfile)
                outfile.close()
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(self.entityDict)
