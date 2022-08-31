#!/usr/bin/python
import json
import csv
import xml.etree.ElementTree as ET
import sys

class AppEntity(dict):

    def __init__(self,controller):
        super(AppEntity,self).__init__()
        self.update({"controller":controller,"keywords":[],"CSVfields":{},"entities":None})

    def __str__(self):
        return "({0},{1})".format(self.__class__.__name__,len(self['entities']))

    def info(self):
        return "Class ",self.__class__,"Number of entities in ", hex(id(self['entities'])), len(self['entities'])

    def fetch(self,appID,selectors=None):
        """
        Fetch and store entities from controller RESTful API into the class JSON data.
        :param appID: the ID number of the application entities to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetch",app_ID=appID,selectors=selectors)
        return self.load(streamdata=data,appID=appID)

    def fetch_with_details(self,appID,entityName,selectors=None):
        """
        Fetch entity with details from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param entityName: the name of the entity to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the entity data. None if no entity was found.
        """
        streamdata = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetchList",app_ID=appID,selectors=selectors)
        entities = json.loads(streamdata)
        for entity in entities:
            if entity['name'] == entityName:
                try:
                    data = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetchByID",app_ID=appID,entity_ID=entity['id'],selectors=selectors)
                except KeyError:
                    sys.stderr.write("fetch_with_details("+str(self.__class__.__name__)+"): fetchByID API endpoint does not exist.\n")
                    return None

                retValue = self.load(streamdata=data,appID=appID)
                return self['entities'][appID] if retValue else None
        return None

    def fetch_after_time(self,appID,duration,sinceEpoch,selectors=None):
        """
        Fetch entities from controller RESTful API.
        :param appID: the ID number of the application entities to fetch.
        :param duration: duration (in minutes) to return the metric data
        :param sinceEpoch: start time (in unix epoch time) from which the metric data is returned.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self['controller'].RESTfulAPI.send_request( entityClassName=self.__class__.__name__,verb="fetch",app_ID=appID,selectors=selectors,
                                                        **{"time-range-type":"AFTER_TIME","duration-in-mins":duration,"start-time":sinceEpoch})
        return self.load(streamdata=data,appID=appID)

    def fetch_all_entities_with_details(self,appID=None,selectors=None):
        """
        Load entities with details for all entities within an application
        :param streamdata: the stream data with the entity list, in JSON format
        :param appID: the ID number of the application to fetch entities
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        streamdata = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetchList",app_ID=appID,selectors=selectors)
        entities = json.loads(streamdata)
        entityList = []
        for entity in entities:
            entityData = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetchByID",app_ID=appID,entity_ID=entity['id'],selectors=selectors)
            if entityData is None:
                sys.stderr.write("fetch_all_entities_with_details("+str(appID)+"): Failed to retrieve entity "+entity['name']+".\n")
                continue
            try:
                entityJSON = json.loads(entityData)
            except TypeError as error:
                sys.stderr.write("fetch_all_entities_with_details("+str(appID)+"): "+str(error)+"\n")
                continue
            entityList.append(entityJSON)
        if self['entities'] is None:
            self['entities'] = {appID:entityList}
        elif appID not in self['entities']:
            self['entities'].update({appID:entityList})
        else:
            self['entities'][appID].extend(entityList)
        #print(json.dumps(self['entities'][appID]))
        return len(entityList)

    def load(self,streamdata,appID=None):
        """
        Load entities from a JSON stream data.
        :param streamdata: the stream data in JSON format
        :param appID: the ID number of the application where to load the entities data.
        :returns: the number of loaded entities. Zero if no entity was loaded.
        """
        try:
            entities = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("load_AppEntity("+str(appID)+"): "+str(error)+"\n")
            return 0
        # Add loaded entities to the entities dictionary
        #if type(entities) is dict:    entities = [entities]
        if self['entities'] is None:
            self['entities'] = {appID:entities}
        elif appID not in self['entities']:
            self['entities'].update({appID:entities})
        else:
            self['entities'][appID].extend(entities)
        return len(entities)

    def create_or_update(self,appID,filePath):
        """
        Import, create new entity or update existing entity for a specific application, using an entity data input file.
        :param appID: the ID number of the application to update an existing entity
        :param filePath: the path to the file where data is stored
        :returns: true if the new entity was successfully created/updated. False otherwise.
        """
        if self['entities'] is None:
            self.fetch(appID=appID)

        streamdata = open(filePath).read()
        JSONdata = root = None
        try:
            JSONdata = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("create_or_update "+ str(self.__class__) +": "+str(error)+"\n")
            try:
                root = ET.fromstring(streamdata)
            except (TypeError,ET.ParseError) as error:
                if 'DEBUG' in locals(): sys.stderr.write("create_or_update "+ str(self.__class__)+": "+str(error)+"\n")
                return False

        if type(JSONdata) is dict and 'id' in JSONdata: # Data file in New format
            response = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="create",app_ID=appID,streamdata=streamdata)
            if response == "409": # Entity already exists, try with update
                for entity in self['entities'][appID]:
                    if entity['name'] == JSONdata['name']:
                        response = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="update",app_ID=appID,entity_ID=entity['id'],streamdata=streamdata)
                        break
            return response < 400
        elif (type(JSONdata) is list and 'id' not in JSONdata[0]) or 'root' in locals(): # Data file in Old format
                response = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="import",app_ID=appID,filePath=filePath)
                return response < 400
        else:
            return False


    # *****************************************************************************************************
    # ************************ EXPERIMENTAL: Only tested for health rule schedules ************************
    # *****************************************************************************************************
    # * https://nvie.com/posts/modifying-deeply-nested-structures/                                       **
    # * https://www.geeksforgeeks.org/python-update-nested-dictionary/                                   **
    # * https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth **
    # *****************************************************************************************************
    def patch(self,patchJSON,appID=None,sourcedata=None,selectors=None):
        """
        Patch entities for a list of applications, using an entity data input.
        :param patchJSON: the stream data with the entity configuration, in JSON format
        :param appID: the ID number of the application to patch entities
        :param sourcedata: the input source data to be patched
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

        if sourcedata is not None:
            if self.load(streamdata=sourcedata) > 0:
                appID = 0
        elif appID is not None:
            # Reload entity data for provided application
            if self.fetch_all_entities_with_details(appID) == 0:
                sys.stderr.write("patch: Failed to retrieve entities for application " + str(appID) + "...\n")
                return 0

        if selectors is not None and 'entityname' in selectors:
            # Generate the list of entity IDs to be patched
            entityNames = selectors['entityname'].split(',')
            entityIDs = [ entity['id'] for entity in self['entities'][appID] if 'name' in entity and entity['name'] in entityNames ]
        else:
            entityIDs = [ entity['id'] for entity in self['entities'][appID] ]

        # Run the patching
        count = 0
        for entity in self['entities'][appID]:
            if entity['id'] in entityIDs:
                # Do the replacement in loaded data
                entity.update(changesJSON)
                ### Fix for "policy anomalyEvents" bug found in the API
                if 'events' in entity:
                    entity['events'].pop('anomalyEvents')
                if not sourcedata:
                    # Update controller data
                    if self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="update",app_ID=appID,entity_ID=entity['id'],streamdata=entity) == True:
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
        fieldnames = ['Application'] + [ name for name in self['CSVfields'] ]
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for appID in self['entities']:
            if appID_List is not None and type(appID_List) is list and int(appID) not in appID_List:
                if 'DEBUG' in locals(): print ("Application "+appID +" is not loaded in dictionary.")
                continue
            for entity in self['entities'][appID]:
                if  'header_is_printed' not in locals():
                    filewriter.writeheader()
                    header_is_printed=True
                row = { name: self['CSVfields'][name](entity) for name in self['CSVfields'] }
                appName = self['controller'].applications.getAppName(appID)
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
            entities = [ self['entities'][appID] for appID in appID_List if appID in self['entities'] ]
        else:
            entities = self['entities']

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


