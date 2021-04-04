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
 # Check if an application exists in the controller.
 # @param HOST Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APP_NAME Name of the application. i.e.: myApp
 # @return true if application name exists. False if the application was not found.
###
application_exists() {
  HOST=$1
  USER=$2
  PASS=$3
  APPLICATION=$4
    App_List=$(curl -s --user "${USER}:${PASS}" https://${HOST}/controller/rest/applications/ | grep -o "<name>[^<>]*</name>" | awk -F"[<>]" '{print $3}')
    if [ $? -ne 0 ]; then
       echo "Something went wrong with the cURL command. Exiting..."
       return 1
    fi
    for app in $App_List; do
       if [ "$app" = "$APPLICATION" ]; then return 0; fi
    done
    return 1
}
#if application_exists $APPLICATION ; then echo "Application exists"; else echo "Application does NOT exist."; fi

###
 # Fetch access token from a controller.
 # @param HOSTNAME Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param APICLIENT Full username, including account. i.e.: myuser@customer1
 # @param APISECRET password for the specified user and host. i.e.: mypassword
 # @return the access token string. Empty string if there was a problem getting the access token.
###
echo_appd_access_token() {
  HOSTNAME=$1
  APICLIENT=$2
  APISECRET=$3
  # https://docs.appdynamics.com/display/PRO45/API+Clients#APIClients-using-the-access-token
  # https://docs.appdynamics.com/display/PRO45/API+Clients
  curl -s --user "$APICLIENT:$APISECRET" \
          -X POST -H "Content-Type: application/vnd.appd.cntrl+protobuf;v=1" \
          -d "grant_type=client_credentials&client_id=$APICLIENT&client_secret=$APISECRET" \
          "https://${HOSTNAME}/controller/api/oauth/access_token" | grep -o "\"access_token\": \"[^\"]*\"," | awk -F\" '{print $4}'
}

###
 # Get the Application ID for an application name.
 # @param HOSTNAME Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @return the ID of the specified application name. Nothing if the application was not found.
###
get_App_ID() {
  HOSTNAME=$1
  ACCESS_TOKEN=$2
  response=$(curl -si -H "Authorization:Bearer $ACCESS_TOKEN" \
          https://${HOSTNAME}/controller/rest/applications/${APPLICATION})
  respCode=$(echo $response | grep -o "^HTTP\/......." | awk '{print $2}')
  if [ "$respCode" = "200" ]; then
    echo $response | grep -o "<id>.*</id>" | awk -F"[<>]" '{print $3}'
  fi
}

###
 # Import / Export of entities to a SaaS or OnPrem Appdynamics controller.
 # @param HOSTNAME Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @param APP_ID Application ID number to be imported/exported.
###
run_ImpExp() {
  HOSTNAME=$1
  ACCESS_TOKEN=$2
  APP_ID=$3
  FILEPATH=$ENVIRONMENT/$APPLICATION

  if [ ! -d ${FILEPATH} ]; then
   if [ "$OPERATION" == "retrieve" ]; then mkdir -p ${FILEPATH}; else echo "Path ${FILEPATH} does not exist"; return; fi
  fi

  for ENTITY in health-rules actions policies schedules; do
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
      curl -s -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                      https://$HOSTNAME/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      if [ ! -z "$ENTITY_LIST" ] && [ ! -d ${FILEPATH}/${ENTITY} ]; then mkdir -p ${FILEPATH}/${ENTITY}; fi
      for ELEMENT in $ENTITY_LIST; do
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APPLICATION($APP_ID)... "
        curl -s -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      https://$HOSTNAME/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY/$ELEMENT
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
      done
    elif [ $OPERATION = "create" ]; then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      for ELEMENT in $ENTITY_LIST; do
        if [ ! -f ${FILEPATH}/${ENTITY}/${ELEMENT}.json ]; then echo "missing data file ${ENTITY}/${ELEMENT}.json"; continue; fi
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APPLICATION($APP_ID)... "
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" \
                      -H "Content-Type: application/json" --data=@${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      https://$HOSTNAME/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
      done
    elif [ $OPERATION = "update" ];  then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      ENTITY_LIST=$(grep -o "\"id\":[0-9]*" ${FILEPATH}/${ENTITY}.json | awk -F: '{print $2}')
      for ELEMENT in $ENTITY_LIST; do
        if [ ! -f ${FILEPATH}/${ENTITY}/${ELEMENT}.json ]; then echo "missing data file ${ENTITY}/${ELEMENT}.json"; continue; fi
        echo -ne "$OPERATION $ENTITY $ELEMENT for application $APPLICATION($APP_ID)... "
        curl -sL -w "%{http_code}" -X PUT -H "Authorization:Bearer $ACCESS_TOKEN" \
                      -H "Content-Type: application/json" -T ${FILEPATH}/${ENTITY}/${ELEMENT}.json \
                      https://$HOSTNAME/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY/$ELEMENT
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
      done
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom transactiondetection-exclude; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
        curl -s -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${FILE}.xml \
                      https://$HOSTNAME/controller/$ENTITY/$APP_ID/$TYPE
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION = "create" ]; then
        if [ ! -f ${FILEPATH}/${FILE}.xml ]; then echo "missing data file ${FILE}.xml"; continue; fi
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" -F file=@${FILEPATH}/${FILE}.xml \
                      https://$HOSTNAME/controller/$ENTITY/$APP_ID/$TYPE
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION = "update" ]; then
        if [ ! -f ${FILEPATH}/${FILE}.xml ]; then echo "missing data file ${FILE}.xml"; continue; fi
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" -F file=@${FILEPATH}/${FILE}.xml \
                      "https://$HOSTNAME/controller/$ENTITY/$APP_ID/$TYPE?overwrite=true"
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  if [ $OPERATION = "retrieve" ]; then
    for ENTITY in business-transactions backends; do
      echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
      curl -sG -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                      -d 'output=JSON' \
                      https://$HOSTNAME/controller/rest/applications/$APP_ID/$ENTITY
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    done
    ENTITY="healthrule-violations"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOSTNAME/controller/rest/applications/$APP_ID/problems/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    ENTITY="request-snapshots"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOSTNAME/controller/rest/applications/$APP_ID/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
  fi
}

