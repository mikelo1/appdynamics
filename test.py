#!/usr/bin/python
import unittest
import os.path
import subprocess
from zipfile import ZipFile
from appdConfig import AppD_Configuration, BasicAuth
from appd_API import Controller

class TestSum(unittest.TestCase):
    def test_contexts(self):
        """
        Integrity tests for contexts
        """
        if os.path.isfile("appdconfig.yaml"):
            answer = ""
            while answer not in ["y", "n"]:
                answer = raw_input("Do you want to replace the file appdconfig.yaml [Y/N]?").lower()
            if answer == "y": os.remove("appdconfig.yaml")
            else: return

        print "Try to get appdynamics context file, when file doesn't exist"
        result = subprocess.call("./appdctl.py config get-contexts ", shell=True)
        self.assertEqual(result, 0)

        print "Create new appdynamics context file and add new context"
        result = subprocess.call("./appdctl.py config set-context EVO.PRO --controller-url https://evobanco.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco", shell=True)
        self.assertEqual(result, 0)

        print "Append context to appdynamics context file"
        result = subprocess.call("./appdctl.py config set-context EVO.UAT --controller-url https://evobanco-dev.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco-dev", shell=True)
        self.assertEqual(result, 0)
        result = subprocess.call("./appdctl.py config set-context localhost --controller-url http://localhost:8090 --user-API APIClient@customer1", shell=True)
        self.assertEqual(result, 0)

        print "Add already existing context to appdynamics context file"
        result = subprocess.call("./appdctl.py config set-context EVO.UAT --controller-url https://evobanco-dev.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco-dev", shell=True)
        self.assertEqual(result, 0)

        print "Get contexts from appdynamics context file"
        result = subprocess.call("./appdctl.py config get-contexts", shell=True)
        self.assertEqual(result, 0)

        print "Use existing context on appdynamics context file"
        result = subprocess.call("./appdctl.py config use-context EVO.UAT", shell=True)
        self.assertEqual(result, 0)

        print "Use non existing context on appdynamics context file"
        result = subprocess.call("./appdctl.py config use-context nonexist", shell=True)
        self.assertEqual(result, 0)

        print "Delete existing context on appdynamics context file"
        result = subprocess.call("./appdctl.py config delete-context localhost", shell=True)
        self.assertEqual(result, 0)

        print "Delete non existing context on appdynamics context file"
        result = subprocess.call("./appdctl.py config delete-context nonexist", shell=True)
        self.assertEqual(result, 0)

    def test_entities_load(self):
        """
        Integrity tests for loading XML and JSON files containing entity data
        """
        with ZipFile('tests.zip', 'r') as testzip:

            FNULL = open(os.devnull, 'w')
            print "Get XML entities from file"
            for XML_ENTITY in ['healthrules','transactiondetection-custom']:
                print "### Get "+XML_ENTITY+" ###"
                with testzip.open(XML_ENTITY+".xml") as testfile:
                    filedata = testfile.read()
                    filePipe = subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE)
                    result = subprocess.call("./appdctl.py  get -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
                    self.assertEqual(result, 0)
                    filePipe.stdout.close()

                #unzip -p tests.zip $XML_ENTITY.xml | $SCRIPTPATH/./appdctl.py  get -f -

            print "Get JSON entities from file"
            for JSON_ENTITY in ['actions','actions-legacy','health-rules','policies','policies-legacy','schedules', \
                                 'allothertraffic','backends','business-transactions', \
                                 'applications','dashboards','healthrule-violations','request-snapshots']:
                print "### Get "+JSON_ENTITY+" ###"
                with testzip.open(JSON_ENTITY+".json") as testfile:
                    filedata = testfile.read()
                    filePipe = subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE)
                    result = subprocess.call("./appdctl.py  get -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
                    self.assertEqual(result, 0)
                    filePipe = subprocess.Popen(["echo",filedata],stdout=subprocess.PIPE)
                    result = subprocess.call("./appdctl.py  get -o JSON -f - ", stdin=filePipe.stdout, stdout=FNULL, shell=True)
                    self.assertEqual(result, 0)
                    filePipe.stdout.close()

    def test_entities_basicauth(self):
        """
        Integrity tests for API entity export calls, using basic auth
        """
        FNULL = open(os.devnull, 'w')
        if os.path.isfile("basicauth.csv") == False:
            print "Missing basic auth file, can't run test set."
            return

        print "Get appdynamics applications"
        result = subprocess.call("./appdctl.py get applications --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        print "Get appdynamics dashboards"
        result = subprocess.call("./appdctl.py get dashboards --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        print "Get appdynamics settings"
        result = subprocess.call("./appdctl.py get config --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        print "Get appdynamics users"
        result = subprocess.call("./appdctl.py get users --basic-auth-file=basicauth.csv ", stdout=FNULL, shell=True)
        self.assertEqual(result, 0)

        appD_Config = AppD_Configuration()
        user = appD_Config.get_current_context_user()
        self.assertIsNotNone(user)
        bAuth = BasicAuth(basicAuthFile="basicauth.csv")
        password = bAuth.get_password(user)
        self.assertIsNotNone(password)
        controller = Controller(appD_Config,{user:password})
        controller.applications.fetch()
        applicationList = controller.applications.get_application_ID_list()
        self.assertNotEqual(len(applicationList), 0)
        print applicationList



if __name__ == '__main__':
    unittest.main()