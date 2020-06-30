#!/usr/bin/python
import sys
import os.path
import re
from datetime import datetime, timedelta
from appdRESTfulAPI import get_access_token
from appdconfig import get_current_context_serverURL, get_current_context_username
from applications import get_applications, getID, get_application_list, get_applications_from_stream
from dashboards import get_dashboards, get_dashboards_from_stream
from transactiondetection import get_detection_rules, get_detection_rules_from_stream
from businesstransactions import get_business_transactions, get_business_transactions_from_stream
from backends import get_backends, get_backends_from_stream
from healthrules import get_health_rules, get_health_rules_from_stream
from policies import get_policies, get_policies_legacy, get_policies_from_stream
from schedules import get_schedules, get_schedules_from_stream, patch_schedules
from actions import get_actions, get_actions_legacy, get_actions_from_stream
from events import get_healthrule_violations, get_healthrule_violations_from_stream
from snapshots import get_snapshots, get_snapshots_from_stream
from optparse import OptionParser, OptionGroup


def time_to_minutes(string):
  total = 0
  #m = re.match(r"((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?", string)
  m_days  = re.search(r"((?P<days>\d+)d)", string)
  if m_days: 
    total = total + int(m_days.group('days'))*24*60
    if 'DEBUG' in locals(): print "Days: ",m_days.group('days')
 
  m_hours = re.search(r"(?P<hours>\d+)h", string)
  if m_hours: 
    total = total + int(m_hours.group('hours'))*60
    if 'DEBUG' in locals(): print "Hours: ",m_hours.group('hours')

  m_mins  = re.search(r"(?P<mins>\d+)m", string)
  if m_mins: 
    total = total + int(m_mins.group('mins'))
    if 'DEBUG' in locals(): print "Minutes: ",m_mins.group('mins')

  return total

usage = "usage: %prog [get|login|patch] [options]"
epilog= "examples: %prog get applications"

optParser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
optParser.add_option("-o", "--output", action="store", dest="outFormat",
                  help="Output format. One of: json|csv")
optParser.add_option("-f", "--filename", action="store", dest="filename",
                  help="Filename, directory, or URL to files identifying the resource to get from a server.")
optParser.add_option("-p", "--patch", action="store", dest="patchJSON",
                  help="The patch to be applied to the resource JSON file")
groupQuery = OptionGroup(optParser, "Query range options")
groupQuery.add_option("-a", "--applications",
                  action="store", dest="applications",
                  help="Application ID list, separated by commas")
groupQuery.add_option("-A", "--all-applications",
                  action="store_true", default=False, dest="allApplications",
                  help="Aply to all applications in the controller")
groupQuery.add_option("-l", "--selector",
                  action="store", dest="selector",
                  help="Selector to filter on, supports '=', '==', and '!='.(e.g. -l key1=value1,key2=value2)")
groupQuery.add_option("--since",
                  action="store", dest="since",
                  help="Only returns newer than a relative duration like 5s, 2m, or 3h (max 14d)")
groupQuery.add_option("--since-time",
                  action="store", dest="sinceTime",
                  help="Only returns after a specific date (RFC3339)")
optParser.add_option_group(groupQuery)

(options, args) = optParser.parse_args()

if len(args) < 1:
    optParser.error("incorrect number of arguments")

COMMAND = args[0]

if COMMAND.lower() == "login":
  if len(args) < 1:
      optParser.error("incorrect number of arguments")
      exit()
  server = None
  current_server = get_current_context_serverURL()
  if current_server is None: current_server = "https://localhost:8090"
  server = raw_input("AppDynamics Controller server [" + current_server + "]: ")
  if len(server) == 0: server = current_server
  if not server.startswith("http"):
    print "Missing HTTP protocol in the URL. Please try login again."
    exit()

  current_user = get_current_context_username()
  if current_user is None: current_user = "APIClient@customer1"
  username = raw_input("API Client username [" + current_user + "]: ")
  if len(username) == 0: username = current_user
  if not username.find('@'):
    print "Missing account in username. Please try login again."
    exit()

  token=get_access_token(server,username)
  if token is not None:
    print "Login successful. "


