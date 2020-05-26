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

if [ $OPERATION != "export" ] && [ $OPERATION != "import" ] && [ $OPERATION != "update" ]; then
  echo "Syntax: $0 <credentials_yaml_file> <environment> <application> <import|export|update>"; exit
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
  APP_NAME=$4
  curl -s --user "${USER}:${PASS}" https://${HOST}/controller/rest/applications/ | grep "<name>$APP_NAME</name>" -B1 -A1 | grep "<id>" | awk -F"[<>]" '{print $3}'
}

###
 # Import / Export of entities to a SaaS or OnPrem Appdynamics controller.
 # @param HOST Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APP_NAME Name of the application to be imported/exported. i.e.: myApp
 # @param FILEPATH Path where the JSON file is stored. i.e.: ./myService/PROD
 # @param OPERATION The operation to be executed (import/export/update). i.e.: import
###
run_ImpExp() {
  HOST=$1
  USER=$2
  PASS=$3
  APP_NAME=$4
  FILEPATH=$5

  if [ $OPERATION == "export" ] && [ ! -d ${FILEPATH} ]; then mkdir -p ${FILEPATH}; elif [ ! -d ${FILEPATH} ]; then echo "Path does not exist"; return; fi

  APP_ID=$(get_App_ID $HOST $USER $PASS $APP_NAME)
  if [ -z $APP_ID ]; then echo "Could not find the App ID for application $app_name."; exit; fi

  for ENTITY in health-rules actions policies schedules; do
    echo -ne "$OPERATION $ENTITY for application $app_name($APP_ID)... "
    if [ $OPERATION == "export" ]; then
      curl -s -X GET --user "${USER}:${PASS}" https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY -o ${FILEPATH}/${ENTITY}.json
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "import" ]; then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY -H "Content-Type: application/json" -F file=@${FILEPATH}/${ENTITY}.json
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION == "update" ];  then
      if [ ! -f ${FILEPATH}/${ENTITY}.json ]; then echo "missing data file ${ENTITY}.json"; continue; fi
      curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" https://$HOST/controller/alerting/rest/v1/applications/$APP_ID/$ENTITY -H "Content-Type: application/json" -F file=@${FILEPATH}/${ENTITY}.json
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
  for FILE in transactiondetection-auto transactiondetection-custom; do
    ENTITY=`echo $FILE | awk -F[.-] '{print $1}'`
    TYPE=`echo $FILE | awk -F[.-] '{print $2}'`
    echo -ne "$OPERATION $ENTITY for application $app_name($APP_ID)... "
    if [ $OPERATION == "export" ]; then
        curl -s --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -o ${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "import" ]; then        
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
}

###
 # Import / Export of entities to a SaaS or OnPrem Appdynamics controller, using the legacy REST application.
 # @param HOST Full hostname of the Appdynamics controller. i.e.: demo1.appdynamics.com:443
 # @param USER Full username, including account. i.e.: myuser@customer1
 # @param PASS password for the specified user and host. i.e.: mypassword
 # @param APP_NAME Name of the application to be imported/exported. i.e.: myApp
 # @param FILEPATH Path where the JSON file is stored. i.e.: ./myService/PROD
 # @param OPERATION The operation to be executed (import/export/update). i.e.: import
###
run_ImpExp_legacy() {
  HOST=$1
  USER=$2
  PASS=$3
  APP_NAME=$4
  FILEPATH=$5

  if [ $OPERATION == "export" ] && [ ! -d ${FILEPATH} ]; then mkdir -p ${FILEPATH}; elif [ ! -d ${FILEPATH} ]; then echo "Path does not exist"; return; fi

  APP_ID=$(get_App_ID $HOST $USER $PASS $APP_NAME)
  if [ -z $APP_ID ]; then echo "Could not find the App ID for application $app_name."; exit; fi

  for FILE in healthrules.xml actions.json policies.json; do
    ENTITY=`echo $FILE | awk -F. '{print $1}'`
    echo -ne "$OPERATION $ENTITY for application $app_name($APP_ID)... "
    if [ $OPERATION == "export" ]; then
      curl -s -X GET --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID -o ${FILEPATH}/${FILE}
      if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "import" ] && [ -f ${FILEPATH}/${FILE} ]; then
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
    echo -ne "$OPERATION $ENTITY for application $app_name($APP_ID)... "
    if [ $OPERATION == "export" ]; then
        curl -s --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -o ${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo "OK"; fi
    elif [ $OPERATION == "import" ]; then        
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" https://$HOST/controller/$ENTITY/$APP_ID/$TYPE -F file=@${FILEPATH}/${FILE}.xml
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    elif [ $OPERATION == "update" ]; then
        curl -sL -w "%{http_code}" -X POST --user "${USER}:${PASS}" "https://$HOST/controller/$ENTITY/$APP_ID/$TYPE?overwrite=true" -F file=@${FILEPATH}/${FILE}.xml
        echo .
        if [ $? -ne 0 ]; then echo "Something went wrong with the cURL command."; else echo .; fi
    fi
  done
}

USER=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F"[:@]" '{print $2}' | sed 's/\s//g'`
ACCOUNT=`grep $ENVIRONMENT -A6 $CRED_FILE | grep username | awk -F"[:@]" '{print $3}' | sed 's/\s//g'`
PASS=`grep $ENVIRONMENT -A6 $CRED_FILE | grep password | awk -F: '{print $2}' | sed 's/\s//g'`
HOST=`grep $ENVIRONMENT -A6 $CRED_FILE | grep url | awk -F: '{print $3}' | sed 's/\///g'`
#env_name=`echo $ENVIRONMENT | awk -F"." '{print $3}' | tr '[:lower:]' '[:upper:]'`

run_ImpExp_legacy $HOST ${USER}@${ACCOUNT} $PASS $APPLICATION $ENVIRONMENT/$APPLICATION $OPERATION