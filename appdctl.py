#!/usr/bin/python
import sys
import os.path
import re
from datetime import datetime, timedelta
from appdRESTfulAPI import get_access_token, AppD_Configuration
from rbac import get_users
from settings import get_config
from applications import get_applications, getAppID, get_application_ID_list, get_applications_from_stream
from dashboards import get_dashboards, get_dashboards_from_stream
from nodes import get_nodes, get_nodes_from_stream, update_nodes
from transactiondetection import get_detection_rules, get_detection_rules_from_stream
from businesstransactions import get_business_transactions, get_business_transactions_from_stream, get_business_transaction_ID
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

def get_help(outputFormat=None):
  sys.stderr.write("Usage: appdctl get [policies|actions|schedules|health-rules|\n" + \
                   "                    detection-rules|businesstransactions|backends|\n" + \
                   "                    healthrule-violations|snapshots|allothertraffic|\n" + \
                   "                    applications|dashboards|nodes] [options]\n\n")

usage = "usage: %prog [get|login|update|patch] [options]"
epilog= "examples: %prog get applications"

optParser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
optParser.add_option("-o", "--output", action="store", dest="outFormat",
                  help="Output format. One of: json|csv")
optParser.add_option("-f", "--filename", action="store", dest="filename",
                  help="Filename, directory, or URL to files identifying the resource to get from a server.")
optParser.add_option("--controller-url", action="store", dest="controllerURL",
                  help="URL of the controller")
optParser.add_option("--api-client", action="store", dest="apiClient",
                  help="API client username")
optParser.add_option("--basic-auth-file", action="store", dest="basicAuthFile",
                  help="Basic authentication file")
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
    exit()

COMMAND = args[0]

if COMMAND.lower() == "help":
  sys.stderr.write("Usage: appdctl [get|login|update|patch] [options]\n\n")

#######################################
############ LOGIN COMMAND ############
#######################################
elif COMMAND.lower() == "login":

  if len(args) == 2 and args[1] == "help":
    sys.stderr.write("Login can be done with manual keyboard input or with a basic authentication file in CSV format\n" + \
                     "Either way, if the context doesn't exist in the **appdconfig.yaml** file, it will create a new entry and set it as the current-context.\n\n" + \
                     "To login with a manual input of the credentials, follow these steps:\n" + \
                     "1. $ ./appdctl.py login\n" + \
                     "2. Input your controller full hostname, including protocol and port\n" + \
                     "   i.e.: https://demo1.appdynamics.com:443\n" + \
                     "3. Input the API Client user name\n" + \
                     "4. Input the API Client user password\n\n" + \
                     "In case of having a basic authentication file, follow this syntax:\n" + \
                     "1. $ ./appdctl.py login --api-client <my_APIClient_username>@<my_account_name1> --basic-auth-file <path_to_auth_file>\n\n")
    exit()

  if options.controllerURL and options.apiClient:
    server = options.controllerURL
    username = options.apiClient
  else:
    server = None
    appD_Config = AppD_Configuration()
    current_server = appD_Config.get_current_context_serverURL()
    if current_server is None: current_server = "https://localhost:8090"
    server = raw_input("AppDynamics Controller server [" + current_server + "]: ")
    if len(server) == 0: server = current_server
    if not server.startswith("http"):
      sys.stderr.write("Missing HTTP protocol in the URL. Please try login again.\n")
      exit()
    current_user = appD_Config.get_current_context_username()
    if current_user is None: current_user = "APIClient@customer1"
    username = raw_input("API Client username [" + current_user + "]: ")
    if len(username) == 0: username = current_user
    if not username.find('@'):
      sys.stderr.write("Missing account in username. Please try login again.\n")
      exit()

  if options.basicAuthFile:
    token=get_access_token(server,username,options.basicAuthFile)
  else:
    token=get_access_token(server,username)
  if token is not None:
    print "Login successful. "

