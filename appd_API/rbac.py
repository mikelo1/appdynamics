import json
import sys
from .entities import ControllerEntity

class RBACDict(ControllerEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        #self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.fetch_users_extended,
        #                            'fetchByID': self.controller.RESTfulAPI.fetch_user_by_ID }
        self.entityKeywords = ["providerUniqueName"]
        self.CSVfields = {  'Name':   self.__str_user_name,
                            'Email':  self.__str_user_email,
                            'Roles':  self.__str_user_roles,
                            'Groups': self.__str_user_groups }


    def __str_user_name(self,user):
        return user['name']

    def __str_user_email(self,user):
        return user['email'] if 'email' in user else None

    def __str_user_roles(self,user):
        return json.dumps(user['roles']) if 'roles' in user else None

    def __str_user_groups(self,user):
        return json.dumps(user['groups']) if 'groups' in user else None


    ###### FROM HERE PUBLIC FUNCTIONS ######


class AccountDict(ControllerEntity):

    def __init__(self,controller):
        self.entityDict = dict()
        self.controller = controller
        #self.entityAPIFunctions = { 'fetch': self.controller.RESTfulAPI.get_account_usage_summary }
        self.entityKeywords = ["usageType"]#["machine-agent","dot-net","nodejs","sim-machine-agent","iot","netviz","synthetic","database","java","mobile-rum","browser-rum","apm"]
        self.CSVfields = {  'Provisioned_Licenses':  self.__str_account_provisioned,
                            'Peak_Usage':  self.__str_account_usage,
                            'expirationDate': self.__str_account_expiration }

    def __str_account_provisioned(self,account):
        return account['numOfProvisionedLicense']

    def __str_account_usage(self,account):
        return account['peakUsage']

    def __str_account_expiration(self,account):
        import datetime
        ts_epoch = int(account['expirationDate'])/1000 if account['expirationDate'] is not None else 0
        return datetime.datetime.fromtimestamp(ts_epoch).strftime('%Y-%m-%d %H:%M:%S') if ts_epoch > 0 else ""


    ###### FROM HERE PUBLIC FUNCTIONS ######

    def generate_CSV(self,fileName=None):
        """
        Generate CSV output from applications data
        :param fileName: output file name
        :returns: None
        """
        import csv
        if fileName is not None:
            try:
                csvfile = open(fileName, 'w')
            except:
                sys.stderr.write("Could not open output file " + fileName + ".")
                return (-1)
        else:
            csvfile = sys.stdout

        fieldnames = ['type']
        fieldnames.extend([ name for name in self.CSVfields ])
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')

        for licenseType in self.entityDict:
            # Check if data belongs to a recognized application type
            if type(self.entityDict[licenseType]) is dict and self.entityDict[licenseType]['isLicensed'] is not None:
                licenseList = [self.entityDict[licenseType]]
            elif type(self.entityDict[licenseType]) is list:
                licenseList = self.entityDict[licenseType]
            else: continue

            if 'header_is_printed' not in locals():
                filewriter.writeheader()
                header_is_printed=True

            for license in licenseList:
                row = {"type":licenseType}
                row.update({ name: self.CSVfields[name](license) for name in self.CSVfields })
                try:
                    filewriter.writerow(row)
                except (TypeError,ValueError) as error:
                    sys.stderr.write("generate_CSV: "+str(error)+"\n")
                    if fileName is not None: csvfile.close()
                    exit(1)
        if fileName is not None: csvfile.close()