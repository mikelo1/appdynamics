import json
import sys
from .entities import AppEntity

class BusinessTransactionDict(AppEntity):

    def __init__(self,controller):
        super(BusinessTransactionDict,self).__init__(controller)
        self['CSVfields'] = {   'name':           self.__str_businesstransaction_name,
                                'entryPointType': self.__str_businesstransaction_entryPointType,
                                'tierName':       self.__str_businesstransaction_tierName }

    def __str_businesstransaction_name(self,BT):
        return BT['name'] if sys.version_info[0] >= 3 else BT['name'].encode('ASCII', 'ignore')

    def __str_businesstransaction_entryPointType(self,BT):
        return BT['entryPointType']

    def __str_businesstransaction_tierName(self,BT):
        return BT['tierName']


    ###### FROM HERE PUBLIC FUNCTIONS ######


    def get_business_transaction_ID(self,appID,transactionName):
        """
        Get the ID for a business transaction name.
        :param appID: the ID of the application
        :param transactionName: the name of the business transaction
        :returns: the ID of the specified business transaction name. Zero if no business transaction was found.
        """
        if appID > 0 and self['entities'] is not None and appID in self['entities']:
            for transaction in self['entities'][appID]:
                if transaction['name'] == transactionName:
                    return transaction['id']
        return 0

    def get_business_transaction_name(self,appID,transactionID):
        """
        Get the name for a business transaction ID. Fetch business transaction data if not loaded yet.
        :param appID: the ID of the application
        :param transactionID: the ID of the business transaction
        :returns: the name of the specified business transaction ID. Empty string if no business transaction was found.
        """
        if appID <= 0 or transactionID <= 0: return ""
        if self['entities'] is None or appID not in self['entities']:
            if not self.fetch(appID=appID):
                return ""
        for transaction in self['entities'][appID]:
            if transaction['id'] == transactionID:
                return transaction['name']
        return ""


    def get_business_transaction_nameList(self,appID):
        """
        Get the list of business transaction names for an application.
        :param appID: the ID of the application
        :returns: the list of business application names of the specified application ID. None if no business transaction was found.
        """
        if appID > 0 and self['entities'] is not None and appID in self['entities']:
            return [transaction['name'] for transaction in self['entities'][appID] ]
        return None