#######################################
############ CONFIG COMMAND ###########
#######################################
elif COMMAND.lower() == "config":

  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  SUBCOMMAND = args[1]

  if SUBCOMMAND in ['help','view','get-contexts','current-context']:
    appD_Config = AppD_Configuration()
    functions = { 'help':appD_Config.get_help,
                  'view':appD_Config.view,    
                  'get-contexts':appD_Config.get_contexts,
                  'current-context':appD_Config.get_current_context
                }
    functions[SUBCOMMAND]()
  elif SUBCOMMAND in ['use-context','delete-context']:
    if len(args) < 3:
      optParser.error("incorrect number of arguments")
      exit()
    appD_Config = AppD_Configuration()
    functions = { 'use-context':appD_Config.select_context,
                  'delete-context':appD_Config.delete_context
                }
    functions[SUBCOMMAND](args[2])
  elif SUBCOMMAND == 'set-context':
    if len(args) < 3:
      optParser.error("incorrect number of arguments")
      exit()
    elif options.controllerURL is None or options.apiClient is None:
      optParser.error("Missing controller URL or APIClient user.")
      exit()
    appD_Config = AppD_Configuration()
    appD_Config.create_context(contextname=args[2],serverURL=options.controllerURL,API_Client=options.apiClient)
  elif SUBCOMMAND == 'rename-context':
    if len(args) < 4:
      optParser.error("incorrect number of arguments")
      exit()
    appD_Config = AppD_Configuration()
    appD_Config.rename_context(args[2],args[3])
  elif SUBCOMMAND in ['unset','set-credentials']:
    print "Subcommand " + SUBCOMMAND + " not implemented yet."
  else:
    optParser.error("incorrect subcommand \""+SUBCOMMAND+"\"")

#######################################
############# GET COMMAND #############
#######################################
elif COMMAND.lower() == "get":
  if options.filename:
    if options.filename == "-":
      data = sys.stdin.read()
    elif os.path.isfile(options.filename):
      data = open(options.filename).read()
    elif options.filename.startswith("http"):
      sys.stderr.write(os.path.basename(__file__)+": URL resources not implemented yet.\n")
      exit()
    else:
      sys.stderr.write("Don't know what to do with "+options.filename+"\n")
      exit()

    functions = { 'load_policies':get_policies_from_stream,
                  'load_actions':get_actions_from_stream,
                  'load_schedules':get_schedules_from_stream,
                  'load_health-rules':get_health_rules_from_stream,
                  'load_detection-rules':get_detection_rules_from_stream,
                  'load_businesstransactions':get_business_transactions_from_stream,
                  'load_backends':get_backends_from_stream,
                  'load_nodes':get_nodes_from_stream,
                  'load_healthrule-violations':get_healthrule_violations_from_stream,
                  'load_snapshots':get_snapshots_from_stream,
                  'load_applications':get_applications_from_stream,
                  'load_dashboards':get_dashboards_from_stream
                }
    for key in functions:
      functions[key](data,outputFormat=options.outFormat)
    exit()

  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]

  # create the filters list, if applies
  selectors = {}
  if options.selector:
    for selector in options.selector.split(','):
      selectors.update({selector.split('=')[0]:selector.split('=')[1]})

  functions = { 'get_help':get_help,
                'get_applications':get_applications,
                'get_dashboards':get_dashboards,
                'get_config':get_config,
                'get_users':get_users,
                'get_policies':get_policies_legacy,
                'get_actions':get_actions_legacy,
                'get_schedules':get_schedules,
                'get_health-rules':get_health_rules,
                'get_detection-rules':get_detection_rules,
                'get_businesstransactions':get_business_transactions,
                'get_backends':get_backends,
                'get_nodes':get_nodes,
                'get_healthrule-violations':get_healthrule_violations,
                'get_snapshots':get_snapshots
          }

  if ENTITY in ['help','applications','dashboards','config','users']:
    functions["get_"+ENTITY](outputFormat=options.outFormat)
  elif ENTITY in ['policies','actions','schedules','health-rules','detection-rules','businesstransactions','backends','nodes']:
    if not options.applications and not options.allApplications:
        optParser.error("Missing application (use -A for all applications)")
        exit()
    elif options.applications:
      #applicationList = map(lambda x: str(getID(x)), options.applications.split(',') )
      applicationList = []
      for appName in options.applications.split(','):
        appID = getAppID(appName)
        applicationList.append(appID) if appID is not None else sys.stderr.write("WARN: Application " + appName + " does not exist.\n")
    else: # if options.allApplications:
      applicationList = get_application_ID_list()
    functions["get_"+ENTITY](applicationList,selectors,outputFormat=options.outFormat)
  elif ENTITY in ['healthrule-violations','snapshots','allothertraffic']:
    if not options.applications and not options.allApplications:
        optParser.error("Missing application (use -A for all applications)")
        exit()
    elif options.applications:
      #applicationList = map(lambda x: str(getID(x)), options.applications.split(',') )
      applicationList = []
      for appName in options.applications.split(','):
        appID = getAppID(appName)
        applicationList.append(appID) if appID is not None else sys.stderr.write("WARN: Application " + appName + " does not exist.\n")
    else: # if options.allApplications:
      applicationList = get_application_ID_list()
    if options.since is None:
      optParser.error("No duration was specified. (use --since=0 for all events)")
      exit()
    max_duration = 14*24*60
    minutes = time_to_minutes(options.since) if options.since != "0" else max_duration
    if minutes > max_duration: minutes = max_duration
    if minutes == 0:
      optParser.error("Specified duration not correctly formatted. (use --since=<days>d<hours>h<minutes>m format)")
      exit()
    if ENTITY == "allothertraffic":
      AllOtherTraffic_ID = get_business_transaction_ID(appID,"_APPDYNAMICS_DEFAULT_TX_")
      if AllOtherTraffic_ID == 0:
        sys.stderr.write("All Other Traffic transaction not found in application "+str(appID)+"\n")
        exit()
      selectors.update({"business-transaction-ids": ''+str(AllOtherTraffic_ID)+''})
      ENTITY="snapshots"
    functions["get_"+ENTITY](applicationList,minutes,selectors,outputFormat=options.outFormat)
  else:
    optParser.error("incorrect entity \""+ENTITY+"\"")