###
 # Import / Export of entities to a SaaS or OnPrem Appdynamics controller, using the legacy REST application.
 # https://docs.appdynamics.com/display/PRO44/Configuration+Import+and+Export+API
 # @param HOSTNAME Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param ACCESS_TOKEN Authentication access token.
 # @param APP_ID Application ID number to be imported/exported.
###
run_ImpExp_legacy() {
  HOSTNAME=$1
  ACCESS_TOKEN=$2
  APP_ID=$3
  FILEPATH=$ENVIRONMENT/$APPLICATION

  if [ ! -d ${FILEPATH} ]; then
   if [ "$OPERATION" == "retrieve" ]; then mkdir -p ${FILEPATH}; else echo "Path ${FILEPATH} does not exist"; return; fi
  fi

  for FILE in healthrules.xml actions.json policies.json; do
    ENTITY=`echo $FILE | awk -F. '{print $1}'`
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
      curl -s -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${FILE} \
                      https://$HOSTNAME/controller/$ENTITY/$APP_ID
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION = "create" ] && [ -f ${FILEPATH}/${FILE} ]; then
      curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" -F file=@${FILEPATH}/${FILE} \
                      https://$HOSTNAME/controller/$ENTITY/$APP_ID
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION = "update" ] && [ ${FILEPATH}/${FILE} ];  then
      curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" -F file=@${FILEPATH}/${FILE} \
                      "https://$HOSTNAME/controller/$ENTITY/$APP_ID?overwrite=true"
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    if [ $OPERATION = "retrieve" ]; then
        curl -s -H "Authorization:Bearer $ACCESS_TOKEN" \
                      https://$HOSTNAME/controller/$ENTITY/$APP_ID/$TYPE -o ${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION = "create" ]; then
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" \
                      https://$HOSTNAME/controller/$ENTITY/$APP_ID/$TYPE -F file=@${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION = "update" ]; then
        curl -sL -w "%{http_code}" -X POST -H "Authorization:Bearer $ACCESS_TOKEN" \
                      "https://$HOSTNAME/controller/$ENTITY/$APP_ID/$TYPE?overwrite=true" -F file=@${FILEPATH}/${FILE}.xml
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  if [ $OPERATION = "retrieve" ]; then
    for ENTITY in business-transactions backends; do
      echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
      curl -sG -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                      -d 'output=JSON' \
                      https://$HOSTNAME/controller/rest/applications/$APP_ID/$ENTITY
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    done
    ENTITY="healthrule-violations"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOSTNAME/controller/rest/applications/$APP_ID/problems/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    ENTITY="request-snapshots"
    echo -ne "$OPERATION $ENTITY for application $APPLICATION($APP_ID)... "
    curl -sG -X GET -H "Authorization:Bearer $ACCESS_TOKEN" -o ${FILEPATH}/${ENTITY}.json \
                    -d 'time-range-type=BEFORE_NOW' -d 'duration-in-mins=1440' -d 'output=JSON' \
                      https://$HOSTNAME/controller/rest/applications/$APP_ID/$ENTITY
    if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
  fi
}

USER=`grep $ENVIRONMENT -A6 $CRED_FILE | grep apiclient | awk -F"[:@]" '{print $2}' | sed 's/\s//g'`
ACCOUNT=`grep $ENVIRONMENT -A6 $CRED_FILE | grep apiclient | awk -F"[:@]" '{print $3}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A6 $CRED_FILE | grep apisecret | awk -F: '{print $2}' | sed 's/\s//g' | base64 -d`
HOST=`grep $ENVIRONMENT -A6 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`
#env_name=`echo $ENVIRONMENT | awk -F"." '{print $3}' | tr '[:lower:]' '[:upper:]'`
#echo $USER@$ACCOUNT $PASS $HOST $ENVIRONMENT/$APPLICATION

ACCESS_TOKEN=$(echo_appd_access_token $HOST ${USER}@${ACCOUNT} $PASS)
APP_ID=$(get_App_ID $HOST $ACCESS_TOKEN)
if [ -z $APP_ID ]; then echo "Could not find the App ID for application $APP_NAME."; exit; fi

run_ImpExp_legacy $HOST ${ACCESS_TOKEN} $APP_ID