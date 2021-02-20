#!/usr/bin/python
import sys
import os.path
import re
from datetime import datetime, timedelta
import time
from appdRESTfulAPI import AppD_Configuration
from applications import applications
from dashboards import dashboards
from rbac import users
from settings import config
from nodes import nodes
from transactiondetection import transactiondetection
from businesstransactions import businesstransactions
from backends import backends, entrypoints
from healthrules import healthrules
from policies import policies
from actions import actions
from schedules import schedules
from events import events
from snapshots import snapshots
from optparse import OptionParser, OptionGroup
import json

entityDict =  { 'applications': applications,
                'dashboards': dashboards,
                'config': config,
                'users': users,
                'nodes': nodes,
                'detection-rules': transactiondetection,
                'businesstransactions': businesstransactions,
                'backends': backends,
                'entrypoints': entrypoints,
                'healthrules': healthrules,
                'policies': policies,
                'actions': actions,
                'schedules': schedules,
                'healthrule-violations': events,
                'snapshots': snapshots,
              }

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


def get_help(COMMAND,SUBCOMMAND=None,output=sys.stdout):
  if output not in [sys.stdout,sys.stderr]: return
  if not SUBCOMMAND:
    optParser.print_help()
  elif COMMAND == "login" and SUBCOMMAND=="help":
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
  elif COMMAND=="get" and SUBCOMMAND=="help":
    sys.stderr.write("Usage: appdctl get [policies|actions|schedules|healthrules|\n" + \
                     "                    detection-rules|businesstransactions|backends|\n" + \
                     "                    healthrule-violations|snapshots|allothertraffic|\n" + \
                     "                    applications|dashboards|nodes] [options]\n\n")
  elif COMMAND=="config" and SUBCOMMAND=="help":
    output.write ("Modify appdconfig files using subcommands like \"appdctl config set current-context my-context\"\n\n" + \
                " The loading order follows these rules:\n\n" + \
                "  1.  If the --kubeconfig flag is set, then only that file is loaded. The flag may only be set once and no merging takes place.\n" + \
                "  2.  If $KUBECONFIG environment variable is set, then it is used as a list of paths (normal path delimiting rules for your system). These paths are merged. When a value is modified, it is modified the file that defines the stanza. When a value is created, it is created in the first file that exists. If no files in the chain exist, then it creates the last file in the list.\n" + \
                "  3.  Otherwise, ${HOME}/.kube/config is used and no merging takes place.\n\n" + \
                "Available Commands:\n" + \
                "  current-context Displays the current-context\n" + \
                "  delete-context  Delete the specified context from the kubeconfig\n" + \
                "  get-contexts    Describe one or many contexts\n" + \
                "  rename-context  Renames a context from the kubeconfig file.\n" + \
                "  set-context     Sets a context entry in kubeconfig\n" + \
                "  set-credentials Sets a user entry in kubeconfig\n" + \
                "  unset           Unsets an individual value in a kubeconfig file\n" + \
                "  use-context     Sets the current-context in a kubeconfig file\n" + \
                "  view            Display merged kubeconfig settings or a specified kubeconfig file\n\n" + \
                "Usage:\n" + \
                "  appdctl config SUBCOMMAND [options]\n\n")

def get_application_list():
    if not options.applications and not options.allApplications:
        optParser.error("Missing application (use -A for all applications)")
        return []
    elif options.applications:
      applications.fetch()
      return [ applications.getAppID(appName) for appName in options.applications.split(',') if applications.getAppID(appName) is not None ]
    else: # if options.allApplications:
      applications.fetch()
      return applications.get_application_ID_list()

usage = "usage: %prog [get|login|update|patch] [options]"
epilog= "examples: %prog get applications"

optParser = OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)
#optParser.add_option("-h", "--help", 
#                  action="store_true", default=False, dest="showHelp",
#                  help="Display help for command")
optParser.add_option("-o", "--output", action="store", dest="outFormat",
                  help="Output format. One of: json|csv")
