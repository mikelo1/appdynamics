#!/usr/bin/python
import unittest
import os.path
import sys
import subprocess
from zipfile import ZipFile
from contexts import Contexts, BasicAuth
from appd_API import Controller

class TestSum(unittest.TestCase):

    applicationList = []

    def test_contexts(self):
        """
        Integrity tests for contexts
        """
        if os.path.isfile("appdconfig.yaml"):
            question = "File appdconfig.yaml already exists. Do you want to replace it [Y/N]?"
            answer   = ""
            while answer not in ["y", "n"]:
                if sys.version_info[0] < 3:
                    answer = raw_input(question).lower()
                else:
                    answer = input(question).lower()
            if answer == "y": os.remove("appdconfig.yaml")
            else: return

        if 'VERBOSE' in locals(): print ("Try to get appdynamics context file, when file doesn't exist")
        result = subprocess.call("./appdctl.py config get-contexts ", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Create new appdynamics context file and add new context")
        result = subprocess.call("./appdctl.py config set-context EVO.PRO --controller-url https://evobanco.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Append context to appdynamics context file")
        result = subprocess.call("./appdctl.py config set-context EVO.UAT --controller-url https://evobanco-dev.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco-dev", shell=True)
        self.assertEqual(result, 0)
        result = subprocess.call("./appdctl.py config set-context localhost --controller-url http://localhost:8090 --user-API APIClient@customer1", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Add already existing context to appdynamics context file")
        result = subprocess.call("./appdctl.py config set-context EVO.UAT --controller-url https://evobanco-dev.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco-dev", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Get contexts from appdynamics context file")
        result = subprocess.call("./appdctl.py config get-contexts", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Use existing context on appdynamics context file")
        result = subprocess.call("./appdctl.py config use-context EVO.UAT", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Use non existing context on appdynamics context file")
        result = subprocess.call("./appdctl.py config use-context nonexist", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Delete existing context on appdynamics context file")
        result = subprocess.call("./appdctl.py config delete-context localhost", shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Delete non existing context on appdynamics context file")
        result = subprocess.call("./appdctl.py config delete-context nonexist", shell=True)
        self.assertEqual(result, 0)

#    def test_entities_load(self):
#        """
#        Integrity tests for loading XML and JSON files containing entity data
#        """
#        with ZipFile('tests.zip', 'r') as testzip:
#
#            FNULL = open(os.devnull, 'w')
#            if 'VERBOSE' in locals(): print ("Get XML entities from file")
#            for XML_ENTITY in ['transactiondetection-custom']:
#                if 'VERBOSE' in locals(): print ("### Get "+XML_ENTITY+" ###")
#                with testzip.open(XML_ENTITY+".xml") as testfile:
#                    filedata = testfile.read()
#
#                    if sys.version_info[0] < 3:
#                        filePipe = subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE)
#                        result = subprocess.call("./appdctl.py get -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
#                        self.assertEqual(result, 0, "Loading of file"+XML_ENTITY+".xml failed.")
#                        filePipe.stdout.close()
#                    else:
#                        with subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE) as filePipe:
#                            result = subprocess.call("./appdctl.py get -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
#                            self.assertEqual(result, 0, "Loading of file"+XML_ENTITY+".xml failed.")
#
#                #unzip -p tests.zip $XML_ENTITY.xml | $SCRIPTPATH/./appdctl.py  get -f -
#
#            if 'VERBOSE' in locals(): print ("Get JSON entities from file")
#            for JSON_ENTITY in ['actions','actions-legacy','health-rules','policies','policies-legacy','schedules', \
#                                 'allothertraffic','backends','business-transactions', \
#                                 'applications','dashboards','healthrule-violations','request-snapshots']:
#                if 'VERBOSE' in locals(): print ("### Get "+JSON_ENTITY+" ###")
#                with testzip.open(JSON_ENTITY+".json") as testfile:
#                    filedata = testfile.read()
#
#                    if sys.version_info[0] < 3:
#                        filePipe = subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE)
#                        result = subprocess.call("./appdctl.py get -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
#                        self.assertEqual(result, 0, "Loading of file "+JSON_ENTITY+".xml failed.")
#                        filePipe = subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE)
#                        result = subprocess.call("./appdctl.py get -o JSON -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
#                        self.assertEqual(result, 0, "Loading of file "+JSON_ENTITY+".xml failed.")
#                        filePipe.stdout.close()
#                    else:
#                        with subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE) as filePipe:
#                            result = subprocess.call("./appdctl.py get -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
#                            self.assertEqual(result, 0, "Loading of file "+JSON_ENTITY+".xml failed.")
#                        with subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE) as filePipe:
#                            result = subprocess.call("./appdctl.py get -o JSON -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
#                            self.assertEqual(result, 0, "Loading of file "+JSON_ENTITY+".xml failed.")
#            FNULL.close()


    def test_entities_basicauth(self):
        """
        Integrity tests for API calls, using basic auth
        """
        FNULL = open(os.devnull, 'w')
        if os.path.isfile("basicauth.csv") == False:
            if 'VERBOSE' in locals(): print ("Missing basic auth file, can't run test set.")
            return

        if 'VERBOSE' in locals(): print ("Get appdynamics applications")
        result = subprocess.call("./appdctl.py get applications --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Get appdynamics dashboards")
        result = subprocess.call("./appdctl.py get dashboards --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Get appdynamics settings")
        result = subprocess.call("./appdctl.py get config --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        if 'VERBOSE' in locals(): print ("Get appdynamics users")
        result = subprocess.call("./appdctl.py get users --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        appD_Contexts = Contexts("appdconfig.yaml")
        user = appD_Contexts.get_current_context_user()
        self.assertIsNotNone(user)
        bAuth = BasicAuth(basicAuthFile="basicauth.csv")
        password = bAuth.get_password(user)
        self.assertIsNotNone(password)
        controller = Controller(appD_Contexts,{user:password})
        controller.applications.fetch()
        self.applicationList.extend ( controller.applications.get_application_Name_list(application_type="apmApplications") )
        self.assertNotEqual(len(self.applicationList), 0)

        FNULL.close()


    def test_retrieve_entities(self):
        """
        Integrity tests for retrieving entity data from controller
        """
        FNULL = open(os.devnull, 'w')

        if len(self.applicationList) == 0:
            if 'VERBOSE' in locals(): print ("Last test didn't work well, can't run test set.")
            return

        result = subprocess.call("./appdctl.py get dashboards --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get users --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get config --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get nodes -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get tiers -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get detection-rules -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get businesstransactions -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get backends -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get entrypoints -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get healthrules -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get policies -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get actions -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get schedules -a "+self.applicationList[0]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get healthrule-violations -a "+self.applicationList[0]+" --since=1h --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get snapshots -a "+self.applicationList[0]+" --since=1h --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get errors -a "+self.applicationList[0]+" --since=1h --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get nodes -a "+self.applicationList[0]+","+self.applicationList[1]+" --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py get nodes -A --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        result = subprocess.call("./appdctl.py drain -a sandbox --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        JSON_Content = '{"timezone":"Europe/Belgrade"}'
        result = subprocess.call("./appdctl.py patch schedules -a sandbox -p '"+JSON_Content+"'", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        JSON_Content = '{"timezone":"Europe/Brussels"}'
        result = subprocess.call("./appdctl.py patch schedules -a sandbox -p '"+JSON_Content+"'", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        FNULL.close()

#    def test_import_entities(self):
#        """
#        Integrity tests for importing XML and JSON files containing entity data
#        """
#        if len(self.applicationList) == 0:
#            if 'VERBOSE' in locals(): print ("Last test didn't work well, can't run test set.")
#            return
#
#        with ZipFile('tests.zip', 'r') as testzip:
#            testzip.extractall("/tmp/appdctl.test")
#
#            FNULL = open(os.devnull, 'w')
#            if 'VERBOSE' in locals(): print ("Import XML entities from file")
#            for XML_ENTITY in ['transactiondetection-custom']:
#                if 'VERBOSE' in locals(): print ("### Import "+XML_ENTITY+" ###")
#                fileName = "/tmp/appdctl.test/"+XML_ENTITY+".xml"
#                if os.path.exists(fileName):
#                    result = subprocess.call("./appdctl.py apply -a sandbox -f "+fileName, stdout=FNULL, shell=True)
#                    self.assertEqual(result, 0)
#
#                #unzip -p tests.zip $XML_ENTITY.xml && $SCRIPTPATH/./appdctl.py apply -f $XML_ENTITY.xml
#
#            if 'VERBOSE' in locals(): print ("Import JSON entities from file")
#            for JSON_ENTITY in ['actions-legacy','policies-legacy']: # 'health-rules','dashboards'
#                if 'VERBOSE' in locals(): print ("### Import "+JSON_ENTITY+" ###")
#                fileName = "/tmp/appdctl.test/"+JSON_ENTITY+".json"
#                if os.path.exists(fileName):
#                    result = subprocess.call("./appdctl.py apply -a sandbox -f "+fileName, stdout=FNULL, shell=True)
#                    self.assertEqual(result, 0)
#
#            FNULL.close()


if __name__ == '__main__':
    unittest.main()