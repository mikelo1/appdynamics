#!/usr/bin/python
import unittest
import os.path
import subprocess
from zipfile import ZipFile

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
        result = subprocess.call("./appdctl.py  config get-contexts ", shell=True)
        self.assertEqual(result, 0)

        print "Create new appdynamics context file and add new context"
        result = subprocess.call("./appdctl.py  config set-context EVO.PRO --controller-url https://evobanco.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco", shell=True)
        self.assertEqual(result, 0)

        print "Append context to appdynamics context file"
        result = subprocess.call("./appdctl.py  config set-context EVO.UAT --controller-url https://evobanco-dev.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco-dev", shell=True)
        self.assertEqual(result, 0)

        print "Add already existing context to appdynamics context file"
        result = subprocess.call("./appdctl.py  config set-context EVO.UAT --controller-url https://evobanco-dev.saas.appdynamics.com:443 --user-API EvoAPIClient@evobanco-dev", shell=True)
        self.assertEqual(result, 0)

        print "Delete existing context on appdynamics context file"
        result = subprocess.call("./appdctl.py  config delete-context EVO.UAT", shell=True)
        self.assertEqual(result, 0)

        print "Delete non existing context on appdynamics context file"
        result = subprocess.call("./appdctl.py  config delete-context nonexist", shell=True)
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
        

if __name__ == '__main__':
    unittest.main()