elif COMMAND.lower() == "get":
  if options.filename:
    if options.filename == "-":
      data = sys.stdin.read()
    elif os.path.isfile(options.filename):
      data = open(options.filename).read()
    elif options.filename.startswith("http"):
      print os.path.basename(__file__),": URL resources not implemented yet."
      exit()
    else:
      print "Dont' know what to do with ",options.filename
      exit()

    functions = { 'load_policies':get_policies_from_stream,
                  'load_actions':get_actions_from_stream,
                  'load_schedules':get_schedules_from_stream,
                  'load_health-rules':get_health_rules_from_stream,
                  'load_detection-rules':get_detection_rules_from_stream,
                  'load_businesstransactions':get_business_transactions_from_stream,
                  'load_backends':get_backends_from_stream,
                  'load_healthrule-violations':get_healthrule_violations_from_stream,
                  'load_snapshots':get_snapshots_from_stream,
                  'load_applications':get_applications_from_stream,
                  'load_dashboards':get_dashboards_from_stream
                }
    # TODO: output formats
    for key in functions:
      functions[key](data) #,outputFormat=options.outFormat)
    exit()

  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]
  if ENTITY not in ['policies','schedules','actions','health-rules','healthrule-violations',
                    'detection-rules','businesstransactions','applications','snapshots','backends',
                    'dashboards']:
    optParser.error("incorrect entity "+ENTITY)
    exit()

  server = get_current_context_serverURL()
  username = get_current_context_username()
  token=get_access_token(server,username)
  if token is None: exit()

  # make the application list, if applies
  if ENTITY == "applications":
    get_applications(outputFormat=options.outFormat,includeNodes=False)
    exit()
  elif ENTITY == "dashboards":
    get_dashboards(outputFormat=options.outFormat)
    exit()
  elif not options.applications and not options.allApplications:
      optParser.error("Missing application (use -A for all applications)")
      exit()
  elif options.applications:
    applicationList = options.applications.split(',')
    if len(applicationList) > 1: get_application_list()
  else: # if options.allApplications:
    applicationList = get_application_list()

  # make the filters list, if applies
  if options.selector:
    selectors = {}
    for selector in options.selector.split(','):
      selectors.update({selector.split('=')[0]:selector.split('=')[1]})

  functions = { 'get_policies':get_policies_legacy,
                'get_actions':get_actions_legacy,
                'get_schedules':get_schedules,
                'get_health-rules':get_health_rules,
                'get_detection-rules':get_detection_rules,
                'get_businesstransactions':get_business_transactions,
                'get_backends':get_backends,
                'get_healthrule-violations':get_healthrule_violations,
                'get_snapshots':get_snapshots
          }

  for application in applicationList:
    print COMMAND + " " + ENTITY + " " + application + "..."
    appID = getID(application)
    if appID > 0:
      if ENTITY in ['policies','actions','schedules','health-rules','detection-rules','businesstransactions','backends']:
        functions["get_"+ENTITY](appID,outputFormat=options.outFormat)
      elif ENTITY in ['healthrule-violations','snapshots']:
        if options.since is None:
          optParser.error("No duration was specified. (use --since=0 for all events)")
          exit()
        max_duration = 14*24*60
        minutes = time_to_minutes(options.since) if options.since != "0" else max_duration
        if minutes > max_duration: minutes = max_duration
        if minutes == 0:
          optParser.error("Specified duration not correctly formatted. (use --since=<days>d<hours>h<minutes>m format)")
          exit()
        functions["get_"+ENTITY](appID,minutes,selectors,outputFormat=options.outFormat)
    else:
      print "WARN: Application " + application + " does not exist."
  if 'application' not in locals(): print "No application was selected."





elif COMMAND.lower() == "patch":
  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]
  if ENTITY not in ['policies','schedules']:
    optParser.error("incorrect entity "+ENTITY)
    exit()

 # patch_schedules("dummyserver",app_ID=0,source=options.patchJSON)
 # exit()

  server = get_current_context_serverURL()
  username = get_current_context_username()
  token=get_access_token(server,username)
  if token is None: exit()

  if not options.applications and not options.allApplications:
      optParser.error("Missing application (use -A for all applications)")
      exit()
  elif options.applications:
    applicationList = options.applications.split(',')
    if len(applicationList) > 1: get_application_list()
  else: # if options.allApplications:
    applicationList = get_application_list()
  if not options.patchJSON:
    optParser.error("Missing patch JSON.")
    exit()

  for application in applicationList:
    print COMMAND + " " + ENTITY + " " + application + "..."
    appID = getID(application)
    if appID > 0:
      if ENTITY == "schedules":
        patch_schedules(server,app_ID=appID,source=options.patchJSON,token=token)
    else:
      print "WARN: Application " + application + " does not exist."
  if 'application' not in locals(): print "No application was selected."


else:
    optParser.error("Incorrect or not implemented command ["+COMMAND+"]")
