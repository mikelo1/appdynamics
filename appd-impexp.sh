#/bin/bash

###############################################################
### Kind: Config                                            ###
### contexts:                                               ###
### - context:                                              ###
###     server: <protocol>://<hostname>:<port>              ###
###     user: <apiClient_name>@<account>/<hostname>:<port>  ###
###   name: <context_name>                                  ###
### current-context: <context_name>                         ###
### users:                                                  ###
### - name: <apiClient_name>@<account>/<hostname>:<port>    ###
###   user:                                                 ###
###     password: <base64_password>                         ###
###############################################################


# source: https://github.com/mrbaseman/parse_yaml.git
# parse_yaml provides a bash function that allows parsing simple YAML files.
# The output is shell code that defines shell variables which contain the parsed values.
# bash doesn't support multidimensional arrays. Therefore a separate variable
# is created for each value, and the name of the variable consists of the names of
# all levels in the yaml file, glued together with a separator character which defaults to _.
function parse_yaml {
   local prefix=$2
   local s='[[:space:]-]*' w='[a-zA-Z0-9_-]*' fs=$(echo @|tr @ '\034')
   sed  -e "s|{}||g" $1 | \
   sed -ne "s|^\($s\):|\1|" \
        -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"           |
   awk -F$fs '{
      indent = length($1)/2;
      if (substr($1,length($1)-2,2) == "- ") vname[indent-1]=( substr( vname[indent-1], 0, length(vname[indent-1]) - length(idx[indent-1]) ) ) (++idx[indent-1])
      vname[indent] = $2;
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])(".")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, vname[indent], $3);
      }
   }'
}

###
 # Check if an application exists in the controller.
 # @param BASE_URL The consistent part of the Appdynamics controller web address. i.e.: https://demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APPLICATION Name or ID of the application. i.e.: myApp
 # @return true if application name exists. False if the application was not found.
###
application_exists() {
  BASE_URL=$1
  USER=$2
  PASS=$3
  APPLICATION=$4
    App_List=$(curl -s --user "${USER}:${PASS}" ${BASE_URL}/controller/rest/applications/)
    if [ $? -ne 0 ]; then
       echo "Something went wrong with the cURL command. Exiting..."
       return 1
    fi

    # Try first with Application name
    for appName in $(echo $App_List | grep -o "<name>[^<>]*</name>" | awk -F"[<>]" '{print $3}'); do
       if [ "$appName" = "$APPLICATION" ]; then return 0; fi
    done
    # Try also with Application ID
    for appID in $(echo $App_List | grep -o "<id>[^<>]*</id>" | awk -F"[<>]" '{print $3}'); do
       if [ "$appID" = "$APPLICATION" ]; then return 0; fi
    done

    return 1
}


###
 # Fetch access token from a controller.
 # @param BASE_URL The consistent part of the Appdynamics controller web address. i.e.: https://demo1.appdynamics.com:443
 # @param APICLIENT Full username, including account. i.e.: myuser@customer1
 # @param APISECRET password for the specified user and host. i.e.: mypassword
 # @return the access token string. Empty string if there was a problem getting the access token.
###
echo_appd_access_token() {
  BASE_URL=$1
  APICLIENT=$2
  APISECRET=$3
  # https://docs.appdynamics.com/display/PRO45/API+Clients#APIClients-using-the-access-token
  # https://docs.appdynamics.com/display/PRO45/API+Clients
  curl -s --user "${APICLIENT}:${APISECRET}" \
          -X POST -H "Content-Type: application/vnd.appd.cntrl+protobuf;v=1" \
          -d "grant_type=client_credentials&client_id=${APICLIENT}&client_secret=${APISECRET}" \
          "${BASE_URL}/controller/api/oauth/access_token" | grep -o "\"access_token\": \"[^\"]*\"," | awk -F\" '{print $4}'
}

###
 # Get the Application ID for an application name.
 # @param BASE_URL The consistent part of the Appdynamics controller web address. i.e.: https://demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @return the ID of the specified application name. Nothing if the application was not found.
###
get_App_ID() {
  BASE_URL=$1
  ACCESS_TOKEN=$2
  response=$(curl -si -H "Authorization:Bearer ${ACCESS_TOKEN}" ${BASE_URL}/controller/rest/applications/${APPLICATION})
  respCode=$(echo $response | grep -o "^HTTP\/......." | awk '{print $2}')
  if [ "$respCode" = "200" ]; then
    echo $response | grep -o "<id>.*</id>" | awk -F"[<>]" '{print $3}'
  fi
}

###
 # Import / Export of application entities to a SaaS or OnPrem Appdynamics controller.
 # @param BASE_URL The consistent part of the Appdynamics controller web address. i.e.: https://demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @param APP_ID Application ID number to be imported/exported.
 # @param FILEPATH Path where to import/export files.