#######################################
########### UPDATE COMMAND ############
#######################################
elif COMMAND.lower() == "update":
  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]
  if ENTITY == "help":
    sys.stderr.write("Usage: appdctl update nodes [options]\n\n")
    exit()
  elif ENTITY not in ['nodes']:
    optParser.error("incorrect entity \""+ENTITY+"\"")
    exit()

  if not options.applications and not options.allApplications:
      optParser.error("Missing application (use -A for all applications)")
      exit()
  elif options.applications:
    #applicationList = map(lambda x: str(getID(x)), options.applications.split(',') )
    applicationList = []
    for appName in options.applications.split(','):
      appID = getAppID(appName)
      applicationList.append(appID) if appID is not None else sys.stderr.write("WARN: Application " + appName + " does not exist.\n")
  else: # if options.allApplications:
    applicationList = get_application_ID_list()
  #if not options.patchJSON:
  #  optParser.error("Missing patch JSON.")
  #  exit()

  if 'applicationList' in locals() and len(applicationList)>0 and ENTITY in ['nodes']:
    update_nodes(appID_List=applicationList)
  elif 'applicationList' not in locals() or len(applicationList) == 0:
    sys.stderr.write("No application was selected.\n")


#######################################
############ PATCH COMMAND ############
#######################################
elif COMMAND.lower() == "patch":
  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]
  if ENTITY == "help":
    sys.stderr.write("Usage: appdctl patch [policies|schedules] [options]\n\n")
    exit()
  elif ENTITY not in ['policies','schedules']:
    optParser.error("incorrect entity \""+ENTITY+"\"")
    exit()

  if not options.applications and not options.allApplications:
      optParser.error("Missing application (use -A for all applications)")
      exit()
  elif options.applications:
    #applicationList = map(lambda x: str(getID(x)), options.applications.split(',') )
    applicationList = []
    for appName in options.applications.split(','):
      appID = getAppID(appName)
      applicationList.append(appID) if appID is not None else sys.stderr.write("WARN: Application " + appName + " does not exist.\n")
  else: # if options.allApplications:
    applicationList = get_application_ID_list()
  if not options.patchJSON:
    optParser.error("Missing patch JSON.")
    exit()

  if 'applicationList' in locals() and len(applicationList)>0 and ENTITY in ['schedules']:
    patch_schedules(appID_List=applicationList,source=options.patchJSON)
  elif 'applicationList' not in locals() or len(applicationList) == 0:
    sys.stderr.write("No application was selected.\n")


else:
    optParser.error("Incorrect or not implemented command ["+COMMAND+"]")
