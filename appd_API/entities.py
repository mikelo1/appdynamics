#!/usr/bin/python
import json
import csv
import xml.etree.ElementTree as ET
import sys

class AppEntity:
    entityDict = dict()
    entityAPIFunctions = {} # {'fetch':     RESTfulAPI().fetch_entity
                            #  'fetchByID': RESTfulAPI().fetch_entity_by_ID,
                            #  'import':    RESTfulAPI().import_entity,
                            #  'create':    RESTfulAPI().create_entity,
                            #  'update':    RESTfulAPI().update_entity}
    entityKeywords = []
    controller = None

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

    def fetch_with_details(self,appID,entityName,selectors=None):
        """
        Fetch entity with details from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param entityName: the name of the entity to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the entity data. Empty string if no entity was found.
        """
        streamdata = self.entityAPIFunctions['fetch'](app_ID=appID,selectors=selectors)
        self.load(streamdata,appID)
        for entity in self.entityDict[str(appID)]:
            if entity['name'] == entityName:
                return self.entityAPIFunctions['fetchByID'](appID,entity['id'])
        return ""

    def fetch_after_time(self,appID,duration,sinceEpoch,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self.entityAPIFunctions['fetch'](app_ID=appID,time_range_type="AFTER_TIME",duration=duration,startEpoch=sinceEpoch,selectors=selectors)
        return self.load(streamdata=data,appID=appID)

    def fetch_all_entities_with_details(self,appID=None,selectors=None):
        """
        Load entities with details for all entities within an application
        :param streamdata: the stream data with the entity list, in JSON format
        :param appID: the ID number of the application to fetch entities
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        if appID is None: appID = 0
        streamdata = self.entityAPIFunctions['fetch'](app_ID=appID,selectors=selectors)
        self.load(streamdata,appID)
        index = 0
        for entity in self.entityDict[str(appID)]:
            streamdata = self.entityAPIFunctions['fetchByID'](appID,entity['id'])
            if streamdata is None:
                sys.stderr.write("load_AppEntity_with_details("+str(appID)+"): Failed to retrieve entity "+entity['name']+".\n")
                continue
            try:
                entityJSON = json.loads(streamdata)
            except TypeError as error:
                sys.stderr.write("load_AppEntity_with_details("+str(appID)+"): "+str(error)+"\n")
                continue
            self.entityDict[str(appID)][index] = entityJSON
            index = index + 1
        return index

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
            return len( [ True for keyword in self.entityKeywords if root.find(keyword) is not None ] ) > 0
        # Input data is JSON format
        if dataJSON is not None and type(dataJSON) is list:
            return len( [ True for keyword in self.entityKeywords if keyword in dataJSON[0] ] ) > 0
        elif dataJSON is not None and type(dataJSON) is dict:
            return len( [ True for keyword in self.entityKeywords if keyword in dataJSON ] ) > 0
        return False

    def file_import(self,appID,filePath):
        """
        Import entities within an application, using an entity data input file.
        :param filePath: the path to the file where data is stored
        :param appID: the ID number of the application to fetch entities
        :returns: True if the update was successful. False if no data was updated.
        """
        return self.entityAPIFunctions['import'](app_ID=appID,filePath=filePath)

    def create(self,appID,streamdata):
        """
        Create one entity for a specific application, using an entity data input.
        :param appID: the ID number of the application to create a new entity
        :param streamdata: the stream data with the entity configuration, in JSON format
        :returns: true if the new entity was successfully created. False otherwise.
        """
        return self.entityAPIFunctions['create'](app_ID=appID,dataJSON=streamdata)

    def update(self,appID,streamdata):
        """
        Update existing entity for a specific application, using an entity data input.
        :param appID: the ID number of the application to update an existing entity
        :param streamdata: the stream data with the entity configuration, in JSON format
        :returns: true if the new entity was successfully created. False otherwise.
        """
        if len(self.entityDict) == 0:
            self.fetch(appID=appID)
        entityData = json.loads(streamdata)
        entity_IDs = [ entity['id'] for entity in self.entityDict[str(appID)] if entity['name'] == entityData['name'] ]
        return len(entity_IDs) > 0 and self.entityAPIFunctions['update'](app_ID=appID,entity_ID=entity_IDs[0],dataJSON=streamdata)

    # *****************************************************************************************************
    # ************************ EXPERIMENTAL: Only tested for health rule schedules ************************
    # *****************************************************************************************************
    # * https://nvie.com/posts/modifying-deeply-nested-structures/                                       **
    # * https://www.geeksforgeeks.org/python-update-nested-dictionary/                                   **
    # * https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth **
    # *****************************************************************************************************
    def patch(self,patchJSON,appID=None,streamdata=None,selectors=None):
        """
        Patch entities for a list of applications, using an entity data input.
        :param patchJSON: the stream data with the entity configuration, in JSON format
        :param appID: the ID number of the application to patch entities
        :param streamdata: the input stream data to be patched
        :param selectors: update only entities filtered by specified selectors
        :returns: the number of updated entities. Zero if no entity was updated.
        """
        # Verify if the source is a file or stream JSON data
        DEBUG=True
        try:
            changesJSON = json.loads(patchJSON)
        except ValueError as error:
            if 'DEBUG' in locals(): sys.stderr.write("patch_entity: "+str(error)+"\n")
            return 0

        if streamdata is not None:
            if self.load(streamdata=streamdata) > 0:
                appID = 0
        elif appID is not None:
            # Reload entity data for provided application
            if self.fetch_all_entities_with_details(appID) == 0:
                sys.stderr.write("patch_entity: Failed to retrieve entities for application " + str(appID) + "...\n")
                return 0

        if selectors is not None and 'entityname' in selectors:
            # Generate the list of entity IDs to be patched
            entityNames = selectors['entityname'].split(',')
            entityIDs = [ entity['id'] for entity in self.entityDict[str(appID)] if entity['name'] in entityNames ]
        else:
            entityIDs = [ entity['id'] for entity in self.entityDict[str(appID)] ]

        # Run the patching
        count = 0
        for entity in self.entityDict[str(appID)]:
            if entity['id'] in entityIDs:
                # Do the replacement in loaded data
                entity.update(changesJSON)
                if not streamdata:
                    # Update controller data
                    if self.entityAPIFunctions['update'](app_ID=appID,entity_ID=entity['id'],dataJSON=entity) == True:
                        count = count + 1
                else:
                    # Print updated data
                    print(json.dumps(entity))
                    count = count + 1

        return count


    def generate_CSV(self,appID_List=None,fileName=None):
        """
        Generate CSV output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write("Could not open output file " + fileName + ".\n")
                return (-1)
        else:
            csvfile = sys.stdout

        # create the csv writer object
        fieldnames = ['Application'] + [ name for name in self.CSVfields ]
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self.entityDict:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print ("Application "+appID +" is not loaded in dictionary.")
                continue
            for entity in self.entityDict[appID]:
                if  'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True
                row = { name: self.CSVfields[name](entity) for name in self.CSVfields }
                appName = self.controller.applications.getAppName(appID)
                row['Application'] = appName if appName is not None and sys.version_info[0] >= 3 else appName.encode('ASCII', 'ignore') if appName is not None else ""
                try:
                    filewriter.writerow(row)
                except ValueError as valError:
                    sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                    if fileName is not None: csvfile.close()
                    return (-1)
        if fileName is not None: csvfile.close()
        #raise NotImplementedError("Don't forget to implement the generate_CSV function!")


    def generate_JSON(self,appID_List=None,fileName=None):
        """
        Generate JSON output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
        :param fileName: output file name
        :returns: None
        """
        if appID_List is not None and type(appID_List) is list and len(appID_List) > 0:
            entities = [ self.entityDict[str(appID)] for appID in appID_List if str(appID) in self.entityDict ]
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
            print (json.dumps(entities))


class ControllerEntity:
    entityDict = dict()
    entityAPIFunctions = {} # {'fetch':     RESTfulAPI().fetch_entity
                            #  'fetchByID': RESTfulAPI().fetch_entity_by_ID,
                            #  'import':    RESTfulAPI().import_entity,
                            #  'create':    RESTfulAPI().create_entity,
                            #  'update':    RESTfulAPI().update_entity}
    entityKeywords = []
    controller = None

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

    def fetch_with_details(self,entityName,selectors=None):
        """
        Fetch entity with details from controller RESTful API.
        :param entityName: the name of the entity to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the entity data. Empty string if no entity was found.
        """
        streamdata = self.entityAPIFunctions['fetch']()
        self.load(streamdata=streamdata)
        for entity in self.entityDict:
            if entity['name'] == entityName:
                return self.entityAPIFunctions['fetchByID'](entity['id'])
        return ""

    def fetch_all_entities_with_details(self,selectors=None):
        """
        Load entities with details
        :param streamdata: the stream data with the entity list, in JSON format
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        streamdata = self.entityAPIFunctions['fetch']()
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
            return len( [ True for keyword in self.entityKeywords if root.find(keyword) is not None ] ) > 0
        # Input data is JSON format
        if dataJSON is not None and type(dataJSON) is list:
            return len( [ True for keyword in self.entityKeywords if keyword in dataJSON[0] ] ) > 0
        elif dataJSON is not None and type(dataJSON) is dict:
            return len( [ True for keyword in self.entityKeywords if keyword in dataJSON ] ) > 0
        return False

    def file_import(self,filePath):
        """
        Import entities using an entity data input file.
        :param filePath: the path to the file where data is stored
        :returns: True if the update was successful. False if no data was updated.
        """
        return self.entityAPIFunctions['import'](filePath=filePath)

    def create(self,streamdata):
        """
        Create one entity, using an entity data input.
        :param streamdata: the stream data with the entity configuration, in JSON format
        :returns: true if the new entity was successfully created. False otherwise.
        """
        return self.entityAPIFunctions['create'](dataJSON=streamdata)

    def update(self,streamdata):
        """
        Update existing entity, using an entity data input.
        :param streamdata: the stream data with the entity configuration, in JSON format
        :returns: true if the existing entity was successfully updated. False otherwise.
        """
        if len(self.entityDict) == 0:
            self.fetch()
        entityData = json.loads(streamdata)
        entity_IDs = [ entity['id'] for entity in self.entityDict if entity['name'] == entityData['name'] ]
        return len(entity_IDs) > 0 and self.entityAPIFunctions['update'](entity_ID=entity_IDs[0],dataJSON=streamdata)

    def patch(self,appID,streamdata,selectors=None):
        """
        Patch entities using an entity data input and an optional filter.
        :param streamdata: the stream data with the entity configuration, in JSON format
        :param selectors: update only entities filtered by specified selectors
        :returns: the number of updated entities. Zero if no entity was updated.
        """
        raise NotImplementedError("Don't forget to implement the patch function!")

    def generate_CSV(self,fileName=None):
        """
        Generate CSV output from dictionary data
        :param appID_List: list of application IDs, in order to obtain entities from local entities dictionary
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
        fieldnames = [ name for name in self.CSVfields ]
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for entity in self.entityDict:
            if 'header_is_printed' not in locals():
                filewriter.writeheader()
                header_is_printed=True
            row = { name: self.CSVfields[name](entity) for name in self.CSVfields }
            try:
                filewriter.writerow(row)
            except ValueError as valError:
                sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()
        #raise NotImplementedError("Don't forget to implement the generate_CSV function!")

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
            print (json.dumps(self.entityDict))