###
run_ImpExp() {
  BASE_URL=$1
  ACCESS_TOKEN=$2
  APP_ID=$3
  FILEPATH=$4

  if [ ! -d ${FILEPATH} ]; then
   if [ "$OPERATION" == "retrieve" ]; then mkdir -p ${FILEPATH}; else echo "Path ${FILEPATH} does not exist"; return; fi
  fi

  for ENTITY in health-rules actions policies schedules; do
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
      curl -s -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                      ${BASE_URL}/controller/alerting/rest/v1/applications/${APP_ID}/${ENTITY}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      if [ ! -z "$ENTITY_LIST" ] && [ ! -d ${FILEPATH}/${ENTITY} ]; then mkdir -p ${FILEPATH}/${ENTITY}; fi
      for ELEMENT in $ENTITY_LIST; do
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APPLICATION($APP_ID)... "
        curl -s -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      ${BASE_URL}/controller/alerting/rest/v1/applications/${APP_ID}/${ENTITY}/${ELEMENT}
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
      done
    elif [ $OPERATION = "create" ]; then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      for ELEMENT in $ENTITY_LIST; do
        if [ ! -f ${FILEPATH}/${ENTITY}/${ELEMENT}.json ]; then echo "missing data file ${ENTITY}/${ELEMENT}.json"; continue; fi
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APPLICATION($APP_ID)... "
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" \
                      -H "Content-Type: application/json" -T ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      ${BASE_URL}/controller/alerting/rest/v1/applications/${APP_ID}/${ENTITY}
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
      done
    elif [ $OPERATION = "update" ];  then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      for ELEMENT in $ENTITY_LIST; do
        if [ ! -f ${FILEPATH}/${ENTITY}/${ELEMENT}.json ]; then echo "missing data file ${ENTITY}/${ELEMENT}.json"; continue; fi
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APPLICATION($APP_ID)... "
        curl -sL -w "%{http_code}" -X PUT -H "Authorization:Bearer ${ACCESS_TOKEN}" \
                      -H "Content-Type: application/json" -T ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      ${BASE_URL}/controller/alerting/rest/v1/applications/${APP_ID}/${ENTITY}/${ELEMENT}
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
      done
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom transactiondetection-exclude; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
        curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${FILE}.xml \
                      ${BASE_URL}/controller/${ENTITY}/${APP_ID}/${TYPE}
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION = "create" ]; then
        if [ ! -f ${FILEPATH}/${FILE}.xml ]; then echo "missing data file ${FILE}.xml"; continue; fi
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" -F file=@${FILEPATH}/${FILE}.xml \
                      ${BASE_URL}/controller/${ENTITY}/${APP_ID}/${TYPE}
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION = "update" ]; then
        if [ ! -f ${FILEPATH}/${FILE}.xml ]; then echo "missing data file ${FILE}.xml"; continue; fi
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" -F file=@${FILEPATH}/${FILE}.xml \
                      "${BASE_URL}/controller/${ENTITY}/${APP_ID}/${TYPE}?overwrite=true"
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  if [ $OPERATION = "retrieve" ]; then
    for ENTITY in business-transactions backends; do
      echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
      curl -sG -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                      -d 'output=JSON' \
                      ${BASE_URL}/controller/rest/applications/${APP_ID}/${ENTITY}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    done

    ENTITY="healthrule-violations"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      ${BASE_URL}/controller/rest/applications/${APP_ID}/problems/${ENTITY}
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi

    ENTITY="request-snapshots"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      ${BASE_URL}/controller/rest/applications/${APP_ID}/${ENTITY}
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
  fi
}

###
 # Import / Export of application entities to a SaaS or OnPrem Appdynamics controller, using the legacy REST application.
 # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API
 # @param BASE_URL The consistent part of the Appdynamics controller web address. i.e.: https://demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @param APP_ID Application ID number to be imported/exported.
 # @param FILEPATH Path where to import/export files.
