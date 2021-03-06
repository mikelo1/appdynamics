#!/usr/bin/python
import json
import sys

class AppEntity:
    entityDict = dict()
    entityAPIFunctions = {} # {'fetch': RESTfulAPI().fetch_entity}

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
        except TypeError as error:
            sys.stderr.write("load_entities: "+str(error))
            return 0
        # Add loaded entities to the entities dictionary
        if type(entities) is dict:
            entities = [entities]
        if str(appID) not in self.entityDict:
            self.entityDict.update({str(appID):entities})
        else:
            self.entityDict[str(appID)].extend(entities)
        return len(entities)

    def generate_CSV(self,appID_List,fileName=None):
        pass

    def generate_JSON(self,appID_List,fileName=None):
        """
        Generate JSON output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
        :param fileName: output file name
        :returns: None
        """
        if type(appID_List) is list and len(appID_List) > 1:
            entities = [ self.entityDict[str(appID)]  for appID in appID_List ]
        elif type(appID_List) is list and len(appID_List) == 1:
            entities = self.entityDict[str(appID_List[0])]
        else:
            entities = {}

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


    def generate_CSV(self,fileName=None):
        pass


    def generate_JSON(self,fileName=None):
        """
        Generate JSON output from dictionary data
        :param fileName: output file name
        :returns: None
        """
        data = [ self.entityDict[entityID] for entityID in self.entityDict ]
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(data, outfile)
                outfile.close()
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print json.dumps(data)


    def load(self,streamdata):
        """
        Load entities from a JSON stream data.
        :param streamdata: the stream data in JSON format
        :returns: the number of loaded entities. Zero if no entity was loaded.
        """
        try:
            entities = json.loads(streamdata)
        except TypeError as error:
            sys.stderr.write("load_entities: "+str(error))
            return 0
        for entity in entities:
            # Add loaded entities to the entity dictionary
            entityID = entity['id']
            self.entityDict.update({str(entityID):entity})
        return len(entities)