class ControllerEntity(dict):

    def __init__(self,controller):
        super(ControllerEntity,self).__init__()
        self.update({"controller":controller,"keywords":[],"CSVfields":{},"entities":None})

    def __str__(self):
        return "({0},{1})".format(self.__class__.__name__,len(self['entities']))

    def info(self):
        return "Class ",self.__class__,"Number of entities in ", hex(id(self['entities'])), len(self['entities'])

    def fetch(self,selectors=None):
        """
        Fetch and store entities from controller RESTful API into the class JSON data.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        data = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetch",selectors=selectors)
        return self.load(streamdata=data)

    def fetch_with_details(self,entityName,selectors=None):
        """
        Fetch entity with details from controller RESTful API.
        :param entityName: the name of the entity to fetch.
        :param selectors: fetch only entities filtered by specified selectors
        :returns: the entity data. None if no entity was found.
        """
        if self['entities'] is None:
            self.fetch(selectors=selectors)
        for entity in self['entities']:
            if entity['name'] == entityName:
                entity_ID = entity['id'] if 'id' in entity else entity['name']
                try:
                    data = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetchByID",entity_ID=entity_ID,selectors=selectors)
                except KeyError:
                    sys.stderr.write("fetch_with_details("+str(self.__class__.__name__)+"): fetchByID API endpoint does not exist.\n")
                    return None
                try:
                    return json.loads(data)
                except (TypeError,ValueError) as error:
                    sys.stderr.write("fetch_with_details("+str(appID)+"): "+str(error)+"\n")
                    return None
        return None

    def fetch_all_entities_with_details(self,selectors=None):
        """
        Load entities with details for all entity objects
        :param streamdata: the stream data with the entity list, in JSON format
        :returns: the number of fetched entities. Zero if no entity was found.
        """
        if self['entities'] is None:
            self.fetch(selectors=selectors)
        index = 0
        for entity in self['entities']:
            entity_ID = entity['id'] if 'id' in entity else entity['name']
            streamdata = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="fetchByID",entity_ID=entity_ID,selectors=selectors)
            if streamdata is None:
                sys.stderr.write("fetch_all_entities_with_details("+str(self.__class__.__name__)+"): Failed to retrieve entity "+entity['name']+".\n")
                continue
            try:
                entityJSON = json.loads(streamdata)
            except TypeError as error:
                sys.stderr.write("fetch_all_entities_with_details("+str(self.__class__.__name__)+"): "+str(error)+"\n")
                continue
            self['entities'][index] = entityJSON
            index = index + 1
        return index

    def load(self,streamdata):
        """
        Load entities from a JSON stream data.
        :param streamdata: the stream data in JSON format
        :returns: the number of loaded entities. Zero if no entity was loaded.
        """
        try:
            self['entities'] = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("load_ControllerEntity("+str(appID)+"): "+str(error)+"\n")
            return 0
        return len(self['entities'])

    def create_or_update(self,filePath):
        """
        Import, create new entity or update existing entity, using an entity data input file.
        :param filePath: the path to the file where data is stored
        :returns: true if the existing entity was successfully updated. False otherwise.
        """
        if self['entities'] is None:
            self.fetch()

        streamdata = open(filePath).read()
        try:
            JSONdata = json.loads(streamdata)
        except (TypeError,ValueError) as error:
            if 'DEBUG' in locals(): sys.stderr.write("create_or_update "+ str(self.__class__) +": "+str(error)+"\n")
            try:
                root = ET.fromstring(streamdata)
            except (TypeError,ET.ParseError) as error:
                if 'DEBUG' in locals(): sys.stderr.write("create_or_update "+ str(self.__class__)+": "+str(error)+"\n")
                return False

        if type(JSONdata) is dict and 'id' in JSONdata: # Data file in New format
            response = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="create",streamdata=streamdata)
            if response == "409": # Entity already exists, try with update
                for entity in self['entities']:
                    if entity['name'] == JSONdata['name']:
                        response = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="update",entity_ID=entity['id'],streamdata=streamdata)
                        break
            return response < 400
        elif (type(JSONdata) is list and 'id' not in JSONdata[0]) or 'root' in locals(): # Data file in Old format
                response = self['controller'].RESTfulAPI.send_request(entityClassName=self.__class__.__name__,verb="import",filePath=filePath)
                return response < 400
        else:
            return False

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
        fieldnames = [ name for name in self['CSVfields'] ]
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for entity in self['entities']:
            if 'header_is_printed' not in locals():
                filewriter.writeheader()
                header_is_printed=True
            row = { name: self['CSVfields'][name](entity) for name in self['CSVfields'] }
            try:
                filewriter.writerow(row)
            except ValueError as valError:
                sys.stderr.write("generate_CSV: "+str(valError)+"\n")
                if fileName is not None: csvfile.close()
                return (-1)
        if fileName is not None: csvfile.close()

    def generate_JSON(self,fileName=None):
        """
        Generate JSON output from dictionary data
        :param fileName: output file name
        :returns: None
        """
        if fileName is not None:
            try:
                with open(fileName, 'w') as outfile:
                    json.dump(self['entities'], outfile)
                outfile.close()
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            print (json.dumps(self['entities']))