###
run_ImpExp_legacy() {
  BASE_URL=$1
  ACCESS_TOKEN=$2
  APP_ID=$3
  FILEPATH=$4

  if [ ! -d ${FILEPATH} ]; then
   if [ "$OPERATION" == "retrieve" ]; then mkdir -p ${FILEPATH}; else echo "Path ${FILEPATH} does not exist"; return; fi
  fi

  for FILE in healthrules.xml actions.json policies.json; do
    ENTITY=`echo $FILE | awk -F. '{print $1}'`
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
      curl -s -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${FILE} \
                      ${BASE_URL}/controller/${ENTITY}/${APP_ID}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION = "create" ] && [ -f ${FILEPATH}/${FILE} ]; then
      curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" -F file=@${FILEPATH}/${FILE} \
                      ${BASE_URL}/controller/${ENTITY}/${APP_ID}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION = "update" ] && [ ${FILEPATH}/${FILE} ];  then
      curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" -F file=@${FILEPATH}/${FILE} \
                      "${BASE_URL}/controller/${ENTITY}/${APP_ID}?overwrite=true"
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
        curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" \
                      ${BASE_URL}/controller/${ENTITY}/${APP_ID}/${TYPE} -o ${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION = "create" ]; then
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" \
                      ${BASE_URL}/controller/${ENTITY}/${APP_ID}/${TYPE} -F file=@${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION = "update" ]; then
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer ${ACCESS_TOKEN}" \
                      "${BASE_URL}/controller/${ENTITY}/${APP_ID}/${TYPE}?overwrite=true" -F file=@${FILEPATH}/${FILE}.xml
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  if [ $OPERATION = "retrieve" ]; then
    for ENTITY in business-transactions backends; do
      echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
      curl -sG -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                      -d 'output=JSON' \
                      ${BASE_URL}/controller/rest/applications/${APP_ID}/${ENTITY}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    done
    ENTITY="healthrule-violations"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      ${BASE_URL}/controller/rest/applications/${APP_ID}/problems/${ENTITY}
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    ENTITY="request-snapshots"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer ${ACCESS_TOKEN}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      ${BASE_URL}/controller/rest/applications/${APP_ID}/${ENTITY}
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
  fi
}


###
 # Export of entities to a SaaS or OnPrem Appdynamics controller, using the legacy REST application.
 # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API
 # @param BASE_URL The consistent part of the Appdynamics controller web address. i.e.: https://demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @param FILEPATH Path where to import/export files.
###
run_ImpExp_controller() {
  BASE_URL=$1
  ACCESS_TOKEN=$2
  FILEPATH=$3

  if [ $OPERATION != "retrieve" ]; then echo "ERROR: Only retrieve operation permitted."; exit 1; fi

  GREEN='\033[0;32m'
  NC='\033[0m' # No Color

  #CONTROLLER_VERSION
  echo -ne "AppDynamics Controller version: "
  curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" "${BASE_URL}/controller/rest/configuration?name=schema.version&output=JSON" | grep value | awk '{print $2}' | sed -e 's/"//g'
  if [ $? -ne 0 ]; then
    echo "Something went wrong with the cURL command. Exiting..." ; exit
  fi

  #APPLICATION_LIST
  curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" "${BASE_URL}/controller/restui/applicationManagerUiBean/getApplicationsAllTypes" -o ${FILEPATH}/applications.json
  if [ $? -ne 0 ]; then
    echo "Something went wrong with the cURL command. Exiting..." ; exit
  else
    echo -e "Application list downloaded to file ${GREEN}${FILEPATH}/applications.json${NC}"
  fi

  #CONFIGURATION
  curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" "${BASE_URL}/controller/rest/configuration?output=JSON" -o ${FILEPATH}/config.json
  if [ $? -ne 0 ]; then
    echo "Something went wrong with the cURL command. Exiting..."; exit
  else
    echo -e "Controller configuration downloaded to file ${GREEN}${FILEPATH}/config.json${NC}"
  fi

  #CONTROLLER AUDIT HISTORY
  end_time=`date +%FT%T.000-0000 -d "30 days ago"`
  start_time=`date +%FT%T.000-0000 -d "31 days ago"`
  curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" "${BASE_URL}/controller/ControllerAuditHistory?startTime=${start_time}&endTime=${end_time}" -o ${FILEPATH}/audit_log.json
  if [ $? -ne 0 ]; then
    echo "Something went wrong with the cURL command. Exiting..."; exit
  else
    echo -e "Controller audit history downloaded to file ${GREEN}${FILEPATH}/audit_log.json${NC}"
  fi

  #EMAIL TEMPLATES
  curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" ${BASE_URL}/controller/actiontemplate/email -o ${FILEPATH}/emailTemplates.json
  if [ $? -ne 0 ]; then
    echo "Something went wrong with the cURL command. Exiting..." ; exit
  else
    echo -e "Controller email templates downloaded to file ${GREEN}${FILEPATH}/emailTemplates.json${NC}"
  fi

  #DASHBOARD_LIST
  DASHBOARDS_BY_TYPE=`curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" \
                              "${BASE_URL}/controller/restui/dashboards/getAllDashboardsByType/false"`
  if [ $? -ne 0 ]; then
    echo "Something went wrong with the cURL command. Exiting..."; exit
  else
    echo $DASHBOARDS_BY_TYPE > ${FILEPATH}/dashboards.json
    echo -e "Dashboard list downloaded to file ${GREEN}${FILEPATH}/dashboards.json${NC}"
  fi

  #DASHBOARD_EXPORT_ALL
   if [ $? ] && [ DASHBOARDS_BY_TYPE != "Failed to authenticate: invalid access token." ]; then
    DASHBOARD_LIST=`echo ${DASHBOARDS_BY_TYPE} | grep -o "\"id\" : [0-9]*," | sed -e 's/[id:",]//g'`
    for DASHBOARD_ID in $DASHBOARD_LIST; do
      curl -s -H "Authorization:Bearer ${ACCESS_TOKEN}" "${BASE_URL}/controller/CustomDashboardImportExportServlet?dashboardId=${DASHBOARD_ID}" -o ${FILEPATH}/dashboards/${DASHBOARD_ID}.json
      if [ $? -ne 0 ]; then
        echo "Something went wrong with the cURL command. Exiting..."; exit
      else
        echo -e "Dashboard ${DASHBOARD_ID} downloaded to file ${GREEN}${FILEPATH}/dashboards/${DASHBOARD_ID}.json${NC}"
      fi
    done
  else
    echo $DASHBOARDS_BY_TYPE
  fi
}

