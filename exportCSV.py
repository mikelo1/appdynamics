#!/usr/bin/python
import sys
import os.path
from datetime import datetime, timedelta
from applications import generate_applications_CSV, getID
from transactiondetection import get_detection_rules, get_detection_rules_from_stream
from businesstransactions import get_business_transactions, get_business_transactions_from_stream
from backends import get_backends, get_backends_from_stream
from healthrules import get_health_rules, get_health_rules_from_stream
from schedules import get_schedules, get_schedules_from_stream
from events import get_healthrule_violations, get_healthrule_violations_from_stream
from policies import get_policies_legacy, get_policies_from_stream
from actions import get_actions_legacy, get_actions_from_stream
from snapshots import get_snapshots, get_snapshots_from_stream
from allothertraffic import get_allothertraffic
from dashboards import get_dashboards, get_dashboards_from_stream
from optparse import OptionParser, OptionGroup

def buildBaseURL(controller,port=None,SSLenabled=None):
    url = "http"
    if SSLenabled:
        url = url + "s"
        if not port:
            port = "443"
    elif not port:
            port = "80"
    #print "Base URL: " + url + "://" + controller + ":" + port
    return url + "://" + controller + ":" + port


usage = "usage: %prog [actions|allothertraffic|applications|backends|business-transactions|dashboards|events|healthrules|schedules|policies|transactiondetection|snapshots] [options]"
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
### Application performance related entities
if ENTITY.lower() == "applications":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_applications_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        get_applications(baseUrl,userName=options.user,password=options.password)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "transactiondetection":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_detection_rules_from_stream(data)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_detection_rules(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "business-transactions":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_business_transactions_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_business_transactions(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "backends":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_backends_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_backends(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "snapshots":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_snapshots_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_snapshots(baseUrl,options.application,"1440",userName=options.user,password=options.password)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "allothertraffic":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_snapshots_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_allothertraffic(baseUrl,options.application,"1440",userName=options.user,password=options.password)
    else:
        optParser.error("Missing arguments")

### Alerts & Respond related entities
elif ENTITY.lower() == "healthrules":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_health_rules_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_health_rules(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "schedules":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_schedules_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_schedules(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "events":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_healthrule_violations_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID < 0:
            options.application=str(appID)
        get_healthrule_violations(baseUrl,options.application,"1440",userName=options.user,password=options.password)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "policies":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_policies_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_policies_legacy(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")
elif ENTITY.lower() == "actions":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_actions_from_stream(data,options.outFileName)
    elif options.user and options.password and options.hostname and options.application:
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        appID=getID(options.application)
        if appID > 0:
            options.application=str(appID)
        get_actions_legacy(baseUrl,userName=options.user,password=options.password,app_ID=options.application,fileName=options.outFileName)
    else:
        optParser.error("Missing arguments")

### Dashboards & Reports related entities
elif ENTITY.lower() == "dashboards":
    if options.inFileName:
        data = open(options.inFileName).read()
        get_dashboards_from_stream(data)
    elif options.user and options.password and options.hostname and options.apiClientName and options.apiClientSecret :
        baseUrl = buildBaseURL(options.hostname,options.port,options.SSLEnabled)
        get_dashboards(baseUrl,userName=options.user,password=options.password)
    else:
        optParser.error("Missing arguments")
else:
    optParser.error("Incorrect operand ["+ENTITY+"]")