#!/usr/bin/python
import requests
import sys
import os.path
from datetime import datetime, timedelta
from transactiondetection import load_transactiondetection_XML, fetch_transactiondetection, write_transactiondetection_CSV
from businesstransactions import load_business_transactions_JSON, fetch_business_transactions, write_business_transactions_CSV
from backends import load_backends_JSON, fetch_backends, write_backends_CSV
from healthrules import load_health_rules_XML, fetch_health_rules, write_health_rules_CSV
from events import load_events_XML, fetch_healthrule_violations, write_events_CSV
from policies import load_policies_JSON, fetch_policies, write_policies_CSV
from actions import load_actions_JSON, fetch_actions, write_actions_CSV
from snapshots import load_snapshots_JSON, fetch_snapshots, write_snapshots_CSV
from allothertraffic import load_allothertraffic_JSON, fetch_allothertraffic, write_allothertraffic_CSV
from accesstoken import fetch_access_token
from optparse import OptionParser, OptionGroup

def buildBaseURL(controller,port=None,SSLenabled=None):
    url = "http"
    if SSLenabled:
        url = url + "s"
        if not port:
            port = "443"
    elif not port:
            port = "80"
    #print "Base URL: " + url + "://" + controller + ":" + port + "/controller/"
    return url + "://" + controller + ":" + port + "/controller/"


usage = "usage: %prog [actions|backends|business-transactions|events|healthrules|policies|transactiondetection|snapshots] [options]"
epilog= "examples: %prog healthrules -s -p 443 -H ad-financial.saas.appdynamics.com -u johndoe@ad-financial -p s3cr3tp4ss -a 1001"

optParser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
optParser.add_option("-i", "--inputfile", action="store", dest="inFileName",
                  help="read source data from FILE.  If not provided, read from URL", metavar="FILE")
optParser.add_option("-o", "--outfile", action="store", dest="outFileName",
                  help="write report to FILE.  If not provided, output to STDOUT", metavar="FILE")
groupConn = OptionGroup(optParser, "Connection options")
groupConn.add_option("-H", "--hostname",
                  action="store", dest="hostname",
                  help="Controller hostname")
groupConn.add_option("-P", "--port",
                  action="store", dest="port",
                  help="Controller port")
groupConn.add_option("-s", "--ssl",
                  action="store_true", dest="SSLEnabled",
                  help="Use SSL")
optParser.add_option_group(groupConn)
groupAuth = OptionGroup(optParser, "Authentication options")
groupAuth.add_option("-u", "--user",
                  action="store", dest="user",
                  help="username@account")
groupAuth.add_option("-p", "--password",
                  action="store", dest="password",
                  help="User password")
groupAuth.add_option("--api-client-name",
                  action="store", dest="apiClientName",
                  help="API Client name")
groupAuth.add_option("--api-client-secret",
                  action="store", dest="apiClientSecret",
                  help="API Client secret")
optParser.add_option_group(groupAuth)
groupQuery = OptionGroup(optParser, "Query range options")
groupQuery.add_option("-a", "--application",
                  action="store", dest="application",
                  help="Application ID")
groupQuery.add_option("-t", "--timerange",
                  action="store", dest="timerange",
                  help="Time range (1day..14day)")
optParser.add_option_group(groupQuery)

(options, args) = optParser.parse_args()

if len(args) != 1:
    optParser.error("incorrect number of arguments")

ENTITY = args[0]
if ENTITY.lower() == "transactiondetection":
    if options.inFileName:
        load_transactiondetection_XML(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_transactiondetection(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_transactiondetection_CSV(options.outFileName)
elif ENTITY.lower() == "business-transactions":
    if options.inFileName:
        load_business_transactions_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_business_transactions(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_business_transactions_CSV(options.outFileName)
elif ENTITY.lower() == "backends":
    if options.inFileName:
        load_backends_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_backends(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_backends_CSV(options.outFileName)
elif ENTITY.lower() == "healthrules":
    if options.inFileName:
        load_health_rules_XML(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_health_rules(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_health_rules_CSV(options.outFileName)
elif ENTITY.lower() == "events":
    if options.inFileName:
        load_events_XML(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        for i in range(2,0,-1): # loop latest 2 days in chunks of 1 day
            for retry in range(1,4):
                root = fetch_healthrule_violations(baseUrl,options.user,options.password,options.application, \
                                                    "AFTER_TIME","1440",datetime.today()-timedelta(days=i)) # fetch 1 day of data
                if root is not None:
                    break
                elif retry < 3:
                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
                else:
                    print "Giving up."
                    exit (1)
    else:
        optParser.error("Missing arguments")
    write_events_CSV(options.outFileName)
elif ENTITY.lower() == "policies":
    if options.inFileName:
        load_policies_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_policies(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_policies_CSV(options.outFileName)
elif ENTITY.lower() == "actions":
    if options.inFileName:
        head_tail = os.path.split(options.inFileName)
        policiesXMLFile=head_tail[0] + "/policies.json"
        if os.path.exists(policiesXMLFile):
            load_policies_JSON(policiesXMLFile)
        else:
            print ("File "+policiesXMLFile+" not found.")
        load_actions_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_actions(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_actions_CSV(options.outFileName)
elif ENTITY.lower() == "snapshots":
    if options.inFileName:
        load_snapshots_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        for i in range(3,48,3): # loop latest 48 hours in chunks of 3 hours
            for retry in range(1,4):
                data_chunck = fetch_snapshots(baseUrl,options.user,options.password,options.application, \
                                                "AFTER_TIME","180",datetime.today()-timedelta(hours=i)) # fetch 3 hours of data
                if data_chunck is not None:
                    break
                elif retry < 3:
                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
                else:
                    print "Giving up."
                    exit (1)
    else:
        optParser.error("Missing arguments")
    write_snapshots_CSV(options.outFileName)
elif ENTITY.lower() == "allothertraffic":
    if options.inFileName:
        load_allothertraffic_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_business_transactions(baseUrl,options.user,options.password,options.application)
        for i in range(3,48,3): # loop latest 48 hours in chunks of 3 hours
            for retry in range(1,4):
                data_chunck = fetch_allothertraffic(baseUrl,options.user,options.password,options.application, \
                                                "AFTER_TIME","180",datetime.today()-timedelta(hours=i)) # fetch 3 hours of data
                if data_chunck is not None:
                    break
                elif retry < 3:
                    print "Failed to fetch healthrule violations. Retrying (",retry," of 3)..."
                else:
                    print "Giving up."
                    exit (1)
    else:
        optParser.error("Missing arguments")
    write_allothertraffic_CSV(options.outFileName)
elif ENTITY.lower() == "accesstoken":
    if options.user and options.password and options.hostname and options.apiClientName and options.apiClientSecret :
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_access_token(baseUrl,options.user,options.password,options.apiClientName,options.apiClientSecret)
else:
    optParser.error("Incorrect operand ["+ENTITY+"]")