### Read arguments ###

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -a|--application)
      APPLICATION="$2"
      shift # past argument
      shift # past value
      ;;
    -c|--context)
      CONTEXT="$2"
      shift # past argument
      shift # past value
      ;;
    -f|--file)
      CONF_FILE="$2"
      shift # past argument
      shift # past value
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters
OPERATION=${POSITIONAL_ARGS[0]}


### Verify arguments ###

if [ -z ${CONF_FILE} ] && [ -f "appdconfig.yaml" ]; then
  echo "INFO: No configuration file specified. Using default file appdconfig.yaml."; CONF_FILE="appdconfig.yaml"
elif [ -z ${CONF_FILE} ]; then
  echo "ERROR: No configuration file was specified."; exit 1
fi
if [ -z ${APPLICATION} ]; then
  echo "INFO: No application was specified, retrieve operation only allowed."; OPERATION="retrieve"
elif [ "${OPERATION}" != "retrieve" ] && [ "${OPERATION}" != "create" ] && [ "${OPERATION}" != "update" ]; then
  echo "Syntax: $0 [-f|--file <configuration_file>] [-c|--context <context-name>] [-a|--application <application_name>] <retrieve|create|update>"; exit
fi


### Parse YAML file and get connection details from it ###

CONFIG=$(parse_yaml ${CONF_FILE})

if [ -z ${CONTEXT} ]; then
  CONTEXT=`echo "${CONFIG}" | grep -o "current-context[^ ]*" | awk -F= '{print $2}' | sed 's/\s//g'`
  if [ -z $? ] || [ -z ${CONTEXT} ]; then echo "No current context defined in config YAML file"; exit; fi
fi

CONTEXT_INDEX=`echo "${CONFIG}" | grep "contexts[0-9]*.name=$CONTEXT" | awk -F"." '{print $1}'`
if [ -z $? ]; then echo "No current context definition found in config YAML file"; exit; fi

USER=`echo "${CONFIG}" | grep "$CONTEXT_INDEX.context.user[^ ]*" | awk -F[=] '{print $2}'`
if [ -z $? ]; then echo "No user definition found in config YAML file"; exit; fi

USER_INDEX=`echo "${CONFIG}" | grep "user[0-9]*.name=$USER" | awk -F"." '{print $1}'`
if [ -z $? ]; then echo "No user definition found in config YAML file"; exit; fi

USERNAME=`echo $USER | awk -F[/] '{print $1}' | sed 's/\"//g'`
if [ -z $? ]; then echo "User definition not correctly formatted in config YAML file"; exit; fi

PASS=`echo "${CONFIG}" | grep "$USER_INDEX.user.password[^ ]*" | awk -F[=] '{print $2}' | sed 's/\"//g' | base64 -d`
if [ -z $? ]; then echo "No user password found in config YAML file"; exit; fi

URL=`echo "${CONFIG}" | grep "$CONTEXT_INDEX.context.server[^ ]*" | awk -F[=] '{print $2}' | sed 's/\"//g'`
if [ -z $? ]; then echo "No URL definition found in config YAML file"; exit; fi


### Get access token and Application name ###

ACCESS_TOKEN=$(echo_appd_access_token ${URL} ${USERNAME} ${PASS})
APP_ID=$(get_App_ID ${URL} ${ACCESS_TOKEN})
if [ -z $APP_ID ]; then echo "Could not find the App ID for application $APP_NAME."; exit; fi
#if application_exists $APPLICATION ; then echo "Application exists"; else echo "Application does NOT exist."; fi

### Run Imp/Exp function ###
if [ -z ${APPLICATION} ]; then
  run_ImpExp_controller ${URL} ${ACCESS_TOKEN} $(echo "${CONTEXT}" | sed 's/\"//g')
else
  run_ImpExp_legacy ${URL} ${ACCESS_TOKEN} ${APP_ID} $(echo "${CONTEXT}" | sed 's/\"//g')/${APPLICATION}
fi