optParser.add_option("-f", "--filename", action="store", dest="filename",
                  help="Filename, directory, or URL to files identifying the resource to get from a server.")
optParser.add_option("--controller-url", action="store", dest="controllerURL",
                  help="URL of the controller")
optParser.add_option("--user-API", action="store", dest="apiClient",
                  help="API client username")
#optParser.add_option("--password", action="store", dest="password",
#                  help="Basic authentication password")
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
    get_help(COMMAND)
  else:
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
    functions = { 'help':get_help,
                  'view':appD_Config.view,    
                  'get-contexts':appD_Config.get_contexts,
                  'current-context':appD_Config.get_current_context
                }
    functions[SUBCOMMAND]()
  elif SUBCOMMAND in ['use-context','delete-context','set-credentials','get-credentials']:
    if len(args) < 3:
      optParser.error("incorrect number of arguments")
      exit()
    appD_Config = AppD_Configuration()
    functions = { 'use-context':appD_Config.select_context,
                  'delete-context':appD_Config.delete_context,
                  'set-credentials':appD_Config.set_credentials,
                  'get-credentials':appD_Config.get_credentials
                }
    functions[SUBCOMMAND](args[2])
  elif SUBCOMMAND == 'set-context':
    if len(args) < 3:
      optParser.error("incorrect number of arguments")
      exit()
    if not options.controllerURL or not options.apiClient:
      optParser.error("missing controller URL or API username.")
      exit()
    AppD_Configuration().create_context(contextname=args[2],serverURL=options.controllerURL,API_Client=options.apiClient)
  elif SUBCOMMAND == 'rename-context':
    if len(args) < 4:
      optParser.error("incorrect number of arguments")
      exit()
    appD_Config = AppD_Configuration()
    appD_Config.rename_context(args[2],args[3])    
  elif SUBCOMMAND == 'unset':
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

    entityList = [ entity for entity in entityDict if entityDict[entity].verify(streamdata=data) ]
    if 'DEBUG' in locals(): sys.stderr.write("INFO: Found "+options.filename+" to be a "+str(entity)+" file.\n")
    if len(entityList) == 0: exit()
    entityObj = entityDict[entityList[0]]
    entityObj.load(streamdata=data)
    if options.outFormat and options.outFormat == "JSON":
      entityObj.generate_JSON()
    elif not options.outFormat or options.outFormat == "CSV":
      entityObj.generate_CSV()
    exit()

  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]

  if AppD_Configuration().get_current_context(output="None") is None:
    sys.stderr.write("No context is selected.\n")
    exit()

  # create the filters list, if applies
  selectors = {}
  if options.selector:
    for selector in options.selector.split(','):
      selectors.update({selector.split('=')[0]:selector.split('=')[1]})

  if ENTITY == 'help':
    get_help(COMMAND)

  elif ENTITY in ['applications','dashboards','config','users']:
    entityObj = entityDict[ENTITY]
    entityObj.fetch()
    if options.outFormat and options.outFormat == "JSON":
        entityObj.generate_JSON()
    elif not options.outFormat or options.outFormat == "CSV":
        entityObj.generate_CSV()

  elif ENTITY in ['nodes','detection-rules','businesstransactions','backends','entrypoints','healthrules','policies','actions','schedules']:
    current_context = AppD_Configuration().get_current_context(output="None")
    applicationList = get_application_list()
    if len(applicationList) == 0:
      sys.stderr.write("\rget "+ENTITY+" ("+current_context+"): no application was found.\n")
      exit()

    index = 0
    sys.stderr.write("get "+ENTITY+" ("+current_context+")... 0%")
    sys.stderr.flush()
    entityObj = entityDict[ENTITY]
    for appID in applicationList:
        index += 1
        percentage = index*100/len(applicationList)
        sys.stderr.write("\rget "+ENTITY+" ("+current_context+")... " + str(percentage) + "%")
        sys.stderr.flush()
        entityObj.fetch(appID=appID)
    sys.stderr.write("\n")
    if options.outFormat and options.outFormat == "JSON":
        entityObj.generate_JSON(appID_List=applicationList)
    elif not options.outFormat or options.outFormat == "CSV":
        entityObj.generate_CSV(appID_List=applicationList)

  elif ENTITY in ['healthrule-violations','snapshots','allothertraffic']:
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
      AllOtherTraffic_ID = businesstransactions.get_business_transaction_ID(appID=appID,transactionName="_APPDYNAMICS_DEFAULT_TX_")
      if AllOtherTraffic_ID == 0:
        sys.stderr.write("All Other Traffic transaction not found in application "+str(appID)+"\n")
        exit()
      selectors.update({"business-transaction-ids": ''+str(AllOtherTraffic_ID)+''})
      ENTITY="snapshots"

    current_context = AppD_Configuration().get_current_context(output="None")
    applicationList = get_application_list()
    if len(applicationList) == 0:
     sys.stderr.write("\rget "+ENTITY+" ("+current_context+"): no application was found.\n")
     exit()
    index = 0
    sys.stderr.write("get "+ENTITY+" ("+current_context+")... 0%")
    sys.stderr.flush()
    entityObj = entityDict[ENTITY]
    for appID in applicationList:
        index += 1
        percentage = index*100/len(applicationList)
        sys.stderr.write("\rget "+ENTITY+" ("+current_context+")... " + str(percentage) + "%")
        sys.stderr.flush()
        for i in range(minutes,0,-1440): # loop specified minutes in chunks of 1440 minutes (1 day)
            sinceTime = datetime.today()-timedelta(minutes=i)
            sinceEpoch= long(time.mktime(sinceTime.timetuple())*1000)
            entityObj.fetch_after_time(appID=appID,duration="1440",sinceEpoch=sinceEpoch)
    sys.stderr.write("\n")

    if options.outFormat and options.outFormat == "JSON":
        entityObj.generate_JSON(appID_List=applicationList)
    elif not options.outFormat or options.outFormat == "CSV":
        entityObj.generate_CSV(appID_List=applicationList)

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
  elif ENTITY in ['nodes']:
    current_context = AppD_Configuration().get_current_context(output="None")
    applicationList = get_application_list()
    if len(applicationList) == 0:
     sys.stderr.write("\rget "+ENTITY+" ("+current_context+"): no application was found.\n")
     exit()

    entityObj = entityDict[ENTITY]
    entityObj.update(appID_List=applicationList)

  else:
    optParser.error("incorrect entity \""+ENTITY+"\"")

#######################################
############ PATCH COMMAND ############
#######################################
elif COMMAND.lower() == "patch":
  if len(args) < 2:
      optParser.error("incorrect number of arguments")
      exit()

  ENTITY = args[1]

  # create the filters list, if applies
  if options.selector:
    selectors = {}
    for selector in options.selector.split(','):
      selectors.update({selector.split('=')[0]:selector.split('=')[1]})

  if ENTITY == "help":
    sys.stderr.write("Usage: appdctl patch [healthrules|schedules] [options]\n\n")
    exit()
  elif ENTITY in ['healthrules','schedules']:
    current_context = AppD_Configuration().get_current_context(output="None")
    applicationList = get_application_list()
    if len(applicationList) == 0:
     sys.stderr.write("\rget "+ENTITY+" ("+current_context+"): no application was found.\n")
     exit()

    if not options.patchJSON:
      optParser.error("Missing patch JSON.")
    else:
      entityObj = entityDict[ENTITY]
      entityObj.patch(appID_List=applicationList,source=options.patchJSON,selectors=selectors)
  else:
    optParser.error("incorrect entity \""+ENTITY+"\"")

else:
    optParser.error("Incorrect or not implemented command ["+COMMAND+"]")
