#/bin/bash

###########################################
### Read credentials from YAML file     ###
###########################################
### Script will read from a YAML file   ###
### with the following format:          ###
### ----------------------------------- ###
### <environment>:                      ###
###     secret:                         ###
###         username: <user>@<account>  ###
###         password: <password>        ###
###         apiclient: <apiClient_name> ###
###         apisecret: <client_secret>  ###
###         url: <base_controller_url>  ###
###########################################

if [ $# -ne 4 ]; then 
  echo "Syntax: $0 <credentials_yaml_file> <environment> <application> <operation>"; exit
fi

CRED_FILE=$1
ENVIRONMENT=$2
APPLICATION=$3
OPERATION=$4

if [ $OPERATION != "retrieve" ] && [ $OPERATION != "create" ] && [ $OPERATION != "update" ]; then
  echo "Syntax: $0 <credentials_yaml_file> <environment> <application> <retrieve|create|update>"; exit
fi

###
 # Get the Application ID for an application name.
 # @param HOST Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APP_NAME Name of the application. i.e.: myApp
 # @return the ID of the specified application name. Nothing if the application was not found.
###
get_App_ID() {
  HOST=$1
  USER=$2
  PASS=$3
  APPLICATION=$4
  response=$(curl -si --user "$USER:$PASS" https://${HOST}/controller/rest/applications/${APPLICATION})
  respCode=$(echo $response | grep -o "^HTTP\/......." | awk '{print $2}')
  if [ "$respCode" == "200" ]; then
    echo $response | grep -o "<id>.*</id>" | awk -F"[<>]" '{print $3}'
  fi
}

###
 # Import / Export of entities to a SaaS or OnPrem Appdynamics controller.
 # @param HOST Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APP_NAME Name of the application to be imported/exported. i.e.: myApp
 # @param FILEPATH Path where the JSON file is stored. i.e.: ./myService/PROD
 # @param OPERATION The operation to be executed (retrieve/create/update). i.e.: retrieve
###
run_ImpExp() {
  HOST=$1
  USER=$2
  PASS=$3
  APP_NAME=$4
  FILEPATH=$5

  if [ $OPERATION == "retrieve" ] && [ ! -d ${FILEPATH} ]; then mkdir -p ${FILEPATH}; elif [ ! -d ${FILEPATH} ]; then echo "Path does not exist"; return; fi

  APP_ID=$(get_App_ID $HOST $USER $PASS $APP_NAME)
  if [ -z $APP_ID ]; then echo "Could not find the App ID for application $APP_NAME."; exit; fi

  for ENTITY in health-rules actions policies schedules; do
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    if [ $OPERATION == "retrieve" ]; then
      curl -s -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                      https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      if [ ! -z "$ENTITY_LIST" ] && [ ! -d ${FILEPATH}/${ENTITY} ]; then mkdir -p ${FILEPATH}/${ENTITY}; fi
      for ELEMENT in $ENTITY_LIST; do
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APP_NAME($APP_ID)... "
        curl -s -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                        https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY/$ELEMENT
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
      done
    elif [ $OPERATION == "create" ]; then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      for ELEMENT in $ENTITY_LIST; do
        if [ ! -f ${FILEPATH}/${ENTITY}/${ELEMENT}.json ]; then echo "missing data file ${ENTITY}/${ELEMENT}.json"; continue; fi
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APP_NAME($APP_ID)... "
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" \
                      -H "Content-Type: application/json" --data=@${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
      done
    elif [ $OPERATION == "update" ];  then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      for ELEMENT in $ENTITY_LIST; do
        if [ ! -f ${FILEPATH}/${ENTITY}/${ELEMENT}.json ]; then echo "missing data file ${ENTITY}/${ELEMENT}.json"; continue; fi
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APP_NAME($APP_ID)... "
        curl -sL -w "%{http_code}" -X PUT --user "${USER}:${PASS}" \
                      -H "Content-Type: application/json" -T ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY/$ELEMENT
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
      done
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom transactiondetection-exclude; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    if [ $OPERATION == "retrieve" ]; then
        curl -s --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -o ${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "create" ]; then
        if [ ! -f ${FILEPATH}/${FILE}.xml ]; then echo "missing data file ${FILE}.xml"; continue; fi
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -F file=@${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION == "update" ]; then
        if [ ! -f ${FILEPATH}/${FILE}.xml ]; then echo "missing data file ${FILE}.xml"; continue; fi
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" "https://$HOST/controller/$ENTITY/$APP_ID/$TYPE?overwrite=true" -F file=@${FILEPATH}/${FILE}.xml
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  if [ $OPERATION == "retrieve" ]; then
    for ENTITY in business-transactions backends; do
      echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
      curl -sG -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                      -d 'output=JSON' \
                      https://$HOST/controller/rest/applications/$APP_ID/$ENTITY
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    done
    ENTITY="healthrule-violations"
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    curl -sG -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOST/controller/rest/applications/$APP_ID/problems/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    ENTITY="request-snapshots"
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    curl -sG -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOST/controller/rest/applications/$APP_ID/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
  fi
}

###
 # Import / Export of entities to a SaaS or OnPrem Appdynamics controller, using the legacy REST application.
 # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API
 # @param HOST Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APP_NAME Name of the application to be imported/exported. i.e.: myApp
 # @param FILEPATH Path where the JSON file is stored. i.e.: ./myService/PROD
 # @param OPERATION The operation to be executed (retrieve/create/update). i.e.: retrieve
###
run_ImpExp_legacy() {
  HOST=$1
  USER=$2
  PASS=$3
  APP_NAME=$4
  FILEPATH=$5

  if [ $OPERATION == "retrieve" ] && [ ! -d ${FILEPATH} ]; then mkdir -p ${FILEPATH}; elif [ ! -d ${FILEPATH} ]; then echo "Path does not exist"; return; fi

  APP_ID=$(get_App_ID $HOST $USER $PASS $APP_NAME)
  if [ -z $APP_ID ]; then echo "Could not find the App ID for application $APP_NAME."; exit; fi

  for FILE in healthrules.xml actions.json policies.json; do
    ENTITY=`echo $FILE | awk -F. '{print $1}'`
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    if [ $OPERATION == "retrieve" ]; then
      curl -s -X GET --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID -o ${FILEPATH}/${FILE}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "create" ] && [ -f ${FILEPATH}/${FILE} ]; then
      curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID -F file=@${FILEPATH}/${FILE}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION == "update" ] && [ ${FILEPATH}/${FILE} ];  then
      curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" "https://$HOST/controller/$ENTITY/$APP_ID?overwrite=true" -F file=@${FILEPATH}/${FILE}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    if [ $OPERATION == "retrieve" ]; then
        curl -s --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -o ${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "create" ]; then
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -F file=@${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION == "update" ]; then
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" "https://$HOST/controller/$ENTITY/$APP_ID/$TYPE?overwrite=true" -F file=@${FILEPATH}/${FILE}.xml
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  if [ $OPERATION == "retrieve" ]; then
    for ENTITY in business-transactions backends; do
      echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
      curl -sG -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                      -d 'output=JSON' \
                      https://$HOST/controller/rest/applications/$APP_ID/$ENTITY
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    done
    ENTITY="healthrule-violations"
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    curl -sG -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOST/controller/rest/applications/$APP_ID/problems/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    ENTITY="request-snapshots"
    echo -ne "$OPERATION $ENTITY for application $APP_NAME($APP_ID)... "
    curl -sG -X GET --user "${USER}:${PASS}" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOST/controller/rest/applications/$APP_ID/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
  fi
}

USER=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F"[:@]" '{print $2}' | sed 's/\s//g'`
ACCOUNT=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F"[:@]" '{print $3}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A6 $CRED_FILE | grep password | awk -F: '{print $2}' | sed 's/\s//g'`
HOST=`grep $ENVIRONMENT -A6 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`
#env_name=`echo $ENVIRONMENT | awk -F"." '{print $3}' | tr '[:lower:]' '[:upper:]'`

run_ImpExp_legacy $HOST ${USER}@${ACCOUNT} $PASS $APPLICATION $ENVIRONMENT/$APPLICATION $OPERATION