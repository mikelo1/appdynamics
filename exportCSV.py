#!/usr/bin/python
import requests
import sys
from datetime import datetime, timedelta
from detectrules import load_detect_rules_XML, fetch_detect_rules, write_detect_rules_CSV
from businesstransactions import load_business_transactions_JSON, fetch_business_transactions, write_business_transactions_CSV
from healthrules import load_health_rules_XML, load_health_rules_XML2, fetch_health_rules, write_health_rules_CSV
from events import load_events_XML, fetch_healthrule_violations, write_events_CSV
from policies import load_policies_JSON, fetch_policies, write_policies_CSV
from snapshots import load_snapshots_JSON, fetch_snapshots, write_snapshots_CSV
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


usage = "usage: %prog [actions|backends|BTs|events|healthrules|policies|detectrules|snapshots] [options]"
epilog= "examples: %prog healthrules -s -p 443 -H ad-financial.saas.appdynamics.com -u johndoe@ad-financial -p s3cr3tp4ss -a 1001"

optParser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
optParser.add_option("-i", "--inputfile", action="store", dest="inFileName",
                  help="read source data from FILE.  If not provided, read from URL", metavar="FILE")
optParser.add_option("-o", "--outfile", action="store", dest="outFileName",
                  help="write report to FILE.  If not provided, output to STDOUT", metavar="FILE")
groupConn = OptionGroup(optParser, "Connection Options")
groupConn.add_option("-u", "--user",
                  action="store", dest="user",
                  help="username@account")
groupConn.add_option("-p", "--password",
                  action="store", dest="password",
                  help="User password")
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
groupQuery = OptionGroup(optParser, "Query range Options")
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
if ENTITY.lower() == "detectrules":
    if options.inFileName:
        load_detect_rules_XML(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_detect_rules(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_detect_rules_CSV(options.outFileName)
elif ENTITY.lower() == "bts":
    if options.inFileName:
        load_business_transactions_JSON(options.inFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        fetch_business_transactions(baseUrl,options.user,options.password,options.application)
    else:
        optParser.error("Missing arguments")
    write_business_transactions_CSV(options.outFileName)
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

else:
    optParser.error("Incorrect operand ["+ENTITY+